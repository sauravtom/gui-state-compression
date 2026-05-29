from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path

from src.eval.run_experiment import load_config, run_experiment


def main() -> None:
    parser = argparse.ArgumentParser(description="Run keyframe, compression, and history ablations.")
    parser.add_argument("--config", default="experiments/configs/default.yaml")
    parser.add_argument("--output-dir", default="experiments/ablation")
    args = parser.parse_args()

    base = load_config(args.config)
    configs = []

    keyframe = deepcopy(base)
    keyframe["output_dir"] = str(Path(args.output_dir) / "keyframe")
    keyframe["modes"] = ["hybrid"]
    keyframe["keyframe_interval"] = [1, 2, 4, 8, 16]
    keyframe["history_compression"] = ["state_summary"]
    configs.append(keyframe)

    compression = deepcopy(base)
    compression["output_dir"] = str(Path(args.output_dir) / "compression_type")
    compression["modes"] = ["full_context", "pixel_delta", "semantic_delta", "hybrid"]
    compression["keyframe_interval"] = [4]
    compression["history_compression"] = ["state_summary"]
    configs.append(compression)

    history = deepcopy(base)
    history["output_dir"] = str(Path(args.output_dir) / "history")
    history["modes"] = ["hybrid"]
    history["keyframe_interval"] = [4]
    history["history_compression"] = ["none", "summary", "action_only", "state_summary"]
    configs.append(history)

    for config in configs:
        run_experiment(config)
        print(f"wrote ablation results to {config['output_dir']}")


if __name__ == "__main__":
    main()
