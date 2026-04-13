# Pre-Hermes Phase 2 Checklist

This checklist defines the work that should be finished in `chutes-agent-toolkit` before starting first-class Chutes provider work in a Hermes fork.

## Goal

Enter Hermes implementation work with:
- a clean repo
- stable toolkit docs
- tested credential tooling
- a usable eval baseline
- Hermes-facing integration assets that can be reused directly

## Why this matters

If these toolkit-side pieces are incomplete, Hermes integration work will end up carrying avoidable churn:
- duplicated docs
- unclear install stories
- insecure or underspecified credential handling
- weak test/eval scaffolding
- no clean artifact to point upstream maintainers at

## Required before Phase 2

### 1. Repo hygiene
- ignore generated files (`__pycache__`, `.pytest_cache`, `.hermes`, `.DS_Store`)
- avoid committing local plan artifacts and Python cache files
- make the repo state easy to review

### 2. Credential-tooling baseline
- keep `manage_credentials.py` as the primary secure storage path
- ensure basic command behavior is tested
- expose security posture clearly in docs
- make the fallback encrypted-file backend visible in `check`

### 3. Deprecation story for `save_credentials.py`
- make it clear this script is legacy-only
- document when, if ever, plaintext backup is still acceptable
- point new users toward `manage_credentials.py`

### 4. Hermes-ready assets in this repo
- Hermes quickstart doc
- Hermes config examples
- Hermes-oriented Chutes skill export/package layout
- clear distinction between current custom-provider support and future first-class provider support

### 5. Eval foundation
- multiple categorized eval prompts
- a runner that validates the pack and renders useful outputs
- explicit reminder that live model metadata comes from `https://llm.chutes.ai/v1/models`

### 6. README polish
- surface the new docs and Hermes assets
- keep repo structure/examples aligned with reality

## Definition of done for Phase 1 / toolkit-prep

This repo is ready to hand off into Hermes fork work when:
- tests pass cleanly
- working tree is clean aside from intentional tracked changes
- credential manager is documented and covered by basic tests
- eval runner exists and validates the eval pack
- Hermes docs/examples/skill export exist in-repo
- README points users to the right entry points

## Immediate execution order

1. repo hygiene
2. deprecation story
3. Hermes skill export/package layout
4. README polish
5. full test run
6. prep commit

## Commit target

Suggested prep commit scope:
- docs
- eval runner
- eval pack expansion
- credential-tooling improvements/tests
- Hermes quickstart/examples/skill export
- repo hygiene

Suggested commit message:

`feat: prepare toolkit for Hermes provider integration`
