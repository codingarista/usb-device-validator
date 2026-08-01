"""Aggregate analysis over test history: pass rate, failure rate by test type."""

import matplotlib.pyplot as plt
import pandas as pd

HISTORY_FILE = "logs/test_history.csv"


def load_history() -> pd.DataFrame:
    """Load the test history CSV into a DataFrame."""
    return pd.read_csv(HISTORY_FILE)


def overall_pass_rate(df: pd.DataFrame) -> float:
    """Overall pass rate across all logged tests (0.0 - 1.0)."""
    return df["pass_fail"].mean()


def failure_rate_by_test_type(df: pd.DataFrame) -> pd.Series:
    """Failure rate grouped by test_type, sorted worst-first."""
    failure_rate = 1 - df.groupby("test_type")["pass_fail"].mean()
    return failure_rate.sort_values(ascending=False)


def test_counts_by_type(df: pd.DataFrame) -> pd.Series:
    """How many times each test_type was run (useful context alongside failure rate)."""
    return df["test_type"].value_counts()


def plot_failure_rate_by_type(df: pd.DataFrame, save_path: str = "logs/failure_rate_by_type.png") -> None:
    """Bar chart of failure rate by test_type, saved as PNG."""
    failure_rate = failure_rate_by_test_type(df)
    counts = test_counts_by_type(df)

    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(failure_rate.index, failure_rate.values * 100, color="#d9534f")

    ax.set_ylabel("Failure Rate (%)")
    ax.set_xlabel("Test Type")
    ax.set_title("Failure Rate by Test Type")
    ax.set_ylim(0, 100)

    # Annotate each bar with the failure rate and sample count (n=...)
    for bar, test_type in zip(bars, failure_rate.index):
        height = bar.get_height()
        n = counts[test_type]
        ax.annotate(
            f"{height:.1f}%\n(n={n})",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 5),
            textcoords="offset points",
            ha="center",
        )

    plt.tight_layout()
    plt.savefig(save_path)
    print(f"圖表已儲存: {save_path}")
    plt.close(fig)


def print_summary() -> None:
    """Quick CLI summary for manual checking."""
    df = load_history()

    print(f"總測試筆數: {len(df)}")
    print(f"整體PASS率: {overall_pass_rate(df):.1%}\n")

    print("各測試項目失敗率:")
    print(failure_rate_by_test_type(df).apply(lambda x: f"{x:.1%}"))

    print("\n各測試項目執行次數:")
    print(test_counts_by_type(df))

    plot_failure_rate_by_type(df)


if __name__ == "__main__":
    print_summary()

def generate_aggregate_report(df: pd.DataFrame, save_path: str = "logs/aggregate_report.html") -> None:
    """Generate a standalone HTML report summarizing test history, separate from the single-run report."""
    plot_failure_rate_by_type(df)  # ensures the PNG is up to date

    total_tests = len(df)
    pass_rate = overall_pass_rate(df)
    failure_rate = failure_rate_by_test_type(df)
    counts = test_counts_by_type(df)

    rows_html = "".join(
        f"<tr><td>{test_type}</td><td>{counts[test_type]}</td><td>{rate:.1%}</td></tr>"
        for test_type, rate in failure_rate.items()
    )

    html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>USB Device Validator - Aggregate Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            table {{ border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ccc; padding: 8px 16px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            img {{ margin-top: 20px; max-width: 600px; }}
        </style>
    </head>
    <body>
        <h1>USB Device Validator - Aggregate Report</h1>
        <p>總測試筆數: {total_tests}</p>
        <p>整體PASS率: {pass_rate:.1%}</p>

        <h2>各測試項目失敗率</h2>
        <table>
            <tr><th>Test Type</th><th>Sample Count</th><th>Failure Rate</th></tr>
            {rows_html}
        </table>

        <img src="failure_rate_by_type.png" alt="Failure Rate by Test Type">
    </body>
    </html>
    """

    with open(save_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"彙總報告已儲存: {save_path}")


def print_summary() -> None:
    """Quick CLI summary for manual checking."""
    df = load_history()

    print(f"總測試筆數: {len(df)}")
    print(f"整體PASS率: {overall_pass_rate(df):.1%}\n")

    print("各測試項目失敗率:")
    print(failure_rate_by_test_type(df).apply(lambda x: f"{x:.1%}"))

    print("\n各測試項目執行次數:")
    print(test_counts_by_type(df))

    generate_aggregate_report(df)


if __name__ == "__main__":
    print_summary()