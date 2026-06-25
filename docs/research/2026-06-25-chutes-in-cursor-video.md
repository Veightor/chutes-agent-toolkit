# Video study — "How to use Chutes in Cursor"

- **Source:** https://x.com/chutes_ai/status/2020924504583594312 (@chutes_ai)
- **Studied:** 2026-06-25
- **Format:** 84s, 1280×720, 30fps screen recording. Audio is **music only — no narration**, so all instructions are on-screen captions/UI. Analysis is frames-only (42 frames @ 1/2s), cross-checked across the sequence.

## What it is

A silent, captioned walkthrough of connecting **Chutes as an OpenAI-compatible model provider inside Cursor** — i.e. running open-source Chutes models in Cursor's chat/agent. (Not the MCP path.)

## Steps shown (verbatim from frames)

1. **Settings → Models** (gear icon → Models in the sidebar). Caption: "Click on the settings icon and go to models".
2. Expand **API Keys**. Caption step #2: "Override the openai endpoint with the chutes endpoint `https://llm.chutes.ai/v1`". Enable **Override OpenAI Base URL**, set field to `https://llm.chutes.ai/v1` (replaces default `https://api.openai.com/v1`).
3. Caption step #3: "Enable OpenAI API key and paste your Chutes API key instead." Enable **OpenAI API Key**, paste the Chutes `cpk_…` key into that field.
4. **Get the key** (caption: "Here's how to find your Chutes API Key"): chutes.ai/app → **API** tab → **API Keys** → **Create API Key** → name `cursor - demo` → Create → copy `cpk_…` ("Please copy your API key now. You won't be able to see it again!"). Account shown: Base plan, $3/month, 300 requests/day.
5. Caption: "Next Step — Get your Chutes Model name, and add a new model." On chutes.ai, search a model (demo searched `kimi`) and copy the ID, e.g. **`moonshotai/Kimi-K2.5-TEE`**.
6. In Cursor's **Add or search model** box, type the model ID → "No models available" → click **+ Add Custom Model** → it appears enabled.
7. Caption: "And Finally — Select it in your agent." Open the chat model dropdown (**Switch Model**, `⌘/`) → pick the custom model → type a test message. End card: "Enjoy!"

## Verified values (load-bearing)

- **Base URL:** `https://llm.chutes.ai/v1` (entered into Cursor "Override OpenAI Base URL")
- **Key field:** Cursor "OpenAI API Key" toggle — paste Chutes `cpk_…` key
- **Key source:** https://chutes.ai/app/api → API Keys → Create API Key (shown once)
- **Example model ID:** `moonshotai/Kimi-K2.5-TEE` (other Kimi models seen: `Kimi K2 Instruct 0905` FP8, `Kimi K2 Thinking TEE` INT4)

## Caveats / gaps

- No spoken audio — relies on on-screen captions only.
- No terminal commands or JSON config; this is a pure-UI flow distinct from the MCP server path.
- The override repoints Cursor's OpenAI provider, so OpenAI models route to Chutes while it's on. Toggle off to revert.
- Not toolkit-verified end-to-end → documented under **[BETA]** per repo beta-labeling policy.

## Where it landed

Folded into `plugins/chutes-ai/skills/chutes-mcp-portability/references/cursor-setup.md` as **Option A — Use Chutes models in Cursor (OpenAI-compatible) [BETA]**, with the video linked at the top. The pre-existing MCP instructions were preserved as **Option B**.
