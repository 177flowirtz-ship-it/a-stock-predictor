import json
import time
from datetime import datetime, timedelta
import requests
import pandas as pd
from config.settings import (
    EASTMONEY_CAPITAL_FLOW_URL,
    HEADERS,
    REQUEST_TIMEOUT,
    REQUEST_INTERVAL,
    MAX_RETRIES,
)


def _market_id(market):
    m = str(market)
    return "1" if m.startswith("0") else "0"


def _secid(code, market):
    m = _market_id(market)
    return f"{m}.{code}"


def fetch_capital_flow(code, market):
    for attempt in range(MAX_RETRIES):
        try:
            params = {
                "secid": _secid(code, market),
                "fields1": "f1,f2,f3,f7",
                "fields2": "f51,f52,f53,f54,f55,f56,f57",
                "ut": "7eea3edcaed734bea9cbfce24459ed57",
                "lmt": 30,
                "_": int(time.time() * 1000),
            }
            resp = requests.get(
                EASTMONEY_CAPITAL_FLOW_URL,
                params=params,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
            )
            data = resp.json()
            if not data.get("data") or not data["data"].get("klines"):
                return None

            rows = []
            for line in data["data"]["klines"]:
                parts = line.split(",")
                if len(parts) >= 7:
                    rows.append(
                        {
                            "date": parts[0],
                            "main_net_inflow": _safe_float(parts[1]),
                            "super_large_net_inflow": _safe_float(parts[2]),
                            "large_net_inflow": _safe_float(parts[3]),
                            "medium_net_inflow": _safe_float(parts[4]),
                            "small_net_inflow": _safe_float(parts[5]),
                        }
                    )

            df = pd.DataFrame(rows)
            if not df.empty:
                df["date"] = pd.to_datetime(df["date"])
                df = df.sort_values("date")

            time.sleep(REQUEST_INTERVAL)
            return df

        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(REQUEST_INTERVAL * (2**attempt))
            else:
                return None

    return None


def _safe_float(val):
    try:
        return float(val) if val != "-" else 0.0
    except (ValueError, TypeError):
        return 0.0
