"""Package maps — configuration et logique par carte."""

from maps.map_config import MapConfig, get_map_definition
from maps.city_map import CityMap
from maps.highway_map import HighwayMap
from maps.circuit_map import CircuitMap
from maps.circuit_race import CircuitRace, RivalRacer

__all__ = [
    "MapConfig",
    "get_map_definition",
    "CityMap",
    "HighwayMap",
    "CircuitMap",
]
