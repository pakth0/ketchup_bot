#!/usr/bin/env python3
"""
FastAPI Server with OpenCV Display in Main Thread
This version runs the display in the main thread to avoid OpenCV threading issues
"""

import random
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import socket
import datetime
import os
import json
from typing import Dict, Any
from brain import Brain
import threading
import cv2
import time
import asyncio
from contextlib import asynccontextmanager
import signal
import sys

# Global variables
brain = None
display_running = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    global brain
    print("🧠 Initializing brain for FastAPI server...")
    
    try:
        brain = Brain()
        print("✅ Brain initialized successfully")
        
        # Start brain in background thread
        brain_thread = threading.Thread(target=brain.run, daemon=True)
        brain_thread.start()
        print("🚀 Brain thread started")
        
        # Wait for brain to initialize
        await asyncio.sleep(2)
        
        yield  # Server runs here
        
    except Exception as e:
        print(f"🚨 Failed to initialize brain: {e}")
        raise
    finally:
        # Shutdown
        if brain:
            print("🛑 Shutting down brain...")
            brain.stop()

app = FastAPI(
    title="Ketchup Bot API Server with Display",
    description="FastAPI server with OpenCV camera display",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware to handle frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def home():
    return {
        "status": "running",
        "brain_mode": brain.current_mode if brain else None,
        "brain_fireable": brain.fireable if brain else None,
        "framework": "FastAPI",
        "display": "OpenCV Camera Feed",
        "timestamp": datetime.datetime.now().isoformat(),
    }

@app.get("/status/fireable")
def get_fireable_status():
    """Get current fireable state"""
    if not brain:
        return {"error": "Brain not initialized"}
    return {
        "fireable": brain.fireable,
        "timestamp": datetime.datetime.now().isoformat()
    }

@app.get("/status/tracking")
def get_tracking_status():
    """Get current tracking mode"""
    if not brain:
        return {"error": "Brain not initialized"}
    return {
        "mode": brain.current_mode,
        "timestamp": datetime.datetime.now().isoformat()
    }

@app.get("/status/all")
def get_all_status():
    """Get complete system status for frontend sync"""
    if not brain:
        return {"error": "Brain not initialized"}
    return {
        "fireable": brain.fireable,
        "tracking_mode": brain.current_mode,
        "release_time": brain.release_time,
        "timestamp": datetime.datetime.now().isoformat()
    }

@app.post("/track_mode")
def track_mode(mode: str):
    if not brain:
        return {"error": "Brain not initialized"}
        
    if mode == "face":
        brain.start_tracking_faces()
    elif mode == "hotdog":
        brain.start_tracking_hotdogs()
    elif mode == "off":
        brain.stop()
    else:
        return {"error": "Invalid mode"}
    return {"status": f"Tracking mode set to: {mode}"}

@app.post("/toggle_fireable")
def toggle_fireable(mode: str):
    if not brain:
        return {"error": "Brain not initialized"}
        
    if mode == "on":
        brain.fireable = True
    elif mode == "off":
        brain.fireable = False
    else:
        return {"error": "Invalid mode"}
    return {"status": f"Fireable: {brain.fireable}"}

@app.get("/status/release_time")
def get_release_time():
    """Get current release time"""
    if not brain:
        return {"error": "Brain not initialized"}
    return {
        "release_time": brain.release_time,
        "timestamp": datetime.datetime.now().isoformat()
    }

@app.post("/set_release_time")
def set_release_time(release_time: float):
    """Set the fire release time in seconds"""
    if not brain:
        return {"error": "Brain not initialized"}
        
    if release_time < 0.1 or release_time > 10.0:
        return {"error": "Release time must be between 0.1 and 10.0 seconds"}
    
    brain.release_time = release_time
    return {"status": f"Release time set to: {brain.release_time}s"}

@app.post("/solenoid")
def solenoid(mode: str):
    if not brain:
        return {"error": "Brain not initialized"}
        
    try:
        if mode == "on":
            brain.controller.solenoid_controller.solenoid_on()
        elif mode == "off":
            brain.controller.solenoid_controller.solenoid_off()
        else:
            return {"error": "Invalid mode"}
        return {"status": f"Solenoid: {mode}"}
    except Exception as e:
        return {"error": f"Solenoid control failed: {e}"}

@app.get("/reset")
def reset():
    if not brain:
        return {"error": "Brain not initialized"}
    try:
        brain.reset_to_home()
        return {"status": "Reset completed"}
    except Exception as e:
        return {"error": f"Reset failed: {e}"}

@app.post("/set_release_time")
def set_release_time(release_time: float):
    """Set the solenoid release time"""
    if not brain:
        return {"error": "Brain not initialized"}
    
    try:
        # Validate release time range
        if release_time < 0.1 or release_time > 10.0:
            return {"error": "Release time must be between 0.1 and 10.0 seconds"}
        
        # Set the release time on the brain's solenoid controller
        if hasattr(brain, 'controller') and hasattr(brain.controller, 'solenoid_controller'):
            brain.controller.solenoid_controller.release_time = release_time
            return {"status": f"Release time set to {release_time}s", "release_time": release_time}
        else:
            return {"error": "Solenoid controller not available"}
    except Exception as e:
        return {"error": f"Failed to set release time: {e}"}

def get_host_ip():
    """Get the local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

def signal_handler(signum, frame):
    """Handle signals gracefully"""
    global display_running
    print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
    display_running = False
    cv2.destroyAllWindows()
    if brain:
        brain.stop()
    sys.exit(0)

def run_display_with_server():
    """Run the camera display in the main thread alongside the server"""
    global display_running
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    try:
        signal.signal(signal.SIGTRAP, signal_handler)  # Handle trace trap
    except AttributeError:
        pass  # SIGTRAP might not be available on all systems
    
    print("📺 Starting camera display in main thread...")
    
    try:
        cv2.namedWindow("Ketchup Bot API Server", cv2.WINDOW_AUTOSIZE)
        print("✅ OpenCV window created successfully")
        display_running = True
    except Exception as e:
        print(f"❌ Failed to create OpenCV window: {e}")
        return

    # Start FastAPI server in a separate thread
    port = int(os.environ.get('PORT', 8080))  # Use 8080 instead of 80 to avoid permissions
    host = "0.0.0.0"
    
    print(f"🚀 Starting FastAPI server on {host}:{port}")
    print(f"🌐 URL: http://{host}:{port}")
    print(f"📚 API Docs: http://{host}:{port}/docs")
    
    server_thread = threading.Thread(
        target=lambda: uvicorn.run(app, port=port, log_level="info"),
        daemon=True
    )
    server_thread.start()
    
    # Wait for server and brain to start
    time.sleep(3)
    
    print("🎯 Controls:")
    print("   - Press 'q' in OpenCV window to quit")
    print("   - Press 'f' to start face tracking")
    print("   - Press 'h' to start hotdog tracking")
    print("   - Press 's' to stop tracking")
    print("   - Press 'e' to toggle fireable mode")
    
    # Main display loop
    try:
        while display_running:
            if not brain:
                time.sleep(0.1)
                continue
                
            try:
                # Read from camera
                ret, frame = brain.cap.read()
                if not ret:
                    print("⚠️  Failed to read camera frame")
                    time.sleep(0.1)
                    continue
                
                # Draw crosshair at center
                cv2.line(frame, (brain.center_x - 50, brain.center_y), 
                       (brain.center_x + 50, brain.center_y), (255, 255, 255), 2)
                cv2.line(frame, (brain.center_x, brain.center_y - 50), 
                       (brain.center_x, brain.center_y + 50), (255, 255, 255), 2)
                
                # Draw dead zone
                if brain.current_mode == 'face':
                    dead_zone_size = brain.face_threshold_distance
                    cv2.rectangle(frame, 
                                (brain.center_x - dead_zone_size, brain.center_y - dead_zone_size),
                                (brain.center_x + dead_zone_size, brain.center_y + dead_zone_size),
                                (0, 255, 255), 2)  # Yellow for face dead zone
                elif brain.current_mode == 'hotdog':
                    dead_zone_size = brain.glizzy_threshold_distance
                    cv2.rectangle(frame, 
                                (brain.center_x - dead_zone_size, brain.center_y - dead_zone_size),
                                (brain.center_x + dead_zone_size, brain.center_y + dead_zone_size),
                                (0, 165, 255), 2)  # Orange for hotdog dead zone
                
                # Perform face/hotdog detection and draw boxes
                if brain.current_mode == 'face':
                    try:
                        face_detection = brain.face_tracker.get_biggest_face_coordinates(frame)
                        if face_detection is not None:
                            x, y, w, h = face_detection
                            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
                            cv2.putText(frame, "FACE", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                            center_x = x + w // 2
                            center_y = y + h // 2
                            cv2.circle(frame, (center_x, center_y), 5, (0, 255, 0), -1)
                            cv2.putText(frame, f"({center_x}, {center_y})", (center_x + 10, center_y), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                    except:
                        pass
                
                elif brain.current_mode == 'hotdog':
                    try:
                        hotdog_detection = brain.hotdog_recognizer.find_biggest_hotdog(frame)
                        if hotdog_detection is not None:
                            x, y, w, h = hotdog_detection
                            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 3)
                            cv2.putText(frame, "HOTDOG", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                            center_x = x + w // 2
                            center_y = y + h // 2
                            cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)
                            cv2.putText(frame, f"({center_x}, {center_y})", (center_x + 10, center_y), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                    except Exception as e:
                        print(f"❌ Hotdog detection error: {e}")
                        cv2.putText(frame, "HOTDOG ERROR", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                
                # Show status
                mode_text = f"Mode: {brain.current_mode or 'IDLE'}"
                fire_text = f"Fireable: {'YES' if brain.fireable else 'NO'}"
                server_text = f"API Server: http://{host}:{port}"
                cv2.putText(frame, mode_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(frame, fire_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(frame, server_text, (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
                
                cv2.imshow("Ketchup Bot API Server", frame)
                
                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("👋 Exiting...")
                    break
                elif key == ord('f'):
                    brain.start_tracking_faces()
                    print("👤 Face tracking started")
                elif key == ord('h'):
                    brain.start_tracking_hotdogs()
                    print("🌭 Hotdog tracking started")
                elif key == ord('s'):
                    brain.stop()
                    print("⏹️  Tracking stopped")
                elif key == ord('e'):
                    brain.fireable = not brain.fireable
                    print(f"🎯 Fireable: {brain.fireable}")
                    
                time.sleep(0.02)  # ~50 FPS
                
            except Exception as e:
                print(f"Display error: {e}")
                time.sleep(0.1)
                
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    finally:
        display_running = False
        cv2.destroyAllWindows()
        print("✅ Display closed")

if __name__ == "__main__":
    run_display_with_server()
