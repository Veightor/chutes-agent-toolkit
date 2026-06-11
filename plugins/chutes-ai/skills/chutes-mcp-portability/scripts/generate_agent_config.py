#!/usr/bin/env python3
"""Generate drop-in Chutes configs for popular agent / client targets. [BETA]

Usage:
  python generate_agent_config.py --target cursor,aider,hermes [--out DIR]

Targets:
  cursor         → .cursor/mcp.json
  cline          → cline_mcp_settings.json snippet (paste via Cline's MCP Servers UI)
  claude-desktop → claude_desktop_config.json snippet
  aider          → .aider.conf.yml
  openrouter     → env-var block (stdout)
  hermes         → other-agents/hermes/config-examples/*.yaml
  system-prompt  → other-agents/system-prompt/chutes-prompt.md

Secrets are resolved from the keychain at generation time via
manage_credentials.py; configs use env-var references (${CHUTES_API_KEY})
wherever the target client supports them.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
MCP_SERVER_PATH = Path(__file__).resolve().parent.parent / "mcp-server"

ENV_NOTE = "# Secrets are read via $CHUTES_API_KEY — do NOT paste the cpk_ value here."


def _has_api_key() -> bool:
    if os.environ.get("CHUTES_API_KEY"):
        return True
    script = REPO_ROOT / "plugins" / "chutes-ai" / "skills" / "chutes-ai" / "scripts" / "manage_credentials.py"
    if not script.exists():
        return False
    result = subprocess.run(
        [sys.executable, str(script), "get", "--field", "api_key"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and bool(result.stdout.strip())


def cursor_config(out: Path) -> Path:
    target = out / ".cursor" / "mcp.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "mcpServers": {
            "chutes": {
                "command": "chutes-mcp-server",
                "env": {"CHUTES_API_KEY": "${env:CHUTES_API_KEY}"},
            }
        }
    }
    target.write_text(json.dumps(payload, indent=2))
    return target


def cline_config(out: Path) -> Path:
    # Cline reads a global cline_mcp_settings.json (VS Code globalStorage,
    # saoudrizwan.claude-dev/settings/), edited via Cline's MCP Servers > Configure UI —
    # NOT VS Code settings.json. Shape uses the standard "mcpServers" key with optional
    # per-server "disabled"/"autoApprove" fields (per docs.cline.bot; unverified as of 2026-06-11).
    target = out / "cline-mcp-snippet.json"
    payload = {
        "mcpServers": {
            "chutes": {
                "command": "chutes-mcp-server",
                "env": {"CHUTES_API_KEY": "${env:CHUTES_API_KEY}"},
                "disabled": False,
                "autoApprove": [],
            }
        }
    }
    target.write_text(json.dumps(payload, indent=2))
    return target


def claude_desktop_config(out: Path) -> Path:
    target = out / "claude_desktop_config.snippet.json"
    payload = {
        "mcpServers": {
            "chutes": {
                "command": "chutes-mcp-server",
                "env": {"CHUTES_API_KEY": "${CHUTES_API_KEY}"},
            }
        }
    }
    target.write_text(json.dumps(payload, indent=2))
    return target


def aider_config(out: Path) -> Path:
    target = out / ".aider.conf.yml"
    target.write_text(
        "# Chutes.ai via OpenAI-compatible API\n"
        f"{ENV_NOTE}\n"
        "openai-api-base: https://llm.chutes.ai/v1\n"
        "openai-api-key: ${CHUTES_API_KEY}\n"
        # All hosted Chutes LLMs are -TEE variants as of 2026-06-11; non-TEE ids
        # like deepseek-ai/DeepSeek-V3-0324 no longer exist on /v1/models.
        "model: deepseek-ai/DeepSeek-V3.2-TEE\n"
        "edit-format: diff\n"
    )
    return target


def openrouter_style(out: Path) -> Path:
    target = out / "chutes.env"
    target.write_text(
        "# Drop-in env block for any OpenAI-compatible client.\n"
        f"{ENV_NOTE}\n"
        "OPENAI_API_BASE=https://llm.chutes.ai/v1\n"
        "OPENAI_BASE_URL=https://llm.chutes.ai/v1\n"
        "OPENAI_API_KEY=${CHUTES_API_KEY}\n"
    )
    return target


def hermes_config(out: Path) -> Path:
    """Refresh the checked-in Hermes config examples.

    Hermes v0.16 supports the newer keyed `providers:` shape and still accepts
    the older `custom_providers:` list for compatibility. Prefer `providers:` in
    generated snippets because it is easier to extend with model lists and
    `discover_models`, while still selecting it as `custom:chutes` at runtime.
    """
    hermes_dir = REPO_ROOT / "other-agents" / "hermes" / "config-examples"
    hermes_dir.mkdir(parents=True, exist_ok=True)

    provider_common_latency = (
        "    name: Chutes\n"
        "    base_url: https://llm.chutes.ai/v1\n"
        "    key_env: CHUTES_API_KEY\n"
        "    transport: chat_completions\n"
        "    default_model: default:latency\n"
        "    discover_models: true\n"
        "    models:\n"
        "      default: {}\n"
        "      \"default:latency\": {}\n"
        "      \"default:throughput\": {}\n"
    )
    provider_common_throughput = provider_common_latency.replace(
        "default_model: default:latency", "default_model: default:throughput"
    )

    examples = {
        "chutes-basic.yaml": (
            "# ~/.hermes/config.yaml\n"
            "# Chutes as a named Hermes provider entry.\n"
            "# Put CHUTES_API_KEY=*** in ~/.hermes/.env, not in this file.\n\n"
            "providers:\n"
            "  chutes:\n"
            f"{provider_common_latency}\n"
            "model:\n"
            "  provider: custom:chutes\n"
            "  default: default:latency\n"
        ),
        "chutes-cheap-routing.yaml": (
            "# ~/.hermes/config.yaml\n"
            "# Keep your primary model/provider elsewhere, and let Hermes route cheap/simple work to Chutes.\n\n"
            "providers:\n"
            "  chutes:\n"
            f"{provider_common_latency}\n"
            "smart_model_routing:\n"
            "  enabled: true\n"
            "  cheap_model:\n"
            "    provider: custom:chutes\n"
            "    model: default:latency\n"
        ),
        "chutes-delegation.yaml": (
            "# ~/.hermes/config.yaml\n"
            "# Use your normal primary model/provider for orchestration, and Chutes for delegated/background subtasks.\n\n"
            "providers:\n"
            "  chutes:\n"
            f"{provider_common_throughput}\n"
            "delegation:\n"
            "  provider: custom:chutes\n"
            "  model: default:throughput\n"
            "  reasoning_effort: medium\n"
        ),
        "chutes-dual-endpoints.yaml": (
            "# ~/.hermes/config.yaml\n"
            "# Two named Chutes endpoints: normal inference and opt-in research endpoint.\n"
            "# Use the research endpoint only when the user accepts prompt/response recording.\n\n"
            "providers:\n"
            "  chutes:\n"
            f"{provider_common_latency}\n"
            "  chutes-research:\n"
            "    name: Chutes Research Opt-In\n"
            "    base_url: https://research-data-opt-in-proxy.chutes.ai/v1\n"
            "    key_env: CHUTES_API_KEY\n"
            "    transport: chat_completions\n"
            "    default_model: default:latency\n"
            "    discover_models: true\n"
            "    models:\n"
            "      default: {}\n"
            "      \"default:latency\": {}\n"
            "      \"default:throughput\": {}\n"
        ),
    }

    for name, content in examples.items():
        target = hermes_dir / name
        target.write_text(content)
    return hermes_dir


def system_prompt(out: Path) -> Path:
    prompt_dir = REPO_ROOT / "other-agents" / "system-prompt"
    prompt_dir.mkdir(parents=True, exist_ok=True)
    target = prompt_dir / "chutes-prompt.md"
    target.write_text(
        "# Chutes.ai — System Prompt Block\n\n"
        "Paste this into any system prompt to tell a generic agent how to call Chutes:\n\n"
        "---\n\n"
        "You have access to Chutes.ai, a decentralized inference network serving open-source models via an OpenAI-compatible inference API. As of 2026-06-11 every hosted LLM runs in a TEE (`confidential_compute: true`, `-TEE` id suffix).\n\n"
        "Base URL: `https://llm.chutes.ai/v1`\n"
        "Auth for direct HTTP calls: `Authorization: Bearer cpk_...` (never log or echo the key). Verified live 2026-06-11 on GET /v1/models; Bearer is the platform-recommended header. X-API-Key is no longer recommended on the inference surface.\n"
        "List models: `GET /models` (public, no auth required; always treat this as source of truth; do not hardcode ids).\n"
        "Chat: `POST /chat/completions` with `{model, messages, max_tokens, temperature}`.\n"
        "Routing: pass `default:latency` or `default:throughput` as the model for smart pools.\n"
        "Privacy: filter models by `confidential_compute: true` for TEE-isolated inference.\n\n"
        "Do not paste the Chutes API key into any output.\n"
    )
    return target


TARGETS = {
    "cursor": cursor_config,
    "cline": cline_config,
    "claude-desktop": claude_desktop_config,
    "aider": aider_config,
    "openrouter": openrouter_style,
    "hermes": hermes_config,
    "system-prompt": system_prompt,
}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument(
        "--target",
        required=True,
        help=f"comma-separated list of targets: {', '.join(TARGETS)}",
    )
    p.add_argument(
        "--out",
        default=".",
        help="output directory for file-style configs (default: .)",
    )
    args = p.parse_args()

    if not _has_api_key():
        print(
            "warning: no Chutes API key available in env or keychain. "
            "Generated configs will reference $CHUTES_API_KEY but you need "
            "to populate it before running the target client.",
            file=sys.stderr,
        )

    out = Path(args.out).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)

    requested = [t.strip() for t in args.target.split(",") if t.strip()]
    unknown = [t for t in requested if t not in TARGETS]
    if unknown:
        print(f"error: unknown targets: {', '.join(unknown)}", file=sys.stderr)
        print(f"       valid: {', '.join(TARGETS)}", file=sys.stderr)
        return 1

    results = {}
    for t in requested:
        try:
            path = TARGETS[t](out)
            results[t] = str(path)
            print(f"  {t}: wrote {path}")
        except Exception as e:
            print(f"  {t}: FAILED ({e})", file=sys.stderr)
            results[t] = f"ERROR: {e}"

    print("\nSummary:")
    print(json.dumps(results, indent=2))
    print("\nNext:")
    print(f"  1. load CHUTES_API_KEY from: {sys.executable} plugins/chutes-ai/skills/chutes-ai/scripts/manage_credentials.py get --field api_key")
    # chutes-mcp-server is NOT on PyPI (404 verified 2026-06-11) — local-path install only.
    print("  2. install the MCP server for MCP targets: uv tool install chutes-mcp-server --from plugins/chutes-ai/skills/chutes-mcp-portability/mcp-server")
    print("  3. restart the target client so it picks up the new config")
    return 0


if __name__ == "__main__":
    sys.exit(main())
