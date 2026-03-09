from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

STATE_SPECIES: List[str] = [
    "BOD", "COD_bio", "COD_inert", "TOC", "NH4", "NO3", "PO4", "SS",
    "Alkalinity", "Conductivity", "Phenol", "Formaldehyde", "Glutaraldehyde",
    "Detergent", "Oils", "Pb", "CBZ", "DCF",
]
DISPLAY_SPECIES: List[str] = [
    "BOD", "COD", "TOC", "NH4", "NO3", "PO4", "SS", "Phenol",
    "Formaldehyde", "Glutaraldehyde", "Detergent", "Oils", "Pb", "CBZ", "DCF", "pH"
]
UNITS: Dict[str, str] = {
    "BOD": "mg/L", "COD_bio": "mg/L", "COD_inert": "mg/L", "COD": "mg/L", "TOC": "mg/L",
    "NH4": "mg/L", "NO3": "mg/L", "PO4": "mg/L", "SS": "mg/L",
    "Alkalinity": "mg/L as CaCO3", "Conductivity": "uS/cm", "Phenol": "mg/L",
    "Formaldehyde": "mg/L", "Glutaraldehyde": "mg/L", "Detergent": "mg/L",
    "Oils": "mg/L", "Pb": "mg/L", "CBZ": "mg/L", "DCF": "mg/L", "pH": "-",
}


def available_scenarios() -> List[str]:
    return ["low", "nominal", "high", "shock"]


@dataclass(slots=True)
class PlantConfig:
    flow_m3_per_day: float = 500.0
    duration_h: float = 96.0
    dt_minutes: float = 5.0
    scenario: str = "nominal"
    influent_mode: str = "hospital"
    seed: int = 42
    noise_sigma: float = 0.05
    shock_hour: float = 36.0
    shock_width_h: float = 1.2
    shock_multiplier: float = 2.2
    weekly_variation: float = 0.04
    oxidation_scale: float = 1.0
    adsorption_scale: float = 1.0
    inhibition_scale: float = 1.0

    state_species: List[str] = field(default_factory=lambda: STATE_SPECIES.copy())
    display_species: List[str] = field(default_factory=lambda: DISPLAY_SPECIES.copy())
    units: Dict[str, str] = field(default_factory=lambda: UNITS.copy())

    influent_base: Dict[str, float] = field(default_factory=lambda: {
        "BOD": 150.0,
        "COD_bio": 260.0,
        "COD_inert": 180.0,
        "TOC": 85.0,
        "NH4": 18.0,
        "NO3": 4.5,
        "PO4": 4.4,
        "SS": 260.0,
        "Alkalinity": 360.0,
        "Conductivity": 780.0,
        "Phenol": 0.25,
        "Formaldehyde": 0.10,
        "Glutaraldehyde": 0.35,
        "Detergent": 0.45,
        "Oils": 3.5,
        "Pb": 0.05,
        "CBZ": 0.0020,
        "DCF": 0.0015,
    })
    targets: Dict[str, float] = field(default_factory=lambda: {
        "BOD": 30.0, "COD": 125.0, "TOC": 30.0, "NH4": 5.0, "NO3": 15.0,
        "PO4": 2.0, "SS": 35.0, "Phenol": 0.10, "Formaldehyde": 0.05,
        "Glutaraldehyde": 0.20, "Detergent": 0.20, "Oils": 2.0, "Pb": 0.05,
        "CBZ": 0.0003, "DCF": 0.0002, "pH": 7.0,
    })
    pnec: Dict[str, float] = field(default_factory=lambda: {"CBZ": 0.00050, "DCF": 0.00010, "Phenol": 0.10})

    V_EQ_m3: float = 220.0
    V_MBR_m3: float = 180.0
    V_AOP_m3: float = 30.0
    V_GAC_bed_m3: float = 6.0

    k_mbr_h: Dict[str, float] = field(default_factory=lambda: {
        "BOD": 0.95,
        "COD_bio": 0.55,
        "COD_inert": 0.06,
        "TOC": 0.28,
        "NH4": 0.30,
        "NO3": 0.08,
        "PO4": 0.14,
        "SS": 1.20,
        "Phenol": 0.22,
        "Formaldehyde": 0.32,
        "Glutaraldehyde": 0.18,
        "Detergent": 0.16,
        "Oils": 0.20,
        "Pb": 0.02,
        "CBZ": 0.015,
        "DCF": 0.045,
    })
    k_aop_h: Dict[str, float] = field(default_factory=lambda: {
        "BOD": 0.12,
        "COD_bio": 0.10,
        "COD_inert": 0.28,
        "TOC": 0.18,
        "NH4": 0.00,
        "NO3": 0.00,
        "PO4": 0.00,
        "SS": 0.00,
        "Phenol": 0.40,
        "Formaldehyde": 0.30,
        "Glutaraldehyde": 0.28,
        "Detergent": 0.12,
        "Oils": 0.10,
        "Pb": 0.00,
        "CBZ": 0.42,
        "DCF": 0.34,
    })
    gac_kth_h: Dict[str, float] = field(default_factory=lambda: {
        "COD_inert": 0.10,
        "TOC": 0.08,
        "Phenol": 0.22,
        "CBZ": 0.18,
        "DCF": 0.24,
        "Detergent": 0.10,
    })
    gac_tau_star_h: Dict[str, float] = field(default_factory=lambda: {
        "COD_inert": 150.0,
        "TOC": 140.0,
        "Phenol": 170.0,
        "CBZ": 180.0,
        "DCF": 165.0,
        "Detergent": 130.0,
    })

    fouling_build_h: float = 0.035
    fouling_relief_h: float = 0.020
    fouling_gamma: float = 0.90
    nitrification_yield_no3: float = 0.92
    denit_max_h: float = 0.10
    po4_ss_coupling_h: float = 0.05
    alkalinity_consumption_per_nh4: float = 7.14
    alkalinity_recovery_per_denit: float = 1.8

    inhibition_coeff: Dict[str, float] = field(default_factory=lambda: {
        "Phenol": 1.2,
        "Formaldehyde": 2.6,
        "Glutaraldehyde": 1.8,
        "Detergent": 0.7,
        "Pb": 8.0,
    })

    def apply_scenario(self) -> None:
        scale = {
            "low": 0.70,
            "nominal": 1.00,
            "high": 1.35,
            "shock": 1.15,
        }.get(self.scenario, 1.0)
        toxic_scale = {
            "low": 0.75,
            "nominal": 1.00,
            "high": 1.40,
            "shock": 1.70,
        }.get(self.scenario, 1.0)
        for key in list(self.influent_base):
            if key in {"Phenol", "Formaldehyde", "Glutaraldehyde", "Detergent", "Pb", "CBZ", "DCF"}:
                self.influent_base[key] *= toxic_scale
            elif key in {"Alkalinity", "Conductivity"}:
                self.influent_base[key] *= 0.9 + 0.1 * scale
            else:
                self.influent_base[key] *= scale
        if self.scenario == "low":
            self.noise_sigma = min(self.noise_sigma, 0.03)
        elif self.scenario == "high":
            self.noise_sigma = max(self.noise_sigma, 0.06)
        elif self.scenario == "shock":
            self.shock_multiplier = max(self.shock_multiplier, 3.0)
            self.noise_sigma = max(self.noise_sigma, 0.07)


def default_config(scenario: str = "nominal") -> PlantConfig:
    cfg = PlantConfig(scenario=scenario)
    cfg.apply_scenario()
    return cfg
