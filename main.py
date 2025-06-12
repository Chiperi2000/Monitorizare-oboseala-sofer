# main.py
import os
import yaml
from tkinter import messagebox

import gui.main_window
print(">>> GUI module is at:", gui.main_window.__file__)
# Asigură bază de lucru la calea scriptului, nu la cwd
base_dir = os.path.dirname(os.path.abspath(__file__))
print(">>> START main.py")
print("Base dir:", base_dir)

# Importuri de top-level
from capture.flir_camera import FlirCamera
print(">>> imported FlirCamera")
from feature_extraction.face_mesh import FaceMeshDetector
print(">>> imported FaceMeshDetector")
from decision.alert_logic import AlertLogic
print(">>> imported AlertLogic")
from gui.main_window import MainWindow
print(">>> imported MainWindow")
from feature_extraction.calibrator import Calibrator
print(">>> imported Calibrator")
from feature_extraction.perclos import PERCLOS
print(">>> imported Perclos")

# Încarcă fișierul de configurare
def load_config(config_path):
    print(">>> Încarc configurația…")
    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f)
    print(">>> Config:", cfg)
    return cfg


def main():
    print(">>> ENTER main()")    # **nou**
    # Path configurare și model relatate la base_dir
    config_path = os.path.join(base_dir, 'config', 'settings.yaml')
    config = load_config(config_path)

    # Inițializează componentele
    camera = FlirCamera()
    face_detector = FaceMeshDetector()

    # Instanțiere Calibrator pentru praguri adaptive
    calibrator = Calibrator()
    
    # Instanțiere PERCLOS pentru măsurarea procentului de ochi închiși
    perclos = PERCLOS(window_s=60, sample_rate_hz=20.0)

    # Inițializează logica de alertă
    ear_thresh = config['thresholds']['EAR']
    mar_thresh = config['thresholds']['MAR']
    pitch_thresh = config['thresholds']['PITCH']
    ear_frames = config['consecutive_frames']['EAR']
    mar_frames = config['consecutive_frames']['MAR']
    pitch_frames = config['consecutive_frames']['PITCH']
    alert_cooldown = config.get('alert_cooldown', 5)
    alert_logic = AlertLogic(
        ear_thresh, ear_frames,
        mar_thresh, mar_frames,
        pitch_thresh, pitch_frames,
        alert_cooldown,
        calibrator=calibrator
    )
    MainWindow(camera, face_detector, alert_logic, config, calibrator, perclos)

if __name__ == "__main__":
    main()
