#!/usr/bin/env python3
"""Build a site-ready Chutes agent use-case pack.

The input is data/agent-use-cases.json. The output is either Markdown for
publishing copy or stable JSON for website ingestion.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_PATH = REPO_ROOT / "data" / "agent-use-cases.json"
REQUIRED_TOP_LEVEL_FIELDS = ("version", "updated_at", "use_cases")
REQUIRED_USE_CASE_FIELDS = (
    "id",
    "title",
    "agent",
    "audience",
    "value_prop",
    "setup_path",
    "demo_prompt",
    "proof_points",
    "links",
    "status",
)


def load_payload(path: Path = DEFAULT_DATA_PATH) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    validate_payload(payload)
    return payload


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_links(use_case_id: str, links: Any) -> None:
    if not isinstance(links, list) or not links:
        raise ValueError(f"Use case {use_case_id} field links must be a non-empty list")
    for index, link in enumerate(links):
        if not isinstance(link, dict):
            raise ValueError(f"Use case {use_case_id} link {index} must be an object")
        if not _non_empty_string(link.get("label")):
            raise ValueError(f"Use case {use_case_id} link {index} is missing label")
        has_path = _non_empty_string(link.get("path"))
        has_url = _non_empty_string(link.get("url"))
        if has_path == has_url:
            raise ValueError(f"Use case {use_case_id} link {index} must have exactly one of path or url")


def validate_payload(payload: dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        raise ValueError("Agent use-case payload must be an object")
    for field in REQUIRED_TOP_LEVEL_FIELDS:
        if field not in payload:
            raise ValueError(f"Payload missing required field: {field}")
    if not isinstance(payload["version"], int):
        raise ValueError("version must be an integer")
    if not _non_empty_string(payload["updated_at"]):
        raise ValueError("updated_at must be a non-empty string")
    if not isinstance(payload["use_cases"], list) or not payload["use_cases"]:
        raise ValueError("use_cases must be a non-empty list")

    seen_ids: set[str] = set()
    for index, use_case in enumerate(payload["use_cases"]):
        if not isinstance(use_case, dict):
            raise ValueError(f"Use case {index} must be an object")
        use_case_id = use_case.get("id", f"at index {index}")
        for field in REQUIRED_USE_CASE_FIELDS:
            if field not in use_case:
                raise ValueError(f"Use case {use_case_id} missing required field: {field}")

        if not _non_empty_string(use_case["id"]):
            raise ValueError(f"Use case at index {index} has invalid id")
        if use_case["id"] in seen_ids:
            raise ValueError(f"Duplicate use case id: {use_case['id']}")
        seen_ids.add(use_case["id"])

        for field in ("title", "agent", "audience", "value_prop", "setup_path", "demo_prompt", "status"):
            if not _non_empty_string(use_case[field]):
                raise ValueError(f"Use case {use_case['id']} field {field} must be a non-empty string")

        proof_points = use_case["proof_points"]
        if not isinstance(proof_points, list) or not proof_points:
            raise ValueError(f"Use case {use_case['id']} field proof_points must be a non-empty list")
        for point in proof_points:
            if not _non_empty_string(point):
                raise ValueError(f"Use case {use_case['id']} has an invalid proof point")

        _validate_links(use_case["id"], use_case["links"])


def _matches_focus(use_case: dict[str, Any], focus: str) -> bool:
    needle = focus.strip().lower()
    haystack = [
        str(use_case["id"]).lower(),
        str(use_case["agent"]).lower(),
        str(use_case["title"]).lower(),
    ]
    return any(needle == item or needle in item for item in haystack)


def filter_payload(payload: dict[str, Any], focus: str | None = None) -> dict[str, Any]:
    validate_payload(payload)
    filtered = copy.deepcopy(payload)
    if focus:
        filtered["use_cases"] = [case for case in filtered["use_cases"] if _matches_focus(case, focus)]
        if not filtered["use_cases"]:
            raise ValueError(f"No agent use cases matched focus: {focus}")
    return filtered


def _render_link(link: dict[str, str]) -> str:
    target = link.get("path") or link.get("url")
    return f"[{link['label']}]({target})"


def render_markdown(payload: dict[str, Any]) -> str:
    validate_payload(payload)
    lines: list[str] = [
        "# Chutes Agent Site Pack",
        "",
        f"Version: {payload['version']}",
        f"Updated: {payload['updated_at']}",
        "",
        "Use this copy as a source pack for Chutes site pages, demos, and agent onboarding content. Live model metadata should still come from `https://llm.chutes.ai/v1/models`.",
        "",
    ]

    for use_case in payload["use_cases"]:
        lines.extend(
            [
                f"## {use_case['title']}",
                "",
                f"- Agent: {use_case['agent']}",
                f"- Audience: {use_case['audience']}",
                f"- Status: {use_case['status']}",
                f"- Setup path: {use_case['setup_path']}",
                "",
                "Value prop:",
                use_case["value_prop"],
                "",
                "Demo prompt:",
                use_case["demo_prompt"],
                "",
                "Proof points:",
            ]
        )
        lines.extend(f"- {point}" for point in use_case["proof_points"])
        lines.extend(["", "Links:"])
        lines.extend(f"- {_render_link(link)}" for link in use_case["links"])
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_json(payload: dict[str, Any]) -> str:
    validate_payload(payload)
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def build_output(payload: dict[str, Any], output_format: str, focus: str | None = None) -> str:
    filtered = filter_payload(payload, focus=focus)
    if output_format == "markdown":
        return render_markdown(filtered)
    if output_format == "json":
        return render_json(filtered)
    raise ValueError(f"Unsupported output format: {output_format}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default=str(DEFAULT_DATA_PATH), help="Path to agent use-case JSON")
    parser.add_argument("--focus", help="Filter by use-case id, agent, or title")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown", help="Output format")
    parser.add_argument("--output", help="Write output to this path instead of stdout")
    args = parser.parse_args(argv)

    try:
        payload = load_payload(Path(args.data))
        rendered = build_output(payload, args.format, focus=args.focus)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
