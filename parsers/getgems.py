"""GetGems GraphQL API parser — public, no auth required."""
from __future__ import annotations

import logging
from typing import Optional

import aiohttp

from gifts import Gift
from .base import Platform, PriceResult, nanoton_to_ton

logger = logging.getLogger(__name__)

GRAPHQL_URL = "https://api.getgems.io/graphql"

# Step 1: find collection address by name
_SEARCH_COLLECTION = """
query SearchCollection($query: String!) {
  alphaNftCollectionSearch(query: $query, count: 10) {
    items {
      name
      rawAddress
      isVerified
    }
  }
}
"""

# Step 2: get cheapest for-sale items in that collection (fetch a batch, filter by model locally)
_GET_ITEMS = """
query GetCollectionItems($address: String!, $count: Int!) {
  alphaNftCollectionItems(
    collectionAddress: $address
    count: $count
    orderBy: { key: PRICE, direction: ASC }
    filter: { onSale: true }
  ) {
    items {
      name
      attributes {
        traitType
        value
      }
      sale {
        ... on NftSaleFixPrice {
          fullPrice
        }
      }
    }
  }
}
"""

# Fallback: search by NFT name (model) across all collections
_SEARCH_NFTS = """
query SearchNFTs($query: String!, $count: Int!) {
  alphaNftSearch(query: $query, count: $count, isOnSale: true) {
    items {
      name
      collection {
        name
      }
      attributes {
        traitType
        value
      }
      sale {
        ... on NftSaleFixPrice {
          fullPrice
        }
      }
    }
  }
}
"""

# Cache: collection_name → raw_address
_collection_cache: dict[str, str] = {}


async def _graphql(session: aiohttp.ClientSession, query: str, variables: dict) -> dict:
    async with session.post(
        GRAPHQL_URL,
        json={"query": query, "variables": variables},
        headers={"Content-Type": "application/json"},
        timeout=aiohttp.ClientTimeout(total=15),
    ) as resp:
        resp.raise_for_status()
        return await resp.json()


def _extract_model(attributes: list[dict]) -> str:
    for attr in attributes:
        key = attr.get("traitType", attr.get("key", "")).lower()
        if key == "model":
            return attr.get("value", "")
    return ""


async def _find_collection_address(session: aiohttp.ClientSession, collection_name: str) -> Optional[str]:
    if collection_name in _collection_cache:
        return _collection_cache[collection_name]

    data = await _graphql(session, _SEARCH_COLLECTION, {"query": collection_name})
    items = data.get("data", {}).get("alphaNftCollectionSearch", {}).get("items", [])

    for item in items:
        name = item.get("name", "")
        if name.lower() == collection_name.lower() or collection_name.lower() in name.lower():
            addr = item.get("rawAddress", "")
            if addr:
                _collection_cache[collection_name] = addr
                return addr
    return None


async def get_price(gift: Gift) -> PriceResult:
    url = f"https://getgems.io/gift/{gift.getgems_slug}"
    try:
        async with aiohttp.ClientSession() as session:
            # Try direct collection lookup first
            address = await _find_collection_address(session, gift.collection)
            if address:
                data = await _graphql(session, _GET_ITEMS, {"address": address, "count": 50})
                items = (
                    data.get("data", {})
                    .get("alphaNftCollectionItems", {})
                    .get("items", [])
                )
                for item in items:
                    if _extract_model(item.get("attributes", [])).lower() == gift.model.lower():
                        sale = item.get("sale") or {}
                        raw_price = sale.get("fullPrice")
                        if raw_price:
                            return PriceResult(
                                platform=Platform.GETGEMS,
                                price_ton=nanoton_to_ton(raw_price),
                                url=url,
                            )

            # Fallback: search by model name
            data = await _graphql(session, _SEARCH_NFTS, {"query": gift.model, "count": 20})
            items = data.get("data", {}).get("alphaNftSearch", {}).get("items", [])
            for item in items:
                coll_name = (item.get("collection") or {}).get("name", "")
                if coll_name.lower() != gift.collection.lower():
                    continue
                if _extract_model(item.get("attributes", [])).lower() != gift.model.lower():
                    continue
                sale = item.get("sale") or {}
                raw_price = sale.get("fullPrice")
                if raw_price:
                    return PriceResult(
                        platform=Platform.GETGEMS,
                        price_ton=nanoton_to_ton(raw_price),
                        url=url,
                    )

        return PriceResult(platform=Platform.GETGEMS, error="No listing found")
    except Exception as e:
        logger.warning("GetGems error for %s: %s", gift.display_name, e)
        return PriceResult(platform=Platform.GETGEMS, error=str(e))
