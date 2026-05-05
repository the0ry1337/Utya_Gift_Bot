"""MRKT marketplace parser — requires MRKT_TOKEN in .env."""
from __future__ import annotations

import logging

import aiohttp

import config
from gifts import Gift
from .base import Platform, PriceResult, nanoton_to_ton, looks_like_nanoton

logger = logging.getLogger(__name__)

API_URL = "https://api.tgmrkt.io/api/v1/gifts/saling"


def _make_url(gift: Gift) -> str:
    return f"https://mrkt.fun/en/gifts/{gift.getgems_slug}"


async def get_price(gift: Gift) -> PriceResult:
    url = _make_url(gift)
    if not config.MRKT_TOKEN:
        return PriceResult(platform=Platform.MRKT, error="No MRKT_TOKEN configured")

    headers = {
        "Authorization": config.MRKT_TOKEN,
        "Referer": "https://cdn.tgmrkt.io/",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {
        "collectionNames": [gift.collection],
        "modelNames": [gift.model],
        "ordering": "Price",
        "lowToHigh": True,
        "count": 1,
        "cursor": "",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                API_URL,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                resp.raise_for_status()
                data = await resp.json(content_type=None)

        gifts = data.get("gifts") or data.get("items") or data.get("data") or []
        if not gifts:
            return PriceResult(platform=Platform.MRKT, error="No listing found")

        raw_price = gifts[0].get("price") or gifts[0].get("fullPrice")
        if raw_price is None:
            return PriceResult(platform=Platform.MRKT, error="Price field missing")

        price = float(raw_price)
        ton = nanoton_to_ton(price) if looks_like_nanoton(price) else price
        return PriceResult(platform=Platform.MRKT, price_ton=ton, url=url)

    except aiohttp.ClientResponseError as e:
        if e.status == 401:
            return PriceResult(platform=Platform.MRKT, error="Invalid MRKT_TOKEN (401)")
        logger.warning("MRKT HTTP error for %s: %s", gift.display_name, e)
        return PriceResult(platform=Platform.MRKT, error=f"HTTP {e.status}")
    except Exception as e:
        logger.warning("MRKT error for %s: %s", gift.display_name, e)
        return PriceResult(platform=Platform.MRKT, error=str(e))
