import asyncio
import nxt.locator
import nxt.motor
from nxt.motcont import MotCont
import serial_controller

import time


class PanTiltTurretController:
    def __init__(self, pan_motor_port, tilt_motor_port):
        self.pan_motor_port = pan_motor_port
        self.tilt_motor_port = tilt_motor_port
        self.brick = None
        self.pan_motor = None
        self.tilt_motor = None
        
        try:
            self.brick = nxt.locator.find()
            self.pan_motor = self.brick.get_motor(self.pan_motor_port)
            self.tilt_motor = self.brick.get_motor(self.tilt_motor_port)
            print("Brick initialized")
        except Exception as e:
            print(f"Error initializing brick: {e}")
            return None
        
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

    async def async_reset(self):
        self.reset()
        while not self.MotCont.is_ready(self.pan_motor_port) or not self.MotCont.is_ready(self.tilt_motor_port):
            print(f"Waiting for pan and tilt motors to be ready: {self.MotCont.is_ready(self.pan_motor_port)} | {self.MotCont.is_ready(self.tilt_motor_port)}")
            await asyncio.sleep(0.01)
        return True

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

    def tacho_to_coordinates(self, tacho):
        pass
    
    def coordinates_to_tacho(self, x, y):
        pass

    def aim_at_coordinates(self, x, y):
        #get current tacho position of pan and tilt motors
        #calculate the angle to the target coordinates
        #rotate pan and tilt motors to the target angle, power proportional to distance
        pass

    def fire(self):
        '''fire ketchup using serial_controller'''
        serial_controller.open_valve()
        time.sleep(0.3)
        serial_controller.close_valve()

    def reset(self):
        '''reset position of pan and tilt motors to 0,0'''
        pan_tacho = self.pan_motor.get_tacho().tacho_count
        tilt_tacho = self.tilt_motor.get_tacho().tacho_count
        self.rotate_pan(-50, pan_tacho)
        print(f"Pan tacho: {pan_tacho}")
        self.rotate_tilt(-50, tilt_tacho)
        print(f"Tilt tacho: {tilt_tacho}")
        
            
        


    def destroy(self):
        self.MotCont.stop()

async def main():
    controller = PanTiltTurretController(nxt.motor.Port.B, nxt.motor.Port.A)
    if controller is None:
        print("Failed to initialize controller")
        exit(1)
    await controller.async_rotate_pan(-30, 45)
    await controller.async_rotate_tilt(30, 45)
    await controller.async_rotate_pan(30, 45)
    await controller.async_rotate_tilt(-30, 45)
    while True:
        pass

if __name__ == "__main__":
    asyncio.run(main())


