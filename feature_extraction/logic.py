# logic.py
from enum import Enum

class FatigueRiskLevel(Enum):
    VERY_LOW  = (0, 20, 18, 22, "Foarte scăzut", "green")
    LOW       = (20,40, 38, 42, "Scăzut",        "limegreen")
    MODERATE  = (40,60, 58, 62, "Moderat",       "orange")
    HIGH      = (60,80, 78, 82, "Ridicat",       "orangered")
    CRITICAL  = (80,100,98,100,"Critic",        "red")

    def __init__(self, lo, hi, exit_lo, enter_hi, label, color):
        self.lo, self.hi       = lo, hi
        self.exit_lo, self.enter_hi = exit_lo, enter_hi
        self.label, self.color= label, color

    @classmethod
    def classify(cls, score, prev_level=None):
        # dacă avem nivel anterior, folosim exit_lo/enter_hi
        if prev_level:
            if score < prev_level.exit_lo:
                return next(l for l in cls if l.lo <= score < l.hi)
            for lvl in reversed(list(cls)):
                if score >= lvl.enter_hi:
                    return lvl
            return prev_level
        # la prima clasificare: lo≤score<hi
        return next((l for l in cls if l.lo <= score < l.hi), cls.CRITICAL)


class TrendLevel(Enum):
    UP_FAST   = ( 2.0,   float('inf'), "↑ Rapid", "darkgreen")
    UP_SLOW   = ( 0.5,   2.0,          "↑ Lent",  "green")
    STABLE    = (-0.5,   0.5,          "→ Stabil","grey")
    DOWN_SLOW = (-2.0,  -0.5,          "↓ Lent",  "orange")
    DOWN_FAST = ( float('-inf'), -2.0, "↓ Rapid", "red")

    def __init__(self, lo, hi, label, color):
        self.lo, self.hi = lo, hi
        self.label, self.color = label, color

    @classmethod
    def classify(cls, slope_per_sec: float):
        slope_per_min = slope_per_sec * 60
        for lvl in cls:
            if lvl.lo <= slope_per_min < lvl.hi:
                return lvl
        return cls.STABLE
