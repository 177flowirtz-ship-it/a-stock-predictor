from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from config.settings import OUTPUT_TOP_N


def generate_report(results, elapsed_seconds):
    console = Console()
    today = datetime.now().strftime("%Y-%m-%d")
    weekday = ["一", "二", "三", "四", "五", "六", "日"][datetime.now().weekday()]

    header = Text()
    header.append(" A股短期涨跌预测报告", style="bold cyan")
    header.append(f" — {today} (周{weekday})\n")
    header.append(f"                    数据截止: 15:00 收盘", style="dim")

    console.print(Panel(header, border_style="cyan", padding=(1, 2)))

    total = len(results)
    bullish_count = len([r for r in results if r["score"]["total_score"] >= 55])
    bearish_count = len([r for r in results if r["score"]["total_score"] < 55])
    console.print(
        f"[dim]━━━ 市场概况 ━━━[/dim]\n"
        f"分析股票总数: {total} | 耗时: {elapsed_seconds:.1f}s | "
        f"看涨: {bullish_count} | 看跌: {bearish_count}"
    )

    sorted_results = sorted(results, key=lambda x: x["score"]["total_score"], reverse=True)

    _print_all_results(console, sorted_results)

    console.print(
        Panel(
            "[yellow]⚠ 本报告仅基于量化模型和历史数据，不构成任何投资建议。\n"
            "   股市有风险，投资需谨慎。[/yellow]",
            border_style="red",
            title="风险提示",
        )
    )


def _print_all_results(console, results):
    display = results[:OUTPUT_TOP_N]
    if not display:
        console.print("\n  [dim]暂无数据[/dim]")
        return

    console.print(f"\n[bold cyan]━━━ Top {OUTPUT_TOP_N} 综合分析排行 ━━━[/bold cyan]")

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("排名", style="dim", width=5)
    table.add_column("代码", style="cyan", width=8)
    table.add_column("名称", style="white", width=10)
    table.add_column("技术", justify="right", width=6)
    table.add_column("资金", justify="right", width=6)
    table.add_column("情绪", justify="right", width=6)
    table.add_column("基本", justify="right", width=6)
    table.add_column("总分", justify="right", width=6, style="bold yellow")
    table.add_column("评级", width=12)

    for idx, r in enumerate(display, 1):
        s = r["score"]
        color = "green" if s["total_score"] >= 55 else "red"
        table.add_row(
            str(idx),
            r["code"],
            r["name"],
            str(s["technical"]["total"]),
            str(s["capital"]["total"]),
            str(s["sentiment"]["total"]),
            str(s["fundamental"]["total"]),
            f"[{color}]{s['total_score']}[/{color}]",
            f"[{color}]{s['stars']} {s['rating']}[/{color}]",
        )

    console.print(table)
