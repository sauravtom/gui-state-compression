from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List

from src.utils.types import TaskResult


SUMMARY_FIELDS = [
    "method",
    "keyframe_interval",
    "history_compression",
    "tasks",
    "success_rate",
    "avg_steps",
    "avg_input_tokens",
    "avg_output_tokens",
    "avg_model_calls",
    "avg_latency_ms",
    "avg_end_to_end_ms",
    "avg_cost_usd",
    "compression_ratio",
    "agent_error_rate",
    "recovery_rate",
]


def write_task_results(path: str | Path, results: Iterable[TaskResult]) -> None:
    rows = [result.to_dict() for result in results]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def aggregate_results(results: Iterable[TaskResult]) -> List[Dict[str, object]]:
    groups: Dict[tuple, List[TaskResult]] = defaultdict(list)
    for result in results:
        groups[(result.mode, result.keyframe_interval, result.history_compression)].append(result)

    rows: List[Dict[str, object]] = []
    for (mode, keyframe_interval, history_compression), group in sorted(groups.items()):
        tasks = len(group)
        total_errors = sum(item.agent_errors for item in group)
        total_recovered = sum(item.recovered_errors for item in group)
        total_steps = sum(item.steps for item in group)
        rows.append(
            {
                "method": mode,
                "keyframe_interval": keyframe_interval,
                "history_compression": history_compression,
                "tasks": tasks,
                "success_rate": sum(1 for item in group if item.success) / tasks,
                "avg_steps": total_steps / tasks,
                "avg_input_tokens": sum(item.total_input_tokens for item in group) / tasks,
                "avg_output_tokens": sum(item.total_output_tokens for item in group) / tasks,
                "avg_model_calls": sum(item.model_calls for item in group) / tasks,
                "avg_latency_ms": sum(item.avg_latency_ms for item in group) / tasks,
                "avg_end_to_end_ms": sum(item.end_to_end_time_ms for item in group) / tasks,
                "avg_cost_usd": sum(item.estimated_cost_usd for item in group) / tasks,
                "compression_ratio": sum(item.compression_ratio for item in group) / tasks,
                "agent_error_rate": total_errors / max(1, total_steps),
                "recovery_rate": total_recovered / max(1, total_errors),
            }
        )
    return rows


def write_summary(path: str | Path, rows: Iterable[Dict[str, object]]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
