"""
Auto-publish articles to Toutiao (头条号) using Playwright browser automation.

Uses pre-saved cookies (from cookie_helper.py) to bypass login.
Cookies are stored in GitHub Secrets as TOUTIAO_COOKIES (JSON string).
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time

logger = logging.getLogger(__name__)

# Toutiao MP URLs
LOGIN_URL = "https://mp.toutiao.com"
PUBLISH_URL = "https://mp.toutiao.com/profile_v4/graphic/publish"


def _load_cookies() -> list[dict] | None:
    """Load cookies from environment variable or file."""
    cookie_str = os.getenv("TOUTIAO_COOKIES", "")

    if not cookie_str:
        # Fallback: try local cookies.json
        cookie_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "cookies.json"
        )
        if os.path.exists(cookie_file):
            with open(cookie_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    try:
        return json.loads(cookie_str)
    except json.JSONDecodeError:
        logger.error("TOUTIAO_COOKIES is not valid JSON")
        return None


def _is_logged_in(page) -> bool:
    """Check if we're actually logged in by looking for typical page elements."""
    try:
        # If redirected to login page, the URL will contain "login" or "passport"
        current_url = page.url
        if "login" in current_url.lower() or "passport" in current_url.lower():
            return False
        # Check for common elements on the Toutiao MP dashboard
        # The page title or a specific element that indicates logged-in state
        title = page.title()
        if "登录" in title:
            return False
        return True
    except Exception:
        return False


def publish_article(title: str, content: str, timeout: int = 60000) -> bool:
    """
    Publish one article to Toutiao.

    Args:
        title: Article title
        content: Article body (plain text or simple HTML)
        timeout: Max wait time in ms per step

    Returns:
        True if publishing succeeded (or appeared to succeed)
    """
    cookies = _load_cookies()
    if not cookies:
        logger.error("No Toutiao cookies found. Run cookie_helper.py first.")
        return False

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.error("Playwright not installed")
        return False

    logger.info(f"Publishing to Toutiao: {title[:30]}...")

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
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        context.add_cookies(cookies)
        page = context.new_page()

        try:
            # Step 1: Go to publish page
            logger.info("Navigating to publish page...")
            page.goto(PUBLISH_URL, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000)

            # Step 2: Verify login state
            if not _is_logged_in(page):
                logger.error(
                    "Not logged in. Cookies may have expired. "
                    "Run cookie_helper.py to refresh."
                )
                # Take screenshot for debugging
                page.screenshot(path="toutiao_debug_login.png")
                browser.close()
                return False

            # Step 3: Fill in the title
            logger.info("Filling title...")
            title_selectors = [
                'input[placeholder*="标题"]',
                'input[class*="title"]',
                '[data-placeholder*="标题"]',
            ]
            title_filled = False
            for sel in title_selectors:
                try:
                    title_el = page.wait_for_selector(sel, timeout=5000)
                    if title_el:
                        title_el.click()
                        title_el.fill("")  # Clear existing
                        title_el.fill(title)
                        title_filled = True
                        logger.info(f"Title filled via selector: {sel}")
                        break
                except Exception:
                    continue

            if not title_filled:
                # Try finding any visible input near the top of the page
                try:
                    inputs = page.locator("input[type='text']").all()
                    for inp in inputs:
                        if inp.is_visible():
                            inp.click()
                            inp.fill(title)
                            title_filled = True
                            break
                except Exception:
                    pass

            if not title_filled:
                logger.error("Could not find title input")
                page.screenshot(path="toutiao_debug_title.png")

            # Step 4: Fill in the content
            logger.info("Filling content...")
            content_filled = False

            # Toutiao uses a rich text editor. Try multiple approaches.
            # Approach A: Find contenteditable div
            content_selectors = [
                '[contenteditable="true"]',
                '.editor-content',
                '[class*="editor"]',
                '[data-slate-editor]',
                '.ql-editor',
                '.ProseMirror',
            ]
            for sel in content_selectors:
                try:
                    editor = page.wait_for_selector(sel, timeout=3000)
                    if editor:
                        editor.click()
                        # Clear and fill
                        editor.evaluate("el => el.innerHTML = ''")
                        page.wait_for_timeout(500)
                        # Use innerHTML for formatted content
                        html_content = content.replace("\n", "<br>")
                        editor.evaluate(f"el => el.innerHTML = `{html_content}`")
                        content_filled = True
                        logger.info(f"Content filled via selector: {sel}")
                        break
                except Exception:
                    continue

            if not content_filled:
                # Approach B: Type into focused element after clicking
                try:
                    page.keyboard.press("Tab")  # Tab from title to content
                    page.wait_for_timeout(500)
                    page.keyboard.insert_text(content)
                    content_filled = True
                except Exception:
                    pass

            if not content_filled:
                logger.warning("Could not find content editor, trying fallback...")
                page.screenshot(path="toutiao_debug_content.png")

            # Step 5: Click publish button
            logger.info("Clicking publish...")
            publish_selectors = [
                'button:has-text("发布")',
                'button:has-text("发表")',
                '[class*="publish"]',
                '[class*="submit"]',
                'button:has-text("提交")',
            ]
            published = False
            for sel in publish_selectors:
                try:
                    btn = page.wait_for_selector(sel, timeout=3000)
                    if btn and btn.is_visible():
                        btn.click()
                        page.wait_for_timeout(3000)
                        published = True
                        logger.info(f"Clicked publish via: {sel}")
                        break
                except Exception:
                    continue

            if not published:
                logger.error("Could not find publish button")
                page.screenshot(path="toutiao_debug_publish.png")
                browser.close()
                return False

            # Step 6: Handle confirmation dialog if any
            try:
                confirm_btn = page.wait_for_selector(
                    'button:has-text("确认"), button:has-text("确定"),'
                    '[class*="confirm"]',
                    timeout=5000,
                )
                if confirm_btn and confirm_btn.is_visible():
                    confirm_btn.click()
                    page.wait_for_timeout(2000)
            except Exception:
                pass  # No confirmation needed

            logger.info(f"Article published successfully: {title[:30]}...")
            browser.close()
            return True

        except Exception as e:
            logger.error(f"Publishing error: {e}")
            try:
                page.screenshot(path="toutiao_debug_error.png")
            except Exception:
                pass
            browser.close()
            return False


def publish_articles(articles: list[dict]) -> dict:
    """
    Publish multiple articles. Returns summary dict.

    Args:
        articles: List of {"title": str, "content": str} dicts

    Returns:
        {"success": int, "failed": int, "details": [...]}
    """
    results = {"success": 0, "failed": 0, "details": []}

    for i, art in enumerate(articles):
        logger.info(f"Publishing article {i+1}/{len(articles)}")
        ok = publish_article(art["title"], art["content"])
        results["details"].append({
            "title": art["title"][:50],
            "status": "ok" if ok else "failed",
        })
        if ok:
            results["success"] += 1
        else:
            results["failed"] += 1

        # Wait between articles to avoid rate limiting
        if i < len(articles) - 1:
            time.sleep(5)

    logger.info(
        f"Publish done: {results['success']} success, {results['failed']} failed"
    )
    return results
