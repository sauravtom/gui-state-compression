#!/usr/bin/env bash
set -euo pipefail

if [ -x .venv/bin/python ]; then
  PYTHON_BIN="${PYTHON:-.venv/bin/python}"
else
  PYTHON_BIN="${PYTHON:-python3}"
fi

"$PYTHON_BIN" -m src.eval.run_experiment --config experiments/configs/default.yaml
"$PYTHON_BIN" -m src.visualization.make_figures \
  --summary-csv experiments/results/summary.csv \
  --task-csv experiments/results/benchmark_results.csv \
  --output-dir paper/figures
"$PYTHON_BIN" -m src.visualization.render_trajectory --task-id checkout_001 --output experiments/results/sample_trajectory.html
