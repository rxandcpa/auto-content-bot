"""
Auto-publish articles to Toutiao using Playwright + storageState.

Uses storageState (cookies + localStorage + sessionStorage) saved by cookie_helper.py.
State is stored in GitHub Secrets as TOUTIAO_STATE (JSON string).
"""

from __future__ import annotations

import json
import logging
import os
import time

logger = logging.getLogger(__name__)

PUBLISH_URL = "https://mp.toutiao.com/profile_v4/graphic/publish"


def _load_state() -> dict | None:
    """Load browser storageState from env var or local file."""
    state_str = os.getenv("TOUTIAO_STATE", "")

    if not state_str:
        state_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "toutiao_state.json"
        )
        if os.path.exists(state_file):
            with open(state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    try:
        return json.loads(state_str)
    except json.JSONDecodeError:
        logger.error("TOUTIAO_STATE is not valid JSON")
        return None


def publish_article(title: str, content: str) -> bool:
    """Publish one article. Returns True if it appeared to succeed."""
    state = _load_state()
    if not state:
        logger.error("No Toutiao state found. Run cookie_helper.py first.")
        return False

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.error("Playwright not installed")
        return False

    logger.info(f"Publishing: {title[:40]}...")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        # Restore full browser state
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            storage_state=state,  # This restores cookies + localStorage + etc.
        )
        page = context.new_page()

        try:
            # Navigate to publish page
            page.goto(PUBLISH_URL, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(4000)

            # Check login
            current_url = page.url
            if "login" in current_url.lower() or "passport" in current_url.lower():
                logger.error("State expired — need to re-run cookie_helper.py")
                page.screenshot(path="toutiao_expired.png")
                browser.close()
                return False

            # Fill title
            title_filled = False
            for sel in [
                'input[placeholder*="标题"]',
                '[class*="title"] input',
                'input[type="text"]',
            ]:
                try:
                    el = page.wait_for_selector(sel, timeout=5000)
                    if el and el.is_visible():
                        el.click()
                        el.fill("")
                        el.fill(title)
                        title_filled = True
                        break
                except Exception:
                    continue

            if not title_filled:
                logger.warning("Title fill may have failed")

            # Fill content (rich text editor)
            content_filled = False
            for sel in [
                '[contenteditable="true"]',
                '.ql-editor',
                '.ProseMirror',
                '[data-slate-editor]',
                '[class*="editor"] [contenteditable]',
            ]:
                try:
                    editor = page.wait_for_selector(sel, timeout=5000)
                    if editor:
                        editor.click()
                        page.wait_for_timeout(500)
                        # Use evaluate to set HTML content
                        html = content.replace("\n", "<br>").replace("'", "\\'")
                        editor.evaluate(f"el => {{ el.innerHTML = '{html}'; }}")
                        page.wait_for_timeout(500)
                        # Dispatch input event to trigger editor's change detection
                        editor.evaluate(
                            "el => el.dispatchEvent(new Event('input', {bubbles: true}))"
                        )
                        content_filled = True
                        break
                except Exception:
                    continue

            if not content_filled:
                # Fallback: just type into the body
                try:
                    page.keyboard.press("Tab")
                    page.wait_for_timeout(500)
                    page.keyboard.insert_text(content)
                    content_filled = True
                except Exception:
                    pass

            if not content_filled:
                logger.error("Could not fill content")
                page.screenshot(path="toutiao_content_fail.png")
                browser.close()
                return False

            # Click publish
            page.wait_for_timeout(1000)
            published = False
            for sel in [
                'button:has-text("发布")',
                '[class*="publish"] button',
                'button:has-text("发表")',
                '[class*="submit"]',
            ]:
                try:
                    btn = page.wait_for_selector(sel, timeout=5000)
                    if btn and btn.is_visible() and btn.is_enabled():
                        btn.click()
                        page.wait_for_timeout(3000)
                        published = True
                        break
                except Exception:
                    continue

            if not published:
                logger.error("Could not click publish")
                page.screenshot(path="toutiao_publish_fail.png")
                browser.close()
                return False

            # Dismiss confirmation if any
            try:
                for confirm_sel in [
                    'button:has-text("确认")',
                    'button:has-text("确定")',
                    '[class*="confirm"]',
                ]:
                    btn = page.wait_for_selector(confirm_sel, timeout=3000)
                    if btn and btn.is_visible():
                        btn.click()
                        page.wait_for_timeout(2000)
                        break
            except Exception:
                pass

            logger.info(f"Published: {title[:40]}")
            browser.close()
            return True

        except Exception as e:
            logger.error(f"Publish error: {e}")
            try:
                page.screenshot(path="toutiao_error.png")
            except Exception:
                pass
            browser.close()
            return False


def publish_articles(articles: list[dict]) -> dict:
    """Publish multiple articles."""
    results = {"success": 0, "failed": 0, "details": []}

    for i, art in enumerate(articles):
        logger.info(f"Article {i+1}/{len(articles)}")
        ok = publish_article(art["title"], art["content"])
        results["details"].append({
            "title": art["title"][:50],
            "status": "ok" if ok else "failed",
        })
        if ok:
            results["success"] += 1
        else:
            results["failed"] += 1
        if i < len(articles) - 1:
            time.sleep(8)  # Longer delay between articles

    logger.info(f"Done: {results['success']} ok, {results['failed']} failed")
    return results
