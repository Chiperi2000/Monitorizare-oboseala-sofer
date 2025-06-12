# capture/flir_camera.py
"""
Module pentru captură video de la camera FLIR folosind PySpin.
Gestionează inițializarea camerei, configurările și preluarea cadrelor.
"""
import PySpin
import cv2
import numpy as np

class FlirCamera:
    def __init__(self):
        # Obținem instanța de sistem și lista de camere
        self.system = PySpin.System.GetInstance()
        self.cam_list = self.system.GetCameras()
        if self.cam_list.GetSize() == 0:
            raise RuntimeError("Nicio cameră FLIR detectată.")
        # Inițializăm prima cameră disponibilă
        self.cam = self.cam_list.GetByIndex(0)
        self.cam.Init()
        # Activăm controlul manual al FPS
        if hasattr(self.cam, "AcquisitionFrameRateEnable"):
            self.cam.AcquisitionFrameRateEnable.SetValue(True)

        fps_initial = 20.0
        fps_min = self.cam.AcquisitionFrameRate.GetMin()
        fps_max = self.cam.AcquisitionFrameRate.GetMax()

        if fps_min <= fps_initial <= fps_max:
            self.cam.AcquisitionFrameRate.SetValue(fps_initial)
            print(f"✅ FPS inițial setat la {fps_initial}")
            self.max_fps = fps_max
        else:
            print(f"⚠️ FPS dorit {fps_initial} nu este în intervalul acceptat: {fps_min:.1f} – {fps_max:.1f}")

        try:
            self.cam.PixelFormat.SetValue(PySpin.PixelFormat_BayerRG8)
        except Exception:
            try:
                self.cam.PixelFormat.SetValue(PySpin.PixelFormat_Mono8)
            except Exception as e:
                raise RuntimeError(f"Eroare la setarea formatului pixel: {e}")

        # Setăm modul de achiziție continuă
        self.cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)
        if hasattr(self.cam, 'AcquisitionFrameRateEnable'):
            try:
                self.cam.AcquisitionFrameRateEnable.SetValue(True)
            except Exception:
                pass

        # Obținem fps maxim permis de cameră
        self.max_fps = 30.0
        try:
            self.max_fps = self.cam.AcquisitionFrameRate.GetMax()
        except Exception:
            self.max_fps = 30.0

        # Începem achiziția de cadre
        self.cam.BeginAcquisition()

        # Coordonate și limite pentru ROI (offset și rezoluție)
        try:
            self.width_min = self.cam.Width.GetMin()
            self.width_max = self.cam.Width.GetMax()
            self.width_inc = self.cam.Width.GetInc()
            self.height_min = self.cam.Height.GetMin()
            self.height_max = self.cam.Height.GetMax()
            self.height_inc = self.cam.Height.GetInc()
            self.offset_x_min = self.cam.OffsetX.GetMin()
            self.offset_x_max = self.cam.OffsetX.GetMax()
            self.offset_x_inc = self.cam.OffsetX.GetInc()
            self.offset_y_min = self.cam.OffsetY.GetMin()
            self.offset_y_max = self.cam.OffsetY.GetMax()
            self.offset_y_inc = self.cam.OffsetY.GetInc()
        except Exception:
            self.width_min = self.height_min = 0
            self.width_max = self.height_max = 0
            self.offset_x_min = self.offset_y_min = 0
            self.offset_x_max = self.offset_y_max = 0
    
    def reset_camera(self):
        """
        Reset complet ca la deconectare fizică:
        """
        try:
            print("🔁 Reset software complet — cameră + sistem")
            self.cam.EndAcquisition()
            self.cam.DeInit()
            self.cam_list.Clear()
            self.cam_list = self.system.GetCameras()
            if self.cam_list.GetSize() == 0:
                raise RuntimeError("‼️ Nicio cameră detectată după reset.")

            self.cam = self.cam_list.GetByIndex(0)
            self.cam.Init()

            try:
                self.cam.PixelFormat.SetValue(PySpin.PixelFormat_BayerRG8)
            except:
                self.cam.PixelFormat.SetValue(PySpin.PixelFormat_Mono8)

            self.cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)

            if hasattr(self.cam, "AcquisitionFrameRateEnable"):
                self.cam.AcquisitionFrameRateEnable.SetValue(True)
                fps_reset = 20.0
                fps_min = self.cam.AcquisitionFrameRate.GetMin()
                fps_max = self.cam.AcquisitionFrameRate.GetMax()
                if fps_min <= fps_reset <= fps_max:
                    self.cam.AcquisitionFrameRate.SetValue(fps_reset)
                    print(f"✅ FPS resetat la {fps_reset}")
                else:
                    print(f"⚠️ FPS dorit ({fps_reset}) e în afara limitelor.")

            width  = self.cam.Width.GetMax()
            height = self.cam.Height.GetMax()
            self.cam.Width.SetValue(width)
            self.cam.Height.SetValue(height)
            print(f"✅ Rezoluție resetată la {width}x{height}")

            try:
                self.cam.OffsetX.SetValue(0)
                self.cam.OffsetY.SetValue(0)
                print("✅ Offset resetat la (0,0)")
            except:
                print("⚠️ Offset nu a putut fi resetat (poate nu este suportat)")

            self.cam.BeginAcquisition()
            print("✅ Camera complet resetată și funcțională")

        except Exception as e:
            print(f"‼️ Eroare la reset_camera: {e}")
            import traceback
            traceback.print_exc()

    def get_frame(self):
        """
        Obține un frame valid
        """
        try:
            image_result = self.cam.GetNextImage(PySpin.EVENT_TIMEOUT_INFINITE)

            if image_result.IsIncomplete():
                print("⚠️ Frame incomplet — ignorat.")
                image_result.Release()
                return None  # doar sărim peste

            data = image_result.GetNDArray()
            pf = self.cam.PixelFormat.GetCurrentEntry().GetSymbolic()

            if pf == "Mono8":
                frame = cv2.merge([data, data, data])
            elif pf == "BayerRG8":
                frame = cv2.cvtColor(data, cv2.COLOR_BAYER_RG2BGR)
            else:
                frame = data

            image_result.Release()
            return frame

        except Exception as e:
            print(f"‼️ Eroare la get_frame(): {e}")
            return None



    def get_resolution(self):
        try:
            return self.cam.Width.GetValue(), self.cam.Height.GetValue()
        except Exception as e:
            print(f"Eroare la get_resolution(): {e}")
            return 800, 600
        
    def release(self):
        #Oprește achiziția și eliberează resursele camerei și sistemului.
        try:
            self.cam.EndAcquisition()
            self.cam.DeInit()
        except Exception:
            pass
        try:
            self.cam_list.Clear()
            self.system.ReleaseInstance()
        except Exception:
            pass

    def set_gain_manual(self, value):
        #Setează manual valoarea de gain
        try:
            self.cam.GainAuto.SetValue(PySpin.GainAuto_Off)
            self.cam.Gain.SetValue(float(value))
        except Exception as e:
            print(f"Eroare la setarea gain-ului manual: {e}")

    def set_exposure_manual(self, value):
        #Sează manual timpul de expunere
        try:
            self.cam.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)
            self.cam.ExposureTime.SetValue(float(value))
        except Exception as e:
            print(f"Eroare la setarea expunerii manuale: {e}")

    def set_frame_rate(self, fps):
        try:
            min_fps = self.cam.AcquisitionFrameRate.GetMin()
            max_fps = self.cam.AcquisitionFrameRate.GetMax()

            if not (min_fps <= fps <= max_fps):
                print(f"⚠️ FPS {fps} e în afara limitelor: {min_fps} – {max_fps}")
                return

            if hasattr(self.cam, 'AcquisitionFrameRateEnable'):
                self.cam.AcquisitionFrameRateEnable.SetValue(True)

            # Doar dacă e necesar, oprim stream-ul
            self.cam.EndAcquisition()
            self.cam.AcquisitionFrameRate.SetValue(float(fps))
            self.cam.BeginAcquisition()

            print(f"✅ FPS setat la {fps}")
            self.max_fps = max_fps
        except Exception as e:
            print(f"‼️ Eroare la setarea fps-ului: {e}")

    def set_auto_gain(self, mode, manual_value=None):
        #Setări automate pentru gain. Mode: 'Off', 'Once', 'Continuous'.
        try:
            if mode == "Off":
                self.cam.GainAuto.SetValue(PySpin.GainAuto_Off)
                if manual_value is not None:
                    self.cam.Gain.SetValue(float(manual_value))
            elif mode == "Once":
                self.cam.GainAuto.SetValue(PySpin.GainAuto_Once)
            elif mode == "Continuous":
                self.cam.GainAuto.SetValue(PySpin.GainAuto_Continuous)
        except Exception as e:
            print(f"Eroare la setarea modulului de gain auto: {e}")

    def set_auto_exposure(self, mode, manual_value=None):
        #Setări automate pentru expunere. Mode: 'Off', 'Once', 'Continuous'.
        try:
            if mode == "Off":
                self.cam.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)
                if manual_value is not None:
                    self.cam.ExposureTime.SetValue(float(manual_value))
            elif mode == "Once":
                self.cam.ExposureAuto.SetValue(PySpin.ExposureAuto_Once)
            elif mode == "Continuous":
                self.cam.ExposureAuto.SetValue(PySpin.ExposureAuto_Continuous)
        except Exception as e:
            print(f"Eroare la setarea modulului de expunere auto: {e}")

    def set_auto_white_balance(self, mode, wb_value=None):
        #Setări automate pentru balans de alb. Mode: 'Off', 'Once', 'Continuous'.
        try:
            if mode == "Off":
                self.cam.BalanceWhiteAuto.SetValue(PySpin.BalanceWhiteAuto_Off)
                if wb_value is not None:
                    # valorea manuală balans alb
                    self.cam.BalanceRatioSelector.SetValue(PySpin.BalanceRatioSelector_Red)
                    self.cam.BalanceRatio.SetValue(float(wb_value))
            elif mode == "Once":
                self.cam.BalanceWhiteAuto.SetValue(PySpin.BalanceWhiteAuto_Once)
            elif mode == "Continuous":
                self.cam.BalanceWhiteAuto.SetValue(PySpin.BalanceWhiteAuto_Continuous)
        except Exception as e:
            print(f"Eroare la setarea balansului de alb auto: {e}")

    def set_pixel_format(self, format_name):
        #Setează formatul de pixel (de exemplu 'Mono8' sau 'BayerRG8').
        try:
            self.cam.EndAcquisition()
        except Exception:
            pass
        try:
            if format_name == "Mono8":
                self.cam.PixelFormat.SetValue(PySpin.PixelFormat_Mono8)
            elif format_name == "BayerRG8":
                self.cam.PixelFormat.SetValue(PySpin.PixelFormat_BayerRG8)
        except Exception as e:
            print(f"Eroare la setarea formatului pixel: {e}")
        finally:
            # Reîncepem achiziția după schimbarea formatului
            self.cam.BeginAcquisition()

    def set_resolution(self, width, height):
        try:
            print(f"📐 Setez rezoluția: {width}x{height}")
            self.cam.EndAcquisition()

            # 🧱 Obținem capabilitățile camerei
            width_max = self.cam.Width.GetMax()
            height_max = self.cam.Height.GetMax()
            width_inc = self.cam.Width.GetInc()
            height_inc = self.cam.Height.GetInc()

            # 🔐 Definim minimul acceptat de cameră
            min_width = max(width_inc, 64)
            min_height = max(height_inc, 64)

            # ✅ Verificăm și corectăm dacă valorile sunt prea mici
            if width < min_width or height < min_height:
                print(f"⚠️ Rezoluția {width}x{height} e prea mică. Se setează la 640x480.")
                width, height = 640, 480

            # ✅ Limităm la maxim permis
            width = min(width, width_max)
            height = min(height, height_max)

            # ✅ Ajustăm la increment corect
            width -= width % width_inc
            height -= height % height_inc

            self.cam.Width.SetValue(width)
            self.cam.Height.SetValue(height)

            print(f"✅ Rezoluție aplicată: {width}x{height}")
            self.cam.BeginAcquisition()

        except Exception as e:
            print(f"‼️ Eroare la setarea rezoluției: {e}")
            import traceback
            traceback.print_exc()

    def set_offset(self, x_offset, y_offset):
        try:
            x = int(x_offset)
            y = int(y_offset)

            xmin, xmax, xinc = self.offset_x_min, self.offset_x_max, self.offset_x_inc
            ymin, ymax, yinc = self.offset_y_min, self.offset_y_max, self.offset_y_inc

            if xmax == 0 or ymax == 0:
                print("⚠️ Offsetul nu este suportat de cameră.")
                return
            
            x = max(xmin, min(x, xmax))
            y = max(ymin, min(y, ymax))
            x_adj = xmin + ((x - xmin) // xinc) * xinc
            y_adj = ymin + ((y - ymin) // yinc) * yinc

            # Oprim achiziția
            self.cam.EndAcquisition()

            width  = self.cam.Width.GetValue()
            height = self.cam.Height.GetValue()
            self.cam.Width.SetValue(width)
            self.cam.Height.SetValue(height)

            # Aplicăm offset
            self.cam.OffsetX.SetValue(x_adj)
            self.cam.OffsetY.SetValue(y_adj)

            # Restart achiziție
            self.cam.BeginAcquisition()

            print(f"✅ Offset setat și achiziție repornită: X={x_adj}, Y={y_adj}")
            self.last_applied_offset = (x_adj, y_adj)
        except Exception as e:
            print(f"‼️ Eroare la setarea offsetului: {e}")
            import traceback
            traceback.print_exc()


    def center_roi(self):
        """
        Centrează imaginea în mijlocul senzorului, ajustând offsetul la cel mai apropiat multiplu valid.
        """
        try:
            # Obținem dimensiuni actuale și maxime
            width_curent  = self.cam.Width.GetValue()
            height_curent = self.cam.Height.GetValue()
            width_max     = self.cam.Width.GetMax()
            height_max    = self.cam.Height.GetMax()

            # Obținem incrementul de offset
            xinc = self.offset_x_inc
            yinc = self.offset_y_inc

            # Calculează offsetul ideal pentru centrare
            x_offset = ((width_max - width_curent) // 2) // xinc * xinc
            y_offset = ((height_max - height_curent) // 2) // yinc * yinc

            # Oprim și restartăm achiziția ca să aplicăm în siguranță
            self.cam.EndAcquisition()

            # Reconfirmăm width și height pentru ca offset să se aplice corect
            self.cam.Width.SetValue(width_curent)
            self.cam.Height.SetValue(height_curent)

            self.cam.OffsetX.SetValue(x_offset)
            self.cam.OffsetY.SetValue(y_offset)

            self.cam.BeginAcquisition()

            print(f"✅ ROI centrat la mijloc: X={x_offset}, Y={y_offset}")
        except Exception as e:
            print(f"‼️ Eroare la centrarea ROI-ului: {e}")
            import traceback
            traceback.print_exc()