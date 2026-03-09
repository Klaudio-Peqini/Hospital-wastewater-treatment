from __future__ import annotations

import argparse
from pathlib import Path
from hospital_wwtp.config import default_config
from hospital_wwtp.simulation import simulate_plant
from hospital_wwtp.metrics import summarize_and_save
from hospital_wwtp.plotting import plot_results
from hospital_wwtp.io_utils import save_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the default hospital wastewater example")
    parser.add_argument("--scenario", choices=["low", "nominal", "high", "shock"], default="nominal")
    parser.add_argument("--output-dir", default="outputs")
    args = parser.parse_args()

    cfg = default_config(args.scenario)
    results = simulate_plant(cfg)
    summaries = summarize_and_save(results, args.output_dir)
    plot_results(results, summaries, args.output_dir)
    save_config(cfg, args.output_dir)
    print(f"Example finished. Outputs written to {Path(args.output_dir).resolve()}")


if __name__ == "__main__":
    main()
