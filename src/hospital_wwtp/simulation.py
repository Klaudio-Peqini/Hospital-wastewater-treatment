from __future__ import annotations

from typing import Dict, Tuple
import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp

from .config import PlantConfig
from .influent import build_time_grid, make_influent_profile


def _interp_vector(t: float, t_grid: np.ndarray, values: np.ndarray) -> np.ndarray:
    return np.array([np.interp(t, t_grid, values[:, i]) for i in range(values.shape[1])], dtype=float)


def _species_index(config: PlantConfig) -> Dict[str, int]:
    return {sp: i for i, sp in enumerate(config.state_species)}


def _compute_pH(alk: np.ndarray, nh4: np.ndarray, tox: np.ndarray) -> np.ndarray:
    pH = 6.90 + 0.18 * np.log10(np.maximum(alk, 80.0) / 360.0) - 0.004 * np.maximum(nh4 - 15.0, 0.0) - 0.05 * tox
    return np.clip(pH, 6.2, 7.6)


def _derive_display_frame(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["COD"] = out["COD_bio"] + out["COD_inert"]
    tox = out[["Phenol", "Formaldehyde", "Glutaraldehyde", "Detergent"]].sum(axis=1)
    out["pH"] = _compute_pH(out["Alkalinity"].to_numpy(), out["NH4"].to_numpy(), tox.to_numpy())
    return out


def _mbr_rhs(t: float, y: np.ndarray, config: PlantConfig, t_grid: np.ndarray, influent: np.ndarray) -> np.ndarray:
    idx = _species_index(config)
    n = len(config.state_species)
    c_eq = np.maximum(y[:n], 0.0)
    c_mbr = np.maximum(y[n:2*n], 0.0)
    fouling = max(y[-1], 0.0)
    c_in = _interp_vector(t, t_grid, influent)
    q = config.flow_m3_per_day / 86400.0

    d_eq = (q / max(config.V_EQ_m3, 1e-12)) * (c_in - c_eq)

    tox = (
        config.inhibition_coeff["Phenol"] * c_mbr[idx["Phenol"]]
        + config.inhibition_coeff["Formaldehyde"] * c_mbr[idx["Formaldehyde"]]
        + config.inhibition_coeff["Glutaraldehyde"] * c_mbr[idx["Glutaraldehyde"]]
        + config.inhibition_coeff["Detergent"] * c_mbr[idx["Detergent"]]
        + config.inhibition_coeff["Pb"] * c_mbr[idx["Pb"]]
    ) * config.inhibition_scale
    inhibition = 1.0 / (1.0 + tox)
    pH = float(_compute_pH(np.array([c_mbr[idx["Alkalinity"]]]), np.array([c_mbr[idx["NH4"]]]), np.array([tox]))[0])
    pH_factor = float(np.exp(-((pH - 7.05) / 0.38) ** 2))
    fouling_factor = 1.0 / (1.0 + config.fouling_gamma * fouling)
    qv = q / max(config.V_MBR_m3, 1e-12)

    k = {sp: config.k_mbr_h[sp] / 3600.0 for sp in config.k_mbr_h}
    d_mbr = qv * (c_eq - c_mbr)

    # Bulk organics and solids
    d_mbr[idx["BOD"]] += -k["BOD"] * inhibition * fouling_factor * c_mbr[idx["BOD"]]
    d_mbr[idx["COD_bio"]] += -k["COD_bio"] * inhibition * fouling_factor * c_mbr[idx["COD_bio"]]
    d_mbr[idx["COD_inert"]] += -k["COD_inert"] * fouling_factor * c_mbr[idx["COD_inert"]]
    d_mbr[idx["TOC"]] += -k["TOC"] * inhibition * fouling_factor * c_mbr[idx["TOC"]]
    d_mbr[idx["SS"]] += -k["SS"] * fouling_factor * c_mbr[idx["SS"]]
    d_mbr[idx["Oils"]] += -k["Oils"] * fouling_factor * c_mbr[idx["Oils"]]

    # Nitrogen and phosphorus
    nitrif = k["NH4"] * inhibition * pH_factor * fouling_factor * c_mbr[idx["NH4"]]
    denit_drive = c_mbr[idx["COD_bio"]] / (c_mbr[idx["COD_bio"]] + 40.0)
    denit = (config.denit_max_h / 3600.0) * inhibition * denit_drive * c_mbr[idx["NO3"]]
    d_mbr[idx["NH4"]] += -nitrif
    d_mbr[idx["NO3"]] += config.nitrification_yield_no3 * nitrif - denit
    po4_rem = (k["PO4"] + config.po4_ss_coupling_h * k["SS"] / 3600.0) * inhibition * fouling_factor * c_mbr[idx["PO4"]]
    d_mbr[idx["PO4"]] += -po4_rem

    # Alkalinity and conductivity
    d_mbr[idx["Alkalinity"]] += -(config.alkalinity_consumption_per_nh4 / 3600.0) * nitrif + (config.alkalinity_recovery_per_denit / 3600.0) * denit
    d_mbr[idx["Conductivity"]] += 0.002 * nitrif

    # Toxic compounds and pharmaceuticals
    for sp in ["Phenol", "Formaldehyde", "Glutaraldehyde", "Detergent", "Pb", "CBZ", "DCF"]:
        rate = k[sp] * (inhibition if sp not in {"Pb", "CBZ", "DCF"} else 1.0) * fouling_factor
        d_mbr[idx[sp]] += -rate * c_mbr[idx[sp]]

    # Fouling accumulator
    foul_build = (config.fouling_build_h / 3600.0) * (
        c_mbr[idx["SS"]] / 300.0 + 0.4 * c_mbr[idx["Oils"]] / 5.0 + 0.3 * c_mbr[idx["Detergent"]] / 0.8
    )
    foul_relief = (config.fouling_relief_h / 3600.0) * fouling
    d_foul = foul_build - foul_relief
    return np.concatenate([d_eq, d_mbr, np.array([d_foul])])


def apply_aop(config: PlantConfig, mbr_df: pd.DataFrame) -> pd.DataFrame:
    q_m3_s = config.flow_m3_per_day / 86400.0
    tau_h = config.V_AOP_m3 / max(q_m3_s, 1e-12) / 3600.0
    out = mbr_df.copy()
    tox = out[["Phenol", "Formaldehyde", "Glutaraldehyde", "Detergent"]].sum(axis=1).to_numpy()
    pH = _compute_pH(out["Alkalinity"].to_numpy(), out["NH4"].to_numpy(), tox)
    pH_mod = 0.80 + 0.20 * np.exp(-((pH - 7.0) / 0.45) ** 2)
    for sp, k_h in config.k_aop_h.items():
        eff_tau = tau_h * config.oxidation_scale
        out[sp] = out[sp].to_numpy() * np.exp(-k_h * eff_tau * pH_mod)
    return out


def apply_gac(config: PlantConfig, aop_df: pd.DataFrame, t_s: np.ndarray) -> pd.DataFrame:
    out = aop_df.copy()
    t_h = t_s / 3600.0
    for sp, kth in config.gac_kth_h.items():
        tau_star = config.gac_tau_star_h[sp] * config.adsorption_scale
        f = 1.0 / (1.0 + np.exp(kth * (tau_star - t_h)))
        out[sp] = aop_df[sp].to_numpy() * f
    return out


def simulate_plant(config: PlantConfig) -> Dict[str, object]:
    t_s = build_time_grid(config.duration_h, config.dt_minutes)
    influent = make_influent_profile(config, t_s)
    n = len(config.state_species)
    y0 = np.concatenate([influent[0], influent[0], np.array([0.05])])
    sol = solve_ivp(
        lambda t, y: _mbr_rhs(t, y, config, t_s, influent),
        (t_s[0], t_s[-1]),
        y0,
        t_eval=t_s,
        method="BDF",
        rtol=1e-6,
        atol=1e-9,
    )
    if not sol.success:
        raise RuntimeError(sol.message)

    influent_df = pd.DataFrame(influent, columns=config.state_species)
    eq_df = pd.DataFrame(sol.y[:n, :].T, columns=config.state_species)
    mbr_df = pd.DataFrame(sol.y[n:2*n, :].T, columns=config.state_species)
    aop_df = apply_aop(config, mbr_df)
    out_df = apply_gac(config, aop_df, t_s)

    stages = {
        "IN": _derive_display_frame(influent_df),
        "EQ": _derive_display_frame(eq_df),
        "MBR": _derive_display_frame(mbr_df),
        "AOP": _derive_display_frame(aop_df),
        "OUT": _derive_display_frame(out_df),
    }

    timeseries = pd.DataFrame({"t_s": t_s, "t_h": t_s / 3600.0, "fouling_index": sol.y[-1, :]})
    for label, frame in stages.items():
        for sp in config.display_species:
            timeseries[f"{sp}_{label}"] = frame[sp].to_numpy()
    return {
        "config": config,
        "t_s": t_s,
        "t_h": t_s / 3600.0,
        "stages": stages,
        "influent": stages["IN"],
        "eq": stages["EQ"],
        "mbr": stages["MBR"],
        "aop": stages["AOP"],
        "out": stages["OUT"],
        "timeseries": timeseries,
    }
