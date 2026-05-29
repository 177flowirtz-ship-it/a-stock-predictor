import numpy as np
from config.settings import CAPITAL_MAX_SCORES


def score_capital(capital_flow_df):
    if capital_flow_df is None or len(capital_flow_df) < 5:
        return {
            "main_flow": 0,
            "super_large_flow": 0,
            "north_flow": 0,
            "flow_trend": 0,
            "total": 0,
        }

    scores = {}
    scores["main_flow"] = _score_main_flow(capital_flow_df)
    scores["super_large_flow"] = _score_super_large_flow(capital_flow_df)
    scores["north_flow"] = _score_north_flow(capital_flow_df)
    scores["flow_trend"] = _score_flow_trend(capital_flow_df)
    scores["total"] = sum(scores.values())
    return scores


def _score_main_flow(df):
    if "main_net_inflow" not in df.columns:
        return 0

    recent = df.tail(5)
    main_inflows = recent["main_net_inflow"].values
    positive_days = np.sum(main_inflows > 0)
    total_inflow = np.sum(main_inflows)

    max_score = CAPITAL_MAX_SCORES["main_flow"]
    score = 0

    inflow_ratio = positive_days / 5
    score += max_score * 0.5 * inflow_ratio

    if total_inflow > 1e8:
        score += max_score * 0.3
    elif total_inflow > 0:
        score += max_score * 0.15

    if len(main_inflows) >= 3:
        last_3 = main_inflows[-3:]
        if np.all(last_3 > 0):
            score += max_score * 0.2

    return round(score, 1)


def _score_super_large_flow(df):
    if "super_large_net_inflow" not in df.columns:
        return 0

    recent = df.tail(5)
    super_inflows = recent["super_large_net_inflow"].values
    positive_days = np.sum(super_inflows > 0)
    total_inflow = np.sum(super_inflows)

    max_score = CAPITAL_MAX_SCORES["super_large_flow"]
    score = 0

    score += max_score * 0.4 * (positive_days / 5)

    if total_inflow > 5e7:
        score += max_score * 0.35
    elif total_inflow > 0:
        score += max_score * 0.2

    if "main_net_inflow" in df.columns:
        main_total = np.sum(recent["main_net_inflow"].values)
        if main_total > 0:
            ratio = total_inflow / main_total if main_total != 0 else 0
            if ratio > 0.5:
                score += max_score * 0.25

    return round(score, 1)


def _score_north_flow(df):
    return 0.0


def _score_flow_trend(df):
    if "main_net_inflow" not in df.columns or len(df) < 10:
        return 0

    recent_5 = df.tail(5)["main_net_inflow"].values
    prev_5 = df.tail(10).head(5)["main_net_inflow"].values

    recent_avg = np.mean(recent_5)
    prev_avg = np.mean(prev_5)

    max_score = CAPITAL_MAX_SCORES["flow_trend"]
    score = 0

    if prev_avg < 0 and recent_avg > 0:
        score += max_score * 0.7
    elif recent_avg > prev_avg and recent_avg > 0:
        score += max_score * 0.5
    elif recent_avg > prev_avg:
        score += max_score * 0.3

    if len(recent_5) >= 3:
        last_3 = recent_5[-3:]
        first_3 = recent_5[:3]
        if np.mean(last_3) > np.mean(first_3):
            score += max_score * 0.3

    return round(score, 1)
