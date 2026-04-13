import importlib.util
import json
from pathlib import Path

import pytest


SCRIPT_PATH = Path("scripts/run_evals.py")


@pytest.fixture()
def run_evals_module():
    spec = importlib.util.spec_from_file_location("run_evals", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_load_evals_returns_named_eval_set(run_evals_module, tmp_path):
    module = run_evals_module
    path = tmp_path / "evals.json"
    path.write_text(json.dumps({
        "skill_name": "chutes-ai",
        "evals": [{"id": 1, "prompt": "hi", "expected_output": "hello"}],
    }))

    payload = module.load_evals(path)

    assert payload["skill_name"] == "chutes-ai"
    assert payload["evals"][0]["id"] == 1


def test_validate_evals_rejects_duplicate_ids(run_evals_module):
    module = run_evals_module
    payload = {
        "skill_name": "chutes-ai",
        "evals": [
            {"id": 1, "prompt": "a", "expected_output": "x"},
            {"id": 1, "prompt": "b", "expected_output": "y"},
        ],
    }

    with pytest.raises(ValueError, match="Duplicate eval id"):
        module.validate_evals(payload)


def test_build_summary_reports_eval_count(run_evals_module):
    module = run_evals_module
    payload = {
        "skill_name": "chutes-ai",
        "evals": [
            {"id": 1, "prompt": "a", "expected_output": "x"},
            {"id": 2, "prompt": "b", "expected_output": "y"},
        ],
    }

    summary = module.build_summary(payload)

    assert summary["skill_name"] == "chutes-ai"
    assert summary["eval_count"] == 2
    assert summary["ids"] == [1, 2]


def test_render_markdown_contains_prompt_and_expected_output(run_evals_module):
    module = run_evals_module
    payload = {
        "skill_name": "chutes-ai",
        "evals": [
            {"id": 7, "prompt": "How do I list models?", "expected_output": "Use /v1/models"},
        ],
    }

    rendered = module.render_markdown(payload)

    assert "# Eval Pack: chutes-ai" in rendered
    assert "## Eval 7" in rendered
    assert "How do I list models?" in rendered
    assert "Use /v1/models" in rendered
