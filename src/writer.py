"""AI content writer using DeepSeek API."""

from __future__ import annotations

import logging
import requests

import src.config as config
from src.utils import today_cn

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一位专业的中文财经/生活资讯作者，擅长用通俗语言解读数据。
写作要求：
1. 标题要吸引点击但不夸张，15-25字
2. 正文800字左右，段落分明
3. 开头要有亮点数据抓人眼球
4. 中间展开分析+背景知识
5. 结尾给出简短总结或建议
6. 语言自然流畅，像真人写的，不要AI腔（避免"值得注意的是""综上所述""此外"等套话）
7. 如果涉及数据，给出普通人能理解的类比或解读

输出格式（严格按此格式）：
===TITLE===
文章标题
===CONTENT===
文章正文（800字左右）"""


def call_deepseek(prompt: str) -> str | None:
    """Call DeepSeek Chat API. Returns response text or None on failure."""
    headers = {
        "Authorization": f"Bearer {config.DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.8,
        "max_tokens": 2048,
    }
    try:
        resp = requests.post(
            f"{config.DEEPSEEK_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        logger.info(
            f"DeepSeek OK. tokens: {usage.get('total_tokens', '?')} "
            f"(prompt: {usage.get('prompt_tokens', '?')}, "
            f"completion: {usage.get('completion_tokens', '?')})"
        )
        return content
    except Exception as e:
        logger.error(f"DeepSeek API call failed: {e}")
        return None


def parse_article(raw: str) -> dict:
    """Parse the ===TITLE=== / ===CONTENT=== formatted output."""
    title = ""
    content = ""
    if "===TITLE===" in raw and "===CONTENT===" in raw:
        parts = raw.split("===TITLE===", 1)[1]
        title_part, content_part = parts.split("===CONTENT===", 1)
        title = title_part.strip()
        content = content_part.strip()
    else:
        # Fallback: use first line as title
        lines = raw.strip().split("\n")
        title = lines[0].strip().lstrip("#").strip()
        content = "\n".join(lines[1:]).strip()

    return {"title": title, "content": content}


def write_gold_article(gold_data_str: str) -> dict | None:
    """Generate an article about today's gold price."""
    prompt = f"""今天的日期是{today_cn()}。

以下是最新的黄金价格数据：
{gold_data_str}

请根据以上数据写一篇财经资讯文章。要求：
- 解读今日金价变化及原因
- 给普通投资者3条实用建议
- 字数约{config.ARTICLE_WORD_COUNT}字"""

    raw = call_deepseek(prompt)
    if not raw:
        return None
    return parse_article(raw)


def write_weather_article(weather_data_str: str) -> dict | None:
    """Generate a weather forecast article."""
    prompt = f"""今天的日期是{today_cn()}。

以下是今日天气预报数据：
{weather_data_str}

请据此写一篇生活服务类天气资讯文章。要求：
- 概括全国主要城市天气趋势
- 给出出行/穿衣/健康方面的提醒
- 语气亲切，像一位贴心的生活管家
- 字数约{config.ARTICLE_WORD_COUNT}字"""

    raw = call_deepseek(prompt)
    if not raw:
        return None
    return parse_article(raw)


def write_history_article(history_data_str: str) -> dict | None:
    """Generate a 'today in history' article."""
    prompt = f"""今天的日期是{today_cn()}。

{history_data_str}

请据此写一篇"历史上的今天"文章。要求：
- 挑选3-5件最重要的事件展开讲
- 每个事件补充有趣的背景故事
- 结尾以当天的历史规律做一句话总结
- 字数约{config.ARTICLE_WORD_COUNT}字"""

    raw = call_deepseek(prompt)
    if not raw:
        return None
    return parse_article(raw)
