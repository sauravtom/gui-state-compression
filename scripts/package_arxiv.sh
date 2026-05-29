#!/usr/bin/env bash
set -euo pipefail

ROOT="$(pwd)"
OUT_DIR="$ROOT/dist/arxiv/gui-state-compression"
ARCHIVE="$ROOT/dist/arxiv/gui-state-compression-arxiv.tar.gz"

rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR/figures"

cp paper/main.tex "$OUT_DIR/main.tex"
cp paper/references.bib "$OUT_DIR/references.bib"
cp paper/figures/*.png "$OUT_DIR/figures/"
cp paper/figures/results_table.tex "$OUT_DIR/figures/results_table.tex"

cat > "$OUT_DIR/README.txt" <<'EOF'
arXiv source package for:
GUI State Compression for Computer-Use Agents Using Keyframes and Delta Encoding

Top-level TeX file:
main.tex

Expected compiler:
PDFLaTeX

The code and benchmark artifacts are available at:
https://github.com/sauravtom/gui-state-compression
EOF

# Build a flat source archive. COPYFILE_DISABLE prevents macOS AppleDouble
# metadata entries (._*) from entering the tarball.
(cd "$OUT_DIR" && COPYFILE_DISABLE=1 tar -czf "$ARCHIVE" main.tex references.bib README.txt figures)
echo "Wrote $ARCHIVE"
