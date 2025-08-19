#!/usr/bin/env python3
"""
FastAPI Server for HTTP Request Testing
A lightweight server using FastAPI and Uvicorn to handle HTTP requests on port 80.
"""

import random
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
import socket
import datetime
import os
import json
from typing import Dict, Any
from brain import Brain
import threading

app = FastAPI(
    title="HTTP Request Test Server",
    description="A FastAPI server for testing HTTP requests on port 80",
    version="1.0.0"
)

brain = Brain()
brain_thread = threading.Thread(target=brain.run, daemon=True)
brain_thread.start()


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
    
    print("🚀 Starting FastAPI HTTP Test Server...")
    print(f"📍 Host: {host} (accessible via {get_host_ip()})")
    print(f"🔌 Port: {port}")
    print(f"🌐 URL: http://{get_host_ip()}:{port}")
    print(f"📚 API Docs: http://{get_host_ip()}:{port}/docs")
    print(f"⏰ Started: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🛑 Press Ctrl+C to stop")
    print("-" * 60)
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    ) 