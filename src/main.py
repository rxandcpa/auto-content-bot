"""Main orchestrator: fetch data → generate articles → save → auto-publish."""

from __future__ import annotations

import logging
import os
import random
import subprocess
import sys

from src.utils import setup_logging, today_str, today_cn
from src.config import CONTENT_TYPE
from src.fetchers.gold_price import fetch_gold_price, format_gold_data
from src.fetchers.weather import fetch_all_weather, format_weather_data
from src.fetchers.history import fetch_today_history, format_history_data
from src.fetchers.trending import fetch_trending, format_trending_data
from src.writer import (
    write_gold_article,
    write_weather_article,
    write_history_article,
    write_trending_article,
)
from src.publisher import save_article, save_daily_bundle, save_publish_log

logger = logging.getLogger(__name__)


def run_pipeline(topic: str, fetch_fn, format_fn, write_fn) -> dict | None:
    """Run one content pipeline: fetch → format → write → save."""
    logger.info(f"=== {topic} pipeline ===")

    data = fetch_fn()
    if isinstance(data, list):
        if not any(d.get("success") for d in data):
            logger.warning(f"{topic}: no data, skip")
            return {"topic": topic, "status": "skipped", "reason": "no data"}
    elif isinstance(data, dict):
        if not data.get("success"):
            logger.warning(f"{topic}: no data, skip")
            return {"topic": topic, "status": "skipped", "reason": "no data"}

    formatted = format_fn(data)
    article = write_fn(formatted)
    if not article:
        logger.error(f"{topic}: AI generation failed")
        return {"topic": topic, "status": "failed", "reason": "AI error"}

    save_article(article["title"], article["content"], topic)
    logger.info(f"{topic}: done. Title: {article['title'][:50]}...")

    return {
        "topic": topic,
        "status": "ok",
        "title": article["title"],
        "content": article["content"],
    }


def _commit_output() -> bool:
    """Commit output/ directory back to the repo so articles appear on GitHub."""
    output_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "output"
    )
    if not os.path.isdir(output_dir):
        return False

    # Only proceed if running in GitHub Actions
    if not os.getenv("GITHUB_ACTIONS"):
        logger.info("Not in GitHub Actions, skipping auto-commit")
        return False

    try:
        subprocess.run(["git", "config", "user.name", "Article Bot"], check=True)
        subprocess.run(
            ["git", "config", "user.email", "bot@auto-content.local"], check=True
        )
        subprocess.run(["git", "add", "output/"], check=True, cwd=os.path.dirname(output_dir))
        # Check if there are changes to commit
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=os.path.dirname(output_dir),
        )
        if result.returncode == 0:
            logger.info("No new changes to commit")
            return True
        subprocess.run(
            ["git", "commit", "-m", f"📝 {today_cn()} 每日文章"],
            check=True,
            cwd=os.path.dirname(output_dir),
        )
        subprocess.run(["git", "push"], check=True, cwd=os.path.dirname(output_dir))
        logger.info("Articles committed and pushed to repo")
        return True
    except Exception as e:
        logger.warning(f"Auto-commit failed (non-critical): {e}")
        return False


def main():
    setup_logging()
    logger.info(f"=== Auto Content Bot - {today_cn()} ===")
    logger.info(f"Content type: {CONTENT_TYPE}")

    articles = []

    # Pipeline definitions: (topic, fetch, format, write)
    all_pipelines = [
        ("gold", fetch_gold_price, format_gold_data, write_gold_article),
        ("weather", fetch_all_weather, format_weather_data, write_weather_article),
        ("history", fetch_today_history, format_history_data, write_history_article),
        ("trending", fetch_trending, format_trending_data, write_trending_article),
    ]

    if CONTENT_TYPE == "all":
        # Run 2-3 randomly selected pipelines for variety
        selected = random.sample(all_pipelines, k=random.choice([2, 3]))
        # But always include at least gold or trending (high engagement topics)
        high_engagement = [p for p in all_pipelines if p[0] in ("gold", "trending")]
        if not any(p[0] in [s[0] for s in selected] for p in high_engagement):
            selected[0] = random.choice(high_engagement)
    else:
        selected = [p for p in all_pipelines if p[0] == CONTENT_TYPE]

    for topic, fetch_fn, format_fn, write_fn in selected:
        result = run_pipeline(topic, fetch_fn, format_fn, write_fn)
        if result:
            articles.append(result)

    # Save combined daily bundle
    successful = [a for a in articles if a.get("status") == "ok" and "content" in a]
    if successful:
        bundle_path = save_daily_bundle(successful)
        logger.info(f"Daily bundle ready: {bundle_path}")
    else:
        logger.warning("No successful articles to bundle")

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

    # Auto-commit articles to repo (GitHub Actions only)
    _commit_output()

    # ── Auto-publish to Toutiao (only if cookies configured) ──
    if os.getenv("TOUTIAO_COOKIES"):
        logger.info("=== Auto-publishing to Toutiao ===")
        try:
            from src.publisher_toutiao import publish_articles as toutiao_publish
            pub_articles = [
                {"title": a["title"], "content": a["content"]}
                for a in articles
                if a.get("status") == "ok" and "content" in a
            ]
            if pub_articles:
                pub_result = toutiao_publish(pub_articles)
                logger.info(
                    f"Publish: {pub_result['success']} ok, {pub_result['failed']} failed"
                )
        except Exception as e:
            logger.warning(f"Auto-publish failed (non-critical): {e}")

    ok_count = sum(1 for a in articles if a["status"] == "ok")
    logger.info(f"=== Done: {ok_count}/{len(articles)} articles ===")

    if ok_count == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
