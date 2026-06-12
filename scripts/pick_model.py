#!/usr/bin/env python3
"""Recommend a Chutes model (or routing pool) for a task, from the live catalog.

Queries GET https://llm.chutes.ai/v1/models (public, no auth); falls back to the
daily snapshot in data/chutes-models.json when offline. This is also the
reference logic for the chutes.ai "model picker" site widget (see site/README.md).

Examples:
    python scripts/pick_model.py --task agentic
    python scripts/pick_model.py --need tools,structured_outputs --modality image
    python scripts/pick_model.py --task cheap --max-input-price 0.2 --json
    python scripts/pick_model.py --task chat --routing latency
"""

import argparse
import json
import pathlib
import sys
import urllib.request

LIVE_URL = "https://llm.chutes.ai/v1/models"
SNAPSHOT = pathlib.Path(__file__).resolve().parent.parent / "data" / "chutes-models.json"

# Task presets: required features/modalities plus how to weight price.
# in_weight reflects the typical input:output token ratio for the workload.
TASKS = {
    "chat":         {"need": [], "in_weight": 0.5},
    "agentic":      {"need": ["tools"], "in_weight": 0.75},  # agents are prompt-heavy
    "reasoning":    {"need": ["reasoning"], "in_weight": 0.4},
    "extraction":   {"need": ["structured_outputs"], "in_weight": 0.8},
    "vision":       {"need": [], "modality": ["image"], "in_weight": 0.6},
    "long-context": {"need": [], "min_context": 190_000, "in_weight": 0.8},
    "cheap":        {"need": [], "in_weight": 0.5},
}


def fetch_models(offline: bool) -> tuple[list[dict], str]:
    if not offline:
        try:
            with urllib.request.urlopen(LIVE_URL, timeout=15) as r:
                return json.load(r)["data"], "live"
        except Exception as e:  # noqa: BLE001 - any network failure -> snapshot
            print(f"note: live fetch failed ({e}); using snapshot", file=sys.stderr)
    snap = json.loads(SNAPSHOT.read_text())
    return snap["data"], f"snapshot {snap.get('fetched_at', '?')}"


def blended_price(m: dict, in_weight: float) -> float:
    p = m.get("pricing", {})
    return in_weight * p.get("prompt", 0) + (1 - in_weight) * p.get("completion", 0)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--task", choices=sorted(TASKS), default="chat")
    ap.add_argument("--need", default="", help="comma list: tools,json_mode,structured_outputs,reasoning")
    ap.add_argument("--modality", default="", help="comma list: image,video")
    ap.add_argument("--min-context", type=int, default=0)
    ap.add_argument("--max-input-price", type=float, default=None, help="USD per 1M prompt tokens")
    ap.add_argument("--max-output-price", type=float, default=None, help="USD per 1M completion tokens")
    ap.add_argument("--tee-only", action="store_true", help="require confidential_compute (currently the whole catalog)")
    ap.add_argument("--top", type=int, default=3)
    ap.add_argument("--routing", choices=["failover", "latency", "throughput"], default=None,
                    help="emit an inline routing string built from the top picks")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--offline", action="store_true", help="use the repo snapshot, skip the live call")
    args = ap.parse_args()

    preset = TASKS[args.task]
    need = set(preset["need"]) | {f for f in args.need.split(",") if f}
    modality = set(preset.get("modality", [])) | {m for m in args.modality.split(",") if m}
    min_context = max(preset.get("min_context", 0), args.min_context)

    models, source = fetch_models(args.offline)

    picks = []
    for m in models:
        feats = set(m.get("supported_features") or [])
        mods = set(m.get("input_modalities") or [])
        ctx = m.get("context_length") or 0
        p = m.get("pricing", {})
        if need - feats or modality - mods or ctx < min_context:
            continue
        if args.tee_only and not m.get("confidential_compute"):
            continue
        if args.max_input_price is not None and p.get("prompt", 0) > args.max_input_price:
            continue
        if args.max_output_price is not None and p.get("completion", 0) > args.max_output_price:
            continue
        picks.append(m)

    picks.sort(key=lambda m: blended_price(m, preset["in_weight"]))
    picks = picks[: args.top]

    if not picks:
        print("no model matches those constraints — relax a filter or check the live list", file=sys.stderr)
        return 1

    routing = None
    if args.routing:
        pool = ",".join(m["id"] for m in picks)
        routing = pool if args.routing == "failover" else f"{pool}:{args.routing}"

    if args.json:
        out = {
            "source": source,
            "task": args.task,
            "picks": [
                {
                    "id": m["id"],
                    "pricing": m.get("pricing"),
                    "context_length": m.get("context_length"),
                    "supported_features": m.get("supported_features"),
                    "input_modalities": m.get("input_modalities"),
                    "confidential_compute": m.get("confidential_compute"),
                }
                for m in picks
            ],
            "routing": routing,
        }
        print(json.dumps(out, indent=2))
        return 0

    print(f"task={args.task}  catalog={source}  ({len(picks)} pick(s))\n")
    for i, m in enumerate(picks, 1):
        p = m.get("pricing", {})
        feats = ",".join(m.get("supported_features") or []) or "—"
        ctx = m.get("context_length")
        ctx_s = f"{ctx // 1024}K" if ctx else "?"
        print(f"{i}. {m['id']}")
        print(f"   ${p.get('prompt')}/M in · ${p.get('completion')}/M out · ctx {ctx_s} · {feats}")
    if routing:
        print(f'\nrouting string:\n  model="{routing}"')
    return 0


if __name__ == "__main__":
    sys.exit(main())
