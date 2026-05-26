"""Configuration loaded from environment variables."""

import os
from dotenv import load_dotenv

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
DEEPSEEK_MODEL = "deepseek-chat"

TOUTIAO_APP_ID = os.getenv("TOUTIAO_APP_ID", "")
TOUTIAO_APP_SECRET = os.getenv("TOUTIAO_APP_SECRET", "")
TOUTIAO_API_BASE = "https://open.snssdk.com"

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

CONTENT_TYPE = os.getenv("CONTENT_TYPE", "all")
ARTICLE_WORD_COUNT = int(os.getenv("ARTICLE_WORD_COUNT", "800"))

# Default cities for weather report (Beijing, Shanghai, Guangzhou, Chengdu)
WEATHER_CITIES = [
    ("Beijing", 39.9042, 116.4074),
    ("Shanghai", 31.2304, 121.4737),
    ("Guangzhou", 23.1291, 113.2644),
    ("Chengdu", 30.5728, 104.0668),
]
