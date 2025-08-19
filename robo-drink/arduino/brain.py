import asyncio
import threading
from face_tracker import FaceTracker
# from turret import PanTiltTurretController
from nxt.motor import Port
import math
import cv2
from hotdog_recognizer import HotdogRecognizer
from event_system import EventEmitter
import time

class Brain:
    def __init__(self, threshold_distance=30):
        # self.controller = PanTiltTurretController(Port.A, Port.B)
        self.threshold_distance = threshold_distance
        self.cap = cv2.VideoCapture(0)
        self.face_tracker = FaceTracker(self.cap)
        self.hotdog_recognizer = HotdogRecognizer(self.cap)
        self._setup_event_listeners()

        self.running = False
        self.display_thread = None

    def _setup_event_listeners(self):
        self.face_tracker.on('face_detected', self._on_face_detected)
        self.face_tracker.on('face_lost', self._on_face_lost)
        self.hotdog_recognizer.on('hotdog_detected', self._on_hotdog_detected)
        self.hotdog_recognizer.on('hotdog_lost', self._on_hotdog_lost)
        self.face_tracker.on('error', self._on_error)
        self.hotdog_recognizer.on('error', self._on_error)

    def _on_face_detected(self, event):
        x, y = event['coordinates']
        print(f"Face detected at {x}, {y}")
        # self.controller.aim_at_coordinates(event['x'], event['y'])
    
    def _on_face_lost(self, event):
        print("Face lost")
        # self.controller.reset()
        pass
    
    def _on_hotdog_detected(self, event):
        print(f"Hotdog detected at {event['coordinates']}")
        # self.controller.aim_at_coordinates(event['x'], event['y'])

    def _on_hotdog_lost(self, event):
        print("Hotdog lost")
        # self.controller.reset()
        pass
    
    def _on_error(self, event):
        print(f"Error: {event}")
    
    def _on_frame_ready(self, event):
        #skip gui for now
        pass

    def start_tracking_faces(self):
        self.hotdog_recognizer.stop_tracking()
        self.face_tracker.start_tracking()
    
    def start_tracking_hotdogs(self):
        self.face_tracker.stop_tracking()
        self.hotdog_recognizer.start_tracking()
    
    def stop(self):
        self.face_tracker.stop_tracking()
        self.hotdog_recognizer.stop_tracking()

    def run(self):
        self.running = True
        print("starting brain... use start_tracking_faces() or start_tracking_hotdogs() to start tracking")
        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("stopping brain...")
            self.stop()
        finally:
            self.destroy()

                     
    def destroy(self):
        self.stop()
        self.face_tracker.destroy()
        # self.controller.destroy()
        self.hotdog_recognizer.destroy()
        self.cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    brain = Brain()
    
    try:
        brain_thread = threading.Thread(target=brain.run, daemon=True)
        brain_thread.start()

        # brain.start_tracking_faces()
        brain.start_tracking_hotdogs()

        brain_thread.join()
    except KeyboardInterrupt:
        print("stopping brain...")
    finally:
        brain.destroy()
