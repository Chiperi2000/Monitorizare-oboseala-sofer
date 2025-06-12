
# gui/main_window.py
"""
Modul pentru interfața grafică cu utilizatorul (Tkinter).
Conține logica interfeței și bucla principală.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
from PIL import Image, ImageTk
import time
import traceback
from collections import deque
import json
import threading
import math

from feature_extraction.metrics import (
    normalize_ear, normalize_mar,
    normalize_perclos, normalize_micro, normalize_pitch
)

from feature_extraction.calibrator_full import CalibratorFull
from feature_extraction.logic import FatigueRiskLevel, TrendLevel
from feature_extraction.microsleep import MicroSleepDetector
from feature_extraction.ear import calculate_ear
from feature_extraction.mar import calculate_mar
from feature_extraction.pitch import calculate_head_pitch

class MainWindow:

    def toggle_monitorizare(self):
        self.monitoring_active = not self.monitoring_active

        if self.monitoring_active:
            self.button_monitor.config(text="⏹ Oprește monitorizarea")
            print("✅ Monitorizarea a fost ACTIVATĂ.")
            
            # Reset contorizări
            self.total_frames = 0
            self.frames_with_face = 0
            self.blink_count = 0
            self.yawn_count = 0
            self.head_down_count = 0
            self.attention_scores = []
            self.start_time = time.time()
            
            # Ascunde și curăță rezumatul la început
            self.label_summary.config(text="")
            self.frame_summary.grid_remove()

        else:
            self.button_monitor.config(text="▶️ Pornește monitorizarea")
            print("⛔ Monitorizarea a fost OPRITĂ.")

            # Calcul și afișare REZUMAT
            durata_secunde = int(time.time() - self.start_time) if self.start_time else 0
            minute = durata_secunde // 60
            secunde = durata_secunde % 60
            durata_format = f"{minute} min {secunde} sec"

            scor_med = int(sum(self.attention_scores) / len(self.attention_scores)) if self.attention_scores else 0
            pct_fata = int((self.frames_with_face / self.total_frames) * 100) if self.total_frames else 0

            rezumat = f"""📈 REZUMAT SESIUNE
    ────────────────────────────────────
    📅 Durată monitorizare:    {durata_format}
    🧍 Față detectată:         {pct_fata}% din timp
    👁️ Număr ochi închiși:     {self.blink_count}
    👄 Căscat detectat:        {self.yawn_count} ori
    ↙️ Cap plecat:             {self.head_down_count} evenimente
    🧠 Scor mediu atenție:     {scor_med}%
    ⚠️ Micro-adormiri:         {self.microsleep_detector.count}
    ────────────────────────────────────"""
            print("📤 Trimitem acest rezumat în UI:")
            print(rezumat)
            print("📋 Etichetă existentă?", hasattr(self, "label_summary"))
            self.label_summary.config(text="")            # curăță dacă era ceva
            self.frame_summary.grid()                     # forțează afișarea
            self.label_summary.config(text=rezumat)       # apoi setează textul
            self.frame_summary.update_idletasks()         # forțează UI refresh
    
    def apply_gain(self, *args):
        mode = self.gain_auto_var.get()        # “Off” / “Once” / “Continuous”
        value = self.gain_scale.get()
        if mode != "Off":
            self.camera.set_auto_gain(mode, value)
        else:
            self.camera.set_gain_manual(value)
        messagebox.showinfo("Gain", f"Gain setat: {mode} ({value})")

    def apply_exposure(self, *args):
        mode = self.exp_auto_var.get()
        value = float(self.exp_entry.get())
        if mode != "Off":
            self.camera.set_auto_exposure(mode, value)
        else:
            self.camera.set_exposure_manual(value)
        messagebox.showinfo("Expunere", f"Expunere setată: {mode} ({value} μs)")

    def apply_wb(self, *args):
        mode = self.wb_auto_var.get()
        value = self.wb_scale.get()
        if mode != "Off":
            self.camera.set_auto_white_balance(mode, value)
        else:
            self.camera.set_auto_white_balance("Off", value)
        messagebox.showinfo("White Balance", f"WB setat: {mode} ({value})")

    def apply_pixel_format(self):
        fmt = self.pix_fmt_var.get()  # “Mono8” sau “BayerRG8”
        self.camera.set_pixel_format(fmt)
        messagebox.showinfo("Pixel Format", f"Format pixel: {fmt}")

    def apply_resolution(self, *args):
        w = int(self.width_entry.get())
        h = int(self.height_entry.get())
        try:
            self.camera.set_resolution(w, h)
            actual_w, actual_h = self.camera.get_resolution()
            print(f"Rezoluție setată pe cameră: {actual_w}x{actual_h}")
            self.update_current_res_label()
            messagebox.showinfo("Rezoluție", f"Rezoluția setată la {actual_w}×{actual_h}")
        except Exception as e:
            print(f"Eroare la setarea rezoluției: {e}")
            messagebox.showerror("Eroare", f"Eroare la setarea rezoluției: {e}")

    def on_res_preset_selected(self, event=None):
        preset = self.res_preset.get()
        if preset:
            w, h = preset.split('x')
            self.width_entry.delete(0, tk.END)
            self.width_entry.insert(0, w)
            self.height_entry.delete(0, tk.END)
            self.height_entry.insert(0, h)
            self.apply_resolution()  # aplică direct rezoluția

    def set_offset(self, *args):
        x = int(self.offset_x_entry.get())
        y = int(self.offset_y_entry.get())
        self.camera.set_offset(x, y)
        messagebox.showinfo("Offset", f"Offset setat la ({x}, {y})")

    def center_roi(self, *args):
        self.camera.center_roi()
        messagebox.showinfo("ROI", "ROI centrat automat")

    # Obține FPS-ul maxim permis de cameră
    def get_max_fps(self):
        try:
            return round(self.camera.max_fps, 2)
        except Exception as e:
            print(f"Eroare la obținerea FPS maxim: {e}")
            return 24.0

    def get_current_resolution(self):
        return self.camera.get_resolution()

    # Actualizează eticheta cu rezoluția curentă
    def update_current_res_label(self):
        w, h = self.get_current_resolution()
        self.label_current_res.config(text=f"Rezoluție actuală: {w} x {h}")

    def apply_fps(self, *args):
        fps = float(self.fps_scale.get())
        max_fps = self.get_max_fps()

        if fps > max_fps:
            messagebox.showerror("Eroare FPS", f"Valoarea introdusă ({fps}) depășește maximul permis ({max_fps}).")
            self.fps_scale.set(max_fps)  # setează valoarea la maxim admis
            return

        try:
            self.camera.set_frame_rate(fps)
            # etează cadrele consecutive pentru detectarea căscatului
            durata_cascat = 0.6  # secunde 
            mar_frames = max(2, int(durata_cascat * fps))
            self.alert_logic.mar_consec_frames = mar_frames
            print(f"[INFO] mar_consec_frames setat la {mar_frames} (FPS actual: {fps})")
            messagebox.showinfo("FPS", f"FPS setat la {fps}\nCadre consecutive pentru căscat: {mar_frames}")
        except Exception as e:
            messagebox.showerror("Eroare la setarea FPS-ului", str(e))

    def __init__(self, camera, face_detector, alert_logic, config, calibrator, perclos):
        self.pitch_ema = None
        self.total_frames = 0
        self.frames_with_face = 0
        self.blink_count = 0
        self.yawn_count = 0
        self.head_down_count = 0
        self.attention_scores = []
        self.start_time = None
        self.fatigue_history = deque(maxlen=600)  
        self.micro_sleep_count = 0 
        self.score_buffer = deque(maxlen=8)
        self.prev_risk = None
        self.ema_score       = None    
        self.ema_alpha       = 0.4     # 0.4 înseamnă 40% din raw_score la fiecare pas
        self.last_ui_update  = 0.0
        print(">>> MainWindow.__init__ start")
        self.camera = camera
        self.face_detector = face_detector
        self.alert_logic = alert_logic
        self.config = config
        self.calibrator = calibrator
        self.perclos = perclos

        self.simple_calibrator   = self.calibrator
        # vom popula “avansat” doar dacă există JSON
        self.advanced_calibrator = None
        # ► 3’) Pornim întotdeauna cu pragurile statice din settings.yaml
        self.default_thresholds = dict(self.config['thresholds'])
        self.calibrator = self.simple_calibrator
        self.current_perclos = 0.0
        print(f">>> Calibrator activ (implicit simple): {type(self.calibrator).__name__}")

        # Praguri hard-codate pentru fallback
        self.calibrator.ear_threshold   = self.config['thresholds']['EAR']
        self.calibrator.mar_threshold   = self.config['thresholds']['MAR']
        self.calibrator.pitch_threshold = self.config['thresholds']['PITCH']
        # pragul PERCLOS
        self.perclos_threshold = getattr(
            self.calibrator, 'perclos_threshold',
            self.config['thresholds'].get('PERCLOS', 1.5)
        )
        style_name = (
            "Perclos.Red.Horizontal.TProgressbar"
            if self.current_perclos >= self.perclos_threshold
            else "Perclos.Green.Horizontal.TProgressbar"
        )

        # ▶️ 5) Acum creăm fereastra principală
        print(">>> Creating root window")
        self.root = tk.Tk()

        # ➡ actualizări de stare înainte de crearea ferestrei
        self.current_ear     = None
        self.current_mar     = None
        self.current_pitch   = 0.0

        try:
            self.max_fps = round(camera.max_fps, 2)
            fps_actual = self.max_fps  
            durata_cascat = 0.6        
            mar_frames = max(2, int(durata_cascat * fps_actual))
            self.alert_logic.mar_consec_frames = mar_frames
            print(f"[INIT] mar_consec_frames inițializat la {mar_frames} (FPS actual: {fps_actual})")
            microsleep_time = self.config['thresholds'].get('MICRO_SLEEP_TIME', 1.5)
            self.microsleep_detector = MicroSleepDetector(microsleep_time, self.max_fps)
        except Exception as e:
            print(f"Eroare la preluarea FPS max din camera: {e}")
            self.max_fps = 30.0

        # Creare fereastră
        self.root.title("Monitorizare oboseală șofer")
        self.root.geometry("1280x800+50+50")
        self.root.minsize(1000, 600) 
        # Stilizare pentru progress-bar PERCLOS
        style = ttk.Style(self.root)
        style.theme_use('default')
        style.configure("Perclos.Green.Horizontal.TProgressbar",
                    troughcolor='white', background='green')
        style.configure("Perclos.Red.Horizontal.TProgressbar",
                    troughcolor='white', background='red')
        # Stiluri pentru Fatigue Risk Score
        for lvl in FatigueRiskLevel:
            style.configure(f"{lvl.name}.Horizontal.TProgressbar",
                            troughcolor="white",
                            background=lvl.color)
        # Stiluri pentru Trend Label
        for tr in TrendLevel:
            style.configure(f"{tr.name}.TLabel",
                            foreground=tr.color)

        # Inițializări de stare (după crearea root)
        self.stat_start_time = None
        self.clip_count = 0
        self.eye_closed = False
        self.blink_timestamps = []

         # Construire UI pas 1: Notebook si tab-uri
        print(">>> Building UI (Notebook + Tabs)")
        try:
            notebook = ttk.Notebook(self.root)
            self.tab_live = ttk.Frame(notebook)
            self.tab_config = ttk.Frame(notebook)
            notebook.add(self.tab_live, text="Monitorizare Live")
            notebook.add(self.tab_config, text="Configurare Cameră")
            notebook.pack(fill=tk.BOTH, expand=True)
            print(">>> Notebook and tabs created")

            # Pas 2: frame_video in tab_live
            print(">>> Building Live frame")
            frame_video = ttk.Frame(self.tab_live)
            frame_video.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            # Video Label
            self.video_label = tk.Label(frame_video)
            self.video_label.pack(side=tk.TOP, padx=5, pady=5)
            print(">>> video_label added")

            # Text log
            self.text_log = tk.Text(frame_video, height=10)
            self.text_log.pack(side=tk.TOP, fill=tk.BOTH, padx=5, pady=5, expand=True)
            print(">>> text_log added")

            # Pas 3: frame_controls in tab_live
            print(">>> Building Live controls")
            frame_controls = ttk.Frame(self.tab_live)
            frame_controls.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

            # Pas 4: populatează tab_config
            print(">>> Building Config tab UI")
            # ─── Tab Configurare Cameră ─────────────────────────────────────────────────
            frame_config = ttk.Frame(self.tab_config, padding=10)
            frame_config.pack(fill=tk.BOTH, expand=True)

            # ─── Secțiunea Gain ─────────────────────────────────────────────────────────
            gain_frame = ttk.LabelFrame(frame_config, text="🎛️ Gain", padding=(8,8))
            gain_frame.grid(row=0, column=0, columnspan=2, sticky="we", pady=(0,10))
            gain_frame.columnconfigure(1, weight=1)

            ttk.Label(gain_frame, text="Auto:").grid(row=0, column=0, sticky="w")
            gain_auto_var = tk.StringVar(value=self.config.get('gain_auto_mode', 'Off'))
            ttk.Combobox(gain_frame, textvariable=gain_auto_var, state="readonly",
                        values=["Off","Once","Continuous"], width=12)\
                .grid(row=0, column=1, sticky="w")

            ttk.Label(gain_frame, text="Manual:").grid(row=1, column=0, sticky="w", pady=(8,0))
            gain_scale = tk.Scale(gain_frame, from_=1, to=18, orient=tk.HORIZONTAL, length=180)
            gain_scale.set(self.config.get('gain_manual', 1))
            gain_scale.grid(row=1, column=1, sticky="we", pady=(8,0))

            ttk.Button(gain_frame, text="Aplică Gain", command=self.apply_gain)\
                .grid(row=0, column=2, rowspan=2, padx=10)

            # ─── Secțiunea Pixel & Expunere ─────────────────────────────────────────────
            pixexp_frame = ttk.LabelFrame(frame_config, text="📷 Pixel & Expunere", padding=(8,8))
            pixexp_frame.grid(row=1, column=0, columnspan=2, sticky="we", pady=(0,10))
            pixexp_frame.columnconfigure((1,3), weight=1)

            # Pixel Format
            ttk.Label(pixexp_frame, text="Format Pixel:").grid(row=0, column=0, sticky="w")
            pix_fmt_var = tk.StringVar(value=self.config.get('pixel_format','Mono8'))
            ttk.Combobox(pixexp_frame, textvariable=pix_fmt_var, state="readonly",
                        values=["Mono8","BayerRG8"], width=12)\
                .grid(row=0, column=1, sticky="w", padx=(0,10))
            ttk.Button(pixexp_frame, text="Aplică", command=self.apply_pixel_format)\
                .grid(row=0, column=2)

            # Expunere
            ttk.Label(pixexp_frame, text="Auto Expunere:").grid(row=1, column=0, sticky="w", pady=(8,0))
            exp_auto_var = tk.StringVar(value=self.config.get('exp_auto_mode','Off'))
            ttk.Combobox(pixexp_frame, textvariable=exp_auto_var, state="readonly",
                        values=["Off","Once","Continuous"], width=12)\
                .grid(row=1, column=1, sticky="w", pady=(8,0), padx=(0,10))

            ttk.Label(pixexp_frame, text="Manual (μs):").grid(row=1, column=2, sticky="e", pady=(8,0))
            exp_entry = ttk.Entry(pixexp_frame, width=10)
            exp_entry.insert(0, str(self.config.get('exp_manual',10000)))
            exp_entry.grid(row=1, column=3, sticky="w", pady=(8,0))

            ttk.Button(pixexp_frame, text="Aplică", command=self.apply_exposure)\
                .grid(row=1, column=4, padx=10)

            # ─── Secțiunea White Balance ────────────────────────────────────────────────
            wb_frame = ttk.LabelFrame(frame_config, text="⚖️ White Balance", padding=(8,8))
            wb_frame.grid(row=2, column=0, columnspan=2, sticky="we", pady=(0,10))
            wb_frame.columnconfigure(1, weight=1)

            ttk.Label(wb_frame, text="Auto:").grid(row=0, column=0, sticky="w")
            wb_auto_var = tk.StringVar(value=self.config.get('wb_auto_mode','Off'))
            ttk.Combobox(wb_frame, textvariable=wb_auto_var, state="readonly",
                        values=["Off","Once","Continuous"], width=12)\
                .grid(row=0, column=1, sticky="w")

            ttk.Label(wb_frame, text="Manual:").grid(row=1, column=0, sticky="w", pady=(8,0))
            wb_scale = tk.Scale(wb_frame, from_=1, to=4, orient=tk.HORIZONTAL, length=180)
            wb_scale.set(self.config.get('wb_manual',1))
            wb_scale.grid(row=1, column=1, sticky="we", pady=(8,0))

            ttk.Button(wb_frame, text="Aplică", command=self.apply_wb)\
                .grid(row=0, column=2, rowspan=2, padx=10)

            # ─── Secțiunea Rezoluție & Offset ──────────────────────────────────────────
            res_frame = ttk.LabelFrame(frame_config, text="🖥️ Rezoluție & ROI", padding=(8,8))
            res_frame.grid(row=3, column=0, columnspan=2, sticky="we", pady=(0,10))
            res_frame.columnconfigure((1,3), weight=1)

            # Rezoluție preset
            ttk.Label(res_frame, text="Preset:").grid(row=0, column=0, sticky="w")
            self.res_preset = ttk.Combobox(res_frame, state="readonly",
                                        values=["640x480","800x600","1024x768","1280x720","1920x1080"],
                                        width=12)
            self.res_preset.grid(row=0, column=1, sticky="w")
            self.res_preset.bind("<<ComboboxSelected>>", self.on_res_preset_selected)

            # Lățime / Înălțime custom
            ttk.Label(res_frame, text="W:").grid(row=0, column=2, sticky="e")
            width_entry = ttk.Entry(res_frame, width=6); width_entry.insert(0, str(self.config.get('width',800)))
            width_entry.grid(row=0, column=3, sticky="w", padx=(0,10))
            ttk.Label(res_frame, text="H:").grid(row=0, column=4, sticky="e")
            height_entry = ttk.Entry(res_frame, width=6); height_entry.insert(0, str(self.config.get('height',600)))
            height_entry.grid(row=0, column=5, sticky="w")

            ttk.Button(res_frame, text="Aplică", command=self.apply_resolution)\
                .grid(row=0, column=6, padx=10)

            # Offset
            ttk.Label(res_frame, text="Offset X:").grid(row=1, column=0, sticky="w", pady=(8,0))
            offset_x_entry = ttk.Entry(res_frame, width=6); offset_x_entry.insert(0, str(self.config.get('offset_x',0)))
            offset_x_entry.grid(row=1, column=1, sticky="w", pady=(8,0))
            ttk.Label(res_frame, text="Offset Y:").grid(row=1, column=2, sticky="w", pady=(8,0))
            offset_y_entry = ttk.Entry(res_frame, width=6); offset_y_entry.insert(0, str(self.config.get('offset_y',0)))
            offset_y_entry.grid(row=1, column=3, sticky="w", pady=(8,0))
            ttk.Button(res_frame, text="Aplică Offset", command=self.set_offset).grid(row=1, column=4, columnspan=2, sticky="we", padx=5)


            ttk.Button(res_frame, text="Center ROI", command=self.center_roi)\
                .grid(row=1, column=6, padx=10)

            # ─── Secțiunea FPS ─────────────────────────────────────────────────────────
            fps_frame = ttk.LabelFrame(frame_config, text="🎥 FPS", padding=(8,8))
            fps_frame.grid(row=4, column=0, columnspan=2, sticky="we", pady=(0,10))
            fps_frame.columnconfigure(1, weight=1)

            ttk.Label(fps_frame, text="Valoare:").grid(row=0, column=0, sticky="w")
            self.fps_scale = tk.Scale(fps_frame, from_=1, to=self.max_fps,
                                    orient=tk.HORIZONTAL, resolution=0.1, length=200)
            self.fps_scale.set(min(24, self.max_fps))
            self.fps_scale.grid(row=0, column=1, sticky="we")

            ttk.Button(fps_frame, text="Aplică FPS", command=self.apply_fps)\
                .grid(row=0, column=2, padx=10)

            # ─── Rezoluție actuală ─────────────────────────────────────────────────────
            self.label_current_res = ttk.Label(frame_config, text="Rezoluție actuală: -- x --")
            self.label_current_res.grid(row=5, column=0, columnspan=2, sticky="w")

            # ─── Păstrăm referințele și callback-urile ─────────────────────────────────
            self.gain_auto_var   = gain_auto_var
            self.gain_scale      = gain_scale
            self.pix_fmt_var     = pix_fmt_var
            self.exp_auto_var    = exp_auto_var
            self.exp_entry       = exp_entry
            self.wb_auto_var     = wb_auto_var
            self.wb_scale        = wb_scale
            self.width_entry     = width_entry
            self.height_entry    = height_entry
            self.offset_x_entry  = offset_x_entry
            self.offset_y_entry  = offset_y_entry

            # Inițializare Rezoluție actuală
            self.update_current_res_label()

            print(">>> Config tab UI built")
            label_font = ("Segoe UI", 10)

            self.monitoring_active = False
            # ─── Start/Stop & stare detecție ───────────────────────
            self.button_monitor = ttk.Button(
                frame_controls,
                text="▶️ Pornește monitorizarea",
                command=self.toggle_monitorizare
            )
            self.button_monitor.grid(row=0, column=0, columnspan=2, sticky='we', pady=5)

            self.label_face_detected = ttk.Label(frame_controls, text="Față detectată: Nu")
            self.label_face_detected.grid(row=1, column=0, columnspan=2, sticky='w', pady=(0,8))

            ttk.Separator(frame_controls, orient='horizontal')\
                .grid(row=2, column=0, columnspan=2, sticky='we', pady=8)

            # ─── Metrici de față ────────────────────────────────────
            self.label_ear = ttk.Label(frame_controls, text="👁️ EAR: –", font=label_font, justify='left')
            self.label_ear.grid(row=3, column=0, columnspan=2, sticky='w', padx=5, pady=2)

            self.label_mar = ttk.Label(frame_controls, text="👄  MAR: –", font=label_font, justify='left')
            self.label_mar.grid(row=4, column=0, columnspan=2, sticky='w', padx=5, pady=2)

            self.label_pitch = ttk.Label(frame_controls, text="↙️ Pitch: –°", font=label_font, justify='left')
            self.label_pitch.grid(row=5, column=0, columnspan=2, sticky='w', padx=5, pady=2)

            self.lbl_perclos = ttk.Label(frame_controls, text="PERCLOS: 0.0%", font=label_font)
            self.lbl_perclos.grid(row=6, column=0, sticky='w', padx=5, pady=2)

            self.pb_perclos = ttk.Progressbar(
                frame_controls,
                orient="horizontal",
                length=180,
                mode="determinate",
                maximum=100,
                style="Perclos.Green.Horizontal.TProgressbar"
            )
            self.pb_perclos.grid(row=6, column=1, sticky='e', padx=5, pady=2)

            # ─── Fatigue Risk Score ─────────────────────────────────
            self.lbl_fatigue = ttk.Label(
                frame_controls,
                text="Fatigue: –",
                font=label_font,
                justify="left"
            )
            self.lbl_fatigue.grid(row=7, column=0, sticky='w', padx=5, pady=2)

            self.pb_fatigue = ttk.Progressbar(
                frame_controls,
                orient="horizontal",
                length=180,
                mode="determinate",
                maximum=100,
                style="VERY_LOW.Horizontal.TProgressbar"
            )
            self.pb_fatigue.grid(row=7, column=1, sticky='e', padx=5, pady=2)

            self.lbl_trend = ttk.Label(
                frame_controls,
                text="Trend: –",
                style="STABLE.TLabel"
            )
            self.lbl_trend.grid(row=8, column=0, columnspan=2, sticky='w', padx=5, pady=(2,8))

            ttk.Separator(frame_controls, orient='horizontal')\
                .grid(row=9, column=0, columnspan=2, sticky='we', pady=8)

            # ─── Calibrare ──────────────────────────────────────────
            self.btn_calibrare = ttk.Button(
                frame_controls,
                text="🧑‍🔬 Calibrare Rapidă",
                command=self.on_calibrate_clicked
            )
            self.btn_calibrare.grid(row=10, column=0, columnspan=2, sticky="we", pady=5)

            self.btn_calibrare_avansata = ttk.Button(
                frame_controls,
                text="🧑‍🔬 Calibrare Avansată",
                command=self.on_calibrate_clicked_avansata
            )
            self.btn_calibrare_avansata.grid(row=11, column=0, columnspan=2, sticky="we", pady=5)

            # ─── Mod calibrare & Load Advanced ──────────────────────
            self.mode_var = tk.StringVar(value="simple")
            ttk.Label(
                frame_controls,
                text="Alege modul calibrare:",
                font=("Segoe UI", 9, "italic")
            ).grid(row=12, column=0, columnspan=2, sticky="w", padx=5, pady=(10,2))

            ttk.Radiobutton(
                frame_controls, text="Calibrare Basic",
                variable=self.mode_var, value="simple",
                command=self.on_mode_change
            ).grid(row=13, column=0, sticky="we", padx=5)

            ttk.Radiobutton(
                frame_controls, text="Calibrare Avansată",
                variable=self.mode_var, value="advanced",
                command=self.on_mode_change
            ).grid(row=13, column=1, sticky="we", padx=5)

            ttk.Label(
                frame_controls,
                text="Basic = praguri fixe din setări inițiale (rapid)\n"
                    "Avansată = colectare date în funcție de stare",
                font=("Segoe UI", 8),
                justify="left"
            ).grid(row=14, column=0, columnspan=2, sticky="w", padx=5, pady=(2,8))

            self.btn_load_adv = ttk.Button(
                frame_controls,
                text="Load Advanced",
                command=self.load_advanced,
                state="disabled"
            )
            self.btn_load_adv.grid(row=15, column=0, columnspan=2, sticky="we", pady=5)

            ttk.Separator(frame_controls, orient='horizontal')\
                .grid(row=16, column=0, columnspan=2, sticky='we', pady=8)

            # ─── Reset & Exit ───────────────────────────────────────
            self.btn_reset_yaml = ttk.Button(
                frame_controls,
                text="Restabilește setările",
                command=self.reset_to_yaml
            )
            self.btn_reset_yaml.grid(row=17, column=0, columnspan=2, sticky="we", pady=5)

            self.btn_reset_session = ttk.Button(
                frame_controls,
                text="🔄 Reset sesiune",
                command=self.reset_session
            )
            self.btn_reset_session.grid(row=18, column=0, columnspan=2, sticky="we", pady=5)

            exit_btn = ttk.Button(
                frame_controls,
                text="❌ Inchidere Aplicație",
                command=self.on_closing
            )
            exit_btn.grid(row=19, column=0, columnspan=2, sticky="we", pady=5)

            # ─── Rezumat sesiune ────────────────────────────────────
            self.frame_summary = ttk.LabelFrame(frame_controls, text="📊 Rezumat sesiune")
            self.label_summary = ttk.Label(
                self.frame_summary,
                text="",
                font=("Consolas", 9),
                justify="left",
                anchor="w"
            )
            self.label_summary.pack(anchor="w", padx=5, pady=5)
            self.frame_summary.grid(row=20, column=0, columnspan=2, sticky="we", padx=5, pady=(10,5))
            self.frame_summary.grid_remove()  # ascundem la început


            print(">>> check_monitor added")

        except Exception as e:
            print("‼️ Exception în build UI steps:", e)
            import traceback; traceback.print_exc()
            raise

        # Protocol de închidere
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Programare procesare cadre
        print(">>> Scheduling process_frame via after()")
        self.root.after(0, self.process_frame)
        print("✅ after(0, process_frame) programat")

        # Start mainloop
        print(">>> Entering mainloop()")
        self.root.mainloop()
        print(">>> mainloop exited")


    def compute_trend(self):
        # dacă nu avem minim 3 puncte, nu încercăm
        if len(self.fatigue_history) < 3:
            return 0.0
        # ts = [t0=0, t1, t2, …], vs = [score0, score1, …]
        t0 = self.fatigue_history[0][0]
        ts = np.array([t - t0 for t,_ in self.fatigue_history])
        vs = np.array([v    for _,v in self.fatigue_history])
        # m = pantă din regresie vs ≃ m·ts + b
        m, _ = np.polyfit(ts, vs, 1)
        return m  # % puncte per secundă
    
    def _update_fatigue_ui(self, smooth_score, risk, trend, slope):
        # bara de Fatigue
        self.pb_fatigue.configure(
            style = f"{risk.name}.Horizontal.TProgressbar",
            value = smooth_score
        )
        self.lbl_fatigue.configure(
            text       = f"{risk.label} ({smooth_score:.0f}%)",
            foreground = risk.color
        )
        # eticheta de Trend
        self.lbl_trend.configure(
            text  = f"{trend.label} ({slope*60:+.1f}%/min)",
            style = f"{trend.name}.TLabel"
        )

    def process_frame(self):
        frame = self.camera.get_frame()
        if frame is None:
            print("⚠️ Nu s-a primit niciun frame de la cameră")
            self.root.after(200, self.process_frame)  # încerci din nou, dar cu întârziere
            return
        img = Image.fromarray(frame)
        img = img.resize((640, 480))  # scalare forțată pentru vizibilitate
        imgtk = ImageTk.PhotoImage(img)
        self.video_label.imgtk = imgtk
        self.video_label.config(image=imgtk)

        if self.monitoring_active:
            try:
                detections = []
                print("🔍 Încep analiza frame-ului...")
                width, height = frame.shape[1], frame.shape[0]
                landmarks = self.face_detector.find_landmarks(frame)
                face_detected = landmarks is not None
                self.total_frames += 1
                if face_detected:
                    self.frames_with_face += 1
                # ─── 1) Detectare față și calcul metrici ─────────────────
                from feature_extraction.ear import LEFT_EYE_INDEXES, RIGHT_EYE_INDEXES

                if face_detected:
                    # față detectată → calculăm EAR, MAR, Pitch
                    ear_l = calculate_ear(landmarks, LEFT_EYE_INDEXES, width, height)
                    ear_r = calculate_ear(landmarks, RIGHT_EYE_INDEXES, width, height)
                    ear   = (ear_l + ear_r) / 2.0
                    mar   = calculate_mar(landmarks, width, height)
                    pitch = calculate_head_pitch(landmarks, width, height)

                    # microsleep (rămâne neschimbat)
                    try:
                        ear_thr = getattr(self.calibrator, 'ear_threshold', None) or self.config['thresholds']['EAR']
                        microsleep_new = self.microsleep_detector.update(ear, ear_thr)
                        if microsleep_new:
                            self.micro_sleep_count += 1
                            timestamp = time.strftime('%H:%M:%S')
                            self.text_log.insert(tk.END, f"[{timestamp}] ⚠️ MICRO-ADORMIRE DETECTATĂ!\n")
                            self.text_log.see(tk.END)
                    except Exception as e_ms:
                        print("‼️ EROARE în blocul de microsleep:", e_ms, type(e_ms))
                        traceback.print_exc()

                else:
                    # nu avem față → afișăm “–” și folosim fallback static
                    self.label_ear.config(text="👁️ EAR: –")
                    self.label_mar.config(text="👄 MAR: –")
                    self.label_pitch.config(text="↙️ Pitch: –°")
                    ear_thr = getattr(self.calibrator, 'ear_threshold', None) or self.config['thresholds']['EAR']
                    ear   = ear_thr
                    mar   = 0
                    pitch = 0

                # ─── 2) Salvăm ultimele valori pentru UI și PERCLOS ────────
                self.current_ear   = ear
                self.current_mar   = mar
                self.current_pitch = pitch
                detections        = []

                self.label_face_detected.config(text=f"Față detectată: {'✅' if face_detected else '❌'}", foreground="green" if face_detected else "red")
                self.label_ear.config(text=f"👁️ EAR: {ear:.2f}")
                self.label_mar.config(text=f"👄 MAR: {mar:.2f}")
                self.label_pitch.config(text=f"↙️ Pitch: {pitch:.1f}°")

                # ─── Actualizare PERCLOS ────────────────────────────
                # selectăm prag adaptiv sau fallback static
                ear_thr = getattr(self.calibrator, 'ear_threshold', None) or self.config['thresholds']['EAR']
                self.perclos.update(ear, ear_thr)
                current_perclos = self.perclos.compute()
                self.current_perclos = current_perclos

                # Actualizează UI PERCLOS
                self.lbl_perclos.config(text=f"PERCLOS: {current_perclos:.1f}%")
                style_name = (
                    "Perclos.Red.Horizontal.TProgressbar"
                    if current_perclos >= self.perclos_threshold
                    else "Perclos.Green.Horizontal.TProgressbar"
                )
                self.pb_perclos.config(style=style_name, value=current_perclos)
                # ─────────────────────────────────────────────────────
                events = self.alert_logic.evaluate(ear, mar, pitch, bool(detections))
                print("✅ Evaluare logică completă")
                 # ─── 1) Normalizează fiecare componentă în [0,1]
                ear_r = normalize_ear(ear)
                mar_r = normalize_mar(mar)
                per_r = normalize_perclos(current_perclos)    # current_perclos e 0–100
                mic_r = normalize_micro(self.micro_sleep_count)
                pit_r = normalize_pitch(pitch)

                # ─── 2) Calculează raw_score (0–100) cu detecție de tip calibrator
                if self.pitch_ema is None:
                    self.pitch_ema = pitch
                else:
                    self.pitch_ema = 0.3 * pitch + 0.7 * self.pitch_ema

                values = (ear, mar, current_perclos, self.pitch_ema)
                print(f"[DEBUG MODE] using calibrator: {type(self.calibrator).__name__}")
                if isinstance(self.calibrator, CalibratorFull) and self.calibrator.thresholds and self.calibrator.weights:
                    # debug praguri
                    thr = self.calibrator.thresholds
                    print(f"[DEBUG USED ADV] ear={thr['ear']['enter_hi']}, mar={thr['mar']['enter_hi']}, pitch={thr['pitch']['enter_hi']}")
                    try:
                        raw_score = self.calibrator.score_state(values) * 100
                        if not math.isfinite(raw_score):
                            raw_score = 0.0
                    except Exception as e:
                        print(f"[‼️ SCOR ERROR] {e}")
                        raw_score = 0.0
                else:
                    # debug praguri YAML
                    y = self.config['thresholds']
                    raw_score = (
                        ear_r*0.25 +
                        mar_r*0.10 +
                        per_r*0.30 +
                        mic_r*0.20 +
                        pit_r*0.15
                    ) * 100

                # ─── 3) EMA smoothing + override critic
                if raw_score >= 80:
                    smooth_score   = raw_score
                    self.ema_score = raw_score
                else:
                    if self.ema_score is None:
                        self.ema_score = raw_score
                    else:
                        self.ema_score = (
                            self.ema_alpha * raw_score +
                            (1 - self.ema_alpha) * self.ema_score
                        )
                    smooth_score = self.ema_score

                # ✅ Salvează scorul în toate cazurile (inclusiv peste 80)
                self.attention_scores.append(smooth_score)

                # ─── 4) Istoric trend pe baza smooth_score
                now = time.time()
                self.fatigue_history.append((now, smooth_score))

                # ─── 5) Trend stabil (regresie liniară)
                slope = self.compute_trend()

                # ─── 6) Clasificare cu hysteresis
                risk = FatigueRiskLevel.classify(smooth_score, self.prev_risk)
                self.prev_risk = risk

                # ─── 7) Clasificare trend
                trend = TrendLevel.classify(slope)

                # ─── 8) Actualizare UI la maxim 1×/s
                if now - self.last_ui_update > 1.0:
                    self._update_fatigue_ui(smooth_score, risk, trend, slope)
                    self.last_ui_update = now
                
                from alerting.notifier import Notifier
                for event in events:
                    Notifier.play_alert_sound()
                    if event == "ochi_inchisi":
                        self.blink_count += 1
                    elif event == "cascat":
                        self.yawn_count += 1
                    elif event == "cap_plecat":
                        self.head_down_count += 1
                    timestamp = time.strftime('%H:%M:%S')
                    self.text_log.insert(tk.END, f"[{timestamp}] ALERTĂ: {event.upper()}\n")
                    self.text_log.see(tk.END)

            except Exception as e:
                print(f"‼️ EROARE în analiza frame-ului: {e}")
                traceback.print_exc()
                self.root.after(200, self.process_frame) 

        self.root.after(33, self.process_frame)

    def on_calibrate_clicked(self):
        self._prev_monitoring_active = getattr(self, "monitoring_active", False)
        if not self._prev_monitoring_active:
            self.toggle_monitorizare()   # activează monitorizarea

        # ▶️ Folosim calibratorul simplu
        self.calibrator = self.simple_calibrator
        print(f">>> Calibrator activ la start: {type(self.calibrator).__name__}")
        self.calib_step = 0
        self.start_calibration_step()

    def on_calibrate_clicked_avansata(self):
        # ─── Salvează starea curentă a monitorizării
        self._prev_monitoring_active = getattr(self, "monitoring_active", False)
        # Dacă nu era activă, pornește monitorizarea
        if not self._prev_monitoring_active:
            self.toggle_monitorizare()

        # Mesaj de început calibrare și lansare
        messagebox.showinfo(
            "Calibrare avansată",
            "Calibrare pe trei stări cognitive:\n"
            "  1) Stare de alertă maximă\n"
            "  2) Stare de vigilență moderată\n"
            "  3) Stare semnificativ de oboseală\n\n"
            "Apasă OK pentru a începe calibrarea."
        )
        # construim un nou CalibratorFull
        self.advanced_calibrator = CalibratorFull()
        self.calibrator          = self.advanced_calibrator
        self.calib_step = 0
        # ▶️ Începem primul pas
        self.start_advanced_calibration_step()


    def start_calibration_step(self):
        if self.calib_step == 0:
            messagebox.showinfo("Calibrare", "Pas 1/4: Ține ochii DESCHIȘI, gura închisă și stai nemișcat 6 secunde.")
            self.calibrator.start_ear_open_calibration(6, lambda: (self.current_ear, self.current_mar), on_done=self.next_calibration_step)
        elif self.calib_step == 1:
            messagebox.showinfo("Calibrare", "Pas 2/4: Închide OCHII complet și stai nemișcat 4 secunde.")
            self.calibrator.start_ear_closed_calibration(4, lambda: (self.current_ear, self.current_mar), on_done=self.next_calibration_step)
        elif self.calib_step == 2:
            messagebox.showinfo("Calibrare", "Pas 3/4: Ține gura ÎNCHISĂ (nu vorbi) și stai nemișcat 4 secunde.")
            self.calibrator.start_mar_closed_calibration(4, lambda: (self.current_ear, self.current_mar), on_done=self.next_calibration_step)
        elif self.calib_step == 3:
            messagebox.showinfo("Calibrare", "Pas 4/4: Deschide larg gura ca la căscat și stai așa 4 secunde.")
            self.calibrator.start_mar_open_calibration(4, lambda: (self.current_ear, self.current_mar), on_done=self.next_calibration_step)
        elif self.calib_step == 4:
            self.calibrator.compute_thresholds()
            ear_thr = self.calibrator.ear_threshold
            mar_thr = self.calibrator.mar_threshold
            messagebox.showinfo("Calibrare completă", f"Prag EAR: {ear_thr:.3f}\nPrag MAR: {mar_thr:.3f}")
            print(f"[CALIBRATOR] EAR_THRESHOLD={ear_thr}, MAR_THRESHOLD={mar_thr}")
            if hasattr(self, "_prev_monitoring_active") and not self._prev_monitoring_active:
                self.toggle_monitorizare()
                del self._prev_monitoring_active
            return
    
    
    def next_calibration_step(self):
        self.calib_step += 1
        self.start_calibration_step()
        
    def next_advanced_calibration_step(self):
        self.calib_step += 1
        print(f"[ADV] moving to step {self.calib_step}")
        self.start_advanced_calibration_step()

    def start_advanced_calibration_step(self):
        print(f"[ADV] start step {self.calib_step + 1}/3")
        DUR = 600  # durată (secunde) pentru fiecare fază
        phases = ["alert", "moderate", "tired"]
        labels = [
    (
        "Alertă maximă",
        "• Ține capul drept și privirea fixă spre ecran\n"
        "• Nu clipi decât natural, fără pauze intenționate\n"
        "• Nu căscă, nu mișca gura\n"
        "• Fără înclinare laterală sau verticală a capului"
    ),
    (
        "Vigilență moderată",
        "• Clipiri normale permise (max 1/s)\n"
        "• Poți mișca ușor buzele, dar fără căscat\n"
        "• Capul poate urmări ușor mișcările ochilor (±10°)\n"
        "• Evită mișcări bruște ale capului"
    ),
    (
        "Oboseală accentuată",
        "• Permite clipiri lente și frecvente (≥2/s)\n"
        "• Poți căsca o dată la 5–10 s\n"
        "• Capul poate înclina ușor înainte (≤15°)\n"
    )
]

        # Dacă suntem pe pasul 1–3:
        if 0 <= self.calib_step < len(phases):
            phase = phases[self.calib_step]
            title, desc = labels[self.calib_step]

            messagebox.showinfo(
                f"Calibrare avansată ({self.calib_step+1}/3)",
                f"{title} – {DUR} s\n\n{desc}"
            )

            threading.Thread(
                target=lambda: self.calibrator.start_collect(
                    phase,
                    DUR,
                    self.get_metrics_callback,
                    on_done=self._on_advanced_collect_done
                ),
                daemon=True
            ).start()

        # Când au fost colectate toate cele 3 stări:
        else:
            try:
                self.calibrator.compute_thresholds_and_weights()
                self.save_advanced_calibration_json()
                messagebox.showinfo(
                    "Calibrare completă",
                    "Calibrarea avansată s-a încheiat cu succes.\n"
                    "Pragurile și ponderile au fost salvate în config_avansat.json."
                )
            except Exception as e:
                traceback.print_exc()
                messagebox.showerror(
                    "Eroare la calibrarea avansată",
                    f"A apărut o eroare la salvarea configurației:\n{e}"
                )

            # Restaurăm starea monitorizării dacă era oprită înainte
            if hasattr(self, "_prev_monitoring_active") and not self._prev_monitoring_active:
                self.toggle_monitorizare()
                del self._prev_monitoring_active

            return

    def _on_advanced_collect_done(self):
        print(f"[ADV] finished collect for step {self.calib_step}")
        self.root.after(0, self.next_advanced_calibration_step)

    def get_current_metrics(self):
        """Return the current metrics dict for CalibratorFull."""
        ear   = self.current_ear   if self.current_ear   is not None else 0.0
        mar   = self.current_mar   if self.current_mar   is not None else 0.0
        percl = self.perclos.compute()
        micro = self.micro_sleep_count
        pitch = getattr(self, 'current_pitch', 0.0)
        return {
        'ear': ear,
        'mar': mar,
        'perclos': percl,
        'micro_sleep': micro,
        'pitch': pitch
    }


    def get_metrics_callback(self):
        return (self.current_ear,
                self.current_mar,
                self.current_perclos,
                self.current_pitch)
    
    def save_advanced_calibration_json(self):
        data = self.calibrator.get_advanced_config()  
        with open("config_avansat.json", "w") as f:
            json.dump(data, f, indent=2)

    def on_mode_change(self):
        if self.mode_var.get() == "advanced":
            self.btn_load_adv.config(state="normal")
        else:
            self.btn_load_adv.config(state="disabled")
            self.calibrator = self.simple_calibrator

    def load_advanced(self):
        try:
            with open("config_avansat.json", "r") as f:
                adv = json.load(f)
            self.advanced_calibrator = CalibratorFull()
            t = adv["thresholds"]
            self.advanced_calibrator.thresholds = t
            self.advanced_calibrator.weights    = adv["weights"]
            self.advanced_calibrator.ear_threshold   = t["ear"]["enter_hi"]
            self.advanced_calibrator.mar_threshold   = t["mar"]["enter_hi"]
            self.advanced_calibrator.pitch_threshold = t["pitch"]["enter_hi"]
            self.calibrator = self.advanced_calibrator
            self.alert_logic.calibrator = self.advanced_calibrator

            print("[DEBUG ADV LOADED] thresholds:", t)
            print("[DEBUG ADV LOADED] weights:   ", self.advanced_calibrator.weights)
            messagebox.showinfo("Advanced", "Calibrare avansată încărcată.")
        except Exception as e:
            messagebox.showerror("Error", f"Nu pot încărca config_avansat.json:\n{e}")

    def reset_to_yaml(self):
        # Reinițializează simple_calibrator cu valorile din YAML
        th = self.default_thresholds
        self.simple_calibrator.ear_threshold     = th['EAR']
        self.simple_calibrator.mar_threshold     = th['MAR']
        self.simple_calibrator.pitch_threshold   = th['PITCH']
        self.simple_calibrator.perclos_threshold = th.get('PERCLOS', 1.5)
        self.calibrator = self.simple_calibrator
        self.mode_var.set("simple")
        self.btn_load_adv.config(state="disabled")
        messagebox.showinfo("Reset", "Praguri resetate la valorile din YAML.")


    def reset_session(self):
        # ─── 1) Resetare contori și date interne ─────────────
        self.total_frames      = 0
        self.frames_with_face  = 0
        self.blink_count       = 0
        self.yawn_count        = 0
        self.head_down_count   = 0
        self.attention_scores  = []
        self.micro_sleep_count = 0
        # reset pentru trend + fatigue history
        self.fatigue_history.clear()
        self.prev_risk         = None
        self.ema_score         = None
        self.current_perclos   = 0.0
        self.current_ear       = None
        self.current_mar       = None
        self.current_pitch     = 0.0

        # ─── 2) Resetare timp de start ──────────────────────
        self.start_time = time.time()

        # ─── 3) Curățare log text ───────────────────────────
        self.text_log.delete("1.0", tk.END)

        # ─── 4) Resetare widget-uri metrice ─────────────────
        # Față detectată
        self.label_face_detected.config(
            text="Față detectată: Nu",
            foreground="black"
        )
        # EAR / MAR / Pitch
        self.label_ear.config(text="👁️ EAR: –")
        self.label_mar.config(text="👄  MAR: –")
        self.label_pitch.config(text="↙️ Pitch: –°")

        # PERCLOS
        self.lbl_perclos.config(text="PERCLOS: 0.0%")
        self.pb_perclos.config(
            value=0,
            style="Perclos.Green.Horizontal.TProgressbar"
        )

        # Fatigue Risk Score (bara + etichetă)
        self.pb_fatigue.config(
            value=0,
            style="VERY_LOW.Horizontal.TProgressbar"
        )
        self.lbl_fatigue.config(
            text="Fatigue: –",
            foreground="black"
        )

        # Trend
        self.lbl_trend.config(
            text="Trend: –",
            style="STABLE.TLabel"
        )

        # ─── 5) Ascundere și curățare Rezumat sesiune ───────
        self.label_summary.config(text="")
        self.frame_summary.grid_remove()

    def on_closing(self):
        print(">>> on_closing called")
        # Eliberare resurse
        try:
            self.camera.release()
        except:
            pass
        try:
            self.face_detector.close()
        except:
            pass
        self.root.destroy()
