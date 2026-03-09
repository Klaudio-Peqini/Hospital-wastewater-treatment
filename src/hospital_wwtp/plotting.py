from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable
import matplotlib.pyplot as plt
import pandas as pd

from .config import PlantConfig


def plot_results(results: Dict[str, object], summaries: Dict[str, pd.DataFrame], output_dir: str | Path) -> None:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = results["timeseries"]
    config: PlantConfig = results["config"]

    # Main trends for key quantities.
    fig = plt.figure(figsize=(14, 10), constrained_layout=True)
    axes = fig.subplots(3, 2)
    picks = ["BOD", "COD", "NH4", "NO3", "PO4", "SS"]
    for ax, sp in zip(axes.flat, picks):
        for stage, ls in [("IN", "--"), ("EQ", "-"), ("MBR", "-"), ("AOP", "-"), ("OUT", "-")]:
            alpha = 0.6 if stage in {"IN", "EQ"} else 0.9
            ax.plot(ts["t_h"], ts[f"{sp}_{stage}"], linestyle=ls, linewidth=1.6, alpha=alpha, label=stage)
        if sp in config.targets:
            ax.axhline(config.targets[sp], linestyle=":", linewidth=1.2)
        ax.set_title(f"{sp} [{config.units.get(sp, '-')}]")
        ax.set_xlabel("Time [h]")
        ax.grid(True, alpha=0.3)
    axes[0, 0].legend(ncol=5, fontsize=8)
    fig.suptitle("Hospital wastewater treatment train – key bulk quantities")
    fig.savefig(output_dir / "results_trends.png", dpi=180)
    plt.close(fig)

    # Toxic and pharmaceutical trends.
    fig = plt.figure(figsize=(14, 10), constrained_layout=True)
    axes = fig.subplots(3, 2)
    picks = ["Phenol", "Formaldehyde", "Glutaraldehyde", "Detergent", "CBZ", "DCF"]
    for ax, sp in zip(axes.flat, picks):
        for stage, ls in [("IN", "--"), ("MBR", "-"), ("AOP", "-"), ("OUT", "-")]:
            ax.plot(ts["t_h"], ts[f"{sp}_{stage}"], linestyle=ls, linewidth=1.8, label=stage)
        if sp in config.targets:
            ax.axhline(config.targets[sp], linestyle=":", linewidth=1.2)
        ax.set_title(f"{sp} [{config.units.get(sp, '-')}]")
        ax.set_xlabel("Time [h]")
        ax.grid(True, alpha=0.3)
    axes[0, 0].legend(ncol=4, fontsize=8)
    fig.suptitle("Hospital wastewater treatment train – toxicants and pharmaceuticals")
    fig.savefig(output_dir / "micropollutants_trends.png", dpi=180)
    plt.close(fig)

    # Effluent 24 h bars.
    stage_avg = summaries["stage_avg"].set_index("stage")
    picks = ["BOD", "COD", "NH4", "NO3", "PO4", "SS", "Phenol", "CBZ", "DCF"]
    fig, ax = plt.subplots(figsize=(13, 5), constrained_layout=True)
    values = [stage_avg.loc["OUT", sp] for sp in picks]
    targets = [config.targets.get(sp, float("nan")) for sp in picks]
    x = range(len(picks))
    ax.bar(list(x), values)
    ax.plot(list(x), targets, marker="o", linestyle="--")
    ax.set_xticks(list(x), picks, rotation=25, ha="right")
    ax.set_ylabel("24 h average effluent concentration")
    ax.set_title("Final effluent vs target values")
    ax.grid(True, axis="y", alpha=0.3)
    fig.savefig(output_dir / "effluent_24h_avg.png", dpi=180)
    plt.close(fig)

    # Breakthrough plot.
    fig, ax = plt.subplots(figsize=(12, 5), constrained_layout=True)
    for sp in ["Phenol", "CBZ", "DCF", "Detergent"]:
        ax.plot(ts["t_h"], ts[f"{sp}_OUT"], linewidth=1.8, label=f"{sp} OUT")
    ax.set_xlabel("Time [h]")
    ax.set_ylabel("Concentration [mg/L]")
    ax.set_title("Selected species after GAC – breakthrough behaviour")
    ax.grid(True, alpha=0.3)
    ax.legend(ncol=4, fontsize=8)
    fig.savefig(output_dir / "gac_breakthrough.png", dpi=180)
    plt.close(fig)

    # pH and fouling indicators.
    fig, ax1 = plt.subplots(figsize=(12, 5), constrained_layout=True)
    ax1.plot(ts["t_h"], ts["pH_IN"], linestyle="--", linewidth=1.4, label="pH IN")
    ax1.plot(ts["t_h"], ts["pH_MBR"], linewidth=1.8, label="pH MBR")
    ax1.plot(ts["t_h"], ts["pH_OUT"], linewidth=1.8, label="pH OUT")
    ax1.set_xlabel("Time [h]")
    ax1.set_ylabel("pH [-]")
    ax1.grid(True, alpha=0.3)
    ax2 = ax1.twinx()
    ax2.plot(ts["t_h"], ts["fouling_index"], linewidth=1.2, label="Fouling index")
    ax2.set_ylabel("Fouling index [-]")
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, ncol=4, fontsize=8)
    fig.savefig(output_dir / "pH_and_fouling.png", dpi=180)
    plt.close(fig)
