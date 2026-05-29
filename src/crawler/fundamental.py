import time
import requests
import yfinance as yf
from config.settings import (
    EASTMONEY_FUNDAMENTAL_URL,
    HEADERS,
    REQUEST_TIMEOUT,
    REQUEST_INTERVAL,
    MAX_RETRIES,
)


def _yfinance_ticker(code):
    return f"{code}.SS" if code.startswith("6") else f"{code}.SZ"


def fetch_fundamental_data(code):
    result = _fetch_from_eastmoney(code)
    if result and any(result.values()):
        return result

    result = _fetch_from_yfinance(code)
    if result and any(result.values()):
        return result

    return {"pe": None, "pb": None, "roe": None, "revenue_growth": None}


def _fetch_from_eastmoney(code):
    result = {"pe": None, "pb": None, "roe": None, "revenue_growth": None}
    for attempt in range(MAX_RETRIES):
        try:
            params = {
                "reportName": "RPT_DMSK_FN_MAININDICATOR",
                "columns": "ALL",
                "filter": f'(SECURITY_CODE="{code}")',
                "pageNumber": 1,
                "pageSize": 4,
                "sortTypes": -1,
                "sortColumns": "REPORT_DATE",
                "source": "HSF10",
                "client": "PC",
            }
            resp = requests.get(
                EASTMONEY_FUNDAMENTAL_URL,
                params=params,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
            )
            data = resp.json()
            if data.get("success") and data.get("result") and data["result"].get("data"):
                records = data["result"]["data"]
                if records:
                    latest = records[0]
                    result["pe"] = latest.get("PE_TTM")
                    result["pb"] = latest.get("PB")
                    result["roe"] = latest.get("ROE_WEIGHTAVG")
                    result["revenue_growth"] = latest.get("TOTALOPERATEREVE_YOY")
            time.sleep(REQUEST_INTERVAL)
            break
        except Exception:
            if attempt < MAX_RETRIES - 1:
                time.sleep(REQUEST_INTERVAL * (2**attempt))
    return result


def _fetch_from_yfinance(code):
    result = {"pe": None, "pb": None, "roe": None, "revenue_growth": None}
    try:
        ticker_str = _yfinance_ticker(code)
        ticker = yf.Ticker(ticker_str)
        info = ticker.info
        if info:
            pe = info.get("trailingPE") or info.get("forwardPE")
            pb = info.get("priceToBook")
            roe = info.get("returnOnEquity")
            if roe is not None:
                roe = roe * 100
            rev_growth = info.get("revenueGrowth")
            if rev_growth is not None:
                rev_growth = rev_growth * 100

            result["pe"] = pe
            result["pb"] = pb
            result["roe"] = roe
            result["revenue_growth"] = rev_growth
    except Exception:
        pass
    return result
