"""
Connect to an already-open, already-logged-in browser window.

Step 1: Close ALL Edge windows
Step 2: Paste the command below into a terminal (or Win+R):
        start msedge --remote-debugging-port=9222 --user-data-dir="%TEMP%\edge_tt"

Step 3: In the new Edge window, go to https://mp.toutiao.com and log in
Step 4: Run this script: python -m src.cookie_helper
Step 5: Script connects to your logged-in browser and saves the state
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
    print("  连接已登录的浏览器")
    print("=" * 60)
    print()
    print("  请确认已完成以下操作：")
    print()
    print("  1. 关闭了所有 Edge 窗口")
    print("  2. 在终端或 Win+R 执行了：")
    print("     start msedge --remote-debugging-port=9222 --user-data-dir=%TEMP%\\edge_tt")
    print("  3. 在新 Edge 窗口里登录了 https://mp.toutiao.com")
    print("  4. 登录成功，能看到后台页面")
    print("=" * 60)
    print()

    # Check if Edge with debugging port is running
    import subprocess
    result = subprocess.run(
        ["netstat", "-ano"],
        capture_output=True, text=True,
    )
    if "9222" not in result.stdout:
        print("⚠️  未检测到端口 9222，请确认已用以下命令启动 Edge：")
        print('   start msedge --remote-debugging-port=9222 --user-data-dir="%TEMP%\\edge_tt"')
        print()
        resp = input("如果已启动，按 Enter 继续...")

    input("确认登录完成后按 Enter...")

    with sync_playwright() as p:
        try:
            # Connect to the already-running Edge browser
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            print("✅ 已连接到 Edge 浏览器")
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            print()
            print("请确认：")
            print("  1. Edge 是用上面的命令启动的")
            print("  2. 端口 9222 没有被防火墙阻止")
            print("  3. Edge 窗口还开着")
            sys.exit(1)

        # Get the first context (there should be at least one)
        contexts = browser.contexts
        if not contexts:
            print("❌ 没有找到浏览器上下文，请确认 Edge 已打开网页")
            browser.close()
            sys.exit(1)

        context = contexts[0]

        # Navigate to Toutiao to verify login
        page = context.new_page()
        try:
            page.goto("https://mp.toutiao.com", timeout=15000)
        except Exception:
            pass

        # Check if logged in
        page.wait_for_timeout(3000)
        current_url = page.url
        if "login" in current_url.lower() or "passport" in current_url.lower():
            print()
            print("⚠️  看起来还没登录。请在 Edge 窗口里手动登录，然后按 Enter...")
            input()

        # Export storage state from the logged-in context
        state = context.storage_state()
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

        print()
        print(f"✅ 登录状态已保存到: {STATE_FILE}")
        print(f"   Cookie 数量: {len(state.get('cookies', []))}")

        # Don't close the browser - user might still be using it
        browser.close()

    print()
    print("下一步：")
    print("  1. 打开 toutiao_state.json")
    print("  2. 复制全部内容")
    print("  3. GitHub → Settings → Secrets → Actions → New secret")
    print("     Name:  TOUTIAO_STATE")
    print("     Value: 粘贴 toutiao_state.json 的全部内容")


if __name__ == "__main__":
    main()
