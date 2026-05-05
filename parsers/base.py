from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from gifts import Gift


class Platform(str, Enum):
    GETGEMS = "GetGems"
    FRAGMENT = "Fragment"
    MRKT = "MRKT"
    PORTALS = "Portals"
    TONNEL = "Tonnel"


PLATFORM_EMOJI = {
    Platform.GETGEMS: "💎",
    Platform.FRAGMENT: "🔷",
    Platform.MRKT: "🔥",
    Platform.PORTALS: "🌀",
    Platform.TONNEL: "⚡",
}


@dataclass
class PriceResult:
    platform: Platform
    price_ton: Optional[float] = None
    url: Optional[str] = None
    error: Optional[str] = None

    @property
    def available(self) -> bool:
        return self.price_ton is not None


@dataclass
class AggregatedPrice:
    gift: "Gift"
    results: list[PriceResult] = field(default_factory=list)

    @property
    def available_results(self) -> list[PriceResult]:
        return [r for r in self.results if r.available]

    @property
    def best_price(self) -> Optional[float]:
        prices = [r.price_ton for r in self.available_results]
        return min(prices) if prices else None

    @property
    def best_result(self) -> Optional[PriceResult]:
        available = self.available_results
        if not available:
            return None
        return min(available, key=lambda r: r.price_ton)

    @property
    def avg_price(self) -> Optional[float]:
        prices = [r.price_ton for r in self.available_results]
        return sum(prices) / len(prices) if prices else None

    @property
    def deal_score(self) -> float:
        """Higher = better deal. % below average of all platforms."""
        best = self.best_price
        avg = self.avg_price
        if best is None or avg is None or avg == 0:
            return 0.0
        return (avg - best) / avg * 100


def nanoton_to_ton(value: str | int | float) -> float:
    return float(value) / 1_000_000_000


def looks_like_nanoton(value: float) -> bool:
    return value > 1_000_000
