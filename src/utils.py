"""Logging and helper utilities."""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone, timedelta

# UTC+8 timezone for China Standard Time
CST = timezone(timedelta(hours=8))


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def today_str() -> str:
    """Return today's date string in CST, e.g. '2026-05-27'."""
    return datetime.now(CST).strftime("%Y-%m-%d")


def today_cn() -> str:
    """Return today's date in Chinese format, e.g. '2026年5月27日'."""
    now = datetime.now(CST)
    return f"{now.year}年{now.month}月{now.day}日"


def month_day() -> tuple[int, int]:
    """Return (month, day) in CST."""
    now = datetime.now(CST)
    return now.month, now.day
