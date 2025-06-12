# test_perclos_graph.py
import sys
import os
import matplotlib.pyplot as plt
import numpy as np

# 🛠️ Fix importuri relative
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.insert(0, project_root)

from feature_extraction.perclos import PERCLOS

# Parametri simulare
window_s = 60
sample_rate_hz = 1.0
threshold_ear = 0.2

# Simulăm EAR: 30s deschis (0.3), 30s închis (0.15)
valori_ear = [0.3]*30 + [0.15]*30
timp = np.arange(len(valori_ear))

# Inițializare PERCLOS
p = PERCLOS(window_s=window_s, sample_rate_hz=sample_rate_hz)
istoric_perclos = []

# Procesare frame cu frame
for ear in valori_ear:
    p.update(ear, threshold_ear)
    istoric_perclos.append(p.compute())

# Verificare finală
perclos_final = istoric_perclos[-1]
if round(perclos_final, 2) == 50.0:
    print(f"✅ PAS: PERCLOS calculat corect: {perclos_final}%")
else:
    print(f"❌ EȘEC: PERCLOS incorect: {perclos_final}%")

# 🔍 GRAFIC cu axe duble
fig, ax1 = plt.subplots(figsize=(10, 5))

# EAR pe axa stângă
ax1.set_xlabel("Timp (secunde)")
ax1.set_ylabel("EAR", color='#0077cc')
ax1.plot(timp, valori_ear, color='#0077cc', linewidth=2, label="EAR")
ax1.axhline(threshold_ear, color='red', linestyle='--', label='Prag EAR')
ax1.fill_between(timp, 0, valori_ear, where=np.array(valori_ear)<threshold_ear, color='red', alpha=0.2, label='Ochi închiși')
ax1.tick_params(axis='y', labelcolor='#0077cc')

# Axa dreaptă: PERCLOS
ax2 = ax1.twinx()
ax2.set_ylabel("PERCLOS (%)", color='green')
ax2.plot(timp, istoric_perclos, color='green', linestyle='--', linewidth=2, label="PERCLOS (%)")
ax2.tick_params(axis='y', labelcolor='green')

# Titlu & Legende
fig.suptitle("Evoluția EAR și PERCLOS (60s, 1Hz)", fontsize=14)
fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.85))
fig.tight_layout()
plt.grid(True)
plt.show()