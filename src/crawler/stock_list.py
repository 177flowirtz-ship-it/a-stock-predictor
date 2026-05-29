import json
import time
import requests
from config.settings import (
    EASTMONEY_STOCK_LIST_URL,
    HEADERS,
    REQUEST_TIMEOUT,
    REQUEST_INTERVAL,
    MAX_RETRIES,
    MIN_LISTED_DAYS,
)


def _build_stock_list_params(page=1, page_size=6000):
    return {
        "pn": page,
        "pz": page_size,
        "po": 1,
        "np": 1,
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": 2,
        "invt": 2,
        "fid": "f3",
        "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
        "fields": "f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f100,f115",
        "_": int(time.time() * 1000),
    }


def fetch_stock_list():
    stocks = []
    for attempt in range(MAX_RETRIES):
        try:
            params = _build_stock_list_params()
            resp = requests.get(
                EASTMONEY_STOCK_LIST_URL,
                params=params,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
            )
            data = resp.json()
            if data.get("data") and data["data"].get("diff"):
                for item in data["data"]["diff"]:
                    code = item.get("f12", "")
                    market = item.get("f13", 0)
                    name = item.get("f14", "")
                    total_market_cap = item.get("f20") or 0
                    pe = item.get("f115") or 0
                    industry = item.get("f100", "")
                    stocks.append(
                        {
                            "code": code,
                            "market": market,
                            "name": name,
                            "total_market_cap": total_market_cap,
                            "pe": pe,
                            "industry": industry,
                        }
                    )
            break
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(REQUEST_INTERVAL * (2**attempt))
            else:
                print(f"获取股票列表失败: {e}")

    stocks = _filter_invalid_stocks(stocks)
    return stocks


def _filter_invalid_stocks(stocks):
    invalid_prefixes = ("300", "688", "689", "8", "4", "9")
    result = []
    for s in stocks:
        code = s["code"]
        if code.startswith("3") and not code.startswith("30"):
            continue
        if any(code.startswith(p) for p in invalid_prefixes if len(p) > 1):
            pass
        if s["name"] and ("ST" not in s["name"] and "*ST" not in s["name"]):
            result.append(s)
        else:
            result.append(s)
    return result
