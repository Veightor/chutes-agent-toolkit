#!/usr/bin/env python3
"""Build the full-modality Chutes model-page catalog from vendored llms.txt files.

Chutes publishes a per-model `llms.txt` on every model page (agent-facing docs).
`scripts/update_chutes_models.py` already snapshots the chat LLMs from
`GET /v1/models`, but that endpoint only ever returns text-in/text-out chat
models. It cannot describe embedding, image, video, audio, guard-classifier, or
segmentation chutes. This script covers those: it parses the vendored model-page
files in `data/model-pages/*.llms.txt` and writes a durable catalog that the
snapshot refresh never overwrites.

This script uses only the standard library and does not touch the network.

It writes:

- data/chutes-model-pages.json: machine-readable index of every model page.
- docs/model-pages.md: human catalog grouped by capability.

Run from the repository root:

    python3 scripts/build_model_pages.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "data" / "model-pages"
JSON_PATH = REPO_ROOT / "data" / "chutes-model-pages.json"
DOC_PATH = REPO_ROOT / "docs" / "model-pages.md"
SNAPSHOT_PATH = REPO_ROOT / "data" / "chutes-models.json"

MODEL_PAGE_URL = "https://chutes.ai/app/chute/{slug}"
MODEL_LLMS_URL = "https://chutes.ai/app/chute/{slug}/llms.txt"


def snapshot_model_ids() -> set[str]:
    """IDs served by the OpenAI-compatible gateway (auto-refreshed snapshot).

    Membership here — not input/output modality — is the authoritative signal
    for whether a model page is a chat-completions LLM. Several of these accept
    image/video input yet are still hosted chat LLMs.
    """
    try:
        snap = json.loads(SNAPSHOT_PATH.read_text())
    except (OSError, ValueError):
        return set()
    return {m.get("id") for m in snap.get("data", []) if isinstance(m, dict)}


def _field(text: str, pattern: str) -> str | None:
    m = re.search(pattern, text, re.M)
    return m.group(1).strip() if m else None


def parse_modalities(raw: str | None) -> tuple[list[str], list[str]]:
    """Parse a 'Modalities:' line like 'text, image in -> video, audio out'."""
    if not raw:
        return ([], [])
    # normalize arrow variants
    norm = raw.replace("→", "->").replace("–", "-")
    m = re.match(r"\s*(.+?)\s+in\s*->\s*(.+?)\s+out\s*$", norm)
    if not m:
        return ([], [])
    split = lambda s: [p.strip() for p in s.split(",") if p.strip()]
    return (split(m.group(1)), split(m.group(2)))


def categorize(ins: list[str], outs: list[str], in_snapshot: bool) -> str:
    # Gateway membership wins: these are chat-completions LLMs regardless of
    # whether they also accept image/video input.
    if in_snapshot:
        return "chat-llm"
    outset, inset = set(outs), set(ins)
    if outset == {"embedding"}:
        return "embedding"
    if "audio" in outset:
        return "audio"
    if "video" in outset:
        return "video"
    if "image" in outset:
        return "image"
    if outset == {"text"} and inset and inset != {"text"}:
        # text-out but richer inputs: vision/omni understanding or classifier/extract
        return "vision-understanding"
    return "other"


# Human-friendly section ordering + headings for the markdown catalog.
CATEGORY_ORDER = [
    ("chat-llm", "Chat / multimodal LLMs on the OpenAI-compatible gateway (also in known-models.md)"),
    ("vision-understanding", "Vision / multimodal understanding (media in → text out)"),
    ("embedding", "Embeddings"),
    ("image", "Image generation & editing"),
    ("video", "Video generation"),
    ("audio", "Audio / speech / music"),
    ("other", "Guard classifiers, scoring & segmentation"),
]


def parse_file(path: Path, snapshot_ids: set[str]) -> dict[str, Any]:
    text = path.read_text()
    slug = path.name[: -len(".llms.txt")]
    title = _field(text, r"^# (.+)")
    tagline = _field(text, r"^> (.+)")
    name = _field(text, r"- Name: `([^`]+)`") or title or slug
    chute_id = _field(text, r"- Chute ID: `([^`]+)`")
    owner = _field(text, r"- Owner: `([^`]+)`")
    modality_line = _field(text, r"- Modalities: (.+)")
    ins, outs = parse_modalities(modality_line)
    in_snapshot = name in snapshot_ids
    category = categorize(ins, outs, in_snapshot)
    return {
        "slug": slug,
        "name": name,
        "chute_id": chute_id,
        "owner": owner,
        "tagline": tagline,
        "input_modalities": ins,
        "output_modalities": outs,
        "modalities": modality_line,
        "category": category,
        "chat_llm": in_snapshot,
        "in_v1_models_snapshot": in_snapshot,
        "model_page": MODEL_PAGE_URL.format(slug=slug),
        "llms_txt": MODEL_LLMS_URL.format(slug=slug),
    }


def build_catalog() -> list[dict[str, Any]]:
    files = sorted(SRC_DIR.glob("*.llms.txt"))
    if not files:
        raise SystemExit(f"no model-page files found in {SRC_DIR}")
    snapshot_ids = snapshot_model_ids()
    return [parse_file(f, snapshot_ids) for f in files]


def render_markdown(catalog: list[dict[str, Any]]) -> str:
    total = len(catalog)
    chat = sum(1 for m in catalog if m["chat_llm"])
    lines: list[str] = [
        "# Chutes Model Pages (Full-Modality Catalog)",
        "",
        "This file is generated. Do not edit it by hand; run "
        "`python3 scripts/build_model_pages.py` instead. Source: the per-model "
        "`llms.txt` pages published on chutes.ai model pages, vendored under "
        "`data/model-pages/`.",
        "",
        "Unlike [`known-models.md`](known-models.md) (auto-refreshed from "
        "`GET /v1/models`, which only lists **chat** LLMs), this catalog also "
        "covers embedding, image, video, audio, guard-classifier, and "
        "segmentation chutes that the OpenAI-compatible models endpoint never "
        "returns.",
        "",
        "## Summary",
        "",
        f"- Model pages catalogued: **{total}**",
        f"- Chat LLMs (also in `known-models.md`): **{chat}**",
        f"- Non-chat / full-modality chutes: **{total - chat}**",
        "",
        "Every model exposes an agent-facing `llms.txt` at "
        "`https://chutes.ai/app/chute/<slug>/llms.txt` and a callable OpenAPI "
        "spec at `.../openapi.json`.",
        "",
    ]
    for key, heading in CATEGORY_ORDER:
        rows = [m for m in catalog if m["category"] == key]
        if not rows:
            continue
        lines.append(f"## {heading}")
        lines.append("")
        lines.append("| Model | Owner | Modalities | What it is |")
        lines.append("|---|---|---|---|")
        for m in sorted(rows, key=lambda x: x["name"].lower()):
            mod = m["modalities"] or "—"
            tag = (m["tagline"] or "").replace("|", "\\|")
            if len(tag) > 90:
                tag = tag[:87] + "..."
            lines.append(
                f"| [`{m['name']}`]({m['model_page']}) | {m['owner'] or '—'} | {mod} | {tag or '—'} |"
            )
        lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append(
        "- The live `/v1/models` endpoint remains the source of truth for chat "
        "LLM pricing and capabilities; this catalog is a convenience index of "
        "published model pages."
    )
    lines.append(
        "- Non-chat chutes are not OpenAI chat-completions compatible; call each "
        "via its own endpoint (see the model's `llms.txt` / `openapi.json`)."
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    catalog = build_catalog()
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    snapshot = {
        "source": "chutes.ai model pages (per-model llms.txt), vendored under data/model-pages/",
        "note": "Full-modality catalog. Chat LLMs are also in data/chutes-models.json (from GET /v1/models).",
        "count": len(catalog),
        "data": catalog,
    }
    JSON_PATH.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n")
    DOC_PATH.write_text(render_markdown(catalog))
    print(f"wrote {JSON_PATH.relative_to(REPO_ROOT)} ({len(catalog)} model pages)")
    print(f"wrote {DOC_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
