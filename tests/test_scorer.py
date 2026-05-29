import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.analyzer.scorer import compute_final_score
from src.analyzer.technical import score_technical
from src.analyzer.capital import score_capital
from src.analyzer.sentiment import score_sentiment
from src.analyzer.fundamental import score_fundamental


def test_technical_scoring():
    import pandas as pd
    import numpy as np

    dates = pd.date_range("2026-01-01", periods=120, freq="B")
    np.random.seed(42)
    base_price = 10.0
    closes = [base_price]
    for i in range(1, 120):
        chg = np.random.normal(0.0005, 0.015)
        closes.append(closes[-1] * (1 + chg))

    df = pd.DataFrame(
        {
            "date": dates,
            "open": [c * (1 + np.random.normal(0, 0.005)) for c in closes],
            "close": closes,
            "high": [c * (1 + abs(np.random.normal(0, 0.008))) for c in closes],
            "low": [c * (1 - abs(np.random.normal(0, 0.008))) for c in closes],
            "volume": np.random.uniform(1e6, 1e7, 120),
            "amount": np.zeros(120),
            "amplitude": np.zeros(120),
            "pct_chg": np.zeros(120),
            "change": np.zeros(120),
            "turnover": np.zeros(120),
        }
    )

    result = score_technical(df)
    assert result is not None
    assert "total" in result
    assert 0 <= result["total"] <= 40
    print(f"Technical score: {result}")


def test_capital_scoring():
    import pandas as pd
    import numpy as np

    dates = pd.date_range("2026-01-01", periods=30, freq="B")
    df = pd.DataFrame(
        {
            "date": dates,
            "main_net_inflow": np.random.normal(0, 1e7, 30),
            "super_large_net_inflow": np.random.normal(0, 5e6, 30),
            "large_net_inflow": np.random.normal(0, 5e6, 30),
            "medium_net_inflow": np.random.normal(0, 3e6, 30),
            "small_net_inflow": np.random.normal(0, 2e6, 30),
        }
    )

    result = score_capital(df)
    assert result is not None
    assert "total" in result
    assert 0 <= result["total"] <= 30
    print(f"Capital score: {result}")


def test_sentiment_scoring():
    data = {"news_heat_score": 6.0, "guba_activity_score": 5.0}
    result = score_sentiment(data)
    assert result is not None
    assert "total" in result
    assert 0 <= result["total"] <= 15
    print(f"Sentiment score: {result}")


def test_fundamental_scoring():
    data = {"pe": 15.0, "pb": 2.0, "roe": 18.0, "revenue_growth": 25.0}
    result = score_fundamental(data)
    assert result is not None
    assert "total" in result
    assert 0 <= result["total"] <= 15
    print(f"Fundamental score: {result}")

    data_bad = {"pe": -5.0, "pb": 0, "roe": -10.0, "revenue_growth": -30.0}
    result_bad = score_fundamental(data_bad)
    assert result_bad["total"] == 0


def test_final_scoring():
    tech = {"total": 30, "ma_trend": 6, "macd": 6, "kdj": 4, "rsi": 4, "boll": 5, "volume_price": 5}
    cap = {"total": 22, "main_flow": 7, "super_large_flow": 6, "north_flow": 4, "flow_trend": 5}
    sent = {"total": 10, "news_heat": 6, "guba_activity": 4}
    fund = {"total": 10, "pe_percentile": 4, "pb_percentile": 3, "roe": 2, "revenue_growth": 1}

    result = compute_final_score(tech, cap, sent, fund)
    assert result is not None
    assert "total_score" in result
    assert 0 <= result["total_score"] <= 100
    assert "stars" in result
    assert "rating" in result
    print(f"Final score: {result}")


if __name__ == "__main__":
    test_technical_scoring()
    test_capital_scoring()
    test_sentiment_scoring()
    test_fundamental_scoring()
    test_final_scoring()
    print("\nAll tests passed!")
