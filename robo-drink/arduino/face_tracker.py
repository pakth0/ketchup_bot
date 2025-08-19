import cv2
from event_system import EventEmitter
import threading
import time
import math

class FaceTracker(EventEmitter):
    def __init__(self, cv2_cap: cv2.VideoCapture, fps=30, threshold_distance=30):
        super().__init__()
        self.cap = cv2_cap
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.fps = fps
        self.running = False
        self.thread = None
        self.last_face = None
        self.threshold_distance = threshold_distance
    
    def start_tracking(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._tracking_loop)
            self.thread.start()
    
    def stop_tracking(self):
        self.running = False
        if self.thread:
            self.thread.join()
    
    def _tracking_loop(self):
        frame_time = 1 / self.fps

        while self.running:
            start_time = time.time()
            try:
                ret, frame = self.cap.read()
                # print(f"{frame.shape[1]}x{frame.shape[0]}")
                if not ret:
                    self.emit('error', 'Failed to read frame')
                    break
                face = self.get_biggest_face_coordinates(frame)
                if face is not None:
                    x_center, y_center = map(int, self.get_centroid(face))
                    if self.should_track_face(x_center, y_center):
                        self.emit('face_detected', {
                            'coordinates': (x_center, y_center),
                            'box': face,
                            'frame': frame,
                        })
                    self.emit('face_updated', {
                        'coordinates': (x_center, y_center),
                        'box': face,
                        'frame': frame,
                    })
                elif self.last_face is not None:
                    self.emit('face_lost', None)
                    self.last_face = None
            except Exception as e:
                self.emit('error', f'Error in tracking loop: {e}')
            finally:
                elapsed_time = time.time() - start_time
                sleep_time = max(0, frame_time - elapsed_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)

    def get_centroid(self, box):
        return (box[0] + box[2] / 2, box[1] + box[3] / 2)
    
    def should_track_face(self, x_center, y_center):
        if self.last_face is None:
            return True
        distance = math.sqrt((x_center - self.last_face[0])**2 + (y_center - self.last_face[1])**2)
        return distance > self.threshold_distance

    def get_biggest_face_coordinates(self, frame, min_size=(30, 30)):
        '''
        Returns the coordinates of the biggest face in the frame, or None if no face is found
        '''
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=min_size)
        if len(faces) == 0:
            return None
        sorted_faces = sorted(faces, key=lambda x: x[2] * x[3], reverse=True)
        return sorted_faces[0]
    

    def destroy(self):
        self.stop_tracking()

if __name__ == "__main__":
    face_tracker = FaceTracker()
    face_tracker.track_faces()


