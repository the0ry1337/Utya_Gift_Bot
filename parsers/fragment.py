"""Fragment marketplace parser — public web scraping, no auth required."""
from __future__ import annotations

import json
import logging
import re
from typing import Optional
from urllib.parse import quote_plus

import aiohttp

from gifts import Gift
from .base import Platform, PriceResult, nanoton_to_ton, looks_like_nanoton

logger = logging.getLogger(__name__)

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
}

JSON_HEADERS = {**HEADERS, "Accept": "application/json, text/javascript, */*; q=0.01",
                "X-Requested-With": "XMLHttpRequest"}


def _build_url(gift: Gift) -> str:
    slug = gift.fragment_slug
    model_encoded = quote_plus(gift.model)
    return f"https://fragment.com/gifts/{slug}?model={model_encoded}&sort=cheapest"


async def _try_json_api(session: aiohttp.ClientSession, gift: Gift) -> Optional[float]:
    """Try Fragment's internal JSON API endpoint."""
    slug = gift.fragment_slug
    endpoints = [
        f"https://fragment.com/api/gifts/{slug}?model={quote_plus(gift.model)}&sort=cheapest&count=1",
        f"https://fragment.com/api/gifts?type={slug}&model={quote_plus(gift.model)}&sort=cheapest&count=1",
        f"https://fragment.com/gifts/{slug}?model={quote_plus(gift.model)}&sort=cheapest",
    ]
    for ep in endpoints:
        try:
            async with session.get(
                ep, headers=JSON_HEADERS, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.content_type and "json" in resp.content_type:
                    data = await resp.json(content_type=None)
                    price = _extract_price_from_json(data)
                    if price is not None:
                        return price
        except Exception:
            continue
    return None


def _extract_price_from_json(data: dict | list) -> Optional[float]:
    """Walk common JSON response shapes to find a price."""
    if isinstance(data, list):
        if data:
            return _extract_price_from_json(data[0])
        return None
    if not isinstance(data, dict):
        return None

    for key in ("price", "floor_price", "floorPrice", "min_price", "minPrice"):
        val = data.get(key)
        if val is not None:
            try:
                price = float(val)
                return nanoton_to_ton(price) if looks_like_nanoton(price) else price
            except (TypeError, ValueError):
                pass

    for key in ("items", "gifts", "results", "data", "nfts"):
        val = data.get(key)
        if isinstance(val, list) and val:
            return _extract_price_from_json(val[0])
        if isinstance(val, dict):
            return _extract_price_from_json(val)
    return None


async def _scrape_html(session: aiohttp.ClientSession, gift: Gift) -> Optional[float]:
    """Fall back to scraping HTML from the Fragment gifts page."""
    url = _build_url(gift)
    try:
        async with session.get(
            url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=15)
        ) as resp:
            if resp.status != 200:
                return None
            html = await resp.text()

        # Look for embedded JSON data (common in SSR/Next.js apps)
        json_matches = re.findall(r'<script[^>]*type=["\']application/json["\'][^>]*>(.*?)</script>', html, re.DOTALL)
        for raw in json_matches:
            try:
                data = json.loads(raw)
                price = _extract_price_from_json(data)
                if price is not None:
                    return price
            except json.JSONDecodeError:
                pass

        # Look for price patterns in HTML text: numbers followed by TON
        # e.g. "49.5 TON" or "49,5 TON"
        prices = re.findall(r'([\d,]+(?:\.\d+)?)\s*TON', html)
        float_prices = []
        for p in prices:
            try:
                float_prices.append(float(p.replace(",", ".")))
            except ValueError:
                pass
        if float_prices:
            return min(float_prices)

    except Exception as e:
        logger.debug("Fragment HTML scrape error for %s: %s", gift.display_name, e)
    return None


async def get_price(gift: Gift) -> PriceResult:
    url = _build_url(gift)
    try:
        async with aiohttp.ClientSession() as session:
            price = await _try_json_api(session, gift)
            if price is None:
                price = await _scrape_html(session, gift)

        if price is not None:
            return PriceResult(platform=Platform.FRAGMENT, price_ton=price, url=url)
        return PriceResult(platform=Platform.FRAGMENT, error="No listing found")
    except Exception as e:
        logger.warning("Fragment error for %s: %s", gift.display_name, e)
        return PriceResult(platform=Platform.FRAGMENT, error=str(e))
