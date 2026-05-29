from config.settings import FUNDAMENTAL_MAX_SCORES


def score_fundamental(fundamental_data):
    if fundamental_data is None:
        return {
            "pe_percentile": 0,
            "pb_percentile": 0,
            "roe": 0,
            "revenue_growth": 0,
            "total": 0,
        }

    scores = {}
    scores["pe_percentile"] = _score_pe(fundamental_data.get("pe"))
    scores["pb_percentile"] = _score_pb(fundamental_data.get("pb"))
    scores["roe"] = _score_roe(fundamental_data.get("roe"))
    scores["revenue_growth"] = _score_revenue_growth(fundamental_data.get("revenue_growth"))
    scores["total"] = sum(scores.values())
    return scores


def _score_pe(pe):
    if pe is None:
        return 0

    max_score = FUNDAMENTAL_MAX_SCORES["pe_percentile"]
    score = 0

    try:
        pe = float(pe)
        if pe <= 0:
            return 0
        if 0 < pe <= 15:
            score = max_score * 1.0
        elif 15 < pe <= 25:
            score = max_score * 0.8
        elif 25 < pe <= 40:
            score = max_score * 0.5
        elif 40 < pe <= 60:
            score = max_score * 0.3
        else:
            score = max_score * 0.1
    except (ValueError, TypeError):
        return 0

    return round(score, 1)


def _score_pb(pb):
    if pb is None:
        return 0

    max_score = FUNDAMENTAL_MAX_SCORES["pb_percentile"]
    score = 0

    try:
        pb = float(pb)
        if pb <= 0:
            return 0
        if 0 < pb <= 1.0:
            score = max_score * 1.0
        elif 1.0 < pb <= 2.0:
            score = max_score * 0.8
        elif 2.0 < pb <= 4.0:
            score = max_score * 0.5
        elif 4.0 < pb <= 8.0:
            score = max_score * 0.3
        else:
            score = max_score * 0.1
    except (ValueError, TypeError):
        return 0

    return round(score, 1)


def _score_roe(roe):
    if roe is None:
        return 0

    max_score = FUNDAMENTAL_MAX_SCORES["roe"]
    score = 0

    try:
        roe = float(roe)
        if roe >= 20:
            score = max_score
        elif roe >= 15:
            score = max_score * 0.8
        elif roe >= 10:
            score = max_score * 0.5
        elif roe >= 5:
            score = max_score * 0.3
        elif roe > 0:
            score = max_score * 0.1
    except (ValueError, TypeError):
        return 0

    return round(score, 1)


def _score_revenue_growth(growth):
    if growth is None:
        return 0

    max_score = FUNDAMENTAL_MAX_SCORES["revenue_growth"]
    score = 0

    try:
        growth = float(growth)
        if growth >= 30:
            score = max_score
        elif growth >= 20:
            score = max_score * 0.8
        elif growth >= 10:
            score = max_score * 0.5
        elif growth >= 0:
            score = max_score * 0.3
        elif growth >= -10:
            score = max_score * 0.1
    except (ValueError, TypeError):
        return 0

    return round(score, 1)
