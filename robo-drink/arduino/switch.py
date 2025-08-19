import os
import sys
import time
import argparse
import serial
from serial.tools import list_ports

# Set the baud rate to match the Arduino code (9600)
baud_rate = 9600


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


def open_serial_connection(port: str) -> serial.Serial:
    try:
        ser = serial.Serial(port, baud_rate, timeout=1)
        time.sleep(2)
        print(f"Connected to Arduino on port {port}")
        return ser
    except serial.SerialException as e:
        available = list_available_ports()
        print(
            "Error connecting to the Arduino: "
            f"{e}\nAvailable ports: {available if available else 'None found'}"
        )
        sys.exit(1)


def activate_solenoid(ser: serial.Serial) -> None:
    print("Valve open")
    ser.write(b"1")


def deactivate_solenoid(ser: serial.Serial) -> None:
    print("Valve closed")
    ser.write(b"0")


def interactive_control(ser: serial.Serial) -> None:
    """Interactive control using spacebar to open and Enter to close."""
    print("\n=== Interactive Solenoid Control ===")
    print("Press SPACEBAR to open solenoid")
    print("Press ENTER to close solenoid")
    print("Press 'q' to quit")
    print("=====================================\n")
    
    try:
        import msvcrt  # Windows
        is_windows = True
    except ImportError:
        try:
            import tty
            import termios
            is_windows = False
        except ImportError:
            print("Error: Cannot import required modules for keyboard input.")
            print("This script requires either 'msvcrt' (Windows) or 'tty'/'termios' (Unix/macOS).")
            sys.exit(1)
    
    if is_windows:
        interactive_control_windows(ser)
    else:
        interactive_control_unix(ser)


def interactive_control_windows(ser: serial.Serial) -> None:
    """Windows-specific interactive control."""
    import msvcrt
    
    print("Windows mode - Press SPACE to open, ENTER to close. Press 'q' to quit.")
    
    while True:
        if msvcrt.kbhit():
            key = msvcrt.getch()
            
            if key == b'q':
                break
            elif key == b' ':
                activate_solenoid(ser)
            elif key == b'\r':  # Enter key
                deactivate_solenoid(ser)
        
        # Small delay to prevent excessive CPU usage
        time.sleep(0.01)


def interactive_control_unix(ser: serial.Serial) -> None:
    """Unix/macOS-specific interactive control."""
    import tty
    import termios
    
    # Save terminal settings
    old_settings = termios.tcgetattr(sys.stdin)
    
    try:
        # Set terminal to raw mode
        tty.setraw(sys.stdin.fileno())
        
        print("Unix/macOS mode - Press SPACE to open, ENTER to close. Press 'q' to quit.")
        
        while True:
            if sys.stdin.readable():
                char = sys.stdin.read(1)
                
                if char == 'q':
                    break
                elif char == ' ':
                    activate_solenoid(ser)
                elif char == '\r':  # Enter key
                    deactivate_solenoid(ser)
                        
    finally:
        # Restore terminal settings
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Control Arduino solenoid via serial")
    parser.add_argument(
        "--port",
        dest="port",
        default=os.environ.get("ARDUINO_PORT"),
        help="Serial port path (e.g. /dev/cu.usbmodemXXXX). Defaults to auto-detect or $ARDUINO_PORT.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    port = args.port or auto_detect_arduino_port()
    if not port:
        available = list_available_ports()
        print(
            "Could not auto-detect Arduino serial port. "
            f"Specify with --port or set $ARDUINO_PORT. Available: {available if available else 'None found'}"
        )
        sys.exit(1)

    ser = open_serial_connection(port)
    try:
        interactive_control(ser)
    except KeyboardInterrupt:
        print("\nScript terminated by user.")
    finally:
        try:
            if ser and ser.is_open:
                ser.close()
                print("Serial connection closed.")
        except Exception:
            pass