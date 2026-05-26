"""Fetch 'today in history' events from Wikipedia (free, no API key)."""

from __future__ import annotations

import logging
import requests

from src.utils import month_day

logger = logging.getLogger(__name__)

WIKI_API = "https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/{month}/{day}"


def fetch_today_history() -> dict:
    """Return today's historical events from Wikipedia."""
    month, day = month_day()
    url = WIKI_API.format(month=month, day=day)
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "AutoContentBot/1.0"})
        resp.raise_for_status()
        data = resp.json()
        events = data.get("events", [])
        # Take up to 10 events, prefer ones with more detail
        selected = []
        for ev in events[:20]:
            text = ev.get("text", "").strip()
            year = ev.get("year", "")
            if text and year:
                selected.append(f"{year}年: {text}")
            if len(selected) >= 10:
                break

        logger.info(f"Fetched {len(selected)} historical events for {month}/{day}")
        return {
            "success": True,
            "month": month,
            "day": day,
            "events": selected,
        }
    except Exception as e:
        logger.error(f"Wikipedia history fetch failed: {e}")
        return {"success": False, "events": []}


def format_history_data(data: dict) -> str:
    """Format history events into a text summary."""
    if not data.get("success") or not data.get("events"):
        return "暂无历史事件数据。"
    month, day = data["month"], data["day"]
    header = f"以下是历史上 {month}月{day}日 发生的重要事件：\n"
    events_text = "\n".join(f"• {e}" for e in data["events"])
    return header + events_text
