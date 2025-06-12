import time
import threading
import numpy as np

class Calibrator:
    def __init__(self):
        self.ear_open = []
        self.ear_closed = []
        self.mar_closed = []
        self.mar_open = []
        self.pitch_straight = []
        self.pitch_down = []

        self.ear_threshold = None
        self.mar_threshold = None
        self.pitch_threshold = None
        self._collecting = False
        self._step = 0 
        self._on_done = None

    def start_ear_open_calibration(self, duration_s, get_metrics_callback, on_done=None):
        self.ear_open.clear()
        self._collecting = True
        self._step = 1
        self._on_done = on_done
        def _collect():
            start = time.time()
            while time.time() - start < duration_s:
                ear, _ = get_metrics_callback()
                if ear is not None:
                    self.ear_open.append(ear)
                time.sleep(0.05)
            self._collecting = False
            if self._on_done:
                self._on_done()
        threading.Thread(target=_collect, daemon=True).start()

    def start_ear_closed_calibration(self, duration_s, get_metrics_callback, on_done=None):
        self.ear_closed.clear()
        self._collecting = True
        self._step = 2
        self._on_done = on_done
        def _collect():
            start = time.time()
            while time.time() - start < duration_s:
                ear, _ = get_metrics_callback()
                if ear is not None:
                    self.ear_closed.append(ear)
                time.sleep(0.05)
            self._collecting = False
            if self._on_done:
                self._on_done()
        threading.Thread(target=_collect, daemon=True).start()

    def start_mar_closed_calibration(self, duration_s, get_metrics_callback, on_done=None):
        self.mar_closed.clear()
        self._collecting = True
        self._step = 3
        self._on_done = on_done
        def _collect():
            start = time.time()
            while time.time() - start < duration_s:
                _, mar = get_metrics_callback()
                if mar is not None:
                    self.mar_closed.append(mar)
                time.sleep(0.05)
            self._collecting = False
            if self._on_done:
                self._on_done()
        threading.Thread(target=_collect, daemon=True).start()

    def start_mar_open_calibration(self, duration_s, get_metrics_callback, on_done=None):
        self.mar_open.clear()
        self._collecting = True
        self._step = 4
        self._on_done = on_done
        def _collect():
            start = time.time()
            while time.time() - start < duration_s:
                _, mar = get_metrics_callback()
                if mar is not None:
                    self.mar_open.append(mar)
                time.sleep(0.05)
            self._collecting = False
            if self._on_done:
                self._on_done()
        threading.Thread(target=_collect, daemon=True).start()

    def compute_thresholds(self):
        if self.ear_open and self.ear_closed:
            mean_open = np.mean(self.ear_open)
            mean_closed = np.mean(self.ear_closed)
            self.ear_threshold = mean_closed + 0.6 * (mean_open - mean_closed)
        if self.mar_closed and self.mar_open:
            mean_mar_closed = np.mean(self.mar_closed)
            mean_mar_open = np.mean(self.mar_open)
            self.mar_threshold = mean_mar_closed + 0.6 * (mean_mar_open - mean_mar_closed)
