"""Aggregates prices from all platforms concurrently with TTL caching."""
from __future__ import annotations

import asyncio
import time
import logging
from typing import Optional

import config
from gifts import Gift, GIFTS
from .base import AggregatedPrice, PriceResult
from . import getgems, fragment, mrkt, portals, tonnel

logger = logging.getLogger(__name__)

# Simple in-memory TTL cache: key → (timestamp, value)
_cache: dict[str, tuple[float, AggregatedPrice]] = {}


def _cache_key(gift: Gift) -> str:
    return f"{gift.collection}::{gift.model}"


def _get_cached(gift: Gift) -> Optional[AggregatedPrice]:
    entry = _cache.get(_cache_key(gift))
    if entry and (time.monotonic() - entry[0]) < config.CACHE_TTL:
        return entry[1]
    return None


def _set_cached(gift: Gift, value: AggregatedPrice) -> None:
    _cache[_cache_key(gift)] = (time.monotonic(), value)


def invalidate_cache() -> None:
    _cache.clear()


async def fetch_gift_prices(gift: Gift, use_cache: bool = True) -> AggregatedPrice:
    if use_cache:
        cached = _get_cached(gift)
        if cached is not None:
            return cached

    tasks = [
        getgems.get_price(gift),
        fragment.get_price(gift),
        mrkt.get_price(gift),
        portals.get_price(gift),
        tonnel.get_price(gift),
    ]
    results: list[PriceResult] = await asyncio.gather(*tasks, return_exceptions=False)

    agg = AggregatedPrice(gift=gift, results=list(results))
    _set_cached(gift, agg)
    return agg


async def fetch_all_prices(use_cache: bool = True) -> list[AggregatedPrice]:
    """Fetch prices for all 24 gifts concurrently."""
    results = await asyncio.gather(
        *[fetch_gift_prices(g, use_cache=use_cache) for g in GIFTS],
        return_exceptions=False,
    )
    return list(results)


def sort_by_best_deal(aggregated: list[AggregatedPrice]) -> list[AggregatedPrice]:
    """Sort gifts so the best deals (largest % below avg) come first."""
    def score(a: AggregatedPrice) -> float:
        if a.best_price is None:
            return float("inf")  # push no-data gifts to the end
        return a.best_price  # primary sort: absolute cheapest price

    return sorted(aggregated, key=score)
