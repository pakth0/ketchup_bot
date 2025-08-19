#!/usr/bin/env python3
"""
FastAPI Server for HTTP Request Testing
A lightweight server using FastAPI and Uvicorn to handle HTTP requests on port 80.
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
from threaded_brain_with_display import ThreadedBrainWithDisplay
import threading
import cv2
import time

app = FastAPI(
    title="HTTP Request Test Server",
    description="A FastAPI server for testing HTTP requests on port 80",
    version="1.0.0"
)

# Add CORS middleware to handle frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize brain and display system
try:
    print("🧠 Initializing brain for FastAPI server...")
    brain = Brain()
    print("✅ Brain initialized successfully")
    
    # Start brain in background thread
    brain_thread = threading.Thread(target=brain.run, daemon=True)
    brain_thread.start()
    
    # Initialize display system variables
    display_running = False
    display_thread = None
    
    def start_camera_display():
        """Start camera display in a separate thread"""
        global display_running, display_thread
        if not display_running:
            display_running = True
            # Use non-daemon thread for OpenCV to avoid GUI issues
            display_thread = threading.Thread(target=camera_display_loop, daemon=False)
            display_thread.start()
            print("🖥️  Camera display started")
    
    def stop_camera_display():
        """Stop camera display"""
        global display_running
        display_running = False
        print("📺 Camera display stopped")
    
    def camera_display_loop():
        """Camera display loop for FastAPI server"""
        try:
            cv2.namedWindow("Ketchup Bot API Server", cv2.WINDOW_AUTOSIZE)
            print("✅ OpenCV display window created successfully")
        except Exception as e:
            print(f"⚠️  OpenCV window creation failed: {e}")
            print("📺 Running in headless mode - display disabled")
            return
        
        try:
            while display_running:
                try:
                    # Read from camera
                    ret, frame = brain.cap.read()
                    if ret:
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
                        
                        # Perform face detection and draw boxes
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
                                hotdog_detection = brain.hotdog_recognizer.get_biggest_hotdog_coordinates(frame)
                                if hotdog_detection is not None:
                                    x, y, w, h = hotdog_detection
                                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 3)
                                    cv2.putText(frame, "HOTDOG", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                                    center_x = x + w // 2
                                    center_y = y + h // 2
                                    cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)
                                    cv2.putText(frame, f"({center_x}, {center_y})", (center_x + 10, center_y), 
                                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                            except:
                                pass
                        
                        # Show status
                        mode_text = f"Mode: {brain.current_mode or 'IDLE'}"
                        fire_text = f"Fireable: {'YES' if brain.fireable else 'NO'}"
                        server_text = "FastAPI Server Running"
                        cv2.putText(frame, mode_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                        cv2.putText(frame, fire_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                        cv2.putText(frame, server_text, (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                        
                        cv2.imshow("Ketchup Bot API Server", frame)
                    
                    # Check for exit (though this won't work in server mode)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                        
                    time.sleep(0.02)  # ~50 FPS
                    
                except Exception as e:
                    print(f"Display error: {e}")
                    time.sleep(0.1)
                    
        except Exception as e:
            print(f"Display loop error: {e}")
        finally:
            cv2.destroyWindow("Ketchup Bot API Server")
    
    # Wait for brain to fully initialize
    print("⏳ Waiting for brain to initialize...")
    time.sleep(2)
    
    # Auto-start the display (with fallback to headless mode)
    print("📺 Attempting to start camera display...")
    try:
        start_camera_display()
        print("✅ Camera display system initialized")
        print("💡 TIP: If display doesn't appear, try: curl -X POST 'http://localhost:80/display?mode=on'")
    except Exception as e:
        print(f"⚠️  Camera display failed to start: {e}")
        print("🖥️  Server will run in headless mode (API only)")
        print("💡 You can try to restart display via API: curl -X POST 'http://localhost:80/display?mode=on'")
        display_running = False
    
except Exception as e:
    print(f"🚨 Failed to initialize brain system: {e}")
    raise


@app.get("/")
async def home():
    return {
        "status": "running",
        "framework": "FastAPI",
        "server": "Uvicorn",
        "host": get_host_ip(),
        "port": get_port(),
        "timestamp": datetime.datetime.now().isoformat(),
        "message": "HTTP server is running and accepting requests",
        "uptime": "Server is healthy"
    }

@app.get("/status")
async def get_status():
    """JSON status endpoint"""
    return {
        "status": "running",
        "framework": "FastAPI",
        "server": "Uvicorn",
        "host": get_host_ip(),
        "port": get_port(),
        "timestamp": datetime.datetime.now().isoformat(),
        "message": "HTTP server is running and accepting requests",
        "uptime": "Server is healthy"
    }

@app.get("/tipped_zero")
def tip_zero(body: dict):
    face_index = random.randint(0, len(body['condiments']) - 1)
    for condiment, index in enumerate(body['condiments']):
        while(brain.fireable == True):
            if index == face_index:
                brain.start_tracking_faces()
            else:
                brain.start_tracking_hotdogs()

    return {}

@app.get("/tipped_nonzero")
def tip_nonzero(body: dict):
    for condiment, index in enumerate(body['condiments']):
        while(brain.fireable == True):
            brain.start_tracking_hotdogs()

@app.post("/toggle_fireable")
def toggle_fireable(mode: str):
    if mode == "on":
        brain.fireable = True
    elif mode == "off":
        brain.fireable = False
    else:
        return {"error": "Invalid mode"}
    return {}

@app.post("/track_mode")
def track_mode(mode: str):
    if mode == "face":
        brain.start_tracking_faces()
    elif mode == "hotdog":
        brain.start_tracking_hotdogs()
    elif mode == "off":
        brain.stop()
    else:
        return {"error": "Invalid mode"}
    return {}

@app.post("/solenoid")
def solenoid(mode: str):
    if mode == "on":
        brain.controller.solenoid_controller.solenoid_on()
    elif mode == "off":
        brain.controller.solenoid_controller.solenoid_off()
    else:
        return {"error": "Invalid mode"}
    return {}

@app.get("/reset")
def reset():
    brain.controller.reset()
    return {}

@app.post("/display")
def toggle_display(mode: str):
    """Control the camera display window"""
    if mode == "on":
        start_camera_display()
        return {"status": "Display started", "running": display_running}
    elif mode == "off":
        stop_camera_display()
        return {"status": "Display stopped", "running": display_running}
    else:
        return {"error": "Invalid mode. Use 'on' or 'off'", "running": display_running}

def get_host_ip():
    """Get the local IP address"""
    try:
        # Connect to a remote address to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

def get_port():
    """Get the port from environment or default to 80"""
    return int(os.environ.get('PORT', 80))

if __name__ == "__main__":
    port = get_port()
    host = "0.0.0.0"  # Listen on all interfaces
    
    print("🚀 Starting Ketchup Bot FastAPI Server with Camera Display...")
    print(f"📍 Host: {host} (accessible via {get_host_ip()})")
    print(f"🔌 Port: {port}")
    print(f"🌐 URL: http://{get_host_ip()}:{port}")
    print(f"📚 API Docs: http://{get_host_ip()}:{port}/docs")
    print(f"📺 Camera Display: OpenCV window showing face detection")
    print(f"⏰ Started: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🛑 Press Ctrl+C to stop")
    print("-" * 60)
    print("🎯 Available API endpoints:")
    print("   POST /track_mode?mode=face     - Start face tracking")
    print("   POST /track_mode?mode=hotdog   - Start hotdog tracking") 
    print("   POST /track_mode?mode=off      - Stop tracking")
    print("   POST /toggle_fireable?mode=on  - Enable firing")
    print("   POST /display?mode=on          - Start camera display")
    print("   POST /display?mode=off         - Stop camera display")
    print("-" * 60)
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    ) 