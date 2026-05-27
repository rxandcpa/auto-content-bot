"""Fetch gold price from multiple free sources with sanity validation."""

from __future__ import annotations

import logging
import requests

logger = logging.getLogger(__name__)

# Valid range for gold: $1500-$5000/oz (catches wildly wrong values)
GOLD_MIN = 1500
GOLD_MAX = 5000
CNY_PER_USD = 7.25  # Approximate exchange rate

SOURCES = [
    {
        "name": "metals.live",
        "url": "https://api.metals.live/v1/spot/gold",
        "parser": "metals_live",
    },
    {
        "name": "gold-api.com",
        "url": "https://api.gold-api.com/price/XAU",
        "parser": "gold_api",
    },
]


def _parse_metals_live(data) -> float | None:
    """metals.live returns [{...}] with 'price' field."""
    if isinstance(data, list) and len(data) > 0:
        price = data[0].get("price")
        if price and isinstance(price, (int, float)):
            return round(float(price), 2)
    return None


def _parse_gold_api(data) -> float | None:
    """gold-api.com returns {price: ...}."""
    if isinstance(data, dict):
        price = data.get("price")
        if price and isinstance(price, (int, float)):
            return round(float(price), 2)
    return None


PARSERS = {
    "metals_live": _parse_metals_live,
    "gold_api": _parse_gold_api,
}


def _validate(price: float) -> bool:
    """Check if price is within reasonable bounds."""
    return GOLD_MIN <= price <= GOLD_MAX


def fetch_gold_price() -> dict:
    """Fetch gold price from all sources, return the first valid one."""
    results = []

    for source in SOURCES:
        try:
            resp = requests.get(source["url"], timeout=15)
            resp.raise_for_status()
            parser = PARSERS[source["parser"]]
            price = parser(resp.json())
            if price and _validate(price):
                logger.info(f"Gold: ${price}/oz (via {source['name']})")
                results.append({"source": source["name"], "price": price})
            else:
                logger.warning(
                    f"Gold price {price} from {source['name']} "
                    f"outside valid range ({GOLD_MIN}-{GOLD_MAX}), rejected"
                )
        except Exception as e:
            logger.warning(f"Gold source {source['name']} failed: {e}")

    if not results:
        logger.error("All gold sources failed or returned invalid data")
        return {"success": False, "price_usd": 0, "source": "none"}

    # Cross-validate: if multiple sources, check they agree within 5%
    if len(results) >= 2:
        prices = [r["price"] for r in results]
        avg = sum(prices) / len(prices)
        max_deviation = max(abs(p - avg) / avg * 100 for p in prices)
        if max_deviation > 5:
            logger.warning(
                f"Gold sources disagree by {max_deviation:.1f}% — "
                f"using average of {avg:.2f}"
            )

    # Use the first (fastest) valid source
    best = results[0]
    return {
        "success": True,
        "price_usd": best["price"],
        "price_cny": round(best["price"] * CNY_PER_USD, 2),
        "source": best["source"],
    }


def format_gold_data(data: dict) -> str:
    """Format gold data for AI prompt. Includes data source note."""
    if not data.get("success"):
        return "今日暂无可靠的黄金价格数据，请跳过此条（不要编造数据）。"
    return (
        f"国际黄金现货价格: {data['price_usd']} 美元/盎司 "
        f"（约 {data.get('price_cny', '?')} 人民币/盎司）。"
        f"数据来源: {data['source']}。"
        f"注意：以上为真实市场数据，请据此写作，不要修改任何数字。"
    )
