import time
import numpy as np
import threading

class CalibratorFull:
    STATE_ORDER = ['alert', 'moderate', 'tired']

    def __init__(self):
        self.data = {state: [] for state in self.STATE_ORDER}
        self.thresholds = {}
        self.weights = {}
        self.metrics_names = ["ear", "mar", "perclos", "pitch"]
        self.metric_indices = {name: i for i, name in enumerate(self.metrics_names)}
        self.pitch_baseline = 0.0
        self.system_start_time = time.time()
        self.last_scores = []
        self.max_score_buffer = 5
        self.MIN_PERCLOS_LEN = 10

    def start_collect(self, state, duration_sec, metrics_callback, on_done=None, interval_sec=1.0):
        def collect():
            start_time = time.time()
            samples = []
            while time.time() - start_time < duration_sec:
                values = metrics_callback()
                if values is not None:
                    samples.append(values)
                time.sleep(interval_sec)
            self.data[state].extend(samples)
            print(f"[CALIBRATOR] Collected {len(samples)} samples for state: {state}")
            if on_done:
                on_done()

        threading.Thread(target=collect, daemon=True).start()

    def _get_metric_avg(self, state, metric):
        idx = self.metric_indices[metric]
        if state not in self.data or not self.data[state]:
            return 0.0
        return float(np.nanmean([row[idx] for row in self.data[state]]))

    def _normalize_score(self, val, baseline, target):
        if target == baseline:
            return 0.0
        return np.clip((val - baseline) / (target - baseline), 0, 1)

    def compute_thresholds_and_weights(self):
        thresholds = {}
        weights = {}
        changes = []

        for metric in self.metrics_names:
            idx = self.metric_indices[metric]
            enter_hi = self._get_metric_avg('moderate', metric)
            exit_lo = self._get_metric_avg('alert', metric)
            thresholds[metric] = {'enter_hi': enter_hi, 'exit_lo': exit_lo}

            tired_vals = [row[idx] for row in self.data['tired']]
            alert_vals = [row[idx] for row in self.data['alert']]
            combined_vals = tired_vals + alert_vals
            std = np.std(combined_vals) or 1e-5

            mean_tired = np.mean(tired_vals)
            mean_alert = np.mean(alert_vals)
            z_delta = abs(mean_tired - mean_alert) / std
            changes.append(z_delta)

        change_sum = sum(changes) or 1.0
        for metric, delta in zip(self.metrics_names, changes):
            weights[metric] = delta / change_sum

        self.thresholds = thresholds
        self.weights = weights
        self.pitch_baseline = self._get_metric_avg('alert', 'pitch')

        print("[ADV] thresholds and weights computed")
        print(f"[ADV] pitch_baseline = {self.pitch_baseline:.2f}")

    def score_state(self, values):
        if time.time() - self.system_start_time < 5.0:
            return 0.0

        score = 0
        for metric in self.metrics_names:
            idx = self.metric_indices[metric]
            val = values[idx]

            if metric == 'pitch':
                val = max(0.0, val - self.pitch_baseline)
            if metric == 'perclos':
                val = min(val, 100.0)
                if hasattr(self, 'perclos_buffer') and len(self.perclos_buffer) < self.MIN_PERCLOS_LEN:
                    val = 0.0
            if metric == 'mar' and val < 0.01:
                val = 0.0

            t = self.thresholds[metric]
            w = self.weights[metric]

            baseline = min(t['enter_hi'], t['exit_lo'])
            target = max(t['enter_hi'], t['exit_lo'])
            normalized = self._normalize_score(val, baseline, target)

            score += w * normalized

        self.last_scores.append(score)
        if len(self.last_scores) > self.max_score_buffer:
            self.last_scores.pop(0)
        return float(np.mean(self.last_scores))

    def set_custom_config(self, config):
        self.thresholds = config["thresholds"]
        self.weights = config["weights"]
        self.metrics_names = config["metrics_names"]
        self.metric_indices = {name: i for i, name in enumerate(self.metrics_names)}
        self.pitch_baseline = self._get_metric_avg('alert', 'pitch')

    def get_advanced_config(self):
        return {
            'thresholds': self.thresholds,
            'weights': self.weights,
            'metrics_names': self.metrics_names
        }

    def reset(self):
        self.__init__()
