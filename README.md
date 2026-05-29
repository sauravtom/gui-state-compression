# GUI State Compression for Computer-Use Agents

Research prototype for testing whether computer-use agents can use periodic GUI keyframes plus compact deltas instead of sending full screenshots, DOM trees, accessibility trees, and action history at every step.

Core hypothesis:

```text
GUI(t) = Keyframe(t-k) + DeltaUI(t-k+1 ... t)
```

This repository is intentionally scoped as a workshop-paper prototype. The default evaluation uses a deterministic 40-task custom mini benchmark so the full pipeline runs without external WebArena, VisualWebArena, OSWorld, browser, or model API setup.

## What Is Implemented

- Full-context baseline prompts.
- Screenshot keyframe plus pixel-delta prompts.
- Semantic GUI deltas from DOM, OCR-like text, and accessibility-like trees.
- Hybrid keyframe + semantic delta + compressed history prompts.
- Token, latency, model-call, cost, compression-ratio, error, and recovery metrics.
- A 40-task mini benchmark covering form filling, search, file navigation, settings, checkout, email, dashboard filtering, and document editing.
- Ablation runner for keyframe interval, compression type, and history compression.
- Plot generation and a LaTeX workshop-paper draft.

The default runner uses a deterministic simulated decision policy. It does not call a model API unless you extend the agent adapter. This keeps the prototype reproducible and makes prompt/token/compression accounting easy to inspect.

Project page: <https://sauravtom.github.io/gui-state-compression/>

Paper draft: [`paper/main.pdf`](paper/main.pdf)

License: MIT

## Setup

```bash
cd gui-state-compression
./scripts/setup.sh
source .venv/bin/activate
```

## Run The Custom Benchmark

```bash
python -m src.eval.run_experiment --config experiments/configs/default.yaml
```

Outputs:

```text
experiments/results/benchmark_results.csv
experiments/results/summary.csv
experiments/logs/steps.jsonl
experiments/logs/screenshots/
```

Current default results on the synthetic 40-task benchmark:

```text
Method        Success   Avg input tokens   Latency/step   Compression
full_context  100.0%    6061.8             329.7 ms       1.00x
hybrid K=4     90.0%    2877.2             253.5 ms       1.92x
pixel K=4      75.0%    2411.6             246.8 ms       2.08x
semantic K=4   87.5%    2699.9             249.8 ms       1.99x
```

## Run Ablations

```bash
python -m src.eval.ablation --config experiments/configs/default.yaml --output-dir experiments/ablation
```

This creates separate result folders for:

- keyframe interval ablation: `K = 1, 2, 4, 8, 16`
- compression type ablation: full context, pixel delta, semantic delta, hybrid
- history compression ablation: none, summary, action-only, state-summary

## Regenerate Figures

```bash
python -m src.visualization.make_figures \
  --summary-csv experiments/results/summary.csv \
  --task-csv experiments/results/benchmark_results.csv \
  --output-dir paper/figures
```

Figures:

```text
paper/figures/tokens_success_by_method.png
paper/figures/success_vs_compression_ratio.png
paper/figures/latency_by_method.png
paper/figures/failure_categories.png
paper/figures/results_table.tex
```

## Compile The Paper

```bash
./scripts/generate_paper_assets.sh
```

The script regenerates figures and compiles `paper/main.tex` when `latexmk` or `pdflatex` is installed.

## Example Compressed Prompt

```text
You are controlling a computer. You have a previous keyframe and the following GUI deltas.
Reconstruct the current state mentally and choose the next action as strict JSON.
{
  "instruction": "Apply coupon PAPER10 to the Notebook cart and pay.",
  "previous_keyframe": {"step_id": 0, "screenshot_path": "...", "url": "..."},
  "deltas_since_keyframe": [
    {
      "last_keyframe_id": "kf_0000",
      "screen_summary": "GUI state step 3: Checkout; Notebook; Total $37.00",
      "new_elements": ["Pay Now", "Total $37.00"],
      "removed_elements": ["Apply coupon", "Total $42.00"],
      "changed_elements": [{"element": "Coupon", "old": null, "new": "PAPER10"}],
      "available_actions": ["click Pay Now"]
    }
  ],
  "compressed_history": "Completed 3 actions. Last action was wait on Applying coupon."
}
```

## Example Delta Output

```json
{
  "last_keyframe_id": "kf_0000",
  "changed_regions": [
    {
      "bbox": [54, 58, 511, 70],
      "change_type": "layout_shift",
      "description": "Pixels changed between consecutive GUI observations."
    }
  ],
  "screen_summary": "GUI state step 3 at http://localhost:3000/checkout_flow/checkout_001?step=3: Checkout; Notebook; Pay Now; Total $37.00",
  "new_elements": ["Checkout", "Pay Now", "Total $37.00"],
  "removed_elements": ["Applying coupon", "Please wait."],
  "changed_elements": [],
  "focused_element": null,
  "available_actions": ["click Pay Now"]
}
```

## Extending To Real Benchmarks

The WebArena and OSWorld entrypoints are intentionally thin stubs:

```bash
python -m src.eval.run_webarena --config experiments/configs/default.yaml
python -m src.eval.run_osworld --config experiments/configs/default.yaml
```

To make them live, map benchmark observations into `GUIObservation`:

```python
GUIObservation(
    step_id=step,
    screenshot_path=screenshot_path,
    dom_tree=dom_tree,
    accessibility_tree=accessibility_tree,
    ocr_text=ocr_text,
    url=current_url,
    focused_element=focused_element,
)
```

Then reuse `DeltaEncoder`, prompt builders, and the metrics writer.

## Future Work

- Replace the deterministic simulated decision policy with real model calls.
- Add WebArena and VisualWebArena subsets with execution-based success checks.
- Add OSWorld small tasks once desktop environment setup is available.
- Learn semantic delta salience from failure traces instead of using deterministic rules.
- Add adaptive keyframe scheduling based on uncertainty and UI-change magnitude.

## Citation

```bibtex
@misc{tom2026guistatecompression,
  title = {GUI State Compression for Computer-Use Agents Using Keyframes and Delta Encoding},
  author = {Tomar, Saurav},
  year = {2026},
  url = {https://github.com/sauravtom/gui-state-compression},
  note = {Workshop prototype preprint and code release}
}
```
