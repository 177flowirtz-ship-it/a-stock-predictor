from config.settings import SENTIMENT_MAX_SCORES


def score_sentiment(sentiment_data):
    if sentiment_data is None:
        return {"news_heat": 0, "guba_activity": 0, "total": 0}

    news_heat = sentiment_data.get("news_heat_score", 0)
    guba_activity = sentiment_data.get("guba_activity_score", 0)

    scores = {}
    scores["news_heat"] = _score_news_heat(news_heat)
    scores["guba_activity"] = _score_guba_activity(guba_activity)
    scores["total"] = sum(scores.values())
    return scores


def _score_news_heat(raw_score):
    max_score = SENTIMENT_MAX_SCORES["news_heat"]
    normalized = min(raw_score / 8.0, 1.0)
    return round(normalized * max_score, 1)


def _score_guba_activity(raw_score):
    max_score = SENTIMENT_MAX_SCORES["guba_activity"]
    normalized = min(raw_score / 7.0, 1.0)
    if raw_score > 6.5:
        normalized = 0.6
    return round(normalized * max_score, 1)
