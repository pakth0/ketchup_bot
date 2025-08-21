#!/usr/bin/env python3
"""
Simple Solenoid Control Script
Turns the solenoid on and off with basic commands
"""

import os
import sys
import time
import argparse
import serial
from serial.tools import list_ports


def list_available_ports() -> list[str]:
    ports = list(list_ports.comports())
    return [p.device for p in ports]


def auto_detect_arduino_port() -> str | None:
    candidates = []
    for port in list_ports.comports():
        desc = (port.description or "").lower()
        hwid = (port.hwid or "").lower()
        path = port.device
        # Common macOS and Linux Arduino identifiers
        if (
            "usbmodem" in path.lower()
            or "usbserial" in path.lower()
            or "arduino" in desc
            or "arduino" in hwid
            or "wch" in desc  # CH340 clones
            or "silabs" in desc  # CP210x
        ):
            candidates.append(path)
    # Prefer cu.* on macOS when both cu.* and tty.* exist
    candidates_sorted = sorted(
        candidates,
        key=lambda p: (0 if "/cu." in p or "cu." in p else 1, p),
    )
    return candidates_sorted[0] if candidates_sorted else None


def connect_to_arduino(port=None):
    """Connect to Arduino on the specified port or auto-detect"""
    if port is None:
        port = auto_detect_arduino_port()
        if not port:
            available = list_available_ports()
            print(
                "Could not auto-detect Arduino serial port. "
                f"Available: {available if available else 'None found'}"
            )
            sys.exit(1)
    
    try:
        ser = serial.Serial(port, 9600, timeout=0.5)
        time.sleep(2)  # Wait for Arduino to reset
        print(f"Connected to Arduino on {port}")
        return ser
    except serial.SerialException as e:
        print(f"Error connecting to {port}: {e}")
        print("Available ports:")
        for p in list_available_ports():
            print(f"  {p.device}")
        sys.exit(1)

def solenoid_on(ser):
    """Turn solenoid ON"""
    ser.write(b"1")
    print("Solenoid: ON")

def solenoid_off(ser):
    """Turn solenoid OFF"""
    ser.write(b"0")
    print("Solenoid: OFF")

def main():

    # Connect to Arduinoi
    ser = connect_to_arduino()
    
    solenoid_on(ser)
    time.sleep(10)
    solenoid_off(ser)

if __name__ == "__main__":
    main()
