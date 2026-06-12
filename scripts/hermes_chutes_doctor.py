#!/usr/bin/env python3
"""Hermes + Chutes local smoke test and config helper.

This script is intentionally dependency-free and safe-by-default:

- It fetches the public Chutes model catalog from /v1/models.
- It detects whether Hermes and CHUTES_API_KEY are available locally.
- It never prints raw secrets.
- It only calls authenticated account APIs when --check-auth is passed.

Run from the repository root:

    python3 scripts/hermes_chutes_doctor.py
    python3 scripts/hermes_chutes_doctor.py --emit-config
    python3 scripts/hermes_chutes_doctor.py --check-auth
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

MODELS_URL = "https://llm.chutes.ai/v1/models"
ACCOUNT_URL = "https://api.chutes.ai/users/me"
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HERMES_ENV = Path.home() / ".hermes" / ".env"
USER_AGENT = "chutes-agent-toolkit-hermes-doctor/1.0"


@dataclass(frozen=True)
class SecretStatus:
    source: str | None
    value: str | None

    @property
    def found(self) -> bool:
        return bool(self.value)


@dataclass(frozen=True)
class HermesStatus:
    executable: str | None
    version: str | None
    error: str | None = None

    @property
    def found(self) -> bool:
        return bool(self.executable)


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def numeric(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def format_price(value: Any) -> str:
    parsed = numeric(value)
    if parsed is None:
        return "—"
    if parsed == 0:
        return "0"
    return f"${parsed:.6g}/1M"


def context_tokens(model: dict[str, Any]) -> int | None:
    parsed = numeric(model.get("context_length") or model.get("max_model_len"))
    return int(parsed) if parsed is not None else None


def format_context(model: dict[str, Any]) -> str:
    tokens = context_tokens(model)
    if tokens is None:
        return "—"
    if tokens >= 1000:
        return f"{round(tokens / 1000)}k"
    return str(tokens)


def features(model: dict[str, Any]) -> set[str]:
    return {str(feature) for feature in as_list(model.get("supported_features"))}


def modalities(model: dict[str, Any]) -> set[str]:
    return {str(modality) for modality in as_list(model.get("input_modalities"))}


def total_listed_price(model: dict[str, Any]) -> float:
    pricing = model.get("pricing") or {}
    prompt = numeric(pricing.get("prompt"))
    completion = numeric(pricing.get("completion"))
    total = (prompt if prompt is not None else 9999.0) + (completion if completion is not None else 9999.0)
    return total


def select_cheapest(
    models: list[dict[str, Any]],
    predicate: Callable[[dict[str, Any]], bool] | None = None,
) -> dict[str, Any] | None:
    candidates = [model for model in models if predicate is None or predicate(model)]
    if not candidates:
        return None
    return sorted(candidates, key=lambda m: (total_listed_price(m), str(m.get("id", ""))))[0]


def select_largest_context(models: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [model for model in models if context_tokens(model) is not None]
    if not candidates:
        return None
    return sorted(candidates, key=lambda m: (-(context_tokens(m) or 0), str(m.get("id", ""))))[0]


def model_id(model: dict[str, Any] | None) -> str | None:
    if not model:
        return None
    value = model.get("id")
    return str(value) if value else None


def summarize_models(models: list[dict[str, Any]]) -> dict[str, Any]:
    tool_models = [model for model in models if "tools" in features(model)]
    json_models = [model for model in models if "json_mode" in features(model)]
    structured_models = [model for model in models if "structured_outputs" in features(model)]
    vision_models = [model for model in models if "image" in modalities(model)]
    reasoning_models = [model for model in models if "reasoning" in features(model)]
    tee_count = sum(1 for model in models if model.get("confidential_compute") is True)

    cheapest_tool = select_cheapest(models, lambda m: "tools" in features(m))
    cheapest_json = select_cheapest(models, lambda m: "json_mode" in features(m))
    cheapest_vision = select_cheapest(models, lambda m: "image" in modalities(m))
    longest_context = select_largest_context(models)

    return {
        "count": len(models),
        "tee_count": tee_count,
        "all_tee": bool(models) and tee_count == len(models),
        "tools_count": len(tool_models),
        "json_mode_count": len(json_models),
        "structured_outputs_count": len(structured_models),
        "vision_count": len(vision_models),
        "reasoning_count": len(reasoning_models),
        "cheapest_tool_model": model_id(cheapest_tool),
        "cheapest_tool_price": price_pair(cheapest_tool),
        "cheapest_json_model": model_id(cheapest_json),
        "cheapest_vision_model": model_id(cheapest_vision),
        "longest_context_model": model_id(longest_context),
        "longest_context": format_context(longest_context or {}),
    }


def price_pair(model: dict[str, Any] | None) -> str | None:
    if not model:
        return None
    pricing = model.get("pricing") or {}
    return f"{format_price(pricing.get('prompt'))} in / {format_price(pricing.get('completion'))} out"


def fetch_json(url: str, timeout: int, headers: dict[str, str] | None = None) -> dict[str, Any]:
    request_headers = {
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    }
    request_headers.update(headers or {})
    req = urllib.request.Request(url, headers=request_headers, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as response:  # noqa: S310 - fixed HTTPS endpoints
        if response.status != 200:
            raise RuntimeError(f"{url} returned HTTP {response.status}")
        return json.load(response)


def load_models(timeout: int) -> list[dict[str, Any]]:
    payload = fetch_json(MODELS_URL, timeout=timeout)
    data = payload.get("data")
    if not isinstance(data, list):
        raise ValueError("Chutes /v1/models response is missing list field: data")
    return [model for model in data if isinstance(model, dict)]


def parse_env_file(path: Path, key: str = "CHUTES_API_KEY") -> str | None:
    try:
        lines = path.read_text().splitlines()
    except FileNotFoundError:
        return None
    except OSError:
        return None

    prefix = f"{key}="
    export_prefix = f"export {key}="
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith(export_prefix):
            value = line[len(export_prefix) :]
        elif line.startswith(prefix):
            value = line[len(prefix) :]
        else:
            continue
        value = value.strip().strip('"').strip("'")
        return value or None
    return None


def find_chutes_key(env_path: Path | None = None) -> SecretStatus:
    env_value = os.environ.get("CHUTES_API_KEY")
    if env_value:
        return SecretStatus("environment variable CHUTES_API_KEY", env_value)

    candidate = env_path or DEFAULT_HERMES_ENV
    file_value = parse_env_file(candidate)
    if file_value:
        return SecretStatus(str(candidate), file_value)
    return SecretStatus(None, None)


def mask_secret(value: str | None) -> str:
    if not value:
        return "not found"
    if value.startswith("cpk_"):
        return "cpk_...[redacted]"
    return "[redacted]"


def detect_hermes() -> HermesStatus:
    executable = shutil.which("hermes")
    if not executable:
        return HermesStatus(None, None, "hermes not found on PATH")
    try:
        result = subprocess.run(
            [executable, "--version"],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
    except Exception as exc:  # pragma: no cover - platform/process dependent
        return HermesStatus(executable, None, str(exc))

    version = (result.stdout or result.stderr).strip().splitlines()[0] if (result.stdout or result.stderr).strip() else None
    if result.returncode != 0:
        return HermesStatus(executable, version, f"hermes --version exited {result.returncode}")
    return HermesStatus(executable, version)


def check_auth(secret: SecretStatus, timeout: int) -> dict[str, Any]:
    if not secret.value:
        return {"ok": False, "detail": "CHUTES_API_KEY not found"}
    try:
        payload = fetch_json(
            ACCOUNT_URL,
            timeout=timeout,
            headers={"Authorization": f"Bearer {secret.value}"},
        )
    except urllib.error.HTTPError as exc:
        return {"ok": False, "detail": f"HTTP {exc.code}"}
    except Exception as exc:  # pragma: no cover - network dependent
        return {"ok": False, "detail": str(exc)}

    # Intentionally return non-sensitive presence checks only.
    return {
        "ok": True,
        "has_username": bool(payload.get("username")),
        "has_balance": "balance" in payload,
        "has_user_id": bool(payload.get("user_id") or payload.get("id")),
    }


def render_hermes_config(include_research: bool = False, direct_model: str | None = None) -> str:
    model_lines = [
        '      "default": {}',
        '      "default:latency": {}',
        '      "default:throughput": {}',
    ]
    if direct_model:
        model_lines.append(f'      "{direct_model}": {{}}')

    lines = [
        "# ~/.hermes/config.yaml",
        "# Put CHUTES_API_KEY in ~/.hermes/.env, not in this file.",
        "providers:",
        "  chutes:",
        "    name: Chutes",
        "    base_url: https://llm.chutes.ai/v1",
        "    key_env: CHUTES_API_KEY",
        "    transport: chat_completions",
        "    default_model: default:latency",
        "    discover_models: true",
        "    models:",
        *model_lines,
    ]
    if include_research:
        lines.extend(
            [
                "",
                "  chutes-research:",
                "    name: Chutes Research Opt-In",
                "    base_url: https://research-data-opt-in-proxy.chutes.ai/v1",
                "    key_env: CHUTES_API_KEY",
                "    transport: chat_completions",
                "    default_model: default:latency",
                "    discover_models: true",
                "    models:",
                '      "default": {}',
                '      "default:latency": {}',
                '      "default:throughput": {}',
            ]
        )
    lines.extend(
        [
            "",
            "model:",
            "  provider: custom:chutes",
            "  default: default:latency",
        ]
    )
    return "\n".join(lines) + "\n"


def render_report(
    hermes: HermesStatus,
    secret: SecretStatus,
    summary: dict[str, Any],
    auth_result: dict[str, Any] | None = None,
) -> str:
    lines = [
        "Hermes + Chutes doctor",
        "=======================",
        f"Hermes CLI: {'found' if hermes.found else 'not found'}" + (f" ({hermes.version})" if hermes.version else ""),
    ]
    if hermes.error:
        lines.append(f"Hermes note: {hermes.error}")

    lines.extend(
        [
            f"Chutes key: {mask_secret(secret.value)}" + (f" from {secret.source}" if secret.source else ""),
            "",
            "Live model catalog:",
            f"- source: {MODELS_URL}",
            f"- models returned: {summary['count']}",
            f"- confidential_compute=true: {summary['tee_count']}/{summary['count']}" + (" (currently TEE-only)" if summary["all_tee"] else ""),
            f"- models advertising tools/json/structured outputs: {summary['tools_count']}/{summary['json_mode_count']}/{summary['structured_outputs_count']}",
            f"- image-capable models: {summary['vision_count']}",
            f"- cheapest model advertising tools: {summary['cheapest_tool_model']} ({summary['cheapest_tool_price']})",
            f"- cheapest image-capable model: {summary['cheapest_vision_model']}",
            f"- longest context model: {summary['longest_context_model']} ({summary['longest_context']})",
            "",
            "Recommended Hermes defaults:",
            "- interactive chat: model `default:latency`",
            "- delegated/background work: model `default:throughput`",
            "- privacy-sensitive work: require `confidential_compute: true`; use chutes-tee for evidence claims",
            "- tool/JSON claims: prefer models advertising the feature, then verify with a minimal request for critical paths",
        ]
    )

    if auth_result is not None:
        lines.extend(["", "Auth check (--check-auth):", f"- ok: {auth_result.get('ok')}"])
        detail = auth_result.get("detail")
        if detail:
            lines.append(f"- detail: {detail}")
        if auth_result.get("ok"):
            lines.append("- /users/me returned account-shaped data; username/balance intentionally not printed")
    elif secret.found:
        lines.extend(["", "Auth check: skipped (pass --check-auth to validate the key with GET /users/me)"])
    else:
        lines.extend(["", "Next: add CHUTES_API_KEY to ~/.hermes/.env, then re-run this script"])

    lines.extend(
        [
            "",
            "Useful next commands:",
            "- python3 scripts/hermes_chutes_doctor.py --emit-config",
            "- python3 plugins/chutes-ai/skills/chutes-mcp-portability/scripts/generate_agent_config.py --target hermes",
            "- hermes mcp add chutes --command chutes-mcp-server --env CHUTES_API_KEY=${CHUTES_API_KEY}",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Smoke-test Hermes + Chutes setup without exposing secrets.")
    parser.add_argument("--timeout", type=int, default=30, help="HTTP timeout in seconds")
    parser.add_argument("--env-path", type=Path, default=None, help="Optional Hermes .env path to inspect for CHUTES_API_KEY")
    parser.add_argument("--check-auth", action="store_true", help="Validate CHUTES_API_KEY with GET https://api.chutes.ai/users/me")
    parser.add_argument("--emit-config", action="store_true", help="Print a ready-to-paste Hermes provider config after the report")
    parser.add_argument("--include-research", action="store_true", help="Include the opt-in research endpoint in --emit-config output")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text")
    args = parser.parse_args(argv)

    try:
        models = load_models(timeout=args.timeout)
    except Exception as exc:
        print(f"error: failed to fetch live Chutes models from {MODELS_URL}: {exc}", file=sys.stderr)
        return 2

    summary = summarize_models(models)
    hermes = detect_hermes()
    secret = find_chutes_key(args.env_path)
    auth_result = check_auth(secret, args.timeout) if args.check_auth else None

    direct_model = summary.get("cheapest_tool_model")
    config = render_hermes_config(include_research=args.include_research, direct_model=direct_model)

    if args.json:
        payload = {
            "hermes": {"found": hermes.found, "executable": hermes.executable, "version": hermes.version, "error": hermes.error},
            "chutes_key": {"found": secret.found, "source": secret.source, "masked": mask_secret(secret.value)},
            "models": summary,
            "auth_check": auth_result,
            "config": config if args.emit_config else None,
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(render_report(hermes, secret, summary, auth_result), end="")
        if args.emit_config:
            print("\n--- Hermes config snippet ---")
            print(config, end="")
    return 0 if not auth_result or auth_result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
