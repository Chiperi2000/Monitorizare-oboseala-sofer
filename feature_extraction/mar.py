# feature_extraction/mar.py
"""
Modul pentru calculul Mouth Aspect Ratio (MAR) utilizat la detectarea căscatului.
"""
import math

def calculate_mar(landmarks, width, height):
    # Puncte 13-14: vertical; 61-291: orizontal
    x1, y1 = landmarks[61].x * width, landmarks[61].y * height
    x2, y2 = landmarks[291].x * width, landmarks[291].y * height
    x3, y3 = landmarks[13].x * width, landmarks[13].y * height
    x4, y4 = landmarks[14].x * width, landmarks[14].y * height

    horizontal = math.hypot(x1 - x2, y1 - y2)
    vertical = math.hypot(x3 - x4, y3 - y4)

    if horizontal == 0:
        return 0.0
    mar = vertical / horizontal
    return mar
