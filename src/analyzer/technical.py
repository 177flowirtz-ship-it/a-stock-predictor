import numpy as np
import pandas as pd
from config.settings import TECHNICAL_MAX_SCORES


def score_technical(kline_df):
    if kline_df is None or len(kline_df) < 30:
        return {
            "ma_trend": 0,
            "macd": 0,
            "kdj": 0,
            "rsi": 0,
            "boll": 0,
            "volume_price": 0,
            "total": 0,
        }

    scores = {}
    scores["ma_trend"] = _score_ma_trend(kline_df)
    scores["macd"] = _score_macd(kline_df)
    scores["kdj"] = _score_kdj(kline_df)
    scores["rsi"] = _score_rsi(kline_df)
    scores["boll"] = _score_boll(kline_df)
    scores["volume_price"] = _score_volume_price(kline_df)
    scores["total"] = sum(scores.values())
    return scores


def _score_ma_trend(df):
    closes = df["close"].values
    ma5 = np.mean(closes[-5:])
    ma10 = np.mean(closes[-10:])
    ma20 = np.mean(closes[-20:])
    ma60 = np.mean(closes[-min(60, len(closes)) :])

    score = 0
    max_score = TECHNICAL_MAX_SCORES["ma_trend"]
    if ma5 > ma10:
        score += max_score * 0.25
    if ma10 > ma20:
        score += max_score * 0.25
    if ma20 > ma60:
        score += max_score * 0.25
    if closes[-1] > ma5:
        score += max_score * 0.25
    return round(score, 1)


def _score_macd(df):
    closes = df["close"].values
    ema12 = _ema(closes, 12)
    ema26 = _ema(closes, 26)
    dif = ema12 - ema26
    dea = _ema_from_array(np.array([dif]) if np.isscalar(dif) else dif, 9)
    if np.isscalar(dea):
        dea = np.array([dea])
    macd_bar = 2 * (dif - dea)

    max_score = TECHNICAL_MAX_SCORES["macd"]
    score = 0

    if len(dif) < 2 or len(dea) < 2:
        return 0

    dif_now, dif_prev = dif[-1], dif[-2]
    dea_now = dea[-1]

    if dif_now > dea_now and dif_prev <= dea[-2]:
        score += max_score * 0.5

    if dif_now > 0:
        score += max_score * 0.3

    if len(macd_bar) >= 3:
        bar_now, bar_prev = macd_bar[-1], macd_bar[-2]
        if bar_now > bar_prev:
            score += max_score * 0.2

    return round(score, 1)


def _score_kdj(df):
    n = 9
    closes = df["close"].values
    highs = df["high"].values
    lows = df["low"].values

    if len(closes) < n + 1:
        return 0

    low_n = np.min(lows[-n:])
    high_n = np.max(highs[-n:])
    rsv = ((closes[-1] - low_n) / (high_n - low_n)) * 100 if high_n != low_n else 50

    k = rsv * 1 / 3 + 50 * 2 / 3
    d = k * 1 / 3 + 50 * 2 / 3

    max_score = TECHNICAL_MAX_SCORES["kdj"]
    score = 0

    if 20 <= k <= 80:
        score += max_score * 0.4
    if k > d:
        score += max_score * 0.3
    if 20 <= k <= 50:
        score += max_score * 0.3

    return round(score, 1)


def _score_rsi(df):
    n = 14
    closes = df["close"].values

    if len(closes) < n + 1:
        return 0

    deltas = np.diff(closes[-n - 1 :])
    gain = np.sum(deltas[deltas > 0])
    loss = abs(np.sum(deltas[deltas < 0]))

    if loss == 0:
        rsi = 100
    else:
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

    max_score = TECHNICAL_MAX_SCORES["rsi"]
    score = 0

    if 30 <= rsi <= 70:
        score += max_score * 0.6
    elif rsi < 30:
        score += max_score * 0.8
    elif rsi > 80:
        score += max_score * 0.1

    if rsi > 50:
        score += max_score * 0.2

    return round(score, 1)


def _score_boll(df):
    n = 20
    closes = df["close"].values

    if len(closes) < n:
        return 0

    ma = np.mean(closes[-n:])
    std = np.std(closes[-n:])
    upper = ma + 2 * std
    lower = ma - 2 * std
    now = closes[-1]

    max_score = TECHNICAL_MAX_SCORES["boll"]
    score = 0

    if now > ma:
        score += max_score * 0.5

    bb_position = (now - lower) / (upper - lower) if upper != lower else 0.5
    if 0.4 <= bb_position <= 0.8:
        score += max_score * 0.3
    elif bb_position < 0.2:
        score += max_score * 0.5

    percent_b = (now - lower) / (upper - lower) if upper != lower else 0.5
    if 0.3 < percent_b < 0.7:
        score += max_score * 0.2

    return round(score, 1)


def _score_volume_price(df):
    if len(df) < 5:
        return 0

    closes = df["close"].values
    volumes = df["volume"].values

    price_chg = (closes[-1] - closes[-5]) / closes[-5] if closes[-5] != 0 else 0
    vol_avg_prev = np.mean(volumes[-10:-5]) if len(volumes) >= 10 else np.mean(volumes[:-5])
    vol_avg_now = np.mean(volumes[-5:])
    vol_chg = (vol_avg_now - vol_avg_prev) / vol_avg_prev if vol_avg_prev != 0 else 0

    max_score = TECHNICAL_MAX_SCORES["volume_price"]
    score = 0

    if price_chg > 0 and vol_chg > 0:
        score += max_score * 0.7
    elif price_chg > 0 and vol_chg > -0.1:
        score += max_score * 0.5
    elif price_chg < 0 and vol_chg < -0.2:
        score += max_score * 0.2

    if closes[-1] > closes[-2] and volumes[-1] > volumes[-2]:
        score += max_score * 0.3

    return round(score, 1)


def _ema(data, span):
    data = np.asarray(data, dtype=float)
    alpha = 2 / (span + 1)
    result = np.zeros_like(data)
    result[0] = data[0]
    for i in range(1, len(data)):
        result[i] = alpha * data[i] + (1 - alpha) * result[i - 1]
    return result


def _ema_from_array(data, span):
    return _ema(data, span)
