# test_mar_graph.py
import sys
import os

# 🛠️ Fix pentru imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.insert(0, project_root)

import matplotlib.pyplot as plt
import numpy as np
from decision.alert_logic import AlertLogic

# Inițializare AlertLogic cu praguri fixe
logica = AlertLogic(
    ear_thresh=0.25, ear_frames=3,
    mar_thresh=0.5, mar_frames=3,
    pitch_thresh=20, pitch_frames=2,
    alert_cooldown=0
)

# Simulare MAR: 5 normal, 10 căscat, 5 normal
valori_mar = [0.3]*5 + [0.6]*10 + [0.3]*5
valori_ear = [0.3]*20  # fără clipit
valori_pitch = [10.0]*20  # fără cap plecat

timp = list(range(len(valori_mar)))
evenimente = []

# Evaluăm fiecare frame
for i in range(20):
    ev = logica.evaluate(
        ear=valori_ear[i],
        mar=valori_mar[i],
        pitch=valori_pitch[i],
        distract_detected=False
    )
    evenimente.append("cascat" in ev)

# ✅ Verificare
if any(evenimente[5:15]) and evenimente.count(True) >= 1:
    print("✅ PAS: AlertLogic a detectat corect evenimentul 'cascat'")
else:
    print("❌ EȘEC: Nu a fost detectat 'cascat'")

# 🔍 Grafic MAR
plt.figure(figsize=(10, 4))
plt.plot(timp, valori_mar, marker='s', label='MAR')
plt.axhline(0.5, color='orange', linestyle='--', label='Prag MAR = 0.5')
plt.fill_between(timp, 0, valori_mar, where=np.array(valori_mar)>0.5, color='orange', alpha=0.3, label='Peste prag')

for i, ev in enumerate(evenimente):
    if ev:
        plt.plot(i, valori_mar[i], 'ko', markersize=8, label='Alertă' if i == evenimente.index(True) else None)

plt.title("Grafic simulare alerta MAR")
plt.xlabel("Timp (frame-uri)")
plt.ylabel("MAR")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
