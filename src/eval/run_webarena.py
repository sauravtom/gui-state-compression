from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="WebArena adapter placeholder.")
    parser.add_argument("--config", default="experiments/configs/default.yaml")
    parser.parse_args()
    raise SystemExit(
        "WebArena adapter is intentionally a thin stub in the workshop prototype. "
        "Install WebArena, expose its task runner, then map each observation into GUIObservation."
    )


if __name__ == "__main__":
    main()
