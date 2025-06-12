# test_microsleep_graph.py
import sys
import os
import matplotlib.pyplot as plt
import numpy as np

# 🛠️ Fix importuri relative
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.insert(0, project_root)

from feature_extraction.microsleep import MicroSleepDetector

# Simulare EAR: 5 normal, 8 sub prag, 7 normal
valori_ear = [0.3]*5 + [0.1]*8 + [0.3]*7
timp = list(range(len(valori_ear)))

# Inițializare detector
detector = MicroSleepDetector(threshold_time_s=1.5, fps=4)
prag_ear = 0.2

# Executare detecție pe fiecare frame
detectari = []
microsleep_detectat = False
for i, ear in enumerate(valori_ear):
    detectat = detector.update(ear, prag_ear)
    detectari.append(detectat)
    microsleep_detectat = microsleep_detectat or detectat

# ✅ Verificare logică
if microsleep_detectat:
    print("✅ PAS: Microsleep detectat corect")
else:
    print("❌ EȘEC: Microsleep NU a fost detectat")

# 🔍 GRAFIC
plt.figure(figsize=(10, 4))
plt.plot(timp, valori_ear, marker='o', label='EAR', color='navy')
plt.axhline(prag_ear, color='red', linestyle='--', label='Prag EAR = 0.2')
plt.fill_between(timp, 0, valori_ear, where=np.array(valori_ear)<prag_ear, color='red', alpha=0.2, label='Sub prag')

for i, detected in enumerate(detectari):
    if detected:
        plt.axvline(i, color='black', linestyle=':', label='Microsleep detectat' if i == detectari.index(True) else None)

plt.title("Detectarea microsomnului prin EAR (MicroSleepDetector)")
plt.xlabel("Timp (frame-uri, FPS=4)")
plt.ylabel("EAR")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()