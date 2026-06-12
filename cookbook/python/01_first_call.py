"""Minimal Chutes chat completion. [VERIFIED 2026-06-11: ran live against the paid API]

Chutes speaks the OpenAI API: change the base_url, keep everything else.
Run: CHUTES_API_KEY="<redacted>" python 01_first_call.py
"""

import os

from openai import OpenAI

MODEL = os.environ.get("CHUTES_MODEL", "unsloth/Mistral-Nemo-Instruct-2407-TEE")

client = OpenAI(
    base_url="https://llm.chutes.ai/v1",
    api_key=os.environ["CHUTES_API_KEY"],  # sent as Authorization: Bearer
)

resp = client.chat.completions.create(
    model=MODEL,
    messages=[{"role": "user", "content": "Say hello in one short sentence."}],
)

print(resp.choices[0].message.content)
u = resp.usage
print(f"\n[{MODEL}] {u.prompt_tokens} in / {u.completion_tokens} out tokens")
