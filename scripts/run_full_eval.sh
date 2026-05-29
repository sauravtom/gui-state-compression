#!/usr/bin/env bash
set -euo pipefail

if [ -x .venv/bin/python ]; then
  PYTHON_BIN="${PYTHON:-.venv/bin/python}"
else
  PYTHON_BIN="${PYTHON:-python3}"
fi

"$PYTHON_BIN" -m src.eval.run_experiment --config experiments/configs/default.yaml
"$PYTHON_BIN" -m src.eval.ablation --config experiments/configs/default.yaml --output-dir experiments/ablation
