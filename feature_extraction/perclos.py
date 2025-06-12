import collections
import time

class PERCLOS:
    """
    Calculează procentul de timp în care ochii sunt considerați închiși (EAR < prag)
    pe o fereastră glisantă de `window_s` secunde.
    """
    def __init__(self, window_s: int = 60, sample_rate_hz: float = 20.0):
        # Durata ferestrei în secunde și rata de eșantionare
        self.window_s = window_s
        self.sample_rate = sample_rate_hz
        # Buffer circular pentru indicatori binari (1=ochi închiși, 0=ochi deschiși)
        self.max_len = int(window_s * sample_rate_hz)
        self.buffer = collections.deque(maxlen=self.max_len)

    def update(self, ear: float, threshold: float):
        #Adaugă un nou eșantion la buffer: 1 dacă ear < threshold, altfel 0.
        self.buffer.append(1 if ear < threshold else 0)

    def compute(self) -> float:
        """
        Returnează PERCLOS ca procent din cadrul ferestrei.
        Dacă buffer-ul e gol, returnează 0.0.
        """
        if not self.buffer:
            return 0.0
        return (sum(self.buffer) / len(self.buffer)) * 100.0
