# alerting/notifier.py
"""
Modul pentru notificări audio și logare de mesaje.
"""
import winsound

class Notifier:
    @staticmethod
    def play_alert_sound(frequency=1200, duration=600):
        """
        Redă un semnal sonor simplu (pe Windows) pentru a alerta utilizatorul.
        frequency: frecvența în Hz, duration: durată în ms.
        """
        try:
            winsound.Beep(frequency, duration)
        except RuntimeError as e:
            print(f"Eroare la redarea sunetului de alertă: {e}")
