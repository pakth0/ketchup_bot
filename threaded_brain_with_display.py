#!/usr/bin/env python3
"""
Threaded Brain with Proper Display Handling
"""

import threading
import time
import cv2
from brain import Brain

class ThreadedBrainWithDisplay:
    def __init__(self):
        self.brain = None
        self.brain_thread = None
        self.display_thread = None
        self.running = False
        
    def start_brain_thread(self):
        """Start the brain logic in a background thread"""
        print("🧠 Starting Brain logic thread...")
        
        # Create brain but don't start its display
        try:
            self.brain = Brain()
            print("✅ Brain created successfully")
        except SystemExit as e:
            print(f"🚨 Brain initialization failed: {e}")
            print("🛑 Cannot continue without brain - exiting...")
            raise
        except Exception as e:
            print(f"🚨 Unexpected error creating brain: {e}")
            print("🛑 Cannot continue - exiting...")
            raise SystemExit(f"Failed to create brain: {e}")
        
        # Start brain thread
        self.brain_thread = threading.Thread(target=self._run_brain_logic, daemon=True)
        self.brain_thread.start()
        
        # Wait for brain to initialize
        time.sleep(1)
        return self.brain
    
    def _run_brain_logic(self):
        """Run brain logic without display"""
        self.brain.running = True
        print("starting brain... use start_tracking_faces() or start_tracking_hotdogs() to start tracking")
        
        try:
            while self.brain.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("stopping brain...")
            self.brain.stop()
        finally:
            # Don't call destroy here, let main thread handle it
            pass
    
    def start_main_thread_display(self):
        """Start display in the main thread (safer for OpenCV on macOS)"""
        print("🖥️  Starting display in main thread...")
        
        if not self.brain:
            print("❌ Brain not initialized!")
            return
            
        cv2.namedWindow("Threaded Ketchup Bot", cv2.WINDOW_AUTOSIZE)
        
        try:
            while self.running:
                display_frame = None
                
                # Read directly from camera with timeout handling
                try:
                    ret, frame = self.brain.cap.read()
                    if ret:
                        display_frame = frame
                    else:
                        display_frame = None
                except Exception as e:
                    print(f"Camera read error: {e}")
                    display_frame = None
                
                if display_frame is not None:
                    # Draw crosshair at center
                    cv2.line(display_frame, (self.brain.center_x - 50, self.brain.center_y), 
                            (self.brain.center_x + 50, self.brain.center_y), (255, 255, 255), 2)
                    cv2.line(display_frame, (self.brain.center_x, self.brain.center_y - 50), 
                            (self.brain.center_x, self.brain.center_y + 50), (255, 255, 255), 2)
                    
                    # Draw dead zone
                    if self.brain.current_mode == 'face':
                        dead_zone_size = self.brain.face_threshold_distance
                        cv2.rectangle(display_frame, 
                                    (self.brain.center_x - dead_zone_size, self.brain.center_y - dead_zone_size),
                                    (self.brain.center_x + dead_zone_size, self.brain.center_y + dead_zone_size),
                                    (0, 255, 255), 2)  # Yellow for face dead zone
                    
                    # Perform face detection on display frame and draw bounding boxes
                    if self.brain.current_mode == 'face' and hasattr(self.brain, 'face_tracker'):
                        try:
                            # Get face detections from the frame
                            face_detection = self.brain.face_tracker.get_biggest_face_coordinates(display_frame)
                            if face_detection is not None:
                                x, y, w, h = face_detection
                                # Draw face bounding box
                                cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 3)  # Green for faces
                                cv2.putText(display_frame, "FACE", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                                
                                # Draw center point
                                center_x = x + w // 2
                                center_y = y + h // 2
                                cv2.circle(display_frame, (center_x, center_y), 5, (0, 255, 0), -1)
                                
                                # Show coordinates
                                cv2.putText(display_frame, f"({center_x}, {center_y})", (center_x + 10, center_y), 
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                        except Exception as e:
                            # Don't let detection errors crash the display
                            pass
                    
                    elif self.brain.current_mode == 'hotdog' and hasattr(self.brain, 'hotdog_recognizer'):
                        try:
                            # Get hotdog detections from the frame  
                            hotdog_detection = self.brain.hotdog_recognizer.get_biggest_hotdog_coordinates(display_frame)
                            if hotdog_detection is not None:
                                x, y, w, h = hotdog_detection
                                # Draw hotdog bounding box
                                cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 0, 255), 3)  # Red for hotdogs
                                cv2.putText(display_frame, "HOTDOG", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                                
                                # Draw center point
                                center_x = x + w // 2
                                center_y = y + h // 2
                                cv2.circle(display_frame, (center_x, center_y), 5, (0, 0, 255), -1)
                                
                                # Show coordinates
                                cv2.putText(display_frame, f"({center_x}, {center_y})", (center_x + 10, center_y), 
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                        except Exception as e:
                            # Don't let detection errors crash the display
                            pass
                    
                    # Show status
                    mode_text = f"Mode: {self.brain.current_mode or 'IDLE'}"
                    fire_text = f"Fireable: {'YES' if self.brain.fireable else 'NO'}"
                    cv2.putText(display_frame, mode_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    cv2.putText(display_frame, fire_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    
                    cv2.imshow("Threaded Ketchup Bot", display_frame)
                
                # Check for exit
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("👋 Display window closed")
                    break
                    
                # Reduce sleep time for more responsive camera capture
                time.sleep(0.02)  # ~50 FPS for smoother tracking
                
        except Exception as e:
            print(f"Display error: {e}")
        finally:
            cv2.destroyWindow("Threaded Ketchup Bot")
    
    def start(self):
        """Start the complete system"""
        print("🚀 Starting Threaded Brain System with Display...")
        
        self.running = True
        
        # Start brain in background thread
        brain = self.start_brain_thread()
        
        # Wait a moment for brain to initialize
        time.sleep(2)
        
        # Start face tracking
        print("👤 Starting face tracking...")
        brain.start_tracking_faces()
        
        print("✅ Brain is running in background thread")
        print("🎯 Face tracking is active")
        print("🖥️  Starting display in main thread...")
        print("   - Press 'q' in the window to stop")
        
        # Run display in main thread
        self.start_main_thread_display()
        
        # Cleanup
        self.stop()
    
    def stop(self):
        """Stop the system"""
        print("🛑 Stopping threaded brain system...")
        self.running = False
        
        if self.brain:
            self.brain.stop()
            self.brain.destroy()
        
        print("✅ System stopped")

def main():
    system = ThreadedBrainWithDisplay()
    
    try:
        system.start()
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        system.stop()

if __name__ == "__main__":
    main()
