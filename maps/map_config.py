"""
map_config.py — Définitions des cartes PyRacer.

Rôle: Enum et métadonnées partagées (vitesse, ennemis, musique).
Paramètres: MapConfig, niveau 1-3.
Dépendances: settings.py
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Tuple


class MapConfig(Enum):
    """Identifiants des trois cartes jouables."""
    CITY = "city"
    HIGHWAY = "highway"
    CIRCUIT = "circuit"


@dataclass
class MapDefinition:
    """Métadonnées d'une carte pour un niveau donné."""
    map_id: str
    name: str
    tileset: str
    max_speed_kmh: float
    road_width_mod: float
    friction_mod: float
    obstacles: List[str]
    enemy_types: List[str]
    music_theme: str
    level: int
    max_enemies: int
    extra: dict = field(default_factory=dict)


MAP_META = {
    MapConfig.CITY: {
        "display": "VILLE",
        "tileset": "city_neon",
        "music": "city_theme",
        "friction": 1.05,
    },
    MapConfig.HIGHWAY: {
        "display": "AUTOROUTE",
        "tileset": "highway_neon",
        "music": "highway_theme",
        "friction": 0.95,
    },
    MapConfig.CIRCUIT: {
        "display": "CIRCUIT",
        "tileset": "circuit_neon",
        "music": "circuit_theme",
        "friction": 1.0,
    },
}


def get_map_definition(map_cfg: MapConfig, level: int) -> MapDefinition:
    """
    Retourne la définition complète map+niveau.

    Paramètres:
        map_cfg: Carte (CITY, HIGHWAY, CIRCUIT).
        level: Niveau 1-3.
    """
    level = max(1, min(3, level))
    meta = MAP_META[map_cfg]
    mid = map_cfg.value

    presets = {
        MapConfig.CITY: [
            {"max_speed": 120, "road_mod": 1.0, "enemies": ["standard"], "max_e": 3,
             "obstacles": [], "extra": {"traffic_lights": 0, "pedestrians": False}},
            {"max_speed": 120, "road_mod": 0.85, "enemies": ["standard", "fast"], "max_e": 6,
             "obstacles": ["speed_bump", "traffic_light"], "extra": {"traffic_lights": 3}},
            {"max_speed": 120, "road_mod": 0.70, "enemies": ["standard", "fast", "unpredictable"],
             "max_e": 12, "obstacles": ["speed_bump", "traffic_light", "pedestrian"],
             "extra": {"traffic_lights": 6, "pedestrians": True, "fog": True}},
        ],
        MapConfig.HIGHWAY: [
            {"max_speed": 999, "road_mod": 1.0, "enemies": ["truck"], "max_e": 2,
             "obstacles": [], "extra": {"police": 0, "lanes": 4}},
            {"max_speed": 999, "road_mod": 1.0, "enemies": ["truck", "police"], "max_e": 6,
             "obstacles": ["wind"], "extra": {"police": 2, "wind": 0.3}},
            {"max_speed": 999, "road_mod": 1.0, "enemies": ["truck", "police", "fast"], "max_e": 12,
             "obstacles": ["tunnel", "wind", "storm"],
             "extra": {"police": 4, "tunnel": True, "storm": True}},
        ],
        MapConfig.CIRCUIT: [
            {"max_speed": 280, "road_mod": 1.0, "enemies": ["rival"], "max_e": 2,
             "obstacles": [], "extra": {"laps": 3, "tire_wear": False, "pit": False}},
            {"max_speed": 300, "road_mod": 1.0, "enemies": ["rival", "fast"], "max_e": 5,
             "obstacles": ["drs"], "extra": {"laps": 5, "tire_wear": True, "pit": False}},
            {"max_speed": 320, "road_mod": 1.0, "enemies": ["rival", "fast", "unpredictable"],
             "max_e": 8, "obstacles": ["drs", "weather"],
             "extra": {"laps": 7, "tire_wear": True, "pit": True, "weather": True}},
        ],
    }

    p = presets[map_cfg][level - 1]
    return MapDefinition(
        map_id=mid,
        name=f"{meta['display']} — Niv.{level}",
        tileset=meta["tileset"],
        max_speed_kmh=p["max_speed"],
        road_width_mod=p["road_mod"],
        friction_mod=meta["friction"],
        obstacles=p["obstacles"],
        enemy_types=p["enemies"],
        music_theme=meta["music"],
        level=level,
        max_enemies=p["max_e"],
        extra=p["extra"],
    )


def score_key(map_id: str, level: int) -> str:
    """Clé hi-score: city_2, highway_1, etc."""
    return f"{map_id}_{level}"
