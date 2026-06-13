#!/usr/bin/env python3
"""
Serveur Flask pour streaming vidéo en temps réel avec PiCamera
Compatible avec Raspberry Pi 4 et PiCamera
"""

from flask import Flask, Response
import cv2
import threading
import time
from io import BytesIO
import base64

# Pour Raspberry Pi avec PiCamera (legacy)
try:
    import picamera
    import picamera.array
    PICAMERA_AVAILABLE = True
except ImportError:
    PICAMERA_AVAILABLE = False
    print("PiCamera non disponible, utilisation de la webcam USB")

# Pour Raspberry Pi avec libcamera (Raspberry Pi OS Bullseye+)
try:
    from picamera2 import Picamera2
    PICAMERA2_AVAILABLE = True
except ImportError:
    PICAMERA2_AVAILABLE = False

app = Flask(__name__)

class VideoCamera:
    def __init__(self):
        self.camera = None
        self.frame = None
        self.lock = threading.Lock()
        self.running = False

        # Initialiser la caméra selon la disponibilité
        if PICAMERA2_AVAILABLE:
            self._init_picamera2()
        elif PICAMERA_AVAILABLE:
            self._init_picamera()
        else:
            self._init_usb_camera()

    def _init_picamera2(self):
        """Initialiser PiCamera2 (recommandé pour Raspberry Pi OS récent)"""
        try:
            self.camera = Picamera2()
            camera_config = self.camera.create_preview_configuration(
                main={"format": 'YUV420', "size": (3280, 2464)}
            )
            self.camera.configure(camera_config)
            self.camera.start()
            self.camera_type = "picamera2"
            print("PiCamera2 initialisée avec succès")
        except Exception as e:
            print(f"Erreur PiCamera2: {e}")
            self._init_usb_camera()

    def _init_picamera(self):
        """Initialiser PiCamera (legacy)"""
        try:
            self.camera = picamera.PiCamera()
            self.camera.resolution = (640, 480)
            self.camera.framerate = 30
            self.camera.rotation = 0
            time.sleep(2)
            self.camera_type = "picamera"
            print("PiCamera legacy initialisée avec succès")
        except Exception as e:
            print(f"Erreur PiCamera legacy: {e}")
            self._init_usb_camera()

    def _init_usb_camera(self):
        """Initialiser caméra USB de secours"""
        try:
            self.camera = cv2.VideoCapture(0)
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            self.camera_type = "usb"
            print("Caméra USB initialisée avec succès")
        except Exception as e:
            print(f"Erreur caméra USB: {e}")
            self.camera = None
            self.camera_type = None

    def get_frame(self):
        """Capturer une frame selon le type de caméra"""
        if not self.camera:
            return None

        try:
            if self.camera_type == "picamera2":
                frame = self.camera.capture_array()
                # Convertir XRGB8888 vers BGR pour OpenCV
                # frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                # # Correction de balance des blancs manuelle pour effets IR
                # frame = cv2.convertScaleAbs(frame, alpha=1.0, beta=0)
                frame = cv2.cvtColor(frame, cv2.COLOR_YUV2BGR_I420)
                return frame

            elif self.camera_type == "picamera":
                with picamera.array.PiRGBArray(self.camera) as stream:
                    self.camera.capture(stream, format='bgr')
                    frame = stream.array
                    return frame

            elif self.camera_type == "usb":
                ret, frame = self.camera.read()
                if ret:
                    return frame

        except Exception as e:
            print(f"Erreur capture: {e}")
            return None

        return None

    def generate_frames(self):
        """Générateur de frames pour le streaming"""
        while True:
            frame = self.get_frame()
            if frame is not None:
                ret, buffer = cv2.imencode('.jpg', frame, 
                                         [cv2.IMWRITE_JPEG_QUALITY, 70])
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            else:
                time.sleep(0.1)

    def __del__(self):
        if self.camera:
            try:
                if self.camera_type == "picamera2":
                    self.camera.stop()
                elif self.camera_type == "picamera":
                    self.camera.close()
                elif self.camera_type == "usb":
                    self.camera.release()
            except:
                pass

camera = VideoCamera()

@app.route('/')
def index():
    return """<html><body><h1>Flux vidéo</h1><img src='/video_feed'></body></html>"""

@app.route('/video_feed')
def video_feed():
    return Response(camera.generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/status')
def status():
    if camera.camera:
        return {
            'status': 'OK',
            'camera_type': camera.camera_type,
            'message': 'Caméra fonctionnelle'
        }
    else:
        return {
            'status': 'ERROR',
            'camera_type': None,
            'message': 'Aucune caméra détectée'
        }

if __name__ == '__main__':
    print("\U0001f680 Démarrage du serveur Flask pour PiCamera...")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
