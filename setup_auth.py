"""
One-time Pyrogram session setup.

Run this ONCE before starting the bot:

    python setup_auth.py

Pyrogram will ask for your Telegram phone number and the OTP code.
After that it saves `utya_session.session` to disk.
The bot will use that file to refresh marketplace tokens automatically
— you will never be asked for a code again.
"""
import asyncio
import os
import sys

from dotenv import load_dotenv
from pyrogram import Client

load_dotenv()

API_ID = os.getenv("TELEGRAM_API_ID", "")
API_HASH = os.getenv("TELEGRAM_API_HASH", "")

if not API_ID or not API_HASH:
    print("❌  TELEGRAM_API_ID and TELEGRAM_API_HASH are not set in .env")
    print("    Get them at https://my.telegram.org/apps  →  create an app")
    sys.exit(1)


async def main() -> None:
    print("Connecting to Telegram…")
    async with Client("utya_session", api_id=int(API_ID), api_hash=API_HASH) as client:
        me = await client.get_me()
        name = f"{me.first_name or ''} {me.last_name or ''}".strip()
        uname = f"@{me.username}" if me.username else "(no username)"
        print(f"\n✅  Session created for {name} {uname}")
        print("    File: utya_session.session")
        print("\nYou can now start the bot:  python bot.py")
        print("Tokens will be refreshed automatically every 20 hours.")


if __name__ == "__main__":
    asyncio.run(main())
