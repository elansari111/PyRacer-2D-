# PyRacer: Ultimate Neon Highway - Enhanced Edition v2.0

Jeu de course arcade 2D top-down — Python / Pygame  
Projet étudiant — Compétition 2026

**Version 2.0** - Système audio procédural, météo dynamique, achievements, personnalisation, et plus encore !

---

## Installation

```bash
pip install pygame
```

## Lancement

```bash
cd PyRacer/
python main.py
```

## Contrôles

| Touche         | Action                        |
|----------------|-------------------------------|
| ← / → (ou A/D) | Déplacement latéral           |
| ↑ (ou W)       | Accélérer                     |
| ↓ (ou S)       | Freiner                       |
| ESPACE         | Activer le Nitro              |
| B              | Activer le Bouclier           |
| P              | Pause / Reprendre             |
| ENTRÉE         | Valider (menus / transition)  |

## Structure du projet

```
PyRacer/
├── main.py              # Point d'entrée, boucle principale, delta-time
├── car.py               # Classe Player : contrôles, physique, animation
├── enemy.py             # Classe Enemy + EnemySpawner : 4 types de comportements
├── road.py              # Route défilante, voies, décor parallaxe, obstacles
├── bonus.py             # Bonus + BonusManager : spawn, collecte, effets
├── score.py             # ScoreManager : hiérarchie, multiplicateurs, streak, JSON
├── hud.py               # HUD : score, vies, jauges, popups, flash
├── game_states.py       # State (enum) + ScreenRenderer : tous les écrans
├── settings.py          # Toutes les constantes globales
├── visual_effects.py    # Effets visuels avancés (néon, particules, glow)
├── score.json           # Sauvegarde automatique des meilleurs scores
└── assets/              # (sprites, sons, fonts à ajouter)
```

## Niveaux

| Niveau       | Objectif                          | Difficulté  |
|-------------|-----------------------------------|-------------|
| VILLE        | Atteindre 3 000 pts               | ★★☆         |
| AUTOROUTE    | Effectuer 20 dépassements         | ★★★         |
| CIRCUIT      | Survivre 90 secondes              | ★★★★        |

## Types d'adversaires

| Type          | Comportement                                       |
|---------------|----------------------------------------------------|
| Standard      | Tient sa voie, rare changement de voie lent        |
| Rapide        | Accélérations soudaines, peut dépasser le joueur   |
| Camion        | Très lent, large, bloque les trajectoires          |
| Imprévisible  | Changements de voie fréquents et aléatoires        |

## Bonus

| Bonus    | Effet                                       |
|----------|---------------------------------------------|
| ⚡ Nitro  | +40 jauge, activation = ×2 score + vitesse  |
| 🛡 Bouclier | +40 jauge, absorbe 1 collision             |
| ❤ Vie    | +1 vie (max 3)                              |
| ⏱ Slow   | Trafic ralenti 3 secondes                   |

## Système de score

```
Dépassement Nitro   → +150 pts  (priorité max)
Streak actif        → ×(1 + streak×0.05) multiplicateur
Dépassement normal  → +50 pts
Collecte bonus      → +100 pts
Survie              → +vitesse×0.04 pts/frame
```

---

## Nouveautés v2.0

### 🎵 Système Audio Procédural
- Moteur de son procédural généré en temps réel (pas de fichiers audio externes)
- Sons de moteur adaptatifs selon la vitesse
- Effets sonores : crash, nitro, bonus, dépassements
- Musique de fond procédurale
- Contrôle du volume indépendant (Master/Musique/SFX)

### 🌦️ Effets Météo
- **Pluie** : Gouttes animées avec effet de parallaxe
- **Tempête** : Éclairs et vent
- **Brouillard** : Gradient atmosphérique
- Chaque niveau a sa météo par défaut

### 🏆 Système de Succès (Achievements)
35+ achievements à débloquer :
- **Bronze/Argent/Or/Platine** selon la difficulté
- Succès de score, dépassements, streaks
- Succès secrets à découvrir
- Sauvegarde persistante de la progression

### 🎨 Personnalisation
- **8 couleurs de voiture** : Cyan, Magenta, Jaune, Vert, Rouge, Violet, Orange, Blanc
- Configuration persistante dans `config.json`

### 🗺️ Minimap/Radar
- Affichage temps réel des ennemis
- Différenciation visuelle par type d'ennemi
- Position du joueur et champ de vision

### ⚡ Nouveaux Bonus
| Bonus | Effet |
|-------|-------|
| 🧲 Magnet | Attire automatiquement les bonus |
| 👻 Ghost | Traverser les ennemis sans collision |
| ❄️ Time Freeze | Ralentit le temps pendant 2 secondes |

### ⚙️ Menu Paramètres
- Audio (on/off, volumes)
- Difficulté (Facile/Normal/Difficile)
- Couleur de voiture
- Sauvegarde automatique

### ✨ Effets Visuels Avancés (v2.0)
- **Système de particules physiques** : Étincelles, fumée, feu, trails
- **Effets Néon dynamiques** : Lueurs, glows, halos
- **Rendu avancé des voitures** : Ombres, inclinaison, détails
- **Effets d'écran** : Shake, flash, vignette
- **Animations fluides** : Transitions, pulsations
- **Aura "Ghost" spectrale** avec effet de fantôme
- **Notifications d'achievements** animées

---

## Fichiers de Configuration

| Fichier | Description |
|---------|-------------|
| `config.json` | Paramètres utilisateur (audio, difficulté, couleur) |
| `score.json` | Meilleurs scores par niveau |
| `achievements.json` | Progression des succès |
| `visual_effects.py` | Système d'effets visuels avancés (néon, particules, glow) |

---

## Architecture Étendue

```
PyRacer/
├── main.py              # Point d'entrée (version enhance)
├── sound_manager.py     # Gestion audio procédurale
├── weather.py           # Système météo + particules avancées
├── achievements.py      # Système de succès
├── config.py            # Configuration persistante
├── car.py               # Classe Player (personnalisation ajoutée)
├── bonus.py             # Nouveaux bonus types
├── hud.py               # Minimap + notifications
├── game_states.py       # Menu paramètres + achievements
├── visual_effects.py    # Système d'effets visuels avancés
└── ... (modules originaux)
```
