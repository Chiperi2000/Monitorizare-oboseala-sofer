# feature_extraction/pitch.py
"""
Modul pentru calculul înclinării capului (head pitch).
"""
import numpy as np
import math

def calculate_head_pitch(landmarks, width, height):
    """
    Calculează unghiul pitch (înclinare cap sus/jos) ca unghi față de verticală.
    Un cap drept = 0–15°, cap plecat = >30°.
    """
    nose = landmarks[1]      # vârful nasului
    chin = landmarks[152]    # bărbia

    x1, y1 = nose.x * width, nose.y * height
    x2, y2 = chin.x * width, chin.y * height

    # Vector între cele două puncte
    dx = x2 - x1
    dy = y2 - y1

    # Unghi față de verticală
    vertical_dx, vertical_dy = 0, 1
    dot_product = dx * vertical_dx + dy * vertical_dy
    magnitude1 = math.sqrt(dx ** 2 + dy ** 2)
    magnitude2 = 1  # vertical vector este [0, 1], deci lungimea e 1

    if magnitude1 == 0:
        return 0  # evităm împărțirea la 0

    cos_angle = dot_product / (magnitude1 * magnitude2)
    cos_angle = max(-1.0, min(1.0, cos_angle))  # corectare valori aberante

    angle_rad = math.acos(cos_angle)
    angle_deg = math.degrees(angle_rad)

    return angle_deg