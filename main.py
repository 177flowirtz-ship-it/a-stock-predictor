import sys
import time
import random
from datetime import datetime
from src.crawler.stock_list import fetch_stock_list
from src.crawler.kline import fetch_kline_batch
from src.crawler.capital_flow import fetch_capital_flow
from src.crawler.sentiment import fetch_sentiment_data
from src.crawler.fundamental import fetch_fundamental_data
from src.analyzer.technical import score_technical
from src.analyzer.capital import score_capital
from src.analyzer.sentiment import score_sentiment
from src.analyzer.fundamental import score_fundamental
from src.analyzer.scorer import compute_final_score
from src.reporter.cli_report import generate_report


def main():
    sample_mode = "--full" not in sys.argv
    sample_size = 200 if sample_mode else None

    start_time = time.time()
    print("正在获取A股列表...")
    stocks = fetch_stock_list()
    print(f"获取到 {len(stocks)} 只股票")

    if sample_mode and len(stocks) > sample_size:
        random.seed(42)
        stocks = random.sample(stocks, sample_size)
        print(f"样本模式: 随机选取 {len(stocks)} 只")

    print(f"批量下载K线数据 ({len(stocks)} 只)...")
    kline_data = fetch_kline_batch(stocks)
    print(f"K线数据获取成功: {len(kline_data)} 只")

    print("开始分析...")
    results = []
    total = len(kline_data)
    fund_count = 0

    for i, (code, kline_df) in enumerate(kline_data.items()):
        stock_info = next((s for s in stocks if s["code"] == code), None)
        name = stock_info["name"] if stock_info else code
        market = stock_info["market"] if stock_info else 0

        tech_score = score_technical(kline_df)
        cap_score = score_capital(None)
        sent_score = score_sentiment(None)

        fundamental_data = None
        fund_score = score_fundamental(None)
        try:
            fundamental_data = fetch_fundamental_data(code)
            if fundamental_data and any(v is not None for v in fundamental_data.values()):
                fund_score = score_fundamental(fundamental_data)
                fund_count += 1
        except Exception:
            pass

        final_score = compute_final_score(tech_score, cap_score, sent_score, fund_score)
        results.append({
            "code": code, "name": name, "market": market, "score": final_score,
        })

        if (i + 1) % 50 == 0 or (i + 1) == total:
            elapsed = time.time() - start_time
            print(f"进度: {i+1}/{total} (有效: {len(results)}, 含基本面: {fund_count}) - 已用时 {elapsed:.1f}s")

    elapsed = time.time() - start_time
    results = sorted(results, key=lambda x: x["score"]["total_score"], reverse=True)
    generate_report(results, elapsed)

    bullish_top = [r for r in results if r["score"]["total_score"] >= 55]
    print(f"\n总结: {len(results)} 只, {len(bullish_top)} 只看涨, {fund_count} 只有基本面数据")
    print(f"全量: python main.py --full")


if __name__ == "__main__":
    main()
