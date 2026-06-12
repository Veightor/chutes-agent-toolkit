"""Image input (vision). [VERIFIED 2026-06-11: ran live against the paid API]

Works on models whose input_modalities include "image"
(e.g. the Qwen3.5/3.6 and Kimi-K2 lines — check /v1/models).

Images can be a data URI (shown here, always works) or a public URL — note that
some hosts (e.g. Wikimedia) block Chutes' server-side fetcher with 403, so
prefer data URIs or hosts you control.

Run: CHUTES_API_KEY=cpk_... python 06_vision.py [image_url]
"""

import os
import sys

from openai import OpenAI

MODEL = os.environ.get("CHUTES_MODEL", "Qwen/Qwen3.6-27B-TEE")

# 64x64 test card: red square with a blue corner patch
TEST_IMAGE = "data:image/png;base64," + (
    "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAIAAAAlC+aJAAAAb0lEQVR4nO3PwQmAQBAEwcs/"
    "aY1BEdqBgn7vTp1zrk/65srzDgAAAAAAAAAAAAAAAAAAAADAK0D1GADgJ/ULAMbrFwCM1y8A"
    "GK9fADBevwBgvH4BwHj9AoDx+gUA4/ULAMbrFwCM1y8AGK9fADDeDS4g8OINMbreAAAAAElF"
    "TkSuQmCC"
)
IMAGE_URL = sys.argv[1] if len(sys.argv) > 1 else TEST_IMAGE

client = OpenAI(base_url="https://llm.chutes.ai/v1", api_key=os.environ["CHUTES_API_KEY"])

resp = client.chat.completions.create(
    model=MODEL,
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe this image in one short sentence."},
                {"type": "image_url", "image_url": {"url": IMAGE_URL}},
            ],
        }
    ],
)
print(resp.choices[0].message.content)
