import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")

EASTMONEY_STOCK_LIST_URL = "http://80.push2.eastmoney.com/api/qt/clist/get"
EASTMONEY_KLINE_URL = "http://push2his.eastmoney.com/api/qt/stock/kline/get"
EASTMONEY_CAPITAL_FLOW_URL = "http://push2.eastmoney.com/api/qt/stock/fflow/daykline/get"
EASTMONEY_FUNDAMENTAL_URL = "https://datacenter.eastmoney.com/securities/api/data/v1/get"

REQUEST_TIMEOUT = 30
REQUEST_INTERVAL = 0.5
MAX_RETRIES = 3

KLINE_DAYS = 120
MIN_LISTED_DAYS = 60

WEIGHTS = {
    "technical": 0.40,
    "capital": 0.30,
    "sentiment": 0.15,
    "fundamental": 0.15,
}

RATING_THRESHOLDS = [
    (85, "★★★★★", "强烈看涨"),
    (70, "★★★★☆", "看涨"),
    (55, "★★★☆☆", "中性偏多"),
    (40, "★★★☆☆", "中性偏空"),
    (25, "★★☆☆☆", "看跌"),
    (0, "★☆☆☆☆", "强烈看跌"),
]

TECHNICAL_MAX_SCORES = {
    "ma_trend": 8,
    "macd": 8,
    "kdj": 6,
    "rsi": 6,
    "boll": 6,
    "volume_price": 6,
}

CAPITAL_MAX_SCORES = {
    "main_flow": 10,
    "super_large_flow": 8,
    "north_flow": 7,
    "flow_trend": 5,
}

SENTIMENT_MAX_SCORES = {
    "news_heat": 8,
    "guba_activity": 7,
}

FUNDAMENTAL_MAX_SCORES = {
    "pe_percentile": 5,
    "pb_percentile": 4,
    "roe": 3,
    "revenue_growth": 3,
}

OUTPUT_TOP_N = 20

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "http://quote.eastmoney.com/",
}
