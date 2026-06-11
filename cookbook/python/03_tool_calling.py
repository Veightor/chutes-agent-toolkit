"""Tool / function calling round-trip. [VERIFIED 2026-06-11: ran live against the paid API]

Works on any model whose supported_features includes "tools"
(check GET https://llm.chutes.ai/v1/models — public).
Run: CHUTES_API_KEY=cpk_... python 03_tool_calling.py
"""

import json
import os

from openai import OpenAI

MODEL = os.environ.get("CHUTES_MODEL", "MiniMaxAI/MiniMax-M2.5-TEE")

client = OpenAI(base_url="https://llm.chutes.ai/v1", api_key=os.environ["CHUTES_API_KEY"])

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_word_length",
            "description": "Return the number of letters in a word.",
            "parameters": {
                "type": "object",
                "properties": {"word": {"type": "string"}},
                "required": ["word"],
            },
        },
    }
]

messages = [{"role": "user", "content": "How many letters are in 'decentralized'? Use the tool."}]

# 1. Model decides to call the tool
resp = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)
call = resp.choices[0].message.tool_calls[0]
args = json.loads(call.function.arguments)
print(f"model called {call.function.name}({args})")

# 2. Execute locally and send the result back
result = str(len(args["word"]))
messages.append(resp.choices[0].message)
messages.append({"role": "tool", "tool_call_id": call.id, "content": result})

final = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)
print(final.choices[0].message.content)
