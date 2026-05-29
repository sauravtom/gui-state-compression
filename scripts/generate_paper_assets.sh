#!/usr/bin/env bash
set -euo pipefail

if [ -x .venv/bin/python ]; then
  PYTHON_BIN="${PYTHON:-.venv/bin/python}"
else
  PYTHON_BIN="${PYTHON:-python3}"
fi

"$PYTHON_BIN" -m src.visualization.make_figures \
  --summary-csv experiments/results/summary.csv \
  --task-csv experiments/results/benchmark_results.csv \
  --output-dir paper/figures

if command -v latexmk >/dev/null 2>&1; then
  latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=paper paper/main.tex
elif command -v pdflatex >/dev/null 2>&1; then
  (cd paper && pdflatex -interaction=nonstopmode -halt-on-error main.tex)
  (cd paper && bibtex main || true)
  (cd paper && pdflatex -interaction=nonstopmode -halt-on-error main.tex)
  (cd paper && pdflatex -interaction=nonstopmode -halt-on-error main.tex)
else
  echo "No LaTeX engine found. Rendering fallback PDF from paper/main.tex."
  "$PYTHON_BIN" -m src.visualization.render_paper_pdf \
    --tex paper/main.tex \
    --output paper/main.pdf \
    --figure-dir paper/figures
fi
