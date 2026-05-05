"""
Auto-refreshes MRKT / Portals / Tonnel auth tokens via Pyrogram.

Flow:
  1. Opens a Pyrogram session (created once by setup_auth.py).
  2. Invokes RequestAppWebView for each marketplace mini-app to get fresh initData.
  3. For MRKT: exchanges initData for a JWT via their /auth endpoint.
  4. Writes updated tokens to .env and reloads config in-place.

Background task auto_refresh_loop() is started by bot.py.
"""
from __future__ import annotations

import asyncio
import importlib
import logging
import urllib.parse
from pathlib import Path

import aiohttp
from pyrogram import Client
from pyrogram.raw.functions.messages import RequestAppWebView
from pyrogram.raw.types import InputBotAppShortName

import config

logger = logging.getLogger(__name__)

SESSION_FILE = "utya_session"
REFRESH_INTERVAL_SEC = 20 * 3600  # refresh every 20 h (tokens last ~24-48 h)

# (bot_username, app_short_name)
# Short names come from the t.me/BotName/AppName URL of each mini-app.
_PORTALS = ("portals_market_bot", "market")    # t.me/portals_market_bot/market
_TONNEL  = ("Tonnel_Network_bot", "gifts")     # t.me/Tonnel_Network_bot/gifts
# MRKT short name is configurable via MRKT_APP_SHORT_NAME in .env (default "market").
# If auth fails, check the actual t.me/main_mrkt_bot/??? URL inside Telegram and update.
_MRKT_BOT = "main_mrkt_bot"


# ─── helpers ─────────────────────────────────────────────────────────────────

async def _get_init_data(client: Client, bot_username: str, short_name: str) -> str:
    """Invoke RequestAppWebView and extract tgWebAppData from the returned URL."""
    peer = await client.resolve_peer(bot_username)
    result = await client.invoke(
        RequestAppWebView(
            peer=peer,
            app=InputBotAppShortName(bot_id=peer, short_name=short_name),
            platform="android",
            start_param="",
        )
    )
    fragment = urllib.parse.urlparse(result.url).fragment
    params = urllib.parse.parse_qs(fragment)
    raw = params.get("tgWebAppData", [None])[0]
    return urllib.parse.unquote(raw) if raw else ""


async def _exchange_mrkt_jwt(init_data: str) -> str:
    """Exchange MRKT initData for a JWT via their /auth endpoint."""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.tgmrkt.io/api/v1/auth",
            json={"data": init_data},
            headers={"Content-Type": "application/json"},
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            resp.raise_for_status()
            data = await resp.json(content_type=None)
    # Field name varies across API versions
    return data.get("token") or data.get("access_token") or data.get("jwt") or ""


def _write_env(updates: dict[str, str], env_path: str = ".env") -> None:
    """Update existing keys (or append new ones) in the .env file."""
    path = Path(env_path)
    if not path.exists():
        path.write_text("")

    lines = path.read_text().splitlines()
    updated: set[str] = set()
    out: list[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in updates:
                out.append(f"{key}={updates[key]}")
                updated.add(key)
                continue
        out.append(line)

    for key, val in updates.items():
        if key not in updated:
            out.append(f"{key}={val}")

    path.write_text("\n".join(out) + "\n")


# ─── public API ──────────────────────────────────────────────────────────────

async def refresh_all_tokens() -> bool:
    """
    Connect to Telegram, refresh all marketplace tokens, persist to .env,
    and reload the config module so running parsers pick up the new values.
    Returns True if at least one token was updated.
    """
    if not config.TELEGRAM_API_ID or not config.TELEGRAM_API_HASH:
        logger.warning("TELEGRAM_API_ID / TELEGRAM_API_HASH not configured — skipping refresh")
        return False

    session_string = getattr(config, "SESSION_STRING", "")
    has_file = Path(f"{SESSION_FILE}.session").exists()

    if not session_string and not has_file:
        logger.error(
            "No Pyrogram session found. "
            "Run `python setup_auth.py` to create one, "
            "or set SESSION_STRING in .env for cloud platforms."
        )
        return False

    refreshed: dict[str, str] = {}
    mrkt_short = getattr(config, "MRKT_APP_SHORT_NAME", "market")

    client_kwargs: dict = {
        "api_id": int(config.TELEGRAM_API_ID),
        "api_hash": config.TELEGRAM_API_HASH,
    }
    if session_string:
        client_kwargs["session_string"] = session_string
        client_name = ":memory:"
    else:
        client_name = SESSION_FILE

    try:
        async with Client(client_name, **client_kwargs) as client:

            # MRKT — initData → JWT exchange
            try:
                init_data = await _get_init_data(client, _MRKT_BOT, mrkt_short)
                if init_data:
                    jwt = await _exchange_mrkt_jwt(init_data)
                    if jwt:
                        refreshed["MRKT_TOKEN"] = jwt
                        logger.info("✅ MRKT token refreshed")
                    else:
                        logger.error("MRKT auth exchange returned an empty token")
            except Exception as e:
                logger.error("MRKT refresh failed: %s", e)

            # Portals — raw initData with "tma " prefix
            try:
                bot, app = _PORTALS
                init_data = await _get_init_data(client, bot, app)
                if init_data:
                    refreshed["PORTALS_TOKEN"] = f"tma {init_data}"
                    logger.info("✅ Portals token refreshed")
            except Exception as e:
                logger.error("Portals refresh failed: %s", e)

            # Tonnel — raw initData
            try:
                bot, app = _TONNEL
                init_data = await _get_init_data(client, bot, app)
                if init_data:
                    refreshed["TONNEL_TOKEN"] = init_data
                    logger.info("✅ Tonnel token refreshed")
            except Exception as e:
                logger.error("Tonnel refresh failed: %s", e)

    except Exception as e:
        logger.error("Pyrogram session error: %s", e)
        return False

    if refreshed:
        _write_env(refreshed)
        importlib.reload(config)
        logger.info("Tokens saved to .env and config reloaded: %s", list(refreshed.keys()))
        return True

    return False


async def auto_refresh_loop() -> None:
    """
    Background asyncio task started by bot.py.
    On startup: immediately refreshes if any token is missing.
    Then refreshes every REFRESH_INTERVAL_SEC.
    """
    missing = not all([config.MRKT_TOKEN, config.PORTALS_TOKEN, config.TONNEL_TOKEN])
    if missing:
        logger.info("One or more tokens missing — running initial refresh in 15 s")
        await asyncio.sleep(15)
        await refresh_all_tokens()

    while True:
        await asyncio.sleep(REFRESH_INTERVAL_SEC)
        logger.info("Scheduled token refresh starting…")
        await refresh_all_tokens()
