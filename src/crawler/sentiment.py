import time
import requests
from config.settings import (
    HEADERS,
    REQUEST_TIMEOUT,
    REQUEST_INTERVAL,
    MAX_RETRIES,
)


def fetch_sentiment_data(code):
    result = {"news_heat_score": 0.0, "guba_activity_score": 0.0}

    news_score = _fetch_news_heat(code)
    if news_score is not None:
        result["news_heat_score"] = news_score

    guba_score = _fetch_guba_activity(code)
    if guba_score is not None:
        result["guba_activity_score"] = guba_score

    return result


def _fetch_news_heat(code):
    for attempt in range(MAX_RETRIES):
        try:
            market_code = "1" if code.startswith("6") else "2"
            full_code = f"{market_code}.{code}" if market_code == "1" else f"{market_code}.{code}"
            symbol = f"{market_code}{code}"
            url = f"https://search-api-web.eastmoney.com/search/jsonp"
            params = {
                "cb": "jQuery",
                "param": f'{{"uid":"","keyword":"{symbol}","type":["8196"],"client":"web","clientType":"web","pageNo":1,"pageSize":5,"sort":"default","_":{int(time.time() * 1000)}}}',
            }
            resp = requests.get(url, params=params, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            text = resp.text
            if "jQuery(" in text:
                text = text[text.find("(") + 1 : text.rfind(")")]
            import json

            data = json.loads(text)
            total_count = 0
            if data.get("result") and data["result"].get("totalcount"):
                total_count = int(data["result"]["totalcount"])

            if total_count > 100:
                score = 8.0
            elif total_count > 50:
                score = 6.0
            elif total_count > 20:
                score = 4.0
            elif total_count > 5:
                score = 2.0
            else:
                score = 0.0

            time.sleep(REQUEST_INTERVAL)
            return score

        except Exception:
            if attempt < MAX_RETRIES - 1:
                time.sleep(REQUEST_INTERVAL * (2**attempt))
            else:
                return 0.0

    return 0.0


def _fetch_guba_activity(code):
    for attempt in range(MAX_RETRIES):
        try:
            market_code = "1" if code.startswith("6") else "2"
            full_code = f"{market_code}{code}" if market_code == "1" else f"{market_code}{code}"
            url = f"https://searchapi.eastmoney.com/bussiness/Web/GetCMSSearchResult"
            params = {
                "type": "8197",
                "keyword": code,
                "pageindex": 1,
                "pagesize": 5,
                "name": "guba",
            }
            resp = requests.get(url, params=params, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            data = resp.json()

            total_count = 0
            if data.get("Data") and data["Data"]:
                total_count = len(data["Data"])

            if total_count > 50:
                score = 7.0
            elif total_count > 20:
                score = 5.0
            elif total_count > 10:
                score = 3.0
            elif total_count > 3:
                score = 1.5
            else:
                score = 0.0

            time.sleep(REQUEST_INTERVAL)
            return score

        except Exception:
            if attempt < MAX_RETRIES - 1:
                time.sleep(REQUEST_INTERVAL * (2**attempt))
            else:
                return 0.0

    return 0.0
