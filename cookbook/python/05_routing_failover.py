"""Inline model routing: failover pool + latency strategy. [VERIFIED 2026-06-11: ran live against the paid API]

Pass several model IDs comma-separated in the `model` field:
  - plain list            -> sequential failover (try in order)
  - list + ":latency"     -> fastest first token right now
  - list + ":throughput"  -> most tokens/sec right now
A single concrete model ID bypasses routing entirely.
Run: CHUTES_API_KEY=cpk_... python 05_routing_failover.py
"""

import os

from openai import OpenAI

POOL = os.environ.get(
    "CHUTES_POOL",
    "MiniMaxAI/MiniMax-M2.5-TEE,deepseek-ai/DeepSeek-V3.2-TEE,zai-org/GLM-5-TEE",
)

client = OpenAI(base_url="https://llm.chutes.ai/v1", api_key=os.environ["CHUTES_API_KEY"])

# Sequential failover: if the first model is busy or down, the next one answers.
resp = client.chat.completions.create(
    model=POOL,
    messages=[{"role": "user", "content": "Which model are you? One sentence."}],
)
print("failover  ->", resp.model, "|", resp.choices[0].message.content)

# Latency strategy: route to whichever pool member has the lowest TTFT right now.
resp = client.chat.completions.create(
    model=f"{POOL}:latency",
    messages=[{"role": "user", "content": "Reply with the single word: pong"}],
)
print("latency   ->", resp.model, "|", resp.choices[0].message.content)
