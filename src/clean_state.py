"""Strip unnecessary data from toutiao_state.json to fit GitHub Secret limit (48KB)."""

from __future__ import annotations

import json
import os
import sys

STATE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "toutiao_state.json")
CLEAN_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "toutiao_state_clean.json")

# Only keep cookies from these domains (Toutiao/ByteDance auth)
KEEP_COOKIE_DOMAINS = {
    "mp.toutiao.com",
    ".toutiao.com",
    ".bytedance.com",
    ".snssdk.com",
    "www.toutiao.com",
}

# Only keep localStorage entries whose names contain these keywords
KEEP_LOCALSTORAGE_KEYWORDS = [
    "token", "auth", "login", "user", "uid", "session",
    "passport", "sso", "xmst", "SLARDAR", "tea_cache",
    "csrf", "odin", "sid", "staff", "biz",
]


def should_keep_cookie(cookie: dict) -> bool:
    domain = cookie.get("domain", "")
    return domain in KEEP_COOKIE_DOMAINS


def should_keep_storage(key: str) -> bool:
    for kw in KEEP_LOCALSTORAGE_KEYWORDS:
        if kw.lower() in key.lower():
            return True
    return False


def main():
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        state = json.load(f)

    # Clean cookies
    old_cookies = state.get("cookies", [])
    new_cookies = [c for c in old_cookies if should_keep_cookie(c)]
    state["cookies"] = new_cookies

    # Clean localStorage in origins
    new_origins = []
    for origin in state.get("origins", []):
        old_storage = origin.get("localStorage", [])
        new_storage = [
            s for s in old_storage if should_keep_storage(s.get("name", ""))
        ]
        if new_storage:
            origin["localStorage"] = new_storage
            new_origins.append(origin)
    state["origins"] = new_origins

    # Write cleaned state
    with open(CLEAN_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, separators=(",", ":"))

    original_size = os.path.getsize(STATE_FILE)
    clean_size = os.path.getsize(CLEAN_FILE)

    print(f"原始: {original_size:,} 字节 ({original_size/1024:.1f} KB)")
    print(f"清理后: {clean_size:,} 字节 ({clean_size/1024:.1f} KB)")
    print(f"Cookie: {len(old_cookies)} → {len(new_cookies)} 个")
    print(f"限制: 48,000 字节 (48 KB)")

    if clean_size > 48000:
        print()
        print("⚠️  还是太大！进一步压缩中...")
        # Further strip: remove non-essential cookie fields
        for c in new_cookies:
            for field in ["sameSite", "secure", "httpOnly", "path"]:
                c.pop(field, None)
        with open(CLEAN_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, separators=(",", ":"))
        clean_size = os.path.getsize(CLEAN_FILE)
        print(f"二次压缩后: {clean_size:,} 字节 ({clean_size/1024:.1f} KB)")

    if clean_size <= 48000:
        print()
        print(f"✅ 清理后的文件: {CLEAN_FILE}")
        print("   可以复制到 GitHub Secret 了！")
    else:
        print()
        print(f"❌ 仍然超过 48KB 限制 ({clean_size:,} 字节)")
        print("   请手动删除 toutiao_state.json 中不必要的内容")


if __name__ == "__main__":
    main()
