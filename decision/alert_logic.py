# decision/alert_logic.py
"""
Modul pentru logica de detectare a stării de oboseală și distragere.
"""
import time

class AlertLogic:
    def __init__(self, ear_thresh, ear_frames, mar_thresh, mar_frames,
                pitch_thresh, pitch_frames, alert_cooldown, calibrator=None):
        # Praguri
        self.ear_threshold = ear_thresh
        self.mar_threshold = mar_thresh
        self.pitch_threshold = pitch_thresh

        self.calibrator = calibrator

        self.ear_consec_frames = ear_frames
        self.mar_consec_frames = mar_frames
        self.pitch_consec_frames = pitch_frames
        self.alert_cooldown = alert_cooldown

        self.sleep_eye_frames = 0
        self.yawn_frames = 0
        self.pitch_frames = 0
        self.last_alert_time = 0
        self.pitch_high_since = None 

    def evaluate(self, ear, mar, pitch, distract_detected):
        ear_thr_yaml = self.ear_threshold
        ear_thr_calib = None
        if self.calibrator and getattr(self.calibrator, "ear_threshold", None) is not None:
            ear_thr_calib = self.calibrator.ear_threshold
        ear_thr = ear_thr_calib if ear_thr_calib is not None else ear_thr_yaml

        # MAR threshold: fallback = din yaml, altfel calibrator
        mar_thr_yaml = self.mar_threshold
        mar_thr_calib = None
        if self.calibrator and getattr(self.calibrator, "mar_threshold", None) is not None:
            mar_thr_calib = self.calibrator.mar_threshold
        mar_thr = mar_thr_calib if mar_thr_calib is not None else mar_thr_yaml

        # Pitch threshold: fallback = din yaml, altfel calibrator
        pitch_thr_yaml = self.pitch_threshold
        pitch_thr_calib = None
        if self.calibrator and getattr(self.calibrator, "pitch_threshold", None) is not None:
            pitch_thr_calib = self.calibrator.pitch_threshold
        pitch_thr = pitch_thr_calib if pitch_thr_calib is not None else pitch_thr_yaml

        print(
            f"[DEBUG THRESHOLDS] EAR={ear:.3f} (yaml={ear_thr_yaml:.3f}, calib={ear_thr_calib}), "
            f"MAR={mar:.3f} (yaml={mar_thr_yaml:.3f}, calib={mar_thr_calib}), "
            f"Pitch={pitch:.1f} (yaml={pitch_thr_yaml:.1f}, calib={pitch_thr_calib})"
        )
        print(
            f"[DEBUG USED] ear_thr={ear_thr:.3f}, mar_thr={mar_thr:.3f}, pitch_thr={pitch_thr:.1f}"
        )
        events = []
        current_time = time.time()

        # Respectăm cooldown-ul dintre alerte
        if current_time - self.last_alert_time < self.alert_cooldown:
            return events  # Încă în cooldown, nu generăm evenimente noi

        # — OCHI ÎNCHIȘI (folosim prag dinamic dacă există)
        ear_thr = (self.calibrator.ear_threshold
                   if self.calibrator and self.calibrator.ear_threshold is not None
                   else self.ear_threshold)
        if ear < ear_thr:
            self.sleep_eye_frames += 1
        else:
            self.sleep_eye_frames = 0

        if self.sleep_eye_frames >= self.ear_consec_frames:
            events.append("ochi_inchisi")

            # — CĂSCAT (folosim prag dinamic dacă există)
        mar_thr = (self.calibrator.mar_threshold
                   if self.calibrator and self.calibrator.mar_threshold is not None
                   else self.mar_threshold)
        if mar > mar_thr:
            self.yawn_frames += 1
        else:
            self.yawn_frames = 0

        if self.yawn_frames >= self.mar_consec_frames:
            events.append("cascat")

        # CAP ÎNCLINAT (plecat)
        if pitch > self.pitch_threshold:
            if self.pitch_high_since is None:
                self.pitch_high_since = time.time()
            elif time.time() - self.pitch_high_since > 2.0:
                events.append("cap_plecat")
        else:
            self.pitch_high_since = None

        # Dacă avem evenimente, actualizăm timpul ultimei alerte
        if events:
            self.last_alert_time = current_time

        return events
