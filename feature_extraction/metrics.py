# metrics.py
from math import fabs

def clamp(x: float) -> float:
    return max(0.0, min(1.0, x))

def normalize_ear(ear: float, ref: float = 0.30, min_val: float = 0.10) -> float:
    return clamp((ref - ear) / (ref - min_val))

def normalize_mar(mar: float, ref: float = 0.30, max_val: float = 0.60) -> float:
    return clamp((mar - ref) / (max_val - ref))

def normalize_perclos(perclos_pct: float,
                      min_val_pct: float = 0.0,
                      max_val_pct: float = 80.0) -> float:
    x = float(perclos_pct)
    if x <= min_val_pct:
        return 1.0
    if x >= max_val_pct:
        return 0.0
    return 1.0 - (x - min_val_pct) / (max_val_pct - min_val_pct)


def normalize_micro(micro_count: int, max_count: int = 5) -> float:
    return clamp(micro_count / max_count)

def normalize_pitch(pitch: float, max_deg: float = 20.0) -> float:
    return clamp(fabs(pitch) / max_deg)
