"""Portals marketplace parser — requires PORTALS_TOKEN in .env."""
from __future__ import annotations

import logging
from urllib.parse import urlencode

import aiohttp

import config
from gifts import Gift
from .base import Platform, PriceResult, nanoton_to_ton, looks_like_nanoton

logger = logging.getLogger(__name__)

BASE_URL = "https://portals-market.com/api/"


def _make_url(gift: Gift) -> str:
    return f"https://portals-market.com/gifts/{gift.getgems_slug}"


async def get_price(gift: Gift) -> PriceResult:
    url = _make_url(gift)
    if not config.PORTALS_TOKEN:
        return PriceResult(platform=Platform.PORTALS, error="No PORTALS_TOKEN configured")

    headers = {
        "Authorization": config.PORTALS_TOKEN,
        "Accept": "application/json, text/plain, */*",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
    }

    # Try filterFloors first (returns per-model floor prices efficiently)
    floors_url = BASE_URL + "collections/filters?" + urlencode({"collection": gift.collection})
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                floors_url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                resp.raise_for_status()
                data = await resp.json(content_type=None)

            models = data.get("models") or data.get("floorPrices") or {}
            model_data = models.get(gift.model)
            if model_data:
                raw = model_data.get("floorPrice") or model_data.get("floor_price") or model_data.get("price")
                if raw is not None:
                    price = float(raw)
                    ton = nanoton_to_ton(price) if looks_like_nanoton(price) else price
                    return PriceResult(platform=Platform.PORTALS, price_ton=ton, url=url)

            # Fall back to search
            params = urlencode({
                "collection": gift.collection,
                "model": gift.model,
                "sort": "price_asc",
                "limit": 1,
                "offset": 0,
            })
            async with session.get(
                BASE_URL + "nfts/search?" + params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                resp.raise_for_status()
                data = await resp.json(content_type=None)

            results = data.get("results") or data.get("items") or data.get("nfts") or []
            if not results:
                return PriceResult(platform=Platform.PORTALS, error="No listing found")

            raw = results[0].get("price") or results[0].get("floor_price")
            if raw is None:
                return PriceResult(platform=Platform.PORTALS, error="Price field missing")

            price = float(raw)
            ton = nanoton_to_ton(price) if looks_like_nanoton(price) else price
            return PriceResult(platform=Platform.PORTALS, price_ton=ton, url=url)

    except aiohttp.ClientResponseError as e:
        if e.status == 401:
            return PriceResult(platform=Platform.PORTALS, error="Invalid PORTALS_TOKEN (401)")
        logger.warning("Portals HTTP error for %s: %s", gift.display_name, e)
        return PriceResult(platform=Platform.PORTALS, error=f"HTTP {e.status}")
    except Exception as e:
        logger.warning("Portals error for %s: %s", gift.display_name, e)
        return PriceResult(platform=Platform.PORTALS, error=str(e))
