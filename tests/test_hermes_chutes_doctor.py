import importlib.util
import sys
from pathlib import Path


SCRIPT_PATH = Path("scripts/hermes_chutes_doctor.py")


def load_module():
    spec = importlib.util.spec_from_file_location("hermes_chutes_doctor", SCRIPT_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_mask_secret_never_exposes_raw_key():
    module = load_module()
    raw = "cpk_super_secret_token_value"

    masked = module.mask_secret(raw)

    assert masked == "cpk_...[redacted]"
    assert raw not in masked
    assert "secret_token" not in masked


def test_parse_env_file_accepts_export_and_quotes(tmp_path):
    module = load_module()
    env_file = tmp_path / ".env"
    env_file.write_text("# comment\nexport CHUTES_API_KEY='cpk_test_value'\n")

    assert module.parse_env_file(env_file) == "cpk_test_value"


def test_summarize_models_counts_hermes_relevant_capabilities():
    module = load_module()
    models = [
        {
            "id": "cheap-tools",
            "confidential_compute": True,
            "supported_features": ["tools", "json_mode", "structured_outputs"],
            "input_modalities": ["text"],
            "context_length": 4096,
            "pricing": {"prompt": 0.02, "completion": 0.10},
        },
        {
            "id": "vision-long",
            "confidential_compute": True,
            "supported_features": ["tools", "reasoning"],
            "input_modalities": ["text", "image"],
            "context_length": 262144,
            "pricing": {"prompt": 0.40, "completion": 2.00},
        },
        {
            "id": "metadata-null",
            "confidential_compute": True,
            "supported_features": None,
            "input_modalities": None,
            "context_length": None,
            "pricing": {},
        },
    ]

    summary = module.summarize_models(models)

    assert summary["count"] == 3
    assert summary["tee_count"] == 3
    assert summary["all_tee"] is True
    assert summary["tools_count"] == 2
    assert summary["json_mode_count"] == 1
    assert summary["structured_outputs_count"] == 1
    assert summary["vision_count"] == 1
    assert summary["cheapest_tool_model"] == "cheap-tools"
    assert summary["longest_context_model"] == "vision-long"
    assert summary["longest_context"] == "262k"


def test_render_hermes_config_uses_env_var_and_live_direct_model_without_secret():
    module = load_module()

    config = module.render_hermes_config(include_research=True, direct_model="cheap-tools")

    assert "key_env: CHUTES_API_KEY" in config
    assert "cpk_" not in config
    assert "apiKey" not in config
    assert "https://llm.chutes.ai/v1" in config
    assert "https://research-data-opt-in-proxy.chutes.ai/v1" in config
    assert '"cheap-tools": {}' in config
    assert "provider: custom:chutes" in config
