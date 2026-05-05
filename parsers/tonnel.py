"""Tonnel marketplace parser — requires TONNEL_TOKEN in .env."""
from __future__ import annotations

import json
import logging

import aiohttp

import config
from gifts import Gift
from .base import Platform, PriceResult, nanoton_to_ton, looks_like_nanoton

logger = logging.getLogger(__name__)

PAGE_GIFTS_URL = "https://gifts2.tonnel.network/api/pageGifts"
FILTER_STATS_URL = "https://gifts3.tonnel.network/api/filterStats"

_SORT_PRICE_ASC = json.dumps({"price": 1, "gift_id": -1})


def _make_url(gift: Gift) -> str:
    return f"https://market.tonnel.network/gift/{gift.getgems_slug}"


def _build_headers(authority: str) -> dict:
    return {
        "authority": authority,
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "origin": "https://market.tonnel.network",
        "referer": "https://market.tonnel.network/",
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
    }


async def _try_filter_stats(session: aiohttp.ClientSession, gift: Gift) -> float | None:
    """Get floor price from the filterStats endpoint (faster, one call per collection)."""
    payload = {"user_auth": config.TONNEL_TOKEN}
    try:
        async with session.post(
            FILTER_STATS_URL,
            json=payload,
            headers=_build_headers("gifts3.tonnel.network"),
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            resp.raise_for_status()
            data = await resp.json(content_type=None)

        # Expected shape: {"data": {"Artisan Brick": {"Duck Bath": {"floorPrice": N, ...}}}}
        inner = data.get("data") or data
        coll = inner.get(gift.collection) or {}
        model_data = coll.get(gift.model) or {}
        raw = model_data.get("floorPrice") or model_data.get("floor_price")
        if raw is not None:
            price = float(raw)
            return nanoton_to_ton(price) if looks_like_nanoton(price) else price
    except Exception as e:
        logger.debug("Tonnel filterStats error: %s", e)
    return None


async def _try_page_gifts(session: aiohttp.ClientSession, gift: Gift) -> float | None:
    """Get cheapest listing via the pageGifts search endpoint."""
    filter_dict: dict = {"name": gift.collection}
    # Try both possible model key names
    for model_key in ("model_name", "model"):
        filter_dict[model_key] = gift.model

    payload = {
        "filter": json.dumps({"name": gift.collection, "model_name": gift.model}),
        "limit": 1,
        "page": 1,
        "sort": _SORT_PRICE_ASC,
        "price_range": 0,
        "user_auth": config.TONNEL_TOKEN,
    }
    try:
        async with session.post(
            PAGE_GIFTS_URL,
            json=payload,
            headers=_build_headers("gifts2.tonnel.network"),
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            resp.raise_for_status()
            data = await resp.json(content_type=None)

        items = data.get("gifts") or data.get("items") or data.get("data") or []
        if not items:
            # Retry with "model" key instead of "model_name"
            payload["filter"] = json.dumps({"name": gift.collection, "model": gift.model})
            async with session.post(
                PAGE_GIFTS_URL,
                json=payload,
                headers=_build_headers("gifts2.tonnel.network"),
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                resp.raise_for_status()
                data = await resp.json(content_type=None)
            items = data.get("gifts") or data.get("items") or data.get("data") or []

        if items:
            raw = items[0].get("price")
            if raw is not None:
                price = float(raw)
                return nanoton_to_ton(price) if looks_like_nanoton(price) else price
    except Exception as e:
        logger.debug("Tonnel pageGifts error: %s", e)
    return None


async def get_price(gift: Gift) -> PriceResult:
    url = _make_url(gift)
    if not config.TONNEL_TOKEN:
        return PriceResult(platform=Platform.TONNEL, error="No TONNEL_TOKEN configured")

    try:
        async with aiohttp.ClientSession() as session:
            price = await _try_filter_stats(session, gift)
            if price is None:
                price = await _try_page_gifts(session, gift)

        if price is not None:
            return PriceResult(platform=Platform.TONNEL, price_ton=price, url=url)
        return PriceResult(platform=Platform.TONNEL, error="No listing found")

    except aiohttp.ClientResponseError as e:
        if e.status == 401:
            return PriceResult(platform=Platform.TONNEL, error="Invalid TONNEL_TOKEN (401)")
        logger.warning("Tonnel HTTP error for %s: %s", gift.display_name, e)
        return PriceResult(platform=Platform.TONNEL, error=f"HTTP {e.status}")
    except Exception as e:
        logger.warning("Tonnel error for %s: %s", gift.display_name, e)
        return PriceResult(platform=Platform.TONNEL, error=str(e))
