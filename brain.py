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
        self.controller = PanTiltTurretController(Port.B, Port.A)
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
        self.display_thread = None
        self.display_running = False
        
        # Current detection data for display
        self.current_frame = None
        self.current_face_box = None
        self.current_hotdog_box = None
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
        
        # Store detection data for display
        self.current_frame = event['frame'].copy()
        self.current_face_box = event['box']
        self.current_hotdog_box = None  # Clear hotdog detection when face is active

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

    
    async def _on_face_lost(self, event):
        print("Face lost")
        self.current_face_box = None  # Clear face detection when lost
        await self.controller.async_reset()
        pass
     
    def _on_hotdog_detected(self, event):
        x, y = event['coordinates']
        print(f"hotdog detected at {x}, {y}")
        
        # Store detection data for display
        self.current_frame = event['frame'].copy()
        self.current_hotdog_box = event['box']
        self.current_face_box = None  # Clear face detection when hotdog is active

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
        self.current_hotdog_box = None  # Clear hotdog detection when lost
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

    def _display_loop(self):
        """Display loop that shows current camera feed with bounding boxes"""
        cv2.namedWindow("Ketchup Bot - Detection View", cv2.WINDOW_AUTOSIZE)
        
        while self.display_running:
            try:
                # Get current frame from camera if no detection frame is available
                display_frame = None
                if self.current_frame is not None:
                    display_frame = self.current_frame.copy()
                else:
                    ret, frame = self.cap.read()
                    if ret:
                        display_frame = frame
                
                if display_frame is not None:
                    # Draw crosshair at center
                    cv2.line(display_frame, (self.center_x - 50, self.center_y), (self.center_x + 50, self.center_y), (255, 255, 255), 2)
                    cv2.line(display_frame, (self.center_x, self.center_y - 50), (self.center_x, self.center_y + 50), (255, 255, 255), 2)
                    
                    # Draw dead zone boundaries
                    if self.current_mode == 'face':
                        dead_zone_size = self.face_threshold_distance
                        cv2.rectangle(display_frame, 
                                    (self.center_x - dead_zone_size, self.center_y - dead_zone_size),
                                    (self.center_x + dead_zone_size, self.center_y + dead_zone_size),
                                    (0, 255, 255), 2)  # Yellow for face dead zone
                    elif self.current_mode == 'hotdog':
                        dead_zone_size = self.glizzy_threshold_distance
                        cv2.rectangle(display_frame, 
                                    (self.center_x - dead_zone_size, self.center_y - dead_zone_size),
                                    (self.center_x + dead_zone_size, self.center_y + dead_zone_size),
                                    (0, 165, 255), 2)  # Orange for hotdog dead zone
                    
                    # Draw face detection
                    if self.current_face_box is not None:
                        x, y, w, h = self.current_face_box
                        cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 3)  # Green for faces
                        cv2.putText(display_frame, "FACE", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        
                        # Draw center point
                        center_x = x + w // 2
                        center_y = y + h // 2
                        cv2.circle(display_frame, (center_x, center_y), 5, (0, 255, 0), -1)
                    
                    # Draw hotdog detection
                    if self.current_hotdog_box is not None:
                        x, y, w, h = self.current_hotdog_box
                        cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 0, 255), 3)  # Red for hotdogs
                        cv2.putText(display_frame, "HOTDOG", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        
                        # Draw center point
                        center_x = x + w // 2
                        center_y = y + h // 2
                        cv2.circle(display_frame, (center_x, center_y), 5, (0, 0, 255), -1)
                    
                    # Show current mode and fireable status
                    mode_text = f"Mode: {self.current_mode or 'IDLE'}"
                    fire_text = f"Fireable: {'YES' if self.fireable else 'NO'}"
                    cv2.putText(display_frame, mode_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    cv2.putText(display_frame, fire_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    
                    cv2.imshow("Ketchup Bot - Detection View", display_frame)
                
                # Check for exit key
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
                time.sleep(0.03)  # ~30 FPS
                
            except Exception as e:
                print(f"Display error: {e}")
                break
        
        cv2.destroyWindow("Ketchup Bot - Detection View")

    def start_display(self):
        """Start the display window in a separate thread"""
        if not self.display_running:
            self.display_running = True
            self.display_thread = threading.Thread(target=self._display_loop, daemon=True)
            self.display_thread.start()
            print("Display window started - press 'q' in the window to close")

    def stop_display(self):
        """Stop the display window"""
        self.display_running = False
        if self.display_thread:
            self.display_thread.join()

    def start_tracking_faces(self):
        self.hotdog_recognizer.stop_tracking()
        self.current_mode = 'face'
        self.current_hotdog_box = None
        self.face_tracker.start_tracking()
    
    def start_tracking_hotdogs(self):
        self.face_tracker.stop_tracking()
        self.current_mode = 'hotdog'
        self.current_face_box = None
        self.hotdog_recognizer.start_tracking()
    
    def stop(self):
        self.face_tracker.stop_tracking()
        self.hotdog_recognizer.stop_tracking()
        self.current_mode = None

    def run(self):
        self.running = True
        print("starting brain... use start_tracking_faces() or start_tracking_hotdogs() to start tracking")
        
        # Start the display window automatically
        self.start_display()
        
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
        self.stop_display()  # Stop the display window
        self.face_tracker.destroy()
        self.controller.destroy()
        self.hotdog_recognizer.destroy()
        self.cap.release()
        cv2.destroyAllWindows()


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
