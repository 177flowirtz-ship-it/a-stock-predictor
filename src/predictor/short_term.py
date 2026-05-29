from src.analyzer.scorer import WEIGHTS, RATING_THRESHOLDS


def predict(stock_result):
    score = stock_result.get("score", {}).get("total_score", 0)

    if score >= 85:
        probability = "高 (>70%)"
    elif score >= 70:
        probability = "中高 (55-70%)"
    elif score >= 55:
        probability = "中等 (45-55%)"
    elif score >= 40:
        probability = "中低 (30-45%)"
    elif score >= 25:
        probability = "低 (15-30%)"
    else:
        probability = "极低 (<15%)"

    return {
        "probability": probability,
        "direction": "看涨" if score >= 55 else "看跌",
        "confidence": score,
    }
