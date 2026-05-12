# ============================================================
#  PyRacer: Ultimate Neon Highway
#  achievements.py — Système de succès/achievements
# ============================================================

import json
import os
from typing import Dict, List, Callable
from dataclasses import dataclass, asdict
from enum import Enum


class AchievementTier(Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


@dataclass
class Achievement:
    id: str
    name: str
    description: str
    tier: AchievementTier
    icon: str
    condition: str  # Description de la condition
    unlocked: bool = False
    progress: int = 0
    target: int = 1
    secret: bool = False  # Achievement caché


class AchievementManager:
    """
    Gère tous les achievements du jeu avec progression et sauvegarde.
    """
    
    ACHIEVEMENTS_FILE = "achievements.json"
    
    ACHIEVEMENTS_DATA = [
        # Démarrage
        Achievement("first_steps", "Premiers Pas", "Compléter votre première partie", 
                   AchievementTier.BRONZE, "🚗", "Terminer une partie", target=1),
        Achievement("beginner", "Débutant", "Atteindre 1 000 points", 
                   AchievementTier.BRONZE, "🏁", "Score cumulé 1000", target=1000),
        Achievement("intermediate", "Intermédiaire", "Atteindre 10 000 points", 
                   AchievementTier.SILVER, "🏁", "Score cumulé 10000", target=10000),
        Achievement("master", "Maître", "Atteindre 50 000 points", 
                   AchievementTier.GOLD, "🏆", "Score cumulé 50000", target=50000),
        Achievement("legend", "Légende", "Atteindre 100 000 points", 
                   AchievementTier.PLATINUM, "👑", "Score cumulé 100000", target=100000),
        
        # Dépassements
        Achievement("overtake_10", "Début de Course", "Dépasser 10 véhicules", 
                   AchievementTier.BRONZE, "↗️", "Dépassements 10", target=10),
        Achievement("overtake_50", "Challenger", "Dépasser 50 véhicules", 
                   AchievementTier.SILVER, "↗️", "Dépassements 50", target=50),
        Achievement("overtake_100", "Intouchable", "Dépasser 100 véhicules", 
                   AchievementTier.GOLD, "↗️", "Dépassements 100", target=100),
        Achievement("overtake_500", "As du Volant", "Dépasser 500 véhicules", 
                   AchievementTier.PLATINUM, "🚀", "Dépassements 500", target=500),
        
        # Streaks
        Achievement("streak_5", "En Série", "Atteindre un streak de 5", 
                   AchievementTier.BRONZE, "🔥", "Streak max 5", target=5),
        Achievement("streak_10", "Inarrêtable", "Atteindre un streak de 10", 
                   AchievementTier.SILVER, "🔥", "Streak max 10", target=10),
        Achievement("streak_20", "Divin", "Atteindre un streak de 20", 
                   AchievementTier.GOLD, "🔥", "Streak max 20", target=20),
        Achievement("streak_30", "Dieu de la Route", "Atteindre un streak de 30", 
                   AchievementTier.PLATINUM, "⚡", "Streak max 30", target=30),
        
        # Niveaux
        Achievement("city_complete", "Citadin", "Compléter le niveau Ville", 
                   AchievementTier.BRONZE, "🏙️", "Niveau 1 complété", target=1),
        Achievement("highway_complete", "Autoroutier", "Compléter le niveau Autoroute", 
                   AchievementTier.SILVER, "🛣️", "Niveau 2 complété", target=1),
        Achievement("circuit_complete", "Pilote", "Compléter le niveau Circuit", 
                   AchievementTier.GOLD, "🏎️", "Niveau 3 complété", target=1),
        Achievement("all_levels", "Champion", "Compléter les 3 niveaux en une partie", 
                   AchievementTier.PLATINUM, "🏆", "Victoire complète", target=1),
        
        # Bonus
        Achievement("collector", "Collectionneur", "Collecter 10 bonus", 
                   AchievementTier.BRONZE, "💎", "Bonus collectés 10", target=10),
        Achievement("hoarder", "Magot", "Collecter 50 bonus", 
                   AchievementTier.SILVER, "💎", "Bonus collectés 50", target=50),
        Achievement("nitro_lover", "Amateur de Nitro", "Activer le nitro 20 fois", 
                   AchievementTier.BRONZE, "⚡", "Nitro activé 20", target=20),
        Achievement("shield_master", "Maître du Bouclier", "Activer le bouclier 15 fois", 
                   AchievementTier.BRONZE, "🛡️", "Bouclier activé 15", target=15),
        
        # Technique
        Achievement("no_damage", "Flawless", "Terminer un niveau sans collision", 
                   AchievementTier.SILVER, "✨", "Niveau sans dégât", target=1),
        Achievement("nitro_overtake", "Nitro Boost", "Dépasser 5 véhicules en nitro", 
                   AchievementTier.SILVER, "🚀", "Dépassements nitro 5", target=5),
        Achievement("slow_master", "Maître du Temps", "Utiliser 5 ralentissements", 
                   AchievementTier.BRONZE, "⏱️", "Bonus slow 5", target=5),
        
        # Durée / Distance
        Achievement("survivor", "Survivant", "Survivre 60 secondes au niveau Circuit", 
                   AchievementTier.SILVER, "⏰", "Survie 60s niveau 3", target=60),
        Achievement("marathon", "Marathonien", "Parcourir 10km au total", 
                   AchievementTier.GOLD, "📏", "Distance 10000", target=10000),
        Achievement("speed_demon", "Démon de Vitesse", "Atteindre 350 km/h", 
                   AchievementTier.GOLD, "💨", "Vitesse max 350", target=350),
        
        # Secrets
        Achievement("secret_nitro", "Nitro Fou", "Utiliser le nitro 10 fois en 30 secondes", 
                   AchievementTier.SILVER, "🤫", "Nitro spam 10/30s", target=1, secret=True),
        Achievement("secret_perfect", "Perfect Run", "Gagner avec 3 vies intactes", 
                   AchievementTier.GOLD, "🤫", "Victoire 3 vies", target=1, secret=True),
        Achievement("secret_close", "Close Call", "Frôler 10 collisions", 
                   AchievementTier.SILVER, "🤫", "Close calls 10", target=10, secret=True),
    ]
    
    def __init__(self):
        self.achievements: Dict[str, Achievement] = {}
        self.new_unlocks: List[Achievement] = []
        self.callbacks: List[Callable] = []
        
        # Stats de session pour les achievements
        self.session_stats = {
            "nitro_activations_30s": [],
            "close_calls": 0,
            "level_damage": {0: False, 1: False, 2: False},
        }
        
        self._init_achievements()
        self._load()
        
    def _init_achievements(self):
        """Initialise la liste des achievements."""
        for ach in self.ACHIEVEMENTS_DATA:
            self.achievements[ach.id] = Achievement(**asdict(ach))
            
    def _load(self):
        """Charge la progression depuis le fichier."""
        if os.path.exists(self.ACHIEVEMENTS_FILE):
            try:
                with open(self.ACHIEVEMENTS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for ach_id, ach_data in data.items():
                    if ach_id in self.achievements:
                        self.achievements[ach_id].unlocked = ach_data.get("unlocked", False)
                        self.achievements[ach_id].progress = ach_data.get("progress", 0)
            except (json.JSONDecodeError, IOError) as e:
                print(f"[Achievements] Erreur chargement: {e}")
                
    def _save(self):
        """Sauvegarde la progression."""
        data = {}
        for ach_id, ach in self.achievements.items():
            data[ach_id] = {
                "unlocked": ach.unlocked,
                "progress": ach.progress
            }
        try:
            with open(self.ACHIEVEMENTS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            print(f"[Achievements] Erreur sauvegarde: {e}")
            
    def register_callback(self, callback: Callable):
        """Enregistre un callback pour les nouveaux déblocages."""
        self.callbacks.append(callback)
        
    def update_progress(self, ach_id: str, value: int):
        """Met à jour la progression d'un achievement."""
        if ach_id not in self.achievements:
            return
            
        ach = self.achievements[ach_id]
        if ach.unlocked:
            return
            
        ach.progress = value
        if ach.progress >= ach.target:
            self.unlock(ach_id)
            
    def increment_progress(self, ach_id: str, amount: int = 1):
        """Incrémente la progression."""
        if ach_id in self.achievements:
            self.update_progress(ach_id, self.achievements[ach_id].progress + amount)
            
    def unlock(self, ach_id: str):
        """Débloque un achievement."""
        if ach_id not in self.achievements:
            return
            
        ach = self.achievements[ach_id]
        if ach.unlocked:
            return
            
        ach.unlocked = True
        ach.progress = ach.target
        self.new_unlocks.append(ach)
        self._save()
        
        # Notifie les callbacks
        for callback in self.callbacks:
            callback(ach)
            
    def check_score_achievements(self, score: int):
        """Vérifie les achievements de score."""
        tiers = [
            ("beginner", 1000),
            ("intermediate", 10000),
            ("master", 50000),
            ("legend", 100000),
        ]
        for ach_id, target in tiers:
            if score >= target:
                self.unlock(ach_id)
                
    def check_overtake_achievements(self, total_overtakes: int):
        """Vérifie les achievements de dépassement."""
        tiers = [
            ("overtake_10", 10),
            ("overtake_50", 50),
            ("overtake_100", 100),
            ("overtake_500", 500),
        ]
        for ach_id, target in tiers:
            if total_overtakes >= target:
                self.unlock(ach_id)
                
    def check_streak_achievements(self, streak: int):
        """Vérifie les achievements de streak."""
        if streak >= 30:
            self.unlock("streak_30")
        elif streak >= 20:
            self.unlock("streak_20")
        elif streak >= 10:
            self.unlock("streak_10")
        elif streak >= 5:
            self.unlock("streak_5")
            
    def on_nitro_activated(self):
        """Appelé quand le nitro est activé."""
        self.increment_progress("nitro_lover")
        
        # Track pour secret
        import time
        now = time.time()
        self.session_stats["nitro_activations_30s"].append(now)
        # Garde seulement les 30 dernières secondes
        self.session_stats["nitro_activations_30s"] = [
            t for t in self.session_stats["nitro_activations_30s"] if now - t <= 30
        ]
        if len(self.session_stats["nitro_activations_30s"]) >= 10:
            self.unlock("secret_nitro")
            
    def on_shield_activated(self):
        """Appelé quand le bouclier est activé."""
        self.increment_progress("shield_master")
        
    def on_bonus_collected(self):
        """Appelé quand un bonus est collecté."""
        self.increment_progress("collector")
        self.increment_progress("hoarder")
        
    def on_slow_activated(self):
        """Appelé quand le ralentissement est utilisé."""
        self.increment_progress("slow_master")
        
    def on_level_completed(self, level: int, lives_remaining: int, damage_taken: bool):
        """Appelé à la complétion d'un niveau."""
        if level == 0:
            self.unlock("city_complete")
        elif level == 1:
            self.unlock("highway_complete")
        elif level == 2:
            self.unlock("circuit_complete")
            
        if not damage_taken:
            self.session_stats["level_damage"][level] = True
            # Vérifie si tous les niveaux complétés sans dégât
            if all(self.session_stats["level_damage"].values()):
                self.unlock("no_damage")
                
        if lives_remaining == 3:
            self.unlock("secret_perfect")
            
    def on_victory(self):
        """Appelé quand tous les niveaux sont complétés."""
        self.unlock("all_levels")
        self.unlock("first_steps")
        
    def on_game_over(self):
        """Appelé au game over."""
        self.unlock("first_steps")
        
    def on_speed_reached(self, speed_kmh: float):
        """Appelé quand une vitesse est atteinte."""
        if speed_kmh >= 350:
            self.unlock("speed_demon")
            
    def on_distance_traveled(self, distance: float):
        """Appelé quand de la distance est parcourue."""
        if distance >= 10000:
            self.unlock("marathon")
            
    def on_survival_time(self, seconds: float, level: int):
        """Appelé pour le temps de survie."""
        if level == 2 and seconds >= 60:
            self.unlock("survivor")
            
    def get_unlocked_count(self) -> int:
        """Retourne le nombre d'achievements débloqués."""
        return sum(1 for ach in self.achievements.values() if ach.unlocked)
        
    def get_total_count(self) -> int:
        """Retourne le nombre total d'achievements."""
        return len(self.achievements)
        
    def get_completion_percentage(self) -> float:
        """Retourne le pourcentage de complétion."""
        if not self.achievements:
            return 0.0
        return (self.get_unlocked_count() / self.get_total_count()) * 100
        
    def get_new_unlocks(self) -> List[Achievement]:
        """Récupère et vide la liste des nouveaux déblocages."""
        new = self.new_unlocks.copy()
        self.new_unlocks.clear()
        return new
        
    def get_achievements_by_tier(self) -> Dict[AchievementTier, List[Achievement]]:
        """Retourne les achievements groupés par tier."""
        result = {tier: [] for tier in AchievementTier}
        for ach in self.achievements.values():
            result[ach.tier].append(ach)
        return result
