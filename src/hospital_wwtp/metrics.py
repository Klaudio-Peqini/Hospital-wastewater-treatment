from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List
import numpy as np
import pandas as pd

from .config import PlantConfig


def _tail_rows(timeseries: pd.DataFrame, duration_h: float = 24.0) -> pd.DataFrame:
    return timeseries[timeseries["t_h"] >= (timeseries["t_h"].iloc[-1] - duration_h)].copy()


def stage_24h_average(results: Dict[str, object], species: Iterable[str] | None = None) -> pd.DataFrame:
    config: PlantConfig = results["config"]
    species = list(species or config.display_species)
    tail = _tail_rows(results["timeseries"])
    rows = []
    for stage in ["IN", "EQ", "MBR", "AOP", "OUT"]:
        row = {"stage": stage}
        for sp in species:
            row[sp] = tail[f"{sp}_{stage}"].mean()
        rows.append(row)
    return pd.DataFrame(rows)


def removal_summary(stage_avg: pd.DataFrame, config: PlantConfig) -> pd.DataFrame:
    rows = []
    for sp in config.display_species:
        if sp == "pH":
            continue
        c_in = float(stage_avg.loc[stage_avg["stage"] == "IN", sp].iloc[0])
        for stage in ["EQ", "MBR", "AOP", "OUT"]:
            c_stage = float(stage_avg.loc[stage_avg["stage"] == stage, sp].iloc[0])
            eta = 100.0 * (c_in - c_stage) / max(c_in, 1e-12)
            rows.append({"species": sp, "stage": stage, "influent_24h_avg": c_in, "stage_24h_avg": c_stage, "removal_percent": eta})
    return pd.DataFrame(rows)


def compliance_summary(stage_avg: pd.DataFrame, config: PlantConfig) -> pd.DataFrame:
    out = stage_avg.loc[stage_avg["stage"] == "OUT"].iloc[0]
    rows = []
    for sp, target in config.targets.items():
        value = float(out[sp])
        if sp == "pH":
            compliant = 6.5 <= value <= 8.5
        else:
            compliant = value <= target
        rows.append({"species": sp, "value": value, "target": target, "compliant": compliant})
    return pd.DataFrame(rows)


def risk_summary(stage_avg: pd.DataFrame, config: PlantConfig) -> pd.DataFrame:
    out = stage_avg.loc[stage_avg["stage"] == "OUT"].iloc[0]
    rows = []
    for sp, pnec in config.pnec.items():
        value = float(out[sp])
        rows.append({"species": sp, "effluent_24h_avg": value, "PNEC": pnec, "RQ": value / max(pnec, 1e-12)})
    return pd.DataFrame(rows)


def breakthrough_summary(results: Dict[str, object], frac: float = 0.05, species: Iterable[str] = ("Phenol", "CBZ", "DCF", "Detergent")) -> pd.DataFrame:
    ts = results["timeseries"]
    rows = []
    for sp in species:
        c_in = ts[f"{sp}_IN"].to_numpy()
        c_out = ts[f"{sp}_OUT"].to_numpy()
        threshold = frac * np.nanmax(c_in)
        idx = np.where(c_out >= threshold)[0]
        t_bt = float(ts["t_h"].iloc[idx[0]]) if idx.size else np.nan
        rows.append({"species": sp, "threshold_fraction_of_peak_influent": frac, "breakthrough_time_h": t_bt})
    return pd.DataFrame(rows)


def summarize_and_save(results: Dict[str, object], output_dir: str | Path) -> Dict[str, pd.DataFrame]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stage_avg = stage_24h_average(results)
    removal = removal_summary(stage_avg, results["config"])
    compliance = compliance_summary(stage_avg, results["config"])
    risk = risk_summary(stage_avg, results["config"])
    breakthrough = breakthrough_summary(results)
    stage_avg.to_csv(output_dir / "stage_24h_average.csv", index=False)
    removal.to_csv(output_dir / "removal_summary.csv", index=False)
    compliance.to_csv(output_dir / "compliance_summary.csv", index=False)
    risk.to_csv(output_dir / "risk_summary.csv", index=False)
    breakthrough.to_csv(output_dir / "breakthrough_summary.csv", index=False)
    results["timeseries"].to_csv(output_dir / "simulation_timeseries.csv", index=False)
    return {
        "stage_avg": stage_avg,
        "removal": removal,
        "compliance": compliance,
        "risk": risk,
        "breakthrough": breakthrough,
    }
