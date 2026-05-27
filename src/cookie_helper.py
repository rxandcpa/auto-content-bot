"""
Step 1: Run this script: python -m src.cookie_helper
Step 2: Browser opens → manually log into https://mp.toutiao.com
Step 3: After login, press Enter in terminal
Step 4: Browser state saved to toutiao_state.json (includes cookies + localStorage)
Step 5: Copy entire file content to GitHub Secrets → TOUTIAO_STATE

Use storageState (not just cookies) — much more reliable for preserving login.
"""

from __future__ import annotations

import json
import os
import sys

STATE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "toutiao_state.json")


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Run: pip install playwright && playwright install chromium")
        sys.exit(1)

    print("=" * 60)
    print("  头条号登录状态保存工具 (StorageState)")
    print("=" * 60)
    print()
    print("  1. 浏览器打开后，访问 https://mp.toutiao.com")
    print("  2. 手机号 + 验证码登录")
    print("  3. 确认进入后台后，回到这里按 Enter")
    print()
    print("  （登录时勾选'记住我'可以延长有效期）")
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

        print("浏览器已打开。登录后按 Enter...")
        input()

        # Save FULL browser state (cookies + localStorage + sessionStorage + IndexedDB)
        state = context.storage_state()
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

        browser.close()

    print()
    print(f"✅ 登录状态已保存到: {STATE_FILE}")
    print()
    print("下一步：")
    print(f"  1. 打开 {STATE_FILE}，复制全部内容")
    print("  2. GitHub → 仓库 → Settings → Secrets → Actions")
    print("  3. New secret → Name: TOUTIAO_STATE → Value: 粘贴")
    print()
    print("有效期通常 7-30 天，过期后重新运行本脚本即可。")


if __name__ == "__main__":
    main()
