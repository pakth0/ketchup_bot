from ultralytics import YOLO
import cv2
import threading
import time
from event_system import EventEmitter

HOTDOG_CLASS_ID = 52

class HotdogRecognizer(EventEmitter):
    def __init__(self, cv2_cap, fps=10, threshold_distance=35):  # Lower FPS for YOLO processing
        super().__init__()
        self.cap = cv2_cap
        self.model = YOLO('yolov8n.pt')
        self.fps = fps
        self.running = False
        self.thread = None
        self.last_hotdog = None
        self.threshold_distance = threshold_distance
    
    def start_tracking(self):
        """Start hotdog tracking in a separate thread"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._tracking_loop, daemon=True)
            self.thread.start()
    
    def stop_tracking(self):
        """Stop hotdog tracking"""
        self.running = False
        if self.thread:
            self.thread.join()
    
    def _tracking_loop(self):
        """Main tracking loop that runs in separate thread"""
        frame_time = 1.0 / self.fps
        
        while self.running:
            start_time = time.time()
            
            try:
                success, frame = self.cap.read()
                # print(f"{frame.shape[1]}x{frame.shape[0]}")
                if not success:
                    self.emit('camera_error', 'Failed to read frame')
                    break
                
                hotdog_box = self.find_biggest_hotdog(frame)
                
                if hotdog_box is not None:
                    # Now hotdog_box is [x, y, w, h] format
                    x_center = hotdog_box[0] + hotdog_box[2] / 2
                    y_center = hotdog_box[1] + hotdog_box[3] / 2
                    
                    # Check if hotdog moved significantly
                    self.emit('hotdog_detected', {
                        'coordinates': (x_center, y_center),
                        'box': hotdog_box,
                        'frame': frame
                    })
                    self.last_hotdog = (x_center, y_center)
                
                elif self.last_hotdog is not None:
                    self.emit('hotdog_lost', None)
                    self.last_hotdog = None
                
                    
            except Exception as e:
                self.emit('tracking_error', f"Error in tracking loop: {e}")
                print(f"Hotdog tracking error: {e}")
            
            # Control frame rate
            elapsed = time.time() - start_time
            sleep_time = max(0, frame_time - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)

    
    def find_hotdogs(self, frame):
        """Find hotdog in frame, returns bounding box in [x, y, w, h] format or None"""
        results = self.model(frame, verbose=False)
        res = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                if int(box.cls) == HOTDOG_CLASS_ID:
                    # Convert from [x1, y1, x2, y2] to [x, y, w, h]
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    res.append([x1, y1, x2 - x1, y2 - y1])  # [x, y, width, height]
        return res
    
    def find_biggest_hotdog(self, frame):
        hotdogs = self.find_hotdogs(frame)
        if len(hotdogs) == 0:
            return None
        return max(hotdogs, key=lambda x: x[2] * x[3])
    
    def destroy(self):
        self.stop_tracking()
        if hasattr(self.model, 'close'):
            self.model.close()

if __name__ == "__main__":
    cv2_cap = cv2.VideoCapture(0)
    recognizer = HotdogRecognizer(cv2_cap=cv2_cap)
    cv2.namedWindow("Hotdog Tracker")
    while True:
        ret, frame = cv2_cap.read()
        if not ret:
            break
        box = recognizer.find_biggest_hotdog(frame)
        if box is not None:
            print(f"Hotdog detected: {box}")
            x, y, w, h = box
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.imshow("Hotdog Tracker", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cv2_cap.release()
    cv2.destroyAllWindows()