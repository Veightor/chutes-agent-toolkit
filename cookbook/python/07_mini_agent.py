"""A complete tool-calling agent on Chutes in ~100 lines. [VERIFIED 2026-06-11: ran live against the paid API]

The loop every agent framework wraps: model picks tools, we execute them,
results go back, repeat until the model answers in plain text. No framework,
one dependency (openai), running entirely on open-source TEE models.

Run: CHUTES_API_KEY="<redacted>" python 07_mini_agent.py "What is 21 * 2, and how many letters is the answer spelled out in English?"
"""

import json
import os
import sys

from openai import OpenAI

MODEL = os.environ.get("CHUTES_MODEL", "MiniMaxAI/MiniMax-M2.5-TEE")
MAX_TURNS = 8

# --- tools: plain python functions + their OpenAI schemas -------------------

def calculator(expression: str) -> str:
    """Evaluate basic arithmetic like '21 * 2'. Digits and + - * / ( ) . only."""
    if not set(expression) <= set("0123456789+-*/(). "):
        return "error: only basic arithmetic is allowed"
    try:
        return str(eval(expression, {"__builtins__": {}}, {}))
    except Exception as e:  # noqa: BLE001 - report any eval failure to the model
        return f"error: {e}"

def count_letters(text: str) -> str:
    """Count the letters (a-z only) in a piece of text."""
    return str(sum(c.isalpha() for c in text))

REGISTRY = {"calculator": calculator, "count_letters": count_letters}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": name,
            "description": fn.__doc__,
            "parameters": {
                "type": "object",
                "properties": {arg: {"type": "string"} for arg in fn.__code__.co_varnames[: fn.__code__.co_argcount]},
                "required": list(fn.__code__.co_varnames[: fn.__code__.co_argcount]),
            },
        },
    }
    for name, fn in REGISTRY.items()
]

# --- the agent loop ----------------------------------------------------------

def run_agent(task: str) -> str:
    client = OpenAI(base_url="https://llm.chutes.ai/v1", api_key=os.environ["CHUTES_API_KEY"])
    messages = [
        {"role": "system", "content": "You are a precise assistant. Use the tools for any math or counting; do not do it in your head."},
        {"role": "user", "content": task},
    ]

    for turn in range(MAX_TURNS):
        resp = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)
        msg = resp.choices[0].message

        if not msg.tool_calls:  # plain answer -> done
            return msg.content

        messages.append(msg)
        for call in msg.tool_calls:
            fn = REGISTRY[call.function.name]
            args = json.loads(call.function.arguments)
            result = fn(**args)
            print(f"  [turn {turn}] {call.function.name}({args}) -> {result}")
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})

    return "(gave up: hit MAX_TURNS without a final answer)"


if __name__ == "__main__":
    task = sys.argv[1] if len(sys.argv) > 1 else (
        "What is 21 * 2, and how many letters is the answer spelled out in English?"
    )
    print(f"task: {task}\n")
    print("\nanswer:", run_agent(task))
