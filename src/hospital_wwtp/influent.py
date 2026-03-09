from __future__ import annotations

import numpy as np
from .config import PlantConfig

_DAILY_PROFILE = np.array([
    [0.0, 0.55], [5.0, 0.50], [7.0, 0.72], [9.0, 1.10], [12.0, 1.28],
    [14.0, 1.02], [17.0, 0.92], [20.0, 1.18], [22.0, 0.82], [24.0, 0.58],
], dtype=float)


def build_time_grid(duration_h: float, dt_minutes: float) -> np.ndarray:
    n_steps = int(round(duration_h * 60.0 / dt_minutes))
    return np.linspace(0.0, duration_h * 3600.0, n_steps + 1)


def _piecewise_daily_multiplier(hours: np.ndarray) -> np.ndarray:
    h = np.mod(hours, 24.0)
    return np.interp(h, _DAILY_PROFILE[:, 0], _DAILY_PROFILE[:, 1])


def _make_shock(hours: np.ndarray, hour0: float, width_h: float) -> np.ndarray:
    return np.exp(-0.5 * ((hours - hour0) / max(width_h, 1e-6)) ** 2)


def make_influent_profile(config: PlantConfig, t_s: np.ndarray) -> np.ndarray:
    rng = np.random.default_rng(config.seed)
    hours = t_s / 3600.0
    data = np.zeros((t_s.size, len(config.state_species)), dtype=float)
    if config.influent_mode == "sinusoidal":
        daily = 1.0 + 0.22 * np.sin(2.0 * np.pi * hours / 24.0 - np.pi / 2.0)
    else:
        daily = _piecewise_daily_multiplier(hours)
        week = 1.0 + config.weekly_variation * np.sin(2.0 * np.pi * hours / (24.0 * 7.0))
        daily = daily * week
    shock = _make_shock(hours, config.shock_hour, config.shock_width_h)
    meal_peak = np.exp(-0.5 * ((np.mod(hours, 24.0) - 13.0) / 1.3) ** 2)
    cleaning_peak = np.exp(-0.5 * ((np.mod(hours, 24.0) - 6.5) / 0.8) ** 2)
    noise = rng.normal(0.0, config.noise_sigma, size=data.shape)

    for j, sp in enumerate(config.state_species):
        base = config.influent_base[sp]
        signal = base * daily
        signal *= np.maximum(0.55, 1.0 + noise[:, j])
        if sp in {"BOD", "COD_bio", "TOC", "SS", "Oils"}:
            signal *= 1.0 + 0.10 * meal_peak
        if sp in {"Phenol", "Formaldehyde", "Glutaraldehyde", "Detergent"}:
            signal *= 1.0 + 0.25 * cleaning_peak
        if sp in {"CBZ", "DCF", "Phenol", "Formaldehyde", "Glutaraldehyde", "Detergent"}:
            signal *= 1.0 + 0.55 * shock * (config.shock_multiplier - 1.0)
        if config.scenario == "shock" and sp in {"BOD", "COD_bio", "NH4", "SS"}:
            signal *= 1.0 + 0.25 * shock
        data[:, j] = np.maximum(signal, 0.0)
    return data
