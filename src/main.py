"""Main orchestrator: fetch data → generate articles → save to output/."""

from __future__ import annotations

import logging
import os
import sys

from src.utils import setup_logging, today_str, today_cn
from src.config import CONTENT_TYPE
from src.fetchers.gold_price import fetch_gold_price, format_gold_data
from src.fetchers.weather import fetch_all_weather, format_weather_data
from src.fetchers.history import fetch_today_history, format_history_data
from src.writer import write_gold_article, write_weather_article, write_history_article
from src.publisher import save_article, save_daily_bundle, save_publish_log
from src.publisher_toutiao import publish_articles as toutiao_publish

logger = logging.getLogger(__name__)


def run_pipeline(topic: str, fetch_fn, format_fn, write_fn) -> dict | None:
    """Run one content pipeline: fetch → format → write → save."""
    logger.info(f"=== {topic} pipeline ===")

    # 1. Fetch
    data = fetch_fn()

    # Check if we got valid data (supports both dict and list)
    if isinstance(data, list):
        if not any(d.get("success") for d in data):
            logger.warning(f"{topic}: no data, skip")
            return {"topic": topic, "status": "skipped", "reason": "no data"}
    elif isinstance(data, dict):
        if not data.get("success"):
            logger.warning(f"{topic}: no data, skip")
            return {"topic": topic, "status": "skipped", "reason": "no data"}

    # 2. Format
    formatted = format_fn(data)

    # 3. AI Write
    article = write_fn(formatted)
    if not article:
        logger.error(f"{topic}: AI generation failed")
        return {"topic": topic, "status": "failed", "reason": "AI error"}

    # 4. Save
    save_article(article["title"], article["content"], topic)
    logger.info(f"{topic}: done. Title: {article['title'][:40]}...")

    return {
        "topic": topic,
        "status": "ok",
        "title": article["title"],
        "content": article["content"],
    }


def main():
    setup_logging()
    logger.info(f"=== Auto Content Bot - {today_cn()} ===")
    logger.info(f"Content type: {CONTENT_TYPE}")

    articles = []

    pipelines = [
        ("gold", fetch_gold_price, format_gold_data, write_gold_article),
        ("weather", fetch_all_weather, format_weather_data, write_weather_article),
        ("history", fetch_today_history, format_history_data, write_history_article),
    ]

    for topic, fetch_fn, format_fn, write_fn in pipelines:
        if CONTENT_TYPE == "all" or CONTENT_TYPE == topic:
            result = run_pipeline(topic, fetch_fn, format_fn, write_fn)
            if result:
                articles.append(result)

    # Save combined daily bundle
    successful = [a for a in articles if a.get("status") == "ok" and "content" in a]
    if successful:
        bundle_path = save_daily_bundle(successful)
        logger.info(f"Daily bundle ready: {bundle_path}")

    # Save log
    log_entries = [
        {
            "topic": a["topic"],
            "status": a["status"],
            "title": a.get("title", ""),
            "reason": a.get("reason", ""),
        }
        for a in articles
    ]
    save_publish_log(log_entries)

    # Summary
    ok_count = sum(1 for a in articles if a["status"] == "ok")
    logger.info(f"=== Done: {ok_count}/{len(articles)} articles generated ===")

    if ok_count == 0:
        logger.error("No articles generated, exiting with error")
        sys.exit(1)

    # Auto-publish to Toutiao (only if cookies are configured)
    if os.getenv("TOUTIAO_COOKIES"):
        logger.info("=== Auto-publishing to Toutiao ===")
        pub_articles = [
            {"title": a["title"], "content": a["content"]}
            for a in articles
            if a.get("status") == "ok" and "content" in a
        ]
        if pub_articles:
            pub_result = toutiao_publish(pub_articles)
            logger.info(
                f"Publish result: {pub_result['success']} ok, "
                f"{pub_result['failed']} failed"
            )
    else:
        logger.info("No TOUTIAO_COOKIES set, skipping auto-publish. "
                      "Run cookie_helper.py to set up.")


if __name__ == "__main__":
    main()
