import asyncio
import nxt.locator
import nxt.motor
from nxt.motcont import MotCont
from serial_controller import SolenoidController

import time
import threading


class PanTiltTurretController:
    def __init__(self, pan_motor_port, tilt_motor_port):
        self.pan_motor_port = pan_motor_port
        self.tilt_motor_port = tilt_motor_port
        self.brick = None
        self.pan_motor = None
        self.tilt_motor = None
        self.solenoid_controller = SolenoidController()
        self.cooldown = time.time() - 15 # Initialize cooldown timer
        self.cooldown_lock = threading.Lock()

        # Try to initialize brick with 3 retries
        max_retries = 3
        retry_delay = 2  # seconds between retries
        
        for attempt in range(max_retries):
            try:
                print(f"Attempting to initialize brick (attempt {attempt + 1}/{max_retries})...")
                self.brick = nxt.locator.find()
                self.pan_motor = self.brick.get_motor(self.pan_motor_port)
                self.tilt_motor = self.brick.get_motor(self.tilt_motor_port)
                print("✅ Brick initialized successfully")
                break  # Success! Exit the retry loop
            except Exception as e:
                print(f"❌ Error initializing brick (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:  # Not the last attempt
                    print(f"⏳ Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:  # Last attempt failed
                    print("🚨 CRITICAL ERROR: Failed to initialize brick after 3 attempts")
                    print("🚨 Please check:")
                    print("   - NXT brick is connected via USB")
                    print("   - NXT brick is powered on")
                    print("   - USB cable is properly connected")
                    print("   - No other programs are using the NXT")
                    print("🚨 Exiting program...")
                    raise Exception(f"Failed to initialize NXT brick after {max_retries} attempts. Last error: {e}")
                    
        # Continue with MotCont initialization only if brick was successfully initialized
        if not hasattr(self, 'brick') or self.brick is None:
            raise Exception("Brick initialization failed - cannot continue")
        
        self.MotCont = MotCont(self.brick)
        self.MotCont.start()
        if self.MotCont.is_ready(self.pan_motor_port) and self.MotCont.is_ready(self.tilt_motor_port):
            self.pan_motor = self.brick.get_motor(self.pan_motor_port)
            self.tilt_motor = self.brick.get_motor(self.tilt_motor_port)
        else:
            print("Pan or tilt motor is not ready")
            self.MotCont.stop()
            return None
        
        #turret should be positioned at 0,0 to reset tacho count
        self.MotCont.reset_tacho([self.pan_motor_port, self.tilt_motor_port])

    async def async_rotate_pan(self, power, angle):
        self.MotCont.cmd(self.pan_motor_port, power, angle)
        while not self.MotCont.is_ready(self.pan_motor_port):
            await asyncio.sleep(0.01)
        return True

    async def async_rotate_tilt(self, power, angle):
        self.MotCont.cmd(self.tilt_motor_port, power, angle)
        while not self.MotCont.is_ready(self.tilt_motor_port):
            await asyncio.sleep(0.01)
        return True

    async def async_reset(self, mode:str):
        '''reset position of pan and tilt motors to 0,0'''
        pan_tacho = self.pan_motor.get_tacho().tacho_count
        tilt_tacho = self.tilt_motor.get_tacho().tacho_count
        factor_y = 1
        factor_x = 1
        if pan_tacho < 0:
            pan_tacho = -pan_tacho
            factor_x = -1
        if tilt_tacho < 0:
            factor_y = -1
            tilt_tacho = -tilt_tacho
        print(f"Pan tacho: {pan_tacho}")
        print(f"Tilt tacho: {tilt_tacho}")
        asyncio.run(self.async_rotate_pan(-50*factor_x, pan_tacho))
        print(f"Pan tacho: {pan_tacho}")
        asyncio.run(self.async_rotate_tilt(-50*factor_y, tilt_tacho))
        print(f"Tilt tacho: {tilt_tacho}")

        if mode == "face":
            self.rotate_tilt(-3, 6)
        elif mode == "hotdog":
            self.rotate_tilt(3, 6)

    def rotate_pan(self, power, angle):
        '''positive power is clockwise, negative power is counterclockwise'''
        while not self.MotCont.is_ready(self.pan_motor_port):
            pass
        self.MotCont.cmd(self.pan_motor_port, power, angle)
        return True
    
    def rotate_tilt(self, power, angle):
        '''positive power is down, negative power is up'''
        while not self.MotCont.is_ready(self.tilt_motor_port):
            pass
        self.MotCont.cmd(self.tilt_motor_port, power, angle)
        return True

    def rotate_both(self, pan_power: int, pan_angle: int, tilt_power: int, tilt_angle: int) -> bool:
        """Issue pan & tilt commands together so they move at the same time."""
        # Wait until both are ready before sending either command
        while not (self.MotCont.is_ready(self.pan_motor_port) and self.MotCont.is_ready(self.tilt_motor_port)):
            pass

        if pan_angle:
            self.MotCont.cmd(self.pan_motor_port, pan_power, pan_angle)
        if tilt_angle:
            self.MotCont.cmd(self.tilt_motor_port, tilt_power, tilt_angle)
        # Fire both commands back-to-back
        print(f"Rotating pan: {pan_power} at angle {pan_angle}, tilt: {tilt_power} at angle {tilt_angle}")
        return True

    def _fire_worker(self, release_time):
        with self.cooldown_lock:
            if self.cooldown + 5 < time.time():
                self.cooldown = time.time()
                self.solenoid_controller.solenoid_on()
                time.sleep(release_time)
                self.solenoid_controller.solenoid_off()

    def fire(self, release_time=0.5):
        '''fire ketchup using serial_controller in a separate thread'''
        threading.Thread(target=self._fire_worker, args=(release_time,), daemon=True).start()

    def reset(self, target_pan=0, target_tilt=0):
        '''reset position of pan and tilt motors to target positions (default 0,0)'''
        current_pan = self.pan_motor.get_tacho().tacho_count
        current_tilt = self.tilt_motor.get_tacho().tacho_count
        
        # Calculate movement needed to reach target positions
        pan_movement = current_pan - target_pan
        tilt_movement = current_tilt - target_tilt
        
        print(f"Current position - Pan: {current_pan}, Tilt: {current_tilt}")
        print(f"Target position - Pan: {target_pan}, Tilt: {target_tilt}")
        print(f"Movement needed - Pan: {pan_movement}, Tilt: {tilt_movement}")
        
        # Determine movement direction and power
        pan_power = 0
        tilt_power = 0
        pan_angle = abs(pan_movement)
        tilt_angle = abs(tilt_movement)
        
        if pan_movement > 0:
            pan_power = -50  # Move counter-clockwise to reduce position
        elif pan_movement < 0:
            pan_power = 50   # Move clockwise to increase position
            
        if tilt_movement > 0:
            tilt_power = -50  # Move up to reduce position
        elif tilt_movement < 0:
            tilt_power = 50   # Move down to increase position

        # Only move if there's actual movement needed
        if pan_angle > 0 or tilt_angle > 0:
            self.rotate_both(pan_power, pan_angle, tilt_power, tilt_angle)
            print(f"Reset complete - moved to target position")
        else:
            print("Already at target position - no movement needed")
            
    def destroy(self):
        self.MotCont.stop()

async def main():
    controller = PanTiltTurretController(nxt.motor.Port.B, nxt.motor.Port.A)
    if controller is None:
        print("Failed to initialize controller")
        exit(1)
    await controller.async_rotate_pan(-30, 45)
    await controller.async_rotate_tilt(30, 45)
    controller.reset("face")

if __name__ == "__main__":
    asyncio.run(main())


