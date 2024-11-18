import RPi.GPIO as GPIO
import time

class Nema17:
    def __init__(self, A1_pin, A2_pin, B1_pin, B2_pin):
        """
        Initialize the motor with GPIO pins.
        
        Args:
            A1_pin (int): GPIO pin for IN1.
            A2_pin (int): GPIO pin for IN2.
            B1_pin (int): GPIO pin for IN3.
            B2_pin (int): GPIO pin for IN4.
        """
        self.A1 = A1_pin
        self.A2 = A2_pin
        self.B1 = B1_pin
        self.B2 = B2_pin

        GPIO.setmode(GPIO.BCM)
        
        # Set up GPIO pins as outputs
        GPIO.setup(self.A1, GPIO.OUT)
        GPIO.setup(self.A2, GPIO.OUT)
        GPIO.setup(self.B1, GPIO.OUT)
        GPIO.setup(self.B2, GPIO.OUT)

    full_step = [
    [1, 0, 0, 1],
    [1, 1, 0, 0],
    [0, 1, 1, 0],
    [0, 0, 1, 1]
    ]

    full_step_ccw = [
        [0, 0, 1, 1],
        [1, 0, 0, 1],
        [1, 1, 0, 0],
        [0, 1, 1, 0]
    ]

    half_step = [
        [1, 0, 0, 1],
        [1, 0, 0, 0],
        [1, 1, 0, 0],
        [0, 1, 0, 0],
        [0, 1, 1, 0],
        [0, 0, 1, 0],
        [0, 0, 1, 1],
        [0, 0, 0, 1]
    ]

    half_step_ccw = [
        [0, 0, 0, 1], 
        [1, 0, 0, 1],
        [1, 0, 0, 0],
        [1, 1, 0, 0],
        [0, 1, 0, 0],
        [0, 1, 1, 0],
        [0, 0, 1, 0],
        [0, 0, 1, 1]
    ]

    def rotate_full_step(self, rpm):
        delay = 60/(200 * rpm) # 60 seconds per minute, 200 steps per revolution
        for step in self.full_step:
            GPIO.output([self.A1, self.A2, self.B1, self.B2], step)
            time.sleep(delay)

    def rotate_full_step_ccw(self, rpm):
        delay = 60/(200 * rpm) # 60 seconds per minute, 200 steps per revolution
        for step in self.full_step_ccw:
            GPIO.output([self.A1, self.A2, self.B1, self.B2], step)
            time.sleep(delay)

    def rotate_half_step(self, rpm):
        delay = 60/(400 * rpm) # 60 seconds per minute, 400 steps per revolution
        for step in self.half_step:
            GPIO.output([self.A1, self.A2, self.B1, self.B2], step)
            time.sleep(delay)

    def rotate_half_step_ccw(self, rpm):
        delay = 60/(400 * rpm) # 60 seconds per minute, 400 steps per revolution
        for step in self.half_step_ccw:
            GPIO.output([self.A1, self.A2, self.B1, self.B2], step)
            time.sleep(delay)


if __name__ == "__main__":

    # Set up the GPIO pins
    A1 = 17  # IN1
    A2 = 18  # IN2
    B1 = 27  # IN3
    B2 = 22  # IN4
    
    # Create sensor objects
    stepper = Nema17()
    
    try:
        Nema17.rotate_full_step(10)
        #Nema17.rotate_half_step(10)
        #Nema17.rotate_full_step_ccw(10)
        #Nema17.rotate_half_step_ccw(10)
        
    except KeyboardInterrupt:
        print("\nMeasurement stopped by user")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        GPIO.cleanup()
