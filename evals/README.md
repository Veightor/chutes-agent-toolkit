# Evals

This directory contains scenario-based evals for Chutes agent integrations.

Primary file:
- `evals/evals.json`

## Purpose

These evals are meant to verify that agents using this toolkit respond correctly to common Chutes tasks, including:
- account bootstrap
- API key lifecycle
- secure credential storage
- model discovery
- routing recommendations
- TEE/privacy guidance
- billing and discount flows
- Hermes-specific setup guidance

## Format

The eval pack is a JSON object:

```json
{
  "skill_name": "chutes-ai",
  "evals": [
    {
      "id": 1,
      "category": "account-bootstrap",
      "prompt": "...",
      "expected_output": "...",
      "files": []
    }
  ]
}
```

Fields:
- `skill_name` — logical name of the eval pack
- `evals` — list of eval cases
- `id` — unique numeric identifier
- `category` — optional scenario grouping
- `prompt` — the user prompt to test
- `expected_output` — rubric-style expectation for what a good answer should include
- `files` — optional repo files relevant to the eval

## Runner

Use the lightweight eval utility:

```bash
python3 scripts/run_evals.py --format summary
python3 scripts/run_evals.py --format json
python3 scripts/run_evals.py --format markdown
```

Default input path:
- `evals/evals.json`

You can also point it at another file:

```bash
python3 scripts/run_evals.py --path evals/evals.json --format summary
```

## What the runner does today

The current runner is intentionally lightweight.

It can:
- load and validate eval pack structure
- reject malformed packs and duplicate eval IDs
- print a summary
- export the pack as pretty JSON
- render a markdown-friendly prompt pack

It does not yet:
- call a model automatically
- grade live responses
- score rubric matches
- compare transcript outputs

## Suggested next step for evals

A future version of the runner can add:
- transcript ingestion
- rubric-based scoring
- provider/model labels for result tracking
- live eval execution against multiple agent environments
- pass/fail summaries by category

## Source-of-truth reminder

When an eval depends on current Chutes model inventory, pricing, TEE state, or capability metadata, the live source of truth is:

`https://llm.chutes.ai/v1/models`

Static docs and snapshots in this repo are convenience references only.
