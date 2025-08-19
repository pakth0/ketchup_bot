import cv2
from ultralytics import YOLO
from event_system import EventEmitter
import threading
import time
import math

FACE_CLASS_ID = 0  # Assuming class ID for face is 0

class FaceTracker(EventEmitter):
    def __init__(self, cv2_cap: cv2.VideoCapture, fps=30, threshold_distance=30):
        super().__init__()
        self.cap = cv2_cap
        self.fps = fps
        self.model = YOLO('yolov11n-face.pt')
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
                    self.emit('face_detected', {
                        'coordinates': (x_center, y_center),
                        'box': face,
                        'frame': frame
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

    def find_faces(self, frame):
        """Find faces in frame, returns bounding box in [x, y, w, h] format or None"""
        results = self.model(frame, verbose=False)
        res = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # print(box.conf > 0.6)
                if int(box.cls) == FACE_CLASS_ID and box.conf > 0.6:  # Confidence threshold
                    # Convert from [x1, y1, x2, y2] to [x, y, w, h]
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    res.append([x1, y1, x2 - x1, y2 - y1])  # [x, y, width, height]
        return res

    def get_biggest_face_coordinates(self, frame, min_size=(30, 30)):
        '''
        Returns the coordinates of the biggest face in the frame, or None if no face is found
        '''
        faces = self.find_faces(frame)  # Assuming class 0 is face
        if len(faces) == 0:
            return None
        return max(faces, key=lambda x: x[2] * x[3])
    

    def destroy(self):
        self.stop_tracking()


if __name__ == "__main__":
    box = [None]  # Use a list to hold the box reference
    cv2_cap = cv2.VideoCapture(0)
    face_tracker = FaceTracker(cv2_cap=cv2_cap)
    face_tracker.on('face_detected', lambda data: box.__setitem__(0, data['box']))
    face_tracker.start_tracking()
    cv2.namedWindow("Face Tracker")
    while True:
        ret, frame = cv2_cap.read()
        if not ret:
            break
        if box[0] is not None:
            x, y, w, h = box[0]
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.imshow("Face Tracker", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


