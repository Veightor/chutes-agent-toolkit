"""Streaming completion (SSE deltas). [VERIFIED 2026-06-11: ran live against the paid API]

Run: CHUTES_API_KEY=cpk_... python 02_streaming.py
"""

import os

from openai import OpenAI

MODEL = os.environ.get("CHUTES_MODEL", "unsloth/Mistral-Nemo-Instruct-2407-TEE")

client = OpenAI(base_url="https://llm.chutes.ai/v1", api_key=os.environ["CHUTES_API_KEY"])

stream = client.chat.completions.create(
    model=MODEL,
    messages=[{"role": "user", "content": "Write a haiku about decentralized GPUs."}],
    stream=True,
)

for chunk in stream:
    if chunk.choices and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
print()
