from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Dict, List


def _read_csv(path: str | Path) -> List[Dict[str, str]]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _method_label(row: Dict[str, str]) -> str:
    method = row.get("method") or row.get("mode")
    k = row.get("keyframe_interval", "1")
    if method in {"pixel_delta", "semantic_delta", "hybrid"}:
        return f"{method}\nK={k}"
    return str(method)


def make_figures(summary_csv: str | Path, task_csv: str | Path, output_dir: str | Path) -> None:
    import matplotlib.pyplot as plt

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    summary = _read_csv(summary_csv)
    tasks = _read_csv(task_csv)

    labels = [_method_label(row) for row in summary]
    success = [float(row["success_rate"]) * 100.0 for row in summary]
    input_tokens = [float(row["avg_input_tokens"]) for row in summary]
    ratios = [float(row["compression_ratio"]) for row in summary]
    latency = [float(row["avg_latency_ms"]) for row in summary]

    plt.figure(figsize=(10, 4.8))
    x = range(len(summary))
    bars = plt.bar(x, input_tokens, color="#4C78A8")
    plt.ylabel("Avg input tokens per task")
    plt.xticks(x, labels, rotation=35, ha="right")
    plt.twinx()
    plt.plot(list(x), success, color="#F58518", marker="o", linewidth=2)
    plt.ylabel("Success rate (%)")
    plt.title("Token use and task success by method")
    for bar in bars:
        bar.set_alpha(0.82)
    plt.tight_layout()
    plt.savefig(output / "tokens_success_by_method.png", dpi=180)
    plt.close()

    plt.figure(figsize=(6.8, 4.8))
    plt.scatter(ratios, success, s=90, color="#54A24B")
    for row, ratio, succ in zip(summary, ratios, success):
        plt.annotate(_method_label(row).replace("\n", " "), (ratio, succ), fontsize=8, xytext=(5, 4), textcoords="offset points")
    plt.xlabel("Compression ratio vs full context")
    plt.ylabel("Success rate (%)")
    plt.title("Success versus compression")
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(output / "success_vs_compression_ratio.png", dpi=180)
    plt.close()

    plt.figure(figsize=(8, 4.8))
    plt.bar(labels, latency, color="#B279A2")
    plt.ylabel("Avg latency per step (ms)")
    plt.xticks(rotation=35, ha="right")
    plt.title("Simulated latency by method")
    plt.tight_layout()
    plt.savefig(output / "latency_by_method.png", dpi=180)
    plt.close()

    failures = Counter(row["failure_category"] for row in tasks if row.get("failure_category"))
    if failures:
        plt.figure(figsize=(8, 4.8))
        names, counts = zip(*failures.most_common())
        plt.bar(names, counts, color="#E45756")
        plt.ylabel("Failed task count")
        plt.xticks(rotation=30, ha="right")
        plt.title("Failure categories")
        plt.tight_layout()
        plt.savefig(output / "failure_categories.png", dpi=180)
        plt.close()

    with (output / "results_table.tex").open("w", encoding="utf-8") as handle:
        handle.write("\\begin{tabular}{lrrrr}\\toprule\n")
        handle.write("Method & Success & Input tok. & Latency & Ratio \\\\\n\\midrule\n")
        for row in summary:
            handle.write(
                f"{_method_label(row).replace(chr(10), ' ')} & "
                f"{float(row['success_rate']) * 100:.1f}\\% & "
                f"{float(row['avg_input_tokens']):.0f} & "
                f"{float(row['avg_latency_ms']):.0f} & "
                f"{float(row['compression_ratio']):.2f}$\\times$ \\\\\n"
            )
        handle.write("\\bottomrule\n\\end{tabular}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate experiment figures.")
    parser.add_argument("--summary-csv", default="experiments/results/summary.csv")
    parser.add_argument("--task-csv", default="experiments/results/benchmark_results.csv")
    parser.add_argument("--output-dir", default="paper/figures")
    args = parser.parse_args()
    make_figures(args.summary_csv, args.task_csv, args.output_dir)
    print(f"wrote figures to {args.output_dir}")


if __name__ == "__main__":
    main()
