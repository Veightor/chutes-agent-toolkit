import importlib.util
import json
from pathlib import Path

import pytest


SCRIPT_PATH = Path("scripts/build_agent_site_pack.py")


@pytest.fixture()
def site_pack_module():
    spec = importlib.util.spec_from_file_location("build_agent_site_pack", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def good_payload():
    return {
        "version": 1,
        "updated_at": "2026-06-11",
        "use_cases": [
            {
                "id": "codex",
                "title": "Run Codex on Chutes",
                "agent": "Codex",
                "audience": "Coding agents",
                "value_prop": "Use Chutes for OpenAI-compatible coding-agent inference.",
                "setup_path": "Set CHUTES_API_KEY and the Chutes base URL.",
                "demo_prompt": "Review this repository.",
                "proof_points": ["Bearer auth works with standard OpenAI-compatible clients."],
                "links": [{"label": "Codex guide", "path": "other-agents/codex/README.md"}],
                "status": "flagship_guide",
            },
            {
                "id": "hermes",
                "title": "Run Hermes on Chutes",
                "agent": "Hermes",
                "audience": "Hermes users",
                "value_prop": "Use Chutes as a named provider.",
                "setup_path": "Set providers.chutes in config.",
                "demo_prompt": "Configure Hermes.",
                "proof_points": ["Hermes supports OpenAI-compatible providers."],
                "links": [{"label": "Hermes guide", "path": "other-agents/hermes/README.md"}],
                "status": "active",
            },
        ],
    }


def test_validate_payload_accepts_good_fixture(site_pack_module, good_payload):
    site_pack_module.validate_payload(good_payload)


def test_default_payload_validates(site_pack_module):
    payload = site_pack_module.load_payload()

    assert payload["version"] == 1
    assert any(case["id"] == "codex" for case in payload["use_cases"])


def test_validate_payload_rejects_missing_required_field(site_pack_module, good_payload):
    del good_payload["use_cases"][0]["setup_path"]

    with pytest.raises(ValueError, match="missing required field: setup_path"):
        site_pack_module.validate_payload(good_payload)


def test_filter_payload_focus_codex(site_pack_module, good_payload):
    filtered = site_pack_module.filter_payload(good_payload, focus="codex")

    assert [case["id"] for case in filtered["use_cases"]] == ["codex"]
    assert [case["id"] for case in good_payload["use_cases"]] == ["codex", "hermes"]


def test_render_markdown_contains_headings_and_links(site_pack_module, good_payload):
    rendered = site_pack_module.render_markdown(site_pack_module.filter_payload(good_payload, focus="codex"))

    assert "# Chutes Agent Site Pack" in rendered
    assert "## Run Codex on Chutes" in rendered
    assert "[Codex guide](other-agents/codex/README.md)" in rendered


def test_render_json_is_stable(site_pack_module, good_payload):
    rendered = site_pack_module.render_json(site_pack_module.filter_payload(good_payload, focus="codex"))

    assert rendered == json.dumps(
        {
            "updated_at": "2026-06-11",
            "use_cases": [good_payload["use_cases"][0]],
            "version": 1,
        },
        indent=2,
        sort_keys=True,
    ) + "\n"
