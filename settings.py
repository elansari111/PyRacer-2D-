# ============================================================
#  PyRacer: Ultimate Neon Highway
#  settings.py — Constantes globales
# ============================================================

import pygame

# --- Fenêtre ---
SCREEN_W   = 900
SCREEN_H   = 700
FPS        = 60
TITLE      = "PyRacer: Ultimate Neon Highway"

# --- Route ---
ROAD_WIDTH   = 420
ROAD_X       = (SCREEN_W - ROAD_WIDTH) // 2
LANE_COUNT   = [3, 4, 3]   # par niveau

# --- Voiture joueur ---
PLAYER_W     = 36
PLAYER_H     = 58
PLAYER_SPEED = 6.0          # déplacement latéral (px/frame)

# --- Vitesses ---
BASE_SPEED    = [3.5, 5.0, 6.5]    # vitesse initiale par niveau
MAX_SPEED     = [7.0, 10.0, 13.0]  # vitesse max par niveau
ACCEL_RATE    = 0.06
BRAKE_RATE    = 0.08

# --- Nitro ---
NITRO_MAX         = 100
NITRO_COST        = 40          # consommation par activation
NITRO_REGEN       = 0.15        # par frame
NITRO_MULT        = 1.8         # multiplicateur de vitesse
NITRO_DURATION    = 90          # frames
NITRO_SCORE_MULT  = 2.0

# --- Bouclier ---
SHIELD_MAX      = 100
SHIELD_COST     = 30
SHIELD_REGEN    = 0.0           # se recharge via dépassements
SHIELD_DURATION = 120           # frames
SHIELD_OVERTAKE = 8             # recharge par dépassement

# --- Invincibilité après collision ---
INV_DURATION = 120              # frames

# --- Ennemis ---
# Types : 0=standard, 1=rapide, 2=camion, 3=imprévisible
ENEMY_TYPES_BY_LEVEL = [
    [0, 0, 1, 2],        # Ville
    [0, 1, 1, 3],        # Autoroute
    [0, 1, 2, 3, 3],     # Circuit
]
ENEMY_SIZES = [
    (32, 52),   # standard
    (28, 50),   # rapide
    (36, 68),   # camion
    (30, 50),   # imprévisible
]
ENEMY_SPEED_MULT = [0.65, 1.35, 0.40, 0.80]   # ×vitesse_joueur
SPAWN_INTERVAL   = [90, 65, 48]                # frames entre spawns
SPAWN_INTERVAL_MIN = 28                         # plancher de difficulté

# --- Bonus ---
BONUS_SIZE        = 36
BONUS_SPEED_MULT  = 0.4        # vitesse du bonus vs route
BONUS_SPAWN_PROB  = 0.002      # probabilité par frame
BONUS_TYPES       = ["nitro", "shield", "life", "slow"]
BONUS_WEIGHTS     = [50, 30, 10, 10]
BONUS_NITRO_ADD   = 40
BONUS_SHIELD_ADD  = 40
BONUS_SLOW_FACTOR = 0.6
BONUS_SLOW_DURATION = 180      # frames
BONUS_SCORE       = 100

# --- Score ---
SCORE_PER_SECOND   = 1.0
SCORE_OVERTAKE     = 50
SCORE_OVERTAKE_NITRO = 150
STREAK_MIN         = 3         # streak affiché à partir de
STREAK_BONUS       = 0.02      # pts/frame × streak
SCORE_BONUS_COLLECT = 100

# --- Objectifs par niveau ---
LEVEL_NAMES      = ["VILLE", "AUTOROUTE", "CIRCUIT"]
LEVEL_COLORS     = [(0, 229, 255), (255, 77, 206), (255, 215, 0)]
TARGET_SCORE     = 3000        # Niveau 1
TARGET_OVERTAKES = 20          # Niveau 2
SURVIVE_TIME     = 90          # secondes, Niveau 3

# --- Vies ---
MAX_LIVES = 3

