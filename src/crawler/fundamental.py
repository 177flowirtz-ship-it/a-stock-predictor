import json
import time
import requests
from config.settings import (
    EASTMONEY_FUNDAMENTAL_URL,
    HEADERS,
    REQUEST_TIMEOUT,
    REQUEST_INTERVAL,
    MAX_RETRIES,
)


def fetch_fundamental_data(code):
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

        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(REQUEST_INTERVAL * (2**attempt))
            else:
                pass

    return result
