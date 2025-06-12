# feature_extraction/face_mesh.py
"""
Modul pentru detectarea feței și landmark-urilor faciale cu MediaPipe FaceMesh.
"""
import cv2
import mediapipe as mp

class FaceMeshDetector:
    def __init__(self, max_faces=1, min_detection_confidence=0.5):
        self.mp_face = mp.solutions.face_mesh
        self.face_mesh = self.mp_face.FaceMesh(static_image_mode=False,
                                               max_num_faces=max_faces,
                                               refine_landmarks=True,
                                               min_detection_confidence=min_detection_confidence)

    def find_landmarks(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        if results.multi_face_landmarks:
            # Returnează landmarks pentru prima față detectată
            return results.multi_face_landmarks[0].landmark
        return None

    def close(self):
        #Eliberăm resurse MediaPipe.
        self.face_mesh.close()
