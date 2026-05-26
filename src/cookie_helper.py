"""
Step 1: Run this script on your computer.
Step 2: A browser opens → you log into mp.toutiao.com manually.
Step 3: After login, press Enter in the terminal.
Step 4: Cookies are saved to cookies.json.
Step 5: Copy the entire content of cookies.json to GitHub Secrets as TOUTIAO_COOKIES.
"""

from __future__ import annotations

import json
import os
import sys

COOKIE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cookies.json")


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Please install playwright: pip install playwright && python -m playwright install chromium")
        sys.exit(1)

    print("=" * 60)
    print("  头条号 Cookie 抓取工具")
    print("=" * 60)
    print()
    print("即将打开浏览器，请按以下步骤操作：")
    print()
    print("  1. 浏览器打开后，手动访问 https://mp.toutiao.com")
    print("  2. 用手机号 + 验证码登录")
    print("  3. 确认登录成功后（能看到后台页面）")
    print("  4. 回到这个终端窗口，按 Enter 键")
    print()
    print("  提示：建议在登录时勾选「记住登录状态」")
    print("=" * 60)
    print()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()
        page.goto("https://mp.toutiao.com", wait_until="domcontentloaded", timeout=30000)

        print("浏览器已打开。请手动登录头条号后台。")
        print("登录成功后，按 Enter 键继续...")
        input()

        # Save cookies
        cookies = context.cookies()
        with open(COOKIE_FILE, "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)

        browser.close()

    print()
    print(f"✅ Cookie 已保存到: {COOKIE_FILE}")
    print()
    print("下一步：")
    print(f"  1. 打开 {COOKIE_FILE}")
    print("  2. 复制全部内容")
    print("  3. 进入 GitHub 仓库 → Settings → Secrets → Actions")
    print("  4. 新建 Secret: Name=TOUTIAO_COOKIES, Value=刚才复制的内容")
    print()
    print("注意：Cookie 有效期通常 7-30 天，过期后需重新抓取。")


if __name__ == "__main__":
    main()
