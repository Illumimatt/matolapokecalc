import math
from typing import Dict, Optional

ALL_NATURES = {
    "Adamant": {"up": "atk", "down": "spa"},
    "Bashful": {"up": None, "down": None},
    "Bold":    {"up": "def", "down": "atk"},
    "Brave":   {"up": "atk", "down": "spe"},
    "Calm":    {"up": "spd", "down": "atk"},
    "Careful": {"up": "spd", "down": "spa"},
    "Docile":  {"up": None, "down": None},
    "Gentle":  {"up": "spd", "down": "def"},
    "Hardy":   {"up": None, "down": None},
    "Hasty":   {"up": "spe", "down": "def"},
    "Impish":  {"up": "def", "down": "spa"},
    "Jolly":   {"up": "spe", "down": "spa"},
    "Lax":     {"up": "def", "down": "spd"},
    "Lonely":  {"up": "atk", "down": "def"},
    "Mild":    {"up": "spa", "down": "def"},
    "Modest":  {"up": "spa", "down": "atk"},
    "Naive":   {"up": "spe", "down": "spd"},
    "Naughty": {"up": "atk", "down": "spd"},
    "Quiet":   {"up": "spa", "down": "spe"},
    "Quirky":  {"up": None, "down": None},
    "Rash":    {"up": "spa", "down": "spd"},
    "Relaxed": {"up": "def", "down": "spe"},
    "Sassy":   {"up": "spd", "down": "spe"},
    "Serious": {"up": None, "down": None},
    "Timid":   {"up": "spe", "down": "atk"},
}

def get_nature_multiplier(nature_name: str, stat_name: str) -> float:
    if stat_name == 'hp': return 1.0
    nature_data = ALL_NATURES.get(nature_name)
    if not nature_data: return 1.0
    if nature_data['up'] == stat_name: return 1.1
    if nature_data['down'] == stat_name: return 0.9
    return 1.0

def calculate_stat(base: int, iv: int, ev: int, level: int, nature_mod: float, is_hp: bool = False) -> int:
    if ev > 252: ev = 252
    if iv > 31: iv = 31
    if ev < 0: ev = 0
    if iv < 0: iv = 0
    core_value = (2 * base + iv + (ev // 4)) * level / 100
    if is_hp:
        if base == 1: return 1 
        result = core_value + level + 10
    else:
        result = (core_value + 5) * nature_mod
    return math.floor(result)

def get_ev_from_target_stat(target_stat: int, base: int, iv: int, level: int, nature_mod: float, is_hp: bool) -> int:
    if level == 0: return 0
    if is_hp:
        val_step1 = target_stat - level - 10
    else:
        val_step1 = (target_stat / nature_mod) - 5
        if nature_mod < 1.0: 
             val_step1 = math.ceil(target_stat / nature_mod) - 5
    core_needed = (val_step1 * 100) / level
    ev_needed = (core_needed - (2 * base) - iv) * 4

    return math.ceil(ev_needed)