from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from src.agents.compressed_agent import make_agent
from src.eval.custom_benchmark import load_custom_benchmark
from src.eval.metrics import aggregate_results, write_summary, write_task_results
from src.utils.logging import JSONLLogger
from src.utils.types import TaskResult


def load_config(path: str | Path) -> Dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        text = handle.read()
    try:
        import yaml

        return yaml.safe_load(text)
    except Exception:
        return json.loads(text)


def run_experiment(config: Dict[str, Any]) -> List[TaskResult]:
    output_dir = Path(config.get("output_dir", "experiments"))
    results_dir = output_dir / "results"
    log_dir = output_dir / "logs"
    results_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "steps.jsonl"
    if log_path.exists():
        log_path.unlink()
    logger = JSONLLogger(log_path)

    benchmark_cfg = config.get("benchmark", {})
    tasks_per_type = int(benchmark_cfg.get("tasks_per_type", 5))
    tasks = load_custom_benchmark(output_dir, tasks_per_type=tasks_per_type)
    task_limit = benchmark_cfg.get("task_limit")
    if task_limit:
        tasks = tasks[: int(task_limit)]

    model_cfg = config.get("model_pricing", {})
    modes = config.get("modes", ["full_context", "pixel_delta", "semantic_delta", "hybrid"])
    keyframe_intervals = config.get("keyframe_interval", [1, 2, 4, 8])
    history_modes = config.get("history_compression", ["none"])
    results: List[TaskResult] = []

    for mode in modes:
        intervals = keyframe_intervals if mode in {"pixel_delta", "semantic_delta", "hybrid"} else [1]
        for interval in intervals:
            for history in history_modes:
                agent = make_agent(
                    mode=mode,
                    keyframe_interval=int(interval),
                    history_compression=history,
                    model=config.get("model", "gpt-5.5"),
                    max_steps=int(config.get("max_steps", 30)),
                    input_cost_per_1m=float(model_cfg.get("input_per_1m", 1.25)),
                    output_cost_per_1m=float(model_cfg.get("output_per_1m", 10.0)),
                    seed=int(config.get("seed", 13)),
                )
                for task in tasks:
                    result, step_records = agent.run_task(task)
                    results.append(result)
                    for record in step_records:
                        logger.write(record.__dict__)

    task_results_path = results_dir / config.get("task_results_csv", "benchmark_results.csv")
    summary_path = results_dir / config.get("summary_csv", "summary.csv")
    write_task_results(task_results_path, results)
    summary = aggregate_results(results)
    write_summary(summary_path, summary)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Run GUI state compression experiments.")
    parser.add_argument("--config", default="experiments/configs/default.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    results = run_experiment(config)
    summary = aggregate_results(results)
    print(f"completed {len(results)} task-method runs")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
