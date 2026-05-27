"""
Method: Use an already-logged-in browser instead of trying to log in fresh.

Step 1: Close all Edge windows
Step 2: Run this script: python -m src.cookie_helper
Step 3: A NEW Edge window opens. Navigate to mp.toutiao.com and log in.
Step 4: Press Enter. State saved. Done.

Uses persistent browser profile — no bot detection because it's the real browser.
"""

from __future__ import annotations

import json
import os
import shutil
import sys

# Persistent profile directory
PROFILE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "toutiao_profile")
STATE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "toutiao_state.json")


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Run: pip install playwright && playwright install chromium")
        sys.exit(1)

    # Check if this is a fresh start or a return visit
    is_first_time = not os.path.exists(STATE_FILE)

    print("=" * 60)
    if is_first_time:
        print("  首次设置：需要手动登录头条号")
    else:
        print("  更新登录状态（旧状态可能已过期）")
    print("=" * 60)
    print()
    print("  注意事项：")
    print("  1. 请先关闭所有 Edge 浏览器窗口")
    print("  2. 新窗口打开后，访问 https://mp.toutiao.com")
    print("  3. 用手机号+验证码登录，勾选「记住我」")
    print("  4. 登录成功后，回到终端按 Enter")
    print("=" * 60)
    print()

    input("按 Enter 开始...")

    # Remove old profile for clean start
    if os.path.exists(PROFILE_DIR):
        try:
            shutil.rmtree(PROFILE_DIR)
        except Exception:
            pass

    os.makedirs(PROFILE_DIR, exist_ok=True)

    with sync_playwright() as p:
        # Use persistent context — this creates a real browser profile
        # that persists on disk, drastically reducing bot detection
        context = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            headless=False,
            channel="msedge",  # Use Edge
            viewport={"width": 1440, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"
            ),
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
            ignore_default_args=["--enable-automation"],
            args=[
                "--no-sandbox",
                "--disable-features=AutomationControlled",
            ],
        )

        # Add stealth script
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => false});
            window.chrome = {runtime: {}};
        """)

        page = context.new_page()

        try:
            page.goto("https://mp.toutiao.com", timeout=15000)
        except Exception:
            pass

        print()
        print("浏览器已打开。请在浏览器中操作：")
        print("  → 如果没自动跳转，地址栏输入 https://mp.toutiao.com")
        print("  → 用手机号+验证码登录")
        print("  → 看到后台页面（文章管理/数据概览等）后")
        print("  → 回到这里按 Enter")
        print()
        input("登录完成后按 Enter 保存状态...")

        # Export storageState
        state = context.storage_state()
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

        context.close()

    # Keep the profile for future use (validates state export worked)
    print()
    print(f"✅ 登录状态已保存！")
    print(f"   状态文件: {STATE_FILE}")
    print(f"   浏览器配置: {PROFILE_DIR}")
    print()
    print("下一步：")
    print("  1. 打开 toutiao_state.json → 复制全部内容")
    print("  2. GitHub → 仓库 → Settings → Secrets → Actions")
    print("  3. New secret:")
    print("     Name:  TOUTIAO_STATE")
    print("     Value: toutiao_state.json 的全部内容")
    print()
    print("之后每天早上文章就会自动发布到头条号。")


if __name__ == "__main__":
    main()
