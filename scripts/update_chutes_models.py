#!/usr/bin/env python3
"""Refresh Chutes model snapshots from the public /v1/models endpoint.

This script intentionally uses only Python's standard library and does not send
any authentication headers. It writes:

- data/chutes-models.json: normalized raw-ish snapshot for machines.
- docs/known-models.md: human model reference.
- plugins/chutes-ai/skills/chutes-ai/references/known-models.md: skill mirror.

Run from the repository root:

    python3 scripts/update_chutes_models.py
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ENDPOINT = "https://llm.chutes.ai/v1/models"
REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = REPO_ROOT / "data" / "chutes-models.json"
DOC_PATH = REPO_ROOT / "docs" / "known-models.md"
SKILL_REF_PATH = REPO_ROOT / "plugins" / "chutes-ai" / "skills" / "chutes-ai" / "references" / "known-models.md"


def fetch_models(timeout: int = 30) -> dict[str, Any]:
    req = urllib.request.Request(
        ENDPOINT,
        headers={
            "Accept": "application/json",
            "User-Agent": "chutes-agent-toolkit-model-refresh/1.0",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:  # noqa: S310 - fixed public HTTPS endpoint
        if response.status != 200:
            raise RuntimeError(f"{ENDPOINT} returned HTTP {response.status}")
        return json.load(response)


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def num(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fmt_price(value: Any) -> str:
    parsed = num(value)
    if parsed is None:
        return "—"
    if parsed == 0:
        return "0"
    return f"{parsed:.6g}"


def fmt_context(model: dict[str, Any]) -> str:
    ctx = model.get("context_length") or model.get("max_model_len")
    parsed = num(ctx)
    if parsed is None:
        return "—"
    if parsed >= 1000:
        rounded = int(round(parsed / 1000))
        return f"{rounded}k"
    return str(int(parsed))


def modalities(model: dict[str, Any]) -> str:
    inputs = [str(x) for x in as_list(model.get("input_modalities"))]
    outputs = [str(x) for x in as_list(model.get("output_modalities"))]
    merged: list[str] = []
    for item in inputs + outputs:
        if item and item not in merged:
            merged.append(item)
    return "+".join(merged) if merged else "text"


def feature_text(model: dict[str, Any]) -> str:
    features = [str(x) for x in as_list(model.get("supported_features"))]
    return ", ".join(features) if features else "—"


def sort_key(model: dict[str, Any]) -> tuple[float, float, str]:
    pricing = model.get("pricing") or {}
    out = num(pricing.get("completion"))
    inp = num(pricing.get("prompt"))
    # Expensive/frontier models first in the reference table; name as stable tie-breaker.
    return (-(out if out is not None else -1), -(inp if inp is not None else -1), str(model.get("id", "")))


def cheapest(models: list[dict[str, Any]], predicate=lambda _m: True, limit: int = 3) -> list[dict[str, Any]]:
    candidates = []
    for model in models:
        if not predicate(model):
            continue
        pricing = model.get("pricing") or {}
        prompt = num(pricing.get("prompt"))
        completion = num(pricing.get("completion"))
        if prompt is None and completion is None:
            continue
        candidates.append((prompt if prompt is not None else 9999, completion if completion is not None else 9999, str(model.get("id", "")), model))
    return [entry[-1] for entry in sorted(candidates)[:limit]]


def largest_context(models: list[dict[str, Any]], limit: int = 3) -> list[dict[str, Any]]:
    candidates = []
    for model in models:
        ctx = num(model.get("context_length") or model.get("max_model_len"))
        if ctx is not None:
            candidates.append((-ctx, str(model.get("id", "")), model))
    return [entry[-1] for entry in sorted(candidates)[:limit]]


def model_line(model: dict[str, Any]) -> str:
    pricing = model.get("pricing") or {}
    return f"- `{model.get('id')}` (${fmt_price(pricing.get('prompt'))}/${fmt_price(pricing.get('completion'))}, context {fmt_context(model)}, {modalities(model)})"


def render_markdown(models: list[dict[str, Any]], fetched_at: datetime) -> str:
    date = fetched_at.strftime("%Y-%m-%d %H:%M UTC")
    all_tee = bool(models) and all(model.get("confidential_compute") is True for model in models)
    tee_count = sum(1 for model in models if model.get("confidential_compute") is True)
    tool_count = sum(1 for model in models if "tools" in as_list(model.get("supported_features")))
    json_count = sum(1 for model in models if "json_mode" in as_list(model.get("supported_features")))
    structured_count = sum(1 for model in models if "structured_outputs" in as_list(model.get("supported_features")))

    cheapest_models = cheapest(models, limit=3)
    cheap_vision = cheapest(models, predicate=lambda m: "image" in as_list(m.get("input_modalities")), limit=3)
    long_context = largest_context(models, limit=3)
    tool_models = [m for m in models if "tools" in as_list(m.get("supported_features"))][:5]

    lines: list[str] = [
        "# Known Chutes.ai Models (Auto-Refreshed Snapshot)",
        "",
        "This file is generated from the public Chutes OpenAI-compatible model endpoint. Do not edit it by hand; run `python3 scripts/update_chutes_models.py` instead.",
        "",
        f"Source: `GET {ENDPOINT}` (no auth headers sent)",
        f"Last updated: {date}",
        "",
        "## Summary",
        "",
        f"- Models returned: **{len(models)}**",
        f"- TEE/confidential-compute models: **{tee_count}/{len(models)}**" + (" — the hosted gateway is currently TEE-only." if all_tee else ""),
        f"- Models advertising `tools`: **{tool_count}**",
        f"- Models advertising `json_mode`: **{json_count}**",
        f"- Models advertising `structured_outputs`: **{structured_count}**",
        "- The models endpoint carries pricing and capability metadata, but not TTFT/TPS latency stats. For live latency/throughput data, use `GET https://api.chutes.ai/invocations/stats/llm` or the `default:latency` / `default:throughput` routing aliases.",
        "",
        "## Live model table (USD per 1M tokens)",
        "",
        "| Model ID | $ in | $ out | Cache read | Context | Quant | Engine | TEE | Modalities | Features |",
        "|---|---:|---:|---:|---:|---|---|---|---|---|",
    ]

    for model in sorted(models, key=sort_key):
        pricing = model.get("pricing") or {}
        features = feature_text(model)
        if len(features) > 72:
            features = features[:69] + "..."
        lines.append(
            "| "
            f"`{model.get('id', '—')}` | "
            f"{fmt_price(pricing.get('prompt'))} | "
            f"{fmt_price(pricing.get('completion'))} | "
            f"{fmt_price(pricing.get('input_cache_read'))} | "
            f"{fmt_context(model)} | "
            f"{model.get('quantization') or '—'} | "
            f"{model.get('owned_by') or '—'} | "
            f"{'yes' if model.get('confidential_compute') is True else 'no'} | "
            f"{modalities(model)} | "
            f"{features} |"
        )

    lines.extend([
        "",
        "## Quick picks generated from the live snapshot",
        "",
        "### Cheapest listed models",
        "",
    ])
    lines.extend(model_line(model) for model in cheapest_models)

    lines.extend(["", "### Cheapest image-capable models", ""])
    lines.extend(model_line(model) for model in cheap_vision) if cheap_vision else lines.append("- No image-capable models listed in this snapshot.")

    lines.extend(["", "### Largest context windows", ""])
    lines.extend(model_line(model) for model in long_context)

    lines.extend(["", "### Tool-capable examples", ""])
    lines.extend(model_line(model) for model in tool_models) if tool_models else lines.append("- No models in this snapshot advertise `tools`.")

    lines.extend([
        "",
        "## Routing aliases",
        "",
        "Chutes supports routing aliases that can be used as model values:",
        "",
        "- `default`",
        "- `default:latency`",
        "- `default:throughput`",
        "",
        "Use concrete model IDs when you need a specific model, context window, capability set, or price. Use routing aliases when you want Chutes to choose from the live pool.",
        "",
        "## Defensive usage notes",
        "",
        "- Treat this file as a convenience snapshot; the source of truth is always the live `/v1/models` endpoint.",
        "- Check `confidential_compute` for privacy-sensitive tasks; do not rely only on a `-TEE` suffix.",
        "- Check `supported_features` before promising tools, JSON mode, structured outputs, or reasoning behavior.",
        "- Check `supported_sampling_parameters` before sending advanced sampling controls.",
        "- Prompt-cache pricing, when present, is in `pricing.input_cache_read`.",
    ])
    return "\n".join(lines) + "\n"


def normalize_snapshot(payload: dict[str, Any], fetched_at: datetime) -> dict[str, Any]:
    models = payload.get("data")
    if not isinstance(models, list):
        raise ValueError("models endpoint response missing list field: data")
    return {
        "source": ENDPOINT,
        "fetched_at": fetched_at.isoformat().replace("+00:00", "Z"),
        "object": payload.get("object"),
        "count": len(models),
        "all_confidential_compute": bool(models) and all(m.get("confidential_compute") is True for m in models if isinstance(m, dict)),
        "data": models,
    }


def write_outputs(snapshot: dict[str, Any], markdown: str) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    SKILL_REF_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n")
    DOC_PATH.write_text(markdown)
    SKILL_REF_PATH.write_text(markdown)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=int, default=30, help="HTTP timeout in seconds")
    args = parser.parse_args()

    fetched_at = datetime.now(timezone.utc).replace(microsecond=0)
    payload = fetch_models(timeout=args.timeout)
    snapshot = normalize_snapshot(payload, fetched_at)
    models = [model for model in snapshot["data"] if isinstance(model, dict)]
    markdown = render_markdown(models, fetched_at)
    write_outputs(snapshot, markdown)
    print(f"wrote {DATA_PATH.relative_to(REPO_ROOT)} ({snapshot['count']} models)")
    print(f"wrote {DOC_PATH.relative_to(REPO_ROOT)}")
    print(f"wrote {SKILL_REF_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
