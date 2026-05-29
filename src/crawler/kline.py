import json
import os
import time
from datetime import datetime, timedelta
import requests
import pandas as pd
import yfinance as yf
from config.settings import (
    HEADERS, REQUEST_TIMEOUT, MAX_RETRIES, KLINE_DAYS, DATA_DIR,
)


def _market_prefix(code):
    return "sh" if code.startswith("6") else "sz"


def _eastmoney_secid(code):
    return f"1.{code}" if code.startswith("6") else f"0.{code}"


def _yfinance_ticker(code):
    return f"{code}.SS" if code.startswith("6") else f"{code}.SZ"


def fetch_kline_batch(stock_list):
    tencent_results = {}
    for stock in stock_list:
        code = stock["code"]
        df = _fetch_from_tencent(code, KLINE_DAYS)
        if df is not None and not df.empty:
            tencent_results[code] = df
    if len(tencent_results) > len(stock_list) * 0.5:
        return tencent_results

    ticker_map = {_yfinance_ticker(s["code"]): s["code"] for s in stock_list}
    tickers = list(ticker_map.keys())
    try:
        end = datetime.now()
        start = end - timedelta(days=KLINE_DAYS + 30)
        df_all = yf.download(tickers, start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"), progress=False)
        if df_all.empty:
            return {}
        results = {}
        for yf_ticker, code in ticker_map.items():
            try:
                if "Close" in df_all.columns:
                    sub = df_all.xs(yf_ticker, level=1, axis=1) if len(tickers) > 1 else df_all
                else:
                    sub = df_all
                if sub.empty:
                    continue
                sub = sub.reset_index()
                sub = sub.rename(columns={
                    "Date": "date", "Open": "open", "High": "high",
                    "Low": "low", "Close": "close", "Volume": "volume",
                })
                for col in ["open", "close", "high", "low", "volume"]:
                    if col not in sub.columns:
                        continue
                sub["amount"] = 0
                sub["amplitude"] = 0
                sub["pct_chg"] = 0
                sub["change"] = 0
                sub["turnover"] = 0
                cols = ["date", "open", "close", "high", "low", "volume", "amount", "amplitude", "pct_chg", "change", "turnover"]
                sub = sub[[c for c in cols if c in sub.columns]]
                sub["date"] = pd.to_datetime(sub["date"])
                sub = sub.sort_values("date").tail(KLINE_DAYS)
                if len(sub) >= 20:
                    results[code] = sub
            except Exception:
                pass
        return results
    except Exception:
        for stock in stock_list:
            code = stock["code"]
            df = _fetch_from_yfinance_single(code, KLINE_DAYS)
            if df is not None and not df.empty and len(df) >= 20:
                pass
        return _fetch_batch_sequential(stock_list)


def _fetch_batch_sequential(stock_list):
    results = {}
    for stock in stock_list:
        code = stock["code"]
        df = fetch_kline(code, stock["market"])
        if df is not None and not df.empty and len(df) >= 20:
            results[code] = df
    return results


def fetch_kline(code, market, days=KLINE_DAYS):
    cache_path = _cache_path(code)
    cached = _load_cache(cache_path)
    if cached is not None:
        return cached

    df = _fetch_from_tencent(code, days)
    if df is None:
        df = _fetch_from_eastmoney(code, days)
    if df is None:
        df = _fetch_from_yfinance_single(code, days)

    if df is not None and not df.empty:
        _save_cache(cache_path, df)
    return df


def _fetch_from_tencent(code, days):
    try:
        prefix = _market_prefix(code)
        url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
        params = {"param": f"{prefix}{code},day,,,{days + 10},qfq", "_var": "kline_day"}
        resp = requests.get(url, params=params, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        text = resp.text.replace("kline_day=", "")
        data = json.loads(text)
        stock_data = data.get("data", {}).get(f"{prefix}{code}", {})
        klines = stock_data.get("qfqday") or stock_data.get("day")
        if not klines:
            return None
        rows = []
        for line in klines[-days:]:
            rows.append({
                "date": line[0], "open": float(line[1]), "close": float(line[2]),
                "high": float(line[3]), "low": float(line[4]), "volume": float(line[5]),
                "amount": 0, "amplitude": 0, "pct_chg": 0, "change": 0, "turnover": 0,
            })
        df = pd.DataFrame(rows)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date")
        return df
    except Exception:
        return None


def _fetch_from_eastmoney(code, days):
    try:
        end_date = datetime.now().strftime("%Y%m%d")
        beg_date = (datetime.now() - timedelta(days=days + 30)).strftime("%Y%m%d")
        secid = _eastmoney_secid(code)
        url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
        params = {
            "secid": secid, "klt": "101", "fqt": "1",
            "beg": beg_date, "end": end_date,
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
            "lmt": days + 10, "_": int(time.time() * 1000),
        }
        resp = requests.get(url, params=params, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        data = resp.json()
        if not data.get("data") or not data["data"].get("klines"):
            return None
        rows = []
        for line in data["data"]["klines"]:
            parts = line.split(",")
            if len(parts) >= 11:
                rows.append({
                    "date": parts[0], "open": float(parts[1]),
                    "close": float(parts[2]), "high": float(parts[3]),
                    "low": float(parts[4]), "volume": float(parts[5]),
                    "amount": float(parts[6]),
                    "amplitude": float(parts[7]) if parts[7] != "-" else 0,
                    "pct_chg": float(parts[8]) if parts[8] != "-" else 0,
                    "change": float(parts[9]) if parts[9] != "-" else 0,
                    "turnover": float(parts[10]) if parts[10] != "-" else 0,
                })
        df = pd.DataFrame(rows)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date").tail(days)
        return df
    except Exception:
        return None


def _fetch_from_yfinance_single(code, days):
    try:
        ticker_str = _yfinance_ticker(code)
        ticker = yf.Ticker(ticker_str)
        end = datetime.now()
        start = end - timedelta(days=days + 30)
        df = ticker.history(start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"))
        if df.empty:
            return None
        df = df.reset_index()
        df = df.rename(columns={
            "Date": "date", "Open": "open", "High": "high",
            "Low": "low", "Close": "close", "Volume": "volume",
        })
        df["amount"] = 0
        df["amplitude"] = 0
        df["pct_chg"] = 0
        df["change"] = 0
        df["turnover"] = 0
        for col in ["date", "open", "close", "high", "low", "volume", "amount", "amplitude", "pct_chg", "change", "turnover"]:
            if col not in df.columns:
                df[col] = 0
        df = df[["date", "open", "close", "high", "low", "volume", "amount", "amplitude", "pct_chg", "change", "turnover"]]
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").tail(days)
        return df
    except Exception:
        return None


def _cache_path(code):
    return os.path.join(DATA_DIR, f"kline_{code}.pkl")


def _load_cache(path):
    if not os.path.exists(path):
        return None
    mtime = datetime.fromtimestamp(os.path.getmtime(path))
    if datetime.now() - mtime > timedelta(hours=24):
        return None
    try:
        return pd.read_pickle(path)
    except Exception:
        return None


def _save_cache(path, df):
    try:
        df.to_pickle(path)
    except Exception:
        pass
