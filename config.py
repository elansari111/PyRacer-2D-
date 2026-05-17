# ============================================================
#  PyRacer: Ultimate Neon Highway
#  config.py — Gestionnaire de configuration persistante
# ============================================================

import json
import os
import pygame
from typing import Any


class ConfigManager:
    """
    Gère les paramètres utilisateur avec sauvegarde JSON.
    Paramètres: audio, graphiques, contrôles, profil joueur.
    """
    
    CONFIG_FILE = "config.json"
    
    DEFAULTS = {
        # Audio
        "audio_enabled": True,
        "music_enabled": True,
        "sfx_enabled": True,
        "master_volume": 0.7,
        "music_volume": 0.5,
        "sfx_volume": 0.8,
        
        # Graphiques
        "fullscreen": False,
        "show_particles": True,
        "show_weather": True,
        "screen_shake": True,
        "glow_effects": True,
        "fps_counter": False,
        
        # Gameplay
        "difficulty": "normal",  # easy, normal, hard
        "show_minimap": True,
        "car_color": "cyan",  # cyan, magenta, yellow, green, red, purple
        "car_skin": "default",  # default, racing, neon, stealth
        
        # Contrôles
        "key_left": "left",
        "key_right": "right",
        "key_up": "up",
        "key_down": "down",
        "key_nitro": "space",
        "key_shield": "b",
        "key_pause": "p",
        
        # Profil
        "player_name": "Player",
        "total_games": 0,
        "total_distance": 0,
        "best_streak": 0,
    }
    
    def __init__(self):
        self.data = self.DEFAULTS.copy()
        self._load()
        
    def _load(self):
        """Charge la configuration depuis le fichier."""
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                # Fusionne avec les défauts pour les nouveaux champs
                self.data.update(loaded)
            except (json.JSONDecodeError, IOError) as e:
                print(f"[Config] Erreur chargement: {e}")
                self._save()  # Réécrit avec défauts
        else:
            self._save()
            
    def _save(self):
        """Sauvegarde la configuration."""
        try:
            with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except IOError as e:
            print(f"[Config] Erreur sauvegarde: {e}")
            
    def get(self, key: str, default=None) -> Any:
        """Récupère une valeur."""
        return self.data.get(key, default or self.DEFAULTS.get(key))
        
    def set(self, key: str, value: Any):
        """Définit une valeur et sauvegarde."""
        self.data[key] = value
        self._save()
        
    def reset(self):
        """Réinitialise aux valeurs par défaut."""
        self.data = self.DEFAULTS.copy()
        self._save()
        
    # ----------------------------------------------------------
    # Helpers spécifiques
    # ----------------------------------------------------------
    
    def get_car_color_rgb(self) -> tuple:
        """Retourne la couleur RGB de la voiture."""
        colors = {
            "cyan": (0, 229, 255),
            "magenta": (255, 77, 206),
            "yellow": (255, 215, 0),
            "green": (74, 222, 128),
            "red": (255, 68, 68),
            "purple": (168, 139, 250),
            "orange": (255, 107, 53),
            "white": (232, 244, 253),
        }
        return colors.get(self.data.get("car_color"), colors["cyan"])
        
    def get_difficulty_multiplier(self) -> float:
        """Retourne le multiplicateur de difficulté."""
        mults = {"easy": 0.7, "normal": 1.0, "hard": 1.3}
        return mults.get(self.data.get("difficulty"), 1.0)
        
    def increment_stat(self, key: str, amount: int = 1):
        """Incrémente une statistique."""
        if key in self.data:
            self.data[key] += amount
            self._save()
            
    def get_key_binding(self, action: str) -> int:
        """Retourne le code pygame pour une action."""
        key_map = {
            "left": pygame.K_LEFT,
            "right": pygame.K_RIGHT,
            "up": pygame.K_UP,
            "down": pygame.K_DOWN,
            "space": pygame.K_SPACE,
            "b": pygame.K_b,
            "p": pygame.K_p,
            "a": pygame.K_a,
            "d": pygame.K_d,
            "w": pygame.K_w,
            "s": pygame.K_s,
            "escape": pygame.K_ESCAPE,
            "return": pygame.K_RETURN,
        }
        binding = self.data.get(f"key_{action}", self.DEFAULTS.get(f"key_{action}"))
        code = key_map.get(binding)
        if code is not None:
            return code
        fallbacks = {
            "left": pygame.K_LEFT,
            "right": pygame.K_RIGHT,
            "up": pygame.K_UP,
            "down": pygame.K_DOWN,
            "nitro": pygame.K_SPACE,
            "shield": pygame.K_b,
            "pause": pygame.K_p,
        }
        return fallbacks.get(action, pygame.K_SPACE)


# Singleton global
config = ConfigManager()
