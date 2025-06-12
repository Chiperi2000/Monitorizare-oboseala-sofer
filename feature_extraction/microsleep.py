# feature_extraction/microsleep.py

class MicroSleepDetector:
    def __init__(self, threshold_time_s, fps):
        self.threshold_frames = int(threshold_time_s * fps)
        self.frames = 0
        self.active = False
        self.count = 0

    def update(self, ear, ear_threshold):
        if ear < ear_threshold:
            self.frames += 1
            if self.frames >= self.threshold_frames and not self.active:
                self.active = True
                self.count += 1
                return True  
        else:
            self.frames = 0
            self.active = False
        return False  
