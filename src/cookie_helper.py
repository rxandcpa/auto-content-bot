"""
Run: python -m src.cookie_helper
Browser opens → manually log into mp.toutiao.com → press Enter
Saves full browser state to toutiao_state.json
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
    print("  头条号登录状态保存工具")
    print("=" * 60)
    print()
    print("  1. 浏览器打开后访问 https://mp.toutiao.com")
    print("  2. 用手机号 + 验证码登录")
    print("  3. 看到后台页面后，回到这里按 Enter")
    print("=" * 60)
    print()

    with sync_playwright() as p:
        # Try system browser first (less detectable), fall back to bundled Chromium
        launched = False
        for channel in ["msedge", "chrome", None]:
            try:
                launch_args = {
                    "headless": False,
                    "args": ["--no-sandbox", "--disable-blink-features=AutomationControlled"],
                }
                if channel:
                    launch_args["channel"] = channel
                browser = p.chromium.launch(**launch_args)
                print(f"（使用: {channel or '内置 Chromium'}）")
                launched = True
                break
            except Exception:
                continue

        if not launched:
            print("无法启动浏览器。请确保已安装 Edge 或 Chrome")
            sys.exit(1)

        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
        )

        # Remove webdriver detection
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => false});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en']});
            window.chrome = {runtime: {}};
        """)

        page = context.new_page()

        # Navigate
        try:
            page.goto(
                "https://mp.toutiao.com",
                wait_until="domcontentloaded",
                timeout=30000,
            )
        except Exception:
            print("⚠️  页面加载超时，但浏览器窗口应该已经打开了")
            print("   请在浏览器窗口里手动操作登录")

        print("浏览器已打开。如果页面空白，请手动在地址栏输入 https://mp.toutiao.com")
        print("登录成功后，按 Enter 键...")
        input()

        # Save state
        state = context.storage_state()
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

        browser.close()

    print()
    print(f"✅ 已保存: {STATE_FILE}")
    print()
    print("下一步：")
    print("  1. 打开 toutiao_state.json，复制全部内容")
    print("  2. GitHub → Settings → Secrets → Actions → New secret")
    print("  3. Name: TOUTIAO_STATE")
    print("  4. Value: toutiao_state.json 的全部内容（很长，没关系）")


if __name__ == "__main__":
    main()
