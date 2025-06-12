# feature_extraction/ear.py
"""
Modul pentru calculul Eye Aspect Ratio (EAR) utilizat la detectarea clipitului.
"""
import math

# Indici pentru landmark-urile ochilor (MediaPipe Face Mesh)
LEFT_EYE_INDEXES = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_INDEXES = [362, 385, 387, 263, 373, 380]

def calculate_ear(landmarks, eye_indexes, width, height):
    coords = []
    for i in eye_indexes:
        lm = landmarks[i]
        x, y = int(lm.x * width), int(lm.y * height)
        coords.append((x, y))
    # Calculează distanțe euclidiene
    def dist(a, b):
        return math.hypot(a[0] - b[0], a[1] - b[1])
    # Puncte: orizontal (P1-P4) și vertical (P2-P6, P3-P5)
    P1_P4 = dist(coords[0], coords[3])
    P2_P6 = dist(coords[1], coords[5])
    P3_P5 = dist(coords[2], coords[4])
    # Evităm împărțirea la 0
    if P1_P4 == 0:
        return 0.0
    ear = (P2_P6 + P3_P5) / (2.0 * P1_P4)
    return ear
