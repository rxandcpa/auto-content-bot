"""Save generated articles as publish-ready files. Auto-cleanup old files."""

from __future__ import annotations

import glob
import json
import logging
import os
import time

from src.utils import today_str, today_cn

logger = logging.getLogger(__name__)

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
MAX_AGE_DAYS = 7  # Keep articles for this many days


def save_article(title: str, content: str, category: str = "") -> str:
    """
    Save article as a Markdown file in output/.
    Includes a plain-text copy for easy phone copy-paste.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    safe_title = title.replace("/", "_").replace("\\", "_").replace("?", "_")[:40]
    safe_cat = category if category else "article"
    date_str = today_str()

    # 1. Markdown file (nicely formatted)
    md_filename = f"{date_str}_{safe_cat}_{safe_title}.md"
    md_path = os.path.join(OUTPUT_DIR, md_filename)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write(f"> 自动生成于 {today_cn()}\n\n")
        f.write("---\n\n")
        f.write(content)
        f.write("\n")

    # 2. Plain text file (for easy phone copy-paste, no markdown symbols)
    txt_filename = f"{date_str}_{safe_cat}.txt"
    txt_path = os.path.join(OUTPUT_DIR, txt_filename)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"{title}\n\n")
        f.write(content)

    logger.info(f"Article saved: {md_path}")
    return md_path


def save_daily_bundle(articles: list[dict]) -> str:
    """
    Save all today's articles into one easy-to-use file.
    This is the file you open on your phone each morning.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    date_str = today_str()
    bundle_path = os.path.join(OUTPUT_DIR, f"{date_str}_每日发布.txt")

    lines = [
        f"══════════════════════════════════",
        f"  今日发布内容 - {today_cn()}",
        f"  共 {len(articles)} 篇文章",
        f"══════════════════════════════════",
        "",
    ]

    for i, art in enumerate(articles, 1):
        lines.append(f"╔══════════════════════════════════╗")
        lines.append(f"║  第{i}篇                          ║")
        lines.append(f"╚══════════════════════════════════╝")
        lines.append("")
        lines.append(f"【标题】{art['title']}")
        lines.append("")
        lines.append("【正文】")
        lines.append(art['content'])
        lines.append("")
        lines.append("---")
        lines.append("")

    with open(bundle_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info(f"Daily bundle saved: {bundle_path}")
    return bundle_path


def save_publish_log(entries: list[dict]) -> str:
    """Write a summary log of today's generation results."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    log_path = os.path.join(OUTPUT_DIR, f"{today_str()}_log.json")
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    logger.info(f"Publish log saved: {log_path}")
    return log_path


def cleanup_old_files(max_age_days: int = MAX_AGE_DAYS) -> int:
    """Delete article files older than max_age_days. Returns count of deleted files."""
    if not os.path.isdir(OUTPUT_DIR):
        return 0

    cutoff = time.time() - max_age_days * 86400
    deleted = 0

    for f in glob.glob(os.path.join(OUTPUT_DIR, "*")):
        try:
            if os.path.getmtime(f) < cutoff:
                os.remove(f)
                deleted += 1
                logger.debug(f"Cleaned up: {f}")
        except OSError:
            pass

    if deleted:
        logger.info(f"Cleaned up {deleted} old article files (>{max_age_days} days)")
    return deleted
