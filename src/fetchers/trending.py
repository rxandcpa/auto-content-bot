"""Fetch trending/hot topics from public sources."""

from __future__ import annotations

import logging
import requests

logger = logging.getLogger(__name__)

# Weibo hot search API (public, no auth needed)
WEIBO_API = "https://weibo.com/ajax/side/hotSearch"

# Fallback: Baidu hot search
BAIDU_API = "https://top.baidu.com/board?tab=realtime"


def fetch_weibo_trending() -> dict:
    """Fetch Weibo hot search list. Returns dict with trending items."""
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json",
        }
        resp = requests.get(WEIBO_API, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        items = []
        # Weibo API structure: data["data"]["realtime"]
        realtime = data.get("data", {}).get("realtime", [])
        for item in realtime[:20]:
            word = item.get("word", "").strip()
            rank = item.get("rank", 0)
            if word:
                items.append({"rank": rank, "word": word, "source": "微博热搜"})
        if items:
            logger.info(f"Fetched {len(items)} Weibo trending topics")
            return {"success": True, "items": items, "source": "weibo"}
    except Exception as e:
        logger.warning(f"Weibo trending fetch failed: {e}")

    return _fetch_baidu_fallback()


def _fetch_baidu_fallback() -> dict:
    """Fallback: scrape Baidu hot search."""
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36"
            ),
        }
        resp = requests.get(BAIDU_API, headers=headers, timeout=15)
        resp.raise_for_status()
        # Parse HTML for trending items
        import re
        # Look for title patterns in the HTML
        items = []
        matches = re.findall(r'<div class="c-single-text-ellipsis">(.+?)</div>', resp.text)
        for i, word in enumerate(matches[:15]):
            word = word.strip()
            if word and len(word) > 2:
                items.append({"rank": i + 1, "word": word, "source": "百度热搜"})
        if items:
            logger.info(f"Fetched {len(items)} Baidu trending topics")
            return {"success": True, "items": items, "source": "baidu"}
    except Exception as e:
        logger.warning(f"Baidu trending fetch failed: {e}")

    logger.error("All trending sources failed")
    return {"success": False, "items": []}


def format_trending_data(data: dict) -> str:
    """Format trending items into a text summary for AI."""
    if not data.get("success") or not data.get("items"):
        return "今日暂无热搜数据。"
    source = data.get("source", "热搜")
    lines = [f"以下是今日{source}榜单前{len(data['items'])}条："]
    for item in data["items"]:
        lines.append(f"  #{item['rank']}# {item['word']}")
    return "\n".join(lines)


def fetch_trending() -> dict:
    """Main entry: fetch trending from best available source."""
    return fetch_weibo_trending()
