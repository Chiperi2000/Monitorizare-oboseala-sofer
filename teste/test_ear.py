# test_ear_graph.py
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

# Simulăm EAR: 5 normal, 10 sub prag, 5 normal
valori_ear = [0.30]*5 + [0.20]*10 + [0.28]*5
valori_mar = [0.1]*20  # fără căscat
valori_pitch = [10.0]*20  # fără cap plecat

timp = list(range(len(valori_ear)))
evenimente = []

# Executăm logica reală pe fiecare frame
for i in range(20):
    ev = logica.evaluate(
        ear=valori_ear[i],
        mar=valori_mar[i],
        pitch=valori_pitch[i],
        distract_detected=False
    )
    evenimente.append("ochi_inchisi" in ev)

# ✅ Confirmare logică
if any(evenimente[5:15]) and evenimente.count(True) >= 1:
    print("✅ PAS: AlertLogic a declanșat corect alerta de oboseală (ochi_inchisi)")
else:
    print("❌ EȘEC: AlertLogic NU a declanșat alerta corect")

# 🔍 Grafic
plt.figure(figsize=(10, 4))
plt.plot(timp, valori_ear, marker='o', label='EAR')
plt.axhline(0.25, color='r', linestyle='--', label='Prag EAR = 0.25')
plt.fill_between(timp, 0, valori_ear, where=np.array(valori_ear)<0.25, color='red', alpha=0.3, label='Sub prag')

# Marcăm alertele
for i, ev in enumerate(evenimente):
    if ev:
        plt.plot(i, valori_ear[i], 'ko', markersize=8, label='Alertă' if i == evenimente.index(True) else None)

plt.title("Grafic simulare alerta EAR")
plt.xlabel("Timp (frame-uri)")
plt.ylabel("EAR")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
