"""Schema-enforced structured output. [VERIFIED 2026-06-11: ran live against the paid API]

Works on models advertising "structured_outputs"; for looser JSON use
response_format={"type": "json_object"} on models advertising "json_mode".
Run: CHUTES_API_KEY=cpk_... python 04_structured_output.py
"""

import json
import os

from openai import OpenAI

MODEL = os.environ.get("CHUTES_MODEL", "MiniMaxAI/MiniMax-M2.5-TEE")

client = OpenAI(base_url="https://llm.chutes.ai/v1", api_key=os.environ["CHUTES_API_KEY"])

SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "model_review",
        "schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "pros": {"type": "array", "items": {"type": "string"}},
                "score": {"type": "integer", "minimum": 1, "maximum": 10},
            },
            "required": ["summary", "pros", "score"],
        },
    },
}

resp = client.chat.completions.create(
    model=MODEL,
    messages=[{"role": "user", "content": "Review the idea of running agents on open-source models."}],
    response_format=SCHEMA,
)

data = json.loads(resp.choices[0].message.content)
print(json.dumps(data, indent=2))
