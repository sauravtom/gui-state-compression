from __future__ import annotations

import argparse
import html
from pathlib import Path
from typing import Iterable

from src.eval.custom_benchmark import load_custom_benchmark


def render_task(task_id: str, output_path: str | Path, output_root: str | Path = "experiments") -> None:
    tasks = load_custom_benchmark(output_root)
    matches = [task for task in tasks if task.task_id == task_id]
    if not matches:
        raise ValueError(f"unknown task_id: {task_id}")
    task = matches[0]
    cards = []
    for obs, action in zip(task.trajectory, task.ideal_actions):
        cards.append(
            f"""
            <section class="step">
              <h2>Step {obs.step_id}</h2>
              <p><strong>URL:</strong> {html.escape(obs.url or '')}</p>
              <p><strong>Next action:</strong> {html.escape(str(action.to_dict()))}</p>
              <pre>{html.escape(obs.ocr_text or '')}</pre>
              <img src="{html.escape(obs.screenshot_path or '')}" alt="step {obs.step_id}">
            </section>
            """
        )
    page = f"""
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>{html.escape(task.task_id)} trajectory</title>
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 32px; color: #1f2937; }}
        .step {{ border: 1px solid #d1d5db; border-radius: 8px; padding: 16px; margin-bottom: 18px; }}
        img {{ max-width: 520px; border: 1px solid #e5e7eb; display: block; margin-top: 12px; }}
        pre {{ background: #f8fafc; padding: 12px; white-space: pre-wrap; }}
      </style>
    </head>
    <body>
      <h1>{html.escape(task.task_id)}</h1>
      <p>{html.escape(task.instruction)}</p>
      {''.join(cards)}
    </body>
    </html>
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(page, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Render one synthetic GUI trajectory as HTML.")
    parser.add_argument("--task-id", default="checkout_001")
    parser.add_argument("--output", default="experiments/results/sample_trajectory.html")
    args = parser.parse_args()
    render_task(args.task_id, args.output)
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
