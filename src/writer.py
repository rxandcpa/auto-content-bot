"""AI content writer using DeepSeek API. Human-style prompts for natural output."""

from __future__ import annotations

import logging
import random

import requests

import src.config as config
from src.utils import today_cn

logger = logging.getLogger(__name__)

# ── Base system prompt: establishes the writer's persona ──

SYSTEM_PROMPT = """你叫老七，是一个有10年经验的中文自媒体写手，擅长把复杂信息写成普通人爱看的文章。

你的写作铁律（违反任何一条=失败）：

【真实性——最重要，违反直接报废】
1. 只能使用提供给你的数据。不要编造、修改、或"补充"任何数字、日期、人名、地名
2. 如果数据里说金价是 X 美元，你只能写 X 美元，不能改成其他数字
3. 如果数据不足以支撑一篇完整的分析，可以简短收尾，但绝不能编造来填字数
4. 不要引用"某专家说""据分析""机构预测"这类虚构信源

【文风】
6. 第一句必须制造悬念或抛出一个让人想继续读的事实，禁止用"今天""近日""随着"开头
7. 每段不超过4句话，段落之间用空行隔开
8. 数据必须配上生活化类比（比如"这个数字相当于北京市一年的GDP"）
9. 至少出现一处第一人称的感受或吐槽（"说实话""我看完数据之后""说实话有点意外"）
10. 禁用这些AI套话：值得注意的是、此外、总而言之、综上所述、显而易见、毋庸置疑、众所周知
11. 标题要有情绪但不标题党，让读者产生"这个我得看看"的冲动
12. 结尾要干脆，一句话收住，不要"让我们拭目以待""未来可期"这类废话

输出格式：
===TITLE===
文章标题
===CONTENT===
文章正文"""


def call_deepseek(system: str, user_prompt: str) -> str | None:
    """Call DeepSeek Chat API."""
    headers = {
        "Authorization": f"Bearer {config.DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.85 + random.random() * 0.1,  # 0.85-0.95 for variety
        "max_tokens": 2048,
        "top_p": 0.92,
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
            f"DeepSeek OK. tokens: {usage.get('total_tokens', '?')}"
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
        lines = raw.strip().split("\n")
        title = lines[0].strip().lstrip("#").strip()
        content = "\n".join(lines[1:]).strip()

    return {"title": title, "content": content}


# ── Per-topic prompts ──

def write_gold_article(gold_data_str: str) -> dict | None:
    """Financial news: gold price analysis."""
    system = SYSTEM_PROMPT + """

你是财经类爆款写手。你的读者是普通上班族，不是金融从业者。用最直白的大白话讲清楚金价波动和他们钱包的关系。"""

    angles = [
        "假设你手里有1万块闲钱，今天该不该买黄金？只根据提供的数据给一个明确的判断。",
        "金价变了。只根据数据里的价格，给出具体的投资操作建议（买/卖/持有），不要预测未来价格。",
        "只使用提供的数据，分析当前金价对普通人的3条影响。",
    ]
    angle = random.choice(angles)

    prompt = (
        f"今天是{today_cn()}。\n"
        f"金价数据：{gold_data_str}\n\n"
        f"{angle}\n"
        f"字数{config.ARTICLE_WORD_COUNT}字左右。\n"
        f"重要：只能使用上面提供的数字。不要修改价格。数据来源会在文末标注。"
    )
    # Append data source disclaimer
    raw = call_deepseek(system, prompt)
    if raw:
        article = parse_article(raw)
        article["content"] += "\n\n（数据来源：国际黄金现货市场实时报价）"
        return article
    return None


def write_weather_article(weather_data_str: str) -> dict | None:
    """Lifestyle: weather forecast."""
    system = SYSTEM_PROMPT + """

你是生活类写手，风格像隔壁热心大哥。天气文章要有烟火气，让人感觉你在关心他的日常。"""

    angles = [
        "写一份今天出行指南，重点提醒哪些城市的天气有'坑'（比如看起来凉快实际闷热）。要具体到穿衣建议。",
        "今天的天气对几类人特别不友好：外卖员、接送孩子的家长、晨练老人。从他们的视角写注意事项。",
        "用'全国天气吐槽大会'的风格写，每个城市点评一句话，幽默但不刻薄。",
    ]
    angle = random.choice(angles)

    prompt = (
        f"今天是{today_cn()}。\n"
        f"天气数据：\n{weather_data_str}\n\n"
        f"{angle}\n"
        f"字数{config.ARTICLE_WORD_COUNT}字左右。\n"
        f"只能使用上面提供的温度、湿度、天气描述，不要编造数据。"
    )
    raw = call_deepseek(system, prompt)
    if raw:
        article = parse_article(raw)
        article["content"] += "\n\n（数据来源：国际气象服务实时数据）"
        return article
    return None


def write_history_article(history_data_str: str) -> dict | None:
    """History: today in history."""
    system = SYSTEM_PROMPT + """

你是历史故事写手，擅长挖出历史事件中不为人知的细节和人性故事。不要写成教科书，要写成深夜电台。"""

    angles = [
        "从今天的几个历史事件中挑一个最震撼的，深挖它的来龙去脉。要讲到具体的人物故事，不要只列时间线。",
        "今天历史上的这些事件有什么共同点？找一个让人意想不到的关联，串联起来写。",
        "如果今天的某位普通上班族穿越到历史上今天的某个重大事件现场，他会看到什么、听到什么？用沉浸式写法。",
    ]
    angle = random.choice(angles)

    prompt = (
        f"今天是{today_cn()}。\n{history_data_str}\n\n"
        f"{angle}\n"
        f"字数{config.ARTICLE_WORD_COUNT}字左右。\n"
        f"只使用上面提供的历史事件。可以展开讲背景故事，但不能编造新的事件、年份或人名。"
    )
    raw = call_deepseek(system, prompt)
    if raw:
        article = parse_article(raw)
        article["content"] += "\n\n（数据来源：维基百科「历史上的今天」）"
        return article
    return None


def write_trending_article(trending_data_str: str) -> dict | None:
    """Hot topics: commentary on trending searches."""
    system = SYSTEM_PROMPT + """

你是热点评论写手，能从热搜榜单里找到最有料的话题展开。观点要鲜明但不极端，让人看完觉得"有道理"。"""

    angles = [
        "从今天的微博热搜里挑2-3个最有话题性的事件，写出它们背后的社会情绪。要有观点，不要只是复述。",
        "今天热搜第一名是什么？看起来可能很无聊，但背后反映了一个值得聊的社会现象。把这个现象讲透。",
        "热搜榜单就像一面镜子，照出了当下人们最关心什么。今天的热搜反映了哪几种集体情绪？一一解读。",
    ]
    angle = random.choice(angles)

    prompt = (
        f"今天是{today_cn()}。\n以下是今日网络热搜榜单：\n{trending_data_str}\n\n"
        f"{angle}\n字数{config.ARTICLE_WORD_COUNT}字左右。\n"
        "重要：热搜榜单是真实数据。你可以评论、分析，但不能编造热搜里不存在的事件。"
        "一个话题写透了，比十个话题一笔带过强。"
    )
    raw = call_deepseek(system, prompt)
    if raw:
        article = parse_article(raw)
        article["content"] += "\n\n（数据来源：微博/百度实时热搜榜）"
        return article
    return None
