from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="OSWorld adapter placeholder.")
    parser.add_argument("--config", default="experiments/configs/default.yaml")
    parser.parse_args()
    raise SystemExit(
        "OSWorld adapter is intentionally a thin stub in the workshop prototype. "
        "Install OSWorld and wrap its desktop observations as GUIObservation records."
    )


if __name__ == "__main__":
    main()
