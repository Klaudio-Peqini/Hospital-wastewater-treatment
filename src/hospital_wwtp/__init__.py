"""Hospital wastewater treatment train simulator."""

from .config import PlantConfig, default_config, available_scenarios
from .simulation import simulate_plant

__all__ = ["PlantConfig", "default_config", "available_scenarios", "simulate_plant"]
__version__ = "0.2.0"
