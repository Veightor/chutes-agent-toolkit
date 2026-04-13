#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any, Dict


DEFAULT_EVALS_PATH = Path("evals/evals.json")


def load_evals(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    validate_evals(payload)
    return payload


def validate_evals(payload: Dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        raise ValueError("Eval payload must be an object")
    skill_name = payload.get("skill_name")
    if not isinstance(skill_name, str) or not skill_name.strip():
        raise ValueError("skill_name must be a non-empty string")
    evals = payload.get("evals")
    if not isinstance(evals, list) or not evals:
        raise ValueError("evals must be a non-empty list")

    seen_ids = set()
    for item in evals:
        if not isinstance(item, dict):
            raise ValueError("Each eval must be an object")
        eval_id = item.get("id")
        if eval_id in seen_ids:
            raise ValueError(f"Duplicate eval id: {eval_id}")
        seen_ids.add(eval_id)
        if not isinstance(item.get("prompt"), str) or not item["prompt"].strip():
            raise ValueError(f"Eval {eval_id} is missing a prompt")
        if not isinstance(item.get("expected_output"), str) or not item["expected_output"].strip():
            raise ValueError(f"Eval {eval_id} is missing expected_output")


def build_summary(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "skill_name": payload["skill_name"],
        "eval_count": len(payload["evals"]),
        "ids": [item["id"] for item in payload["evals"]],
    }


def render_markdown(payload: Dict[str, Any]) -> str:
    lines = [f"# Eval Pack: {payload['skill_name']}", ""]
    for item in payload["evals"]:
        lines.extend(
            [
                f"## Eval {item['id']}",
                "",
                "Prompt:",
                item["prompt"],
                "",
                "Expected output:",
                item["expected_output"],
                "",
            ]
        )
        files = item.get("files") or []
        if files:
            lines.append("Files:")
            lines.extend([f"- {path}" for path in files])
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect and export Chutes eval packs")
    parser.add_argument("--path", default=str(DEFAULT_EVALS_PATH), help="Path to evals JSON file")
    parser.add_argument(
        "--format",
        choices=["summary", "json", "markdown"],
        default="summary",
        help="Output format",
    )
    args = parser.parse_args()

    payload = load_evals(Path(args.path))
    if args.format == "summary":
        print(json.dumps(build_summary(payload), indent=2))
    elif args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        print(render_markdown(payload), end="")


if __name__ == "__main__":
    main()
