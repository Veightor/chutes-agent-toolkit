"""Video generation on a media chute. [VERIFIED 2026-08-06: ran live against the paid API]

Video/image/audio chutes are NOT on the OpenAI-compatible gateway. Each one is
served on its own host (`https://<slug>.chutes.ai`) and takes a FLAT JSON body
on `POST /generate` — no `model` field, no `input_args` wrapper. The response
body is the raw media bytes (here: MP4 with H.264 video + AAC stereo audio).

Two gotchas that don't exist for chat models:

1. The call is SYNCHRONOUS — the connection stays open for the whole render,
   and the public edge returns HTTP 504 at ~600 s regardless of the chute's
   own 1800 s cord limit (measured live: 8 s @ 30 steps 504'd at 600.2 s,
   while this file's 4 s @ 20 steps config completed in 272 s). Instances
   serialize renders on a GPU semaphore, so QUEUE TIME COUNTS: two of these
   requests in flight at once both 504'd; run one at a time. Treat a
   non-200 / non-video/mp4 response as failure even if bytes arrived.
2. The published llms.txt/openapi for community chutes may under-document the
   schema. The authoritative contract is the chute's own source code:
   `GET https://api.chutes.ai/chutes/code/<chute_id>` (works with your normal
   API key) — the pydantic `*Input` class in it is the real request schema.

Model: MiniMax H3 FL2VA (vonkaiser-minimaxh3fl2va) — text/image-to-video with
native audio, 768p short side, 24 fps. Full request schema (from chute source):

    prompt              str, required, 1..7000 chars
    first_image_b64     str, optional — first-frame conditioning (image-to-video)
    last_image_b64      str, optional — last-frame conditioning
    duration            int seconds, 4..10 (default 5)
    aspect_ratio        one of 21:9 16:9 4:3 1:1 3:4 9:16 (default 16:9)
    num_inference_steps int, 10..50 (default 30; more = slower + better)
    seed                int, optional, 0..2**32-1

Run: CHUTES_API_KEY=cpk_... python 08_video_generation.py "a corgi surfing"
Cost: media chutes bill per compute-second (this chute: $1.80/hr GPU rate),
so a 5 s clip at 20 steps costs on the order of $0.10-0.30, not fractions of
a cent like chat calls. Budget accordingly.
"""

import json
import os
import sys
import time
import urllib.request

CHUTE_HOST = "https://vonkaiser-minimaxh3fl2va.chutes.ai"
OUT_PATH = "video_out.mp4"

prompt = sys.argv[1] if len(sys.argv) > 1 else (
    "A red fox trotting through a snowy pine forest at dawn, snow crunching underfoot."
)

body = {
    "prompt": prompt,
    "duration": 4,               # 4-10 s; 4 and 5 both hit the 124-frame floor -> 5.2 s of video
    "aspect_ratio": "16:9",      # 1344x768; see docstring for the other five
    "num_inference_steps": 20,   # 10-50; 20 is a good speed/quality test setting
    "seed": 42,                  # reproducible output
}

req = urllib.request.Request(
    f"{CHUTE_HOST}/generate",
    data=json.dumps(body).encode(),
    headers={
        "Authorization": f"Bearer {os.environ['CHUTES_API_KEY']}",
        "Content-Type": "application/json",
    },
)

print(f"Rendering ({body['duration']}s @ {body['num_inference_steps']} steps) — this takes minutes...")
t0 = time.time()
# The edge 504s at ~600 s; 650 covers that plus response streaming. urllib
# raises HTTPError on the 504, so a completed `with` block means real media.
with urllib.request.urlopen(req, timeout=650) as resp, open(OUT_PATH, "wb") as f:
    ctype = resp.headers.get("Content-Type", "")
    if ctype != "video/mp4":
        sys.exit(f"Expected video/mp4, got {ctype!r}")
    while chunk := resp.read(1 << 20):
        f.write(chunk)

size = os.path.getsize(OUT_PATH)
print(f"Wrote {OUT_PATH} ({size / 1e6:.1f} MB) in {time.time() - t0:.0f}s")
