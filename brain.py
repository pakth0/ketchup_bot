import asyncio
import threading
from face_tracker import FaceTracker
from turret import PanTiltTurretController
from nxt.motor import Port
import math
import cv2
from hotdog_recognizer import HotdogRecognizer
from event_system import EventEmitter
import time


class Brain:
    def __init__(self, face_threshold_distance=150, glizzy_threshold_distance=100):
        # Initialize turret controller with retry logic
        try:
            print("🔌 Initializing turret controller...")
            self.controller = PanTiltTurretController(Port.B, Port.A)
            print("✅ Turret controller initialized successfully")
        except Exception as e:
            print(f"🚨 FATAL ERROR: Failed to initialize turret controller: {e}")
            print("🚨 Brain cannot start without turret controller")
            print("🛑 Exiting program...")
            raise SystemExit(f"Brain initialization failed: {e}")
            
        self.face_threshold_distance = face_threshold_distance
        self.glizzy_threshold_distance = glizzy_threshold_distance
        self.cap = cv2.VideoCapture(0) #1920x1080
        self.center_x = 960
        self.center_y = 540
        self.face_tracker = FaceTracker(self.cap)
        self.hotdog_recognizer = HotdogRecognizer(self.cap)
        self.fireable = False
        self._setup_event_listeners()

        self.running = False
        
        # Current detection data
        self.current_mode = None  # 'face' or 'hotdog'
        
        # Hotdog firing delay tracking
        self.hotdog_center_start_time = None
        self.hotdog_fire_delay = 1.0  # 1 second delay before firing
        self.hotdog_in_center = False

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

        #if face is in dead zone, fire solenoid
        if self.fireable and abs(x - self.center_x) < self.face_threshold_distance and abs(y - self.center_y) < self.face_threshold_distance:
            print("Face is in dead zone, FIRE")
            self.controller.fire(release_time=10)

        # --- tunables (play with these) ---
        MIN_POWER_PAN  = 18    # barely enough to overcome friction
        MAX_POWER_PAN  = 100
        MIN_POWER_TILT = 18
        MAX_POWER_TILT = 100

        MIN_STEP_PAN_DEG  = 1  # small taps when close
        MAX_STEP_PAN_DEG  = 20 # bigger chunks when far
        MIN_STEP_TILT_DEG = 1
        MAX_STEP_TILT_DEG = 10

        # Use your dead zone as a threshold; nothing happens inside it
        DEAD_X = self.face_threshold_distance
        DEAD_Y = self.face_threshold_distance

        # Estimate max possible error as distance from center to edge
        # (assuming center_x/center_y are half-width/half-height)
        MAX_DX = max(self.center_x, 1)
        MAX_DY = max(self.center_y, 1)

        def map_range(val, in_min, in_max, out_min, out_max):
            # linear map with clamping
            if in_max <= in_min:
                return out_min
            t = max(0.0, min(1.0, (val - in_min) / (in_max - in_min)))
            return out_min + t * (out_max - out_min)

        pan_power = 0
        pan_angle = 0
        tilt_power = 0
        tilt_angle = 0

        # Horizontal (pan)
        dx = x - self.center_x
        if abs(dx) > DEAD_X:
            # scale power & step by how far past the dead zone we are
            mag = abs(dx)
            scaled_power = map_range(mag, DEAD_X, MAX_DX, MIN_POWER_PAN, MAX_POWER_PAN)
            scaled_step  = map_range(mag, DEAD_X, MAX_DX, MIN_STEP_PAN_DEG, MAX_STEP_PAN_DEG)

            if dx > 0:
                print("Face is to the left")
                pan_power = -int(round(scaled_power))   # negative = counter the left offset (clockwise per your comment)
            else:
                print("Face is to the right")
                pan_power = int(round(scaled_power))

            pan_angle = int(round(scaled_step))

        # Vertical (tilt)
        dy = y - self.center_y
        if abs(dy) > DEAD_Y:
            mag = abs(dy)
            scaled_power = map_range(mag, DEAD_Y, MAX_DY, MIN_POWER_TILT, MAX_POWER_TILT)
            scaled_step  = map_range(mag, DEAD_Y, MAX_DY, MIN_STEP_TILT_DEG, MAX_STEP_TILT_DEG)

            if dy < 0:
                print("Face is above")
                tilt_power = -int(round(scaled_power))  # negative = up (per your comment)
            else:
                print("Face is below")
                tilt_power = int(round(scaled_power))

            tilt_angle = int(round(scaled_step))

        # Move both axes together (only if at least one needs to move)
        if pan_angle or tilt_angle:
            self.controller.rotate_both(pan_power, pan_angle, tilt_power, tilt_angle)

    
    def _on_face_lost(self, event):
        print("Face lost")
        # Use non-blocking reset to avoid camera freezing
        try:
            self.controller.reset()
        except Exception as e:
            print(f"Reset error (non-blocking): {e}")
        pass
     
    def _on_hotdog_detected(self, event):
        x, y = event['coordinates']
        print(f"hotdog detected at {x}, {y}")

        # Check if hotdog is in the center zone
        is_in_center = (self.fireable and 
                       abs(x - self.center_x) < self.hotdog_threshold_distance and 
                       abs(y - self.center_y) < self.hotdog_threshold_distance)
        
        if is_in_center:
            current_time = time.time()
            
            if not self.hotdog_in_center:
                # Hotdog just entered center zone - start timer
                print("Hotdog entered center zone - starting 1 second timer")
                self.hotdog_center_start_time = current_time
                self.hotdog_in_center = True
            else:
                # Hotdog was already in center - check if enough time has passed
                time_in_center = current_time - self.hotdog_center_start_time
                print(f"Hotdog in center for {time_in_center:.1f} seconds")
                
                if time_in_center >= self.hotdog_fire_delay:
                    print("Hotdog stayed in center for 1 second - FIRE!")
                    self.controller.fire(release_time=0.5)
                    self.hotdog_recognizer.stop_tracking()
                    self.controller.reset()
                    # Reset the tracking state
                    self.hotdog_in_center = False
                    self.hotdog_center_start_time = None
        else:
            # Hotdog is not in center zone - reset timer if it was previously in center
            if self.hotdog_in_center:
                print("Hotdog moved out of center zone - resetting timer")
                self.hotdog_in_center = False
                self.hotdog_center_start_time = None


        # --- tunables (play with these) ---
        MIN_POWER_PAN  = 18    # barely enough to overcome friction
        MAX_POWER_PAN  = 100
        MIN_POWER_TILT = 18
        MAX_POWER_TILT = 100

        MIN_STEP_PAN_DEG  = 1  # small taps when close
        MAX_STEP_PAN_DEG  = 20 # bigger chunks when far
        MIN_STEP_TILT_DEG = 1
        MAX_STEP_TILT_DEG = 10

        # Use your dead zone as a threshold; nothing happens inside it
        DEAD_X = self.glizzy_threshold_distance
        DEAD_Y = self.glizzy_threshold_distance

        # Estimate max possible error as distance from center to edge
        # (assuming center_x/center_y are half-width/half-height)
        MAX_DX = max(self.center_x, 1)
        MAX_DY = max(self.center_y, 1)

        def map_range(val, in_min, in_max, out_min, out_max):
            # linear map with clamping
            if in_max <= in_min:
                return out_min
            t = max(0.0, min(1.0, (val - in_min) / (in_max - in_min)))
            return out_min + t * (out_max - out_min)

        pan_power = 0
        pan_angle = 0
        tilt_power = 0
        tilt_angle = 0

        # Horizontal (pan)
        dx = x - self.center_x
        if abs(dx) > DEAD_X:
            # scale power & step by how far past the dead zone we are
            mag = abs(dx)
            scaled_power = map_range(mag, DEAD_X, MAX_DX, MIN_POWER_PAN, MAX_POWER_PAN)
            scaled_step  = map_range(mag, DEAD_X, MAX_DX, MIN_STEP_PAN_DEG, MAX_STEP_PAN_DEG)

            if dx > 0:
                print("Face is to the left")
                pan_power = -int(round(scaled_power))   # negative = counter the left offset (clockwise per your comment)
            else:
                print("Face is to the right")
                pan_power = int(round(scaled_power))

            pan_angle = int(round(scaled_step))

        # Vertical (tilt)
        dy = y - self.center_y
        if abs(dy) > DEAD_Y:
            mag = abs(dy)
            scaled_power = map_range(mag, DEAD_Y, MAX_DY, MIN_POWER_TILT, MAX_POWER_TILT)
            scaled_step  = map_range(mag, DEAD_Y, MAX_DY, MIN_STEP_TILT_DEG, MAX_STEP_TILT_DEG)

            if dy < 0:
                print("Face is above")
                tilt_power = -int(round(scaled_power))  # negative = up (per your comment)
            else:
                print("Face is below")
                tilt_power = int(round(scaled_power))

            tilt_angle = int(round(scaled_step))

        # Move both axes together (only if at least one needs to move)
        if pan_angle or tilt_angle:
            self.controller.rotate_both(pan_power, pan_angle, tilt_power, tilt_angle)

    def _on_hotdog_lost(self, event):
        print("Hotdog lost")
        # Reset the timing state when hotdog is lost
        if self.hotdog_in_center:
            print("Resetting hotdog center timer - hotdog lost")
            self.hotdog_in_center = False
            self.hotdog_center_start_time = None
        # self.controller.reset()
        pass
    
    def _on_error(self, event):
        print(f"Error: {event}")
    
    def _on_frame_ready(self, event):
        #skip gui for now
        pass



    def start_tracking_faces(self):
        self.hotdog_recognizer.stop_tracking()
        self.current_mode = 'face'
        self.face_tracker.start_tracking()
    
    def start_tracking_hotdogs(self):
        self.face_tracker.stop_tracking()
        self.current_mode = 'hotdog'
        self.hotdog_recognizer.start_tracking()
    
    def stop(self):
        self.face_tracker.stop_tracking()
        self.hotdog_recognizer.stop_tracking()
        self.current_mode = None

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
        self.controller.destroy()
        self.hotdog_recognizer.destroy()
        self.cap.release()


if __name__ == "__main__":
    brain = Brain()

    try:
        brain_thread = threading.Thread(target=brain.run, daemon=True)
        brain_thread.start()

        brain.start_tracking_faces()
        # brain.start_tracking_hotdogs()

        brain_thread.join()
    except KeyboardInterrupt:
        print("stopping brain...")
    finally:
        brain.destroy()