# --- Couleurs (R,G,B) ---
C_BG          = (5,   5,  15)
C_ROAD        = [(26, 26, 46), (21, 21, 40), (26, 16,  5)]
C_LANE        = [(255,255,255, 24), (255,255,255,21), (255,255,255,24)]
C_EDGE_GLOW   = [(0,229,255), (255,77,206), (255,215,0)]
C_BUILDING    = [(13, 13, 26), (8, 8, 24), (18, 10, 2)]
C_WHITE       = (255, 255, 255)
C_CYAN        = (0,   229, 255)
C_MAGENTA     = (255,  77, 206)
C_YELLOW      = (255, 215,   0)
C_PURPLE      = (168, 139, 250)
C_RED         = (255,  68,  68)
C_GREEN       = (74,  222, 128)
C_GRAY        = (120, 120, 130)
C_DARK        = (15,  15,  30)

ENEMY_COLORS  = [
    (255, 107,  53),   # standard  — orange
    (255,  23,  68),   # rapide    — rouge vif
    (136, 136, 153),   # camion    — gris
    (168, 85,  247),   # imprévisible — violet
]

BONUS_COLORS = {
    "nitro":  (255, 215,   0),
    "shield": (  0, 229, 255),
    "life":   (255,  77, 206),
    "slow":   (168,  85, 247),
}
BONUS_ICONS = {
    "nitro":  "⚡",
    "shield": "🛡",
    "life":   "❤",
    "slow":   "⏱",
}

# --- Chemins assets ---
FONT_TITLE  = None   # remplacer par chemin .ttf si disponible
FONT_HUD    = None
SCORE_FILE  = "score.json"

# ============================================================
#  ENHANCED FEATURES - v2.0
# ============================================================

# --- Audio ---
AUDIO_ENABLED = True
AUDIO_FREQ = 44100
AUDIO_BUFFER = 512

# --- Weather ---
WEATHER_TYPES = ["clear", "rain", "storm", "fog"]
WEATHER_BY_LEVEL = ["clear", "rain", "storm"]  # Météo par défaut par niveau
RAIN_DROP_COUNT = 300

# --- Minimap ---
MINIMAP_W = 120
MINIMAP_H = 80
MINIMAP_X = SCREEN_W - MINIMAP_W - 10
MINIMAP_Y = 100

# --- New Bonus Types ---
BONUS_TYPES_EXTENDED = ["nitro", "shield", "life", "slow", "magnet", "ghost", "time_freeze"]
BONUS_WEIGHTS_EXTENDED = [40, 25, 8, 8, 8, 6, 5]

BONUS_MAGNET_DURATION = 300      # frames
BONUS_MAGNET_RANGE = 150         # pixels
BONUS_GHOST_DURATION = 180       # frames (traverser les ennemis)
BONUS_TIME_FREEZE_DURATION = 120 # frames

BONUS_COLORS_EXTENDED = {
    "nitro":       (255, 215,   0),
    "shield":      (  0, 229, 255),
    "life":        (255,  77, 206),
    "slow":        (168,  85, 247),
    "magnet":      (255, 140,   0),  # Orange
    "ghost":       (128, 128, 128),  # Gris spectral
    "time_freeze": (255, 255, 255),  # Blanc
}

BONUS_ICONS_EXTENDED = {
    "nitro":       "⚡",
    "shield":      "🛡",
    "life":        "❤",
    "slow":        "⏱",
    "magnet":      "🧲",
    "ghost":       "👻",
    "time_freeze": "❄️",
}

# --- Car Customization ---
CAR_COLORS = {
    "cyan":     (0, 229, 255),
    "magenta":  (255, 77, 206),
    "yellow":   (255, 215, 0),
    "green":    (74, 222, 128),
    "red":      (255, 68, 68),
    "purple":   (168, 139, 250),
    "orange":   (255, 107, 53),
    "white":    (232, 244, 253),
}

# --- Visual Effects ---
SCREEN_SHAKE_MAX = 20.0
SCREEN_SHAKE_DECAY = 0.9
TRAIL_LENGTH = 8
GLOW_INTENSITY = 1.2

# --- Advanced Scoring ---
COMBO_TIMEOUT = 120  # frames avant reset du combo
PERFECT_OVERTAKE_BONUS = 25  # Bonus sans collision proche

# --- Distance Tracking ---
PIXELS_TO_METERS = 0.1  # Conversion pixels -> mètres
