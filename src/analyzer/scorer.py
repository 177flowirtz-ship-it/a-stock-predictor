from config.settings import WEIGHTS, RATING_THRESHOLDS


def compute_final_score(tech_score, cap_score, sent_score, fund_score):
    available_weights = {}
    weighted = 0

    if tech_score is not None and tech_score["total"] > 0:
        available_weights["technical"] = WEIGHTS["technical"]
        weighted += tech_score["total"] * WEIGHTS["technical"]

    if cap_score is not None and cap_score["total"] > 0:
        available_weights["capital"] = WEIGHTS["capital"]
        weighted += cap_score["total"] * WEIGHTS["capital"]

    if sent_score is not None and sent_score["total"] > 0:
        available_weights["sentiment"] = WEIGHTS["sentiment"]
        weighted += sent_score["total"] * WEIGHTS["sentiment"]

    if fund_score is not None and fund_score["total"] > 0:
        available_weights["fundamental"] = WEIGHTS["fundamental"]
        weighted += fund_score["total"] * WEIGHTS["fundamental"]

    weight_sum = sum(available_weights.values()) if available_weights else 1.0

    max_weighted = 0
    if "technical" in available_weights:
        max_weighted += 40 * available_weights["technical"]
    if "capital" in available_weights:
        max_weighted += 30 * available_weights["capital"]
    if "sentiment" in available_weights:
        max_weighted += 15 * available_weights["sentiment"]
    if "fundamental" in available_weights:
        max_weighted += 15 * available_weights["fundamental"]

    normalized = (weighted / max_weighted) * 100 if max_weighted > 0 else 0
    normalized = min(normalized, 100)

    return {
        "total_score": round(normalized, 1),
        "technical": tech_score,
        "capital": cap_score if cap_score else {"total": 0},
        "sentiment": sent_score if sent_score else {"total": 0},
        "fundamental": fund_score if fund_score else {"total": 0},
        "rating": _get_rating(normalized),
        "stars": _get_stars(normalized),
    }


def _get_rating(score):
    for threshold, stars, label in RATING_THRESHOLDS:
        if score >= threshold:
            return label
    return "强烈看跌"


def _get_stars(score):
    for threshold, stars, label in RATING_THRESHOLDS:
        if score >= threshold:
            return stars
    return "★☆☆☆☆"
