from __future__ import annotations

import argparse
from pathlib import Path
from .config import available_scenarios, default_config
from .simulation import simulate_plant
from .metrics import summarize_and_save
from .plotting import plot_results
from .io_utils import save_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Hospital wastewater treatment train simulator")
    sub = parser.add_subparsers(dest="command", required=True)

    sim = sub.add_parser("simulate", help="Run one simulation")
    sim.add_argument("--scenario", choices=available_scenarios(), default="nominal")
    sim.add_argument("--influent-mode", choices=["hospital", "sinusoidal"], default="hospital")
    sim.add_argument("--duration-h", type=float, default=96.0)
    sim.add_argument("--dt-minutes", type=float, default=5.0)
    sim.add_argument("--flow-m3-day", type=float, default=500.0)
    sim.add_argument("--seed", type=int, default=42)
    sim.add_argument("--noise-sigma", type=float, default=0.05)
    sim.add_argument("--shock-hour", type=float, default=36.0)
    sim.add_argument("--shock-width-h", type=float, default=1.2)
    sim.add_argument("--shock-multiplier", type=float, default=2.2)
    sim.add_argument("--oxidation-scale", type=float, default=1.0)
    sim.add_argument("--adsorption-scale", type=float, default=1.0)
    sim.add_argument("--inhibition-scale", type=float, default=1.0)
    sim.add_argument("--V-EQ-m3", type=float, default=None)
    sim.add_argument("--V-MBR-m3", type=float, default=None)
    sim.add_argument("--V-AOP-m3", type=float, default=None)
    sim.add_argument("--V-GAC-bed-m3", type=float, default=None)
    sim.add_argument("--output-dir", default="outputs")
    sim.add_argument("--no-plots", action="store_true")

    batch = sub.add_parser("batch", help="Run low/nominal/high/shock scenarios")
    batch.add_argument("--duration-h", type=float, default=96.0)
    batch.add_argument("--dt-minutes", type=float, default=5.0)
    batch.add_argument("--output-dir", default="outputs/batch")
    batch.add_argument("--seed", type=int, default=42)
    batch.add_argument("--no-plots", action="store_true")
    return parser


def _run_one(args: argparse.Namespace, scenario: str | None = None, outdir: str | None = None) -> None:
    cfg = default_config(scenario or args.scenario)
    cfg.influent_mode = args.influent_mode if hasattr(args, "influent_mode") else "hospital"
    cfg.duration_h = args.duration_h
    cfg.dt_minutes = args.dt_minutes
    cfg.flow_m3_per_day = getattr(args, "flow_m3_day", cfg.flow_m3_per_day)
    cfg.seed = getattr(args, "seed", cfg.seed)
    cfg.noise_sigma = getattr(args, "noise_sigma", cfg.noise_sigma)
    cfg.shock_hour = getattr(args, "shock_hour", cfg.shock_hour)
    cfg.shock_width_h = getattr(args, "shock_width_h", cfg.shock_width_h)
    cfg.shock_multiplier = getattr(args, "shock_multiplier", cfg.shock_multiplier)
    cfg.oxidation_scale = getattr(args, "oxidation_scale", cfg.oxidation_scale)
    cfg.adsorption_scale = getattr(args, "adsorption_scale", cfg.adsorption_scale)
    cfg.inhibition_scale = getattr(args, "inhibition_scale", cfg.inhibition_scale)
    for attr, argname in [("V_EQ_m3", "V_EQ_m3"), ("V_MBR_m3", "V_MBR_m3"), ("V_AOP_m3", "V_AOP_m3"), ("V_GAC_bed_m3", "V_GAC_bed_m3")]:
        value = getattr(args, argname, None)
        if value is not None:
            setattr(cfg, attr, value)
    results = simulate_plant(cfg)
    output_dir = Path(outdir or args.output_dir)
    summaries = summarize_and_save(results, output_dir)
    save_config(cfg, output_dir)
    if not getattr(args, "no_plots", False):
        plot_results(results, summaries, output_dir)
    print(f"Saved outputs to: {output_dir}")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "simulate":
        _run_one(args)
    else:
        for scenario in available_scenarios():
            scenario_dir = Path(args.output_dir) / scenario
            _run_one(args, scenario=scenario, outdir=str(scenario_dir))


if __name__ == "__main__":
    main()
