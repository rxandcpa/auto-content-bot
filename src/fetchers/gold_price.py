"""Fetch international gold price from free public API."""

from __future__ import annotations

import logging
import requests

logger = logging.getLogger(__name__)

# Free gold price API (no key required)
GOLD_API_URL = "https://api.gold-api.com/price/XAU"


def fetch_gold_price() -> dict:
    """
    Returns gold price data or empty dict on failure.
    Expected fields: price (USD/oz), currency, timestamp.
    """
    try:
        resp = requests.get(GOLD_API_URL, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        price = data.get("price", 0)
        logger.info(f"Gold price fetched: ${price}/oz")
        return {
            "price_usd": price,
            "source": "gold-api.com",
            "success": True,
        }
    except Exception as e:
        logger.warning(f"Gold price fetch failed: {e}")
        # Try backup source
        return _fetch_backup()


def _fetch_backup() -> dict:
    """Fallback: scrape from alternative free source."""
    try:
        # Use metals-api free endpoint
        resp = requests.get(
            "https://api.metals.live/v1/spot/gold",
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        price = data[0].get("price", 0) if isinstance(data, list) else 0
        return {
            "price_usd": round(price, 2),
            "source": "metals.live",
            "success": True,
        }
    except Exception as e:
        logger.error(f"Backup gold price fetch also failed: {e}")
        return {"success": False, "price_usd": 0}


def format_gold_data(data: dict) -> str:
    """Convert raw gold data into a text summary for AI rewriting."""
    if not data.get("success"):
        return "今日暂无金价数据，请忽略此条。"
    price = data["price_usd"]
    # Approximate RMB conversion (rough estimate)
    price_cny = round(price * 7.25, 2)
    return (
        f"国际黄金价格: {price} 美元/盎司 (约 {price_cny} 元人民币/盎司)。"
        f"数据来源: {data['source']}。"
    )
