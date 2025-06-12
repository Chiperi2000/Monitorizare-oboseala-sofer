# test_pitch_graph.py
import sys
import os

# 🔧 Import fix
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.insert(0, project_root)

import matplotlib.pyplot as plt
import numpy as np
from decision.alert_logic import AlertLogic

# Inițializare AlertLogic
logica = AlertLogic(
    ear_thresh=0.25, ear_frames=3,
    mar_thresh=0.5, mar_frames=3,
    pitch_thresh=20, pitch_frames=2,
    alert_cooldown=0
)

# Simulare: pitch 10°, apoi 35°, apoi 10°
valori_pitch = [10.0]*5 + [35.0]*10 + [10.0]*5
valori_ear = [0.3]*20  # fără clipit
valori_mar = [0.3]*20  # fără căscat

timp = list(range(len(valori_pitch)))
evenimente = []

# Evaluare pe fiecare frame
for i in range(20):
    ev = logica.evaluate(
        ear=valori_ear[i],
        mar=valori_mar[i],
        pitch=valori_pitch[i],
        distract_detected=False
    )
    evenimente.append("cap_plecat" in ev)

# ✅ Verificare logică
if any(evenimente[5:15]) and evenimente.count(True) >= 1:
    print("✅ PAS: AlertLogic a detectat corect 'cap_plecat'")
else:
    print("❌ EȘEC: AlertLogic NU a detectat înclinarea capului")

# 📊 Grafic pitch
plt.figure(figsize=(10, 4))
plt.plot(timp, valori_pitch, marker='^', label='Pitch (°)')
plt.axhline(20, color='purple', linestyle='--', label='Prag Pitch = 20°')
plt.fill_between(timp, 0, valori_pitch, where=np.array(valori_pitch)>20, color='purple', alpha=0.2, label='Peste prag')

for i, ev in enumerate(evenimente):
    if ev:
        plt.plot(i, valori_pitch[i], 'ko', markersize=8, label='Alertă' if i == evenimente.index(True) else None)

plt.title("Grafic simulare alerta 'cap înclinat'")
plt.xlabel("Timp (frame-uri)")
plt.ylabel("Pitch (grade)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()