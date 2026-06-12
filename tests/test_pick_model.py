import importlib.util
import json
import sys
from pathlib import Path

import pytest


SCRIPT_PATH = Path("scripts/pick_model.py")


@pytest.fixture()
def pick_model_module():
    spec = importlib.util.spec_from_file_location("pick_model", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def snapshot_path(tmp_path):
    path = tmp_path / "chutes-models.json"
    path.write_text(
        json.dumps(
            {
                "fetched_at": "2026-06-11T00:00:00Z",
                "data": [
                    {
                        "id": "cheap-chat",
                        "context_length": 131072,
                        "pricing": {"prompt": 0.1, "completion": 0.2},
                        "supported_features": [],
                        "input_modalities": ["text"],
                        "confidential_compute": True,
                    },
                    {
                        "id": "tool-agent",
                        "context_length": 262144,
                        "pricing": {"prompt": 0.2, "completion": 0.6},
                        "supported_features": ["tools", "structured_outputs", "reasoning"],
                        "input_modalities": ["text", "image"],
                        "confidential_compute": True,
                    },
                    {
                        "id": "expensive-agent",
                        "context_length": 262144,
                        "pricing": {"prompt": 1.0, "completion": 2.0},
                        "supported_features": ["tools", "reasoning"],
                        "input_modalities": ["text"],
                        "confidential_compute": True,
                    },
                ],
            }
        )
    )
    return path


def test_fetch_models_offline_uses_snapshot(pick_model_module, snapshot_path, monkeypatch):
    monkeypatch.setattr(pick_model_module, "SNAPSHOT", snapshot_path)

    models, source = pick_model_module.fetch_models(offline=True)

    assert source == "snapshot 2026-06-11T00:00:00Z"
    assert [model["id"] for model in models] == ["cheap-chat", "tool-agent", "expensive-agent"]


def test_cli_emits_latency_pool_for_agentic_task(pick_model_module, snapshot_path, monkeypatch, capsys):
    monkeypatch.setattr(pick_model_module, "SNAPSHOT", snapshot_path)
    monkeypatch.setattr(
        sys,
        "argv",
        ["pick_model.py", "--offline", "--task", "agentic", "--routing", "latency"],
    )

    assert pick_model_module.main() == 0
    output = capsys.readouterr().out

    assert "tool-agent" in output
    assert 'model="tool-agent,expensive-agent:latency"' in output


def test_cli_filters_by_modality_and_json(pick_model_module, snapshot_path, monkeypatch, capsys):
    monkeypatch.setattr(pick_model_module, "SNAPSHOT", snapshot_path)
    monkeypatch.setattr(
        sys,
        "argv",
        ["pick_model.py", "--offline", "--modality", "image", "--json"],
    )

    assert pick_model_module.main() == 0
    output = json.loads(capsys.readouterr().out)

    assert [pick["id"] for pick in output["picks"]] == ["tool-agent"]
