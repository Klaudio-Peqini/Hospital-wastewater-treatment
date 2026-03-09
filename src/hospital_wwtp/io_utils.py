from __future__ import annotations

from pathlib import Path
import json
from dataclasses import asdict
from .config import PlantConfig


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def save_config(config: PlantConfig, output_dir: str | Path) -> None:
    p = ensure_dir(output_dir) / "config_used.json"
    with p.open("w", encoding="utf-8") as f:
        json.dump(asdict(config), f, indent=2)
