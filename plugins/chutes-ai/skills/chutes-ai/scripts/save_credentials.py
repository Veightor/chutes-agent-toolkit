#!/usr/bin/env python3
"""
Save Chutes.ai credentials to a local backup file.
Usage: python save_credentials.py --username NAME --fingerprint FP --user-id UID [--api-key KEY] [--output PATH]
"""
import argparse
import os
from datetime import datetime


def main():
    parser = argparse.ArgumentParser(description="Save Chutes.ai credentials to a backup file")
    parser.add_argument("--username", required=True, help="Chutes.ai username")
    parser.add_argument("--fingerprint", required=True, help="32-character fingerprint")
    parser.add_argument("--user-id", required=True, help="User UUID")
    parser.add_argument("--api-key", default=None, help="API key (cpk_...)")
    parser.add_argument("--output", default="chutes-credentials-backup.txt", help="Output file path")
    args = parser.parse_args()

    content = f"""========================================
  CHUTES.AI CREDENTIALS BACKUP
  Created: {datetime.now().isoformat()}
========================================

IMPORTANT: Keep this file secure. Do NOT commit it to git or share it publicly.

Username:    {args.username}
User ID:     {args.user_id}
Fingerprint: {args.fingerprint}
"""

    if args.api_key:
        content += f"API Key:     {args.api_key}\n"

    content += """
--- RECOVERY INFO ---
If you lose your fingerprint, you can reset it IF you have a linked Bittensor wallet:
  - Web: https://chutes.ai/auth/reset
  - API: POST https://api.chutes.ai/users/change_fingerprint

If you lose your API key, just create a new one:
  POST https://api.chutes.ai/api_keys/
  Body: { "name": "replacement-key", "admin": false }

--- QUICK START ---
Base URLs:
  Management: https://api.chutes.ai
  Inference:  https://llm.chutes.ai/v1

Auth header:
  Authorization: Bearer <your-api-key>

Dashboard: https://chutes.ai/app
Docs:      https://chutes.ai/docs
"""

    with open(args.output, "w") as f:
        f.write(content)

    print(f"Credentials saved to: {os.path.abspath(args.output)}")
    print("Remember to store this file somewhere safe!")


if __name__ == "__main__":
    main()
