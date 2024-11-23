import RPi.GPIO as GPIO
import time


class Nema17:
    def __init__(self, A1_pin, A2_pin, B1_pin, B2_pin, sleep_pin):
        self.A1 = A1_pin
        self.A2 = A2_pin
        self.B1 = B1_pin
        self.B2 = B2_pin
        self.sleep_pin = sleep_pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup([self.A1, self.A2, self.B1, self.B2, self.sleep_pin], GPIO.OUT)
        self.sleep()  # Start in sleep mode

    def sleep(self):
        GPIO.output([self.A1, self.A2, self.B1, self.B2, self.sleep_pin], GPIO.LOW)

    def wake(self):
        GPIO.output(self.sleep_pin, GPIO.HIGH)

    full_step_ccw = [
        [1, 0, 0, 1],
        [1, 1, 0, 0],
        [0, 1, 1, 0],
        [0, 0, 1, 1]
    ]

    full_step = [
        [0, 0, 1, 1],
        [0, 1, 1, 0],
        [1, 1, 0, 0],
        [1, 0, 0, 1]
    ]

    half_step = [
        [0, 0, 1, 1],
        [0, 0, 1, 0],
        [0, 1, 1, 0],
        [0, 1, 0, 0],
        [1, 1, 0, 0],
        [1, 0, 0, 0],
        [1, 0, 0, 1],
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

    def sleep(self):
        GPIO.output([self.A1, self.A2, self.B1, self.B2], [0, 0, 0, 0])

    def step_helper_v1(self, step, delay):
        '''
        Helper function to be called later in each half/full rotate motor function
        step (pos arg) : list, len = 4
        delay (float) : time between each GPIO update
        '''
        GPIO.output(self.A1, step[0])
        time.sleep(delay)
        GPIO.output(self.B1, step[1])
        time.sleep(delay)
        GPIO.output(self.A2, step[2])
        time.sleep(delay)
        GPIO.output(self.B2, step[3])
        time.sleep(delay)

    def step_helper_v2(self, step, delay):
        '''
        Helper function to be called later in each half/full rotate motor function
        step (pos arg) : list, len = 4
        delay (float) : time between each each step in the sequence
        '''
        GPIO.output([self.A1, self.A2, self.B1, self.B2], step)
        time.sleep(delay)

    def rotate_full_step(self, rpm=10):
        delay = (60/(200 * rpm))/4 # 60 seconds per minute, 200 steps per revolution
        # if using step_helper_v2, use 60/(200 * rpm)
        #start_time = time.time()
        while True:
            for step in self.full_step:
                self.step_helper_v1(step, delay)

    def rotate_full_step_ccw(self, rpm):
        delay = 60/(200 * rpm * 4) # 60 seconds per minute, 200 steps per revolution
        while True:
            for step in self.full_step_ccw:
                self.step_helper_v1(step, delay)

    def rotate_half_step(self, rpm):
        delay = 60/(400 * rpm * 4) # 60 seconds per minute, 400 steps per revolution
        while True:
            for step in self.half_step:
                self.step_helper_v1(step, delay)

    def rotate_half_step_ccw(self, rpm):
        delay = 60/(400 * rpm * 4) # 60 seconds per minute, 400 steps per revolution
        while True:
            for step in self.half_step_ccw:
                self.step_helper_v1(step, delay)

    def test_stepper(self, sequence, delay = None, rpm = None):
        if rpm is not None:
            delay = 60/(200 * rpm * 4)
        else:
            pass
        for step in sequence:
            self.step_helper_v1(step, delay)


if __name__ == "__main__":

    #GPIO.cleanup()
    # Set up the GPIO pins
    A1 = 17  # IN1
    A2 = 18  # IN2
    B1 = 27  # IN3
    B2 = 22  # IN4
    
    # Create sensor objects
    stepper = Nema17(A1, A2, B1, B2, 23)
    stepper.wake()
    
    try:
        #stepper.test_stepper(stepper.full_step, delay = 1e-3, rpm = None)
        stepper.rotate_full_step(50)
        #stepper.rotate_half_step(40)
        #stepper.rotate_full_step_ccw(10)
        #stepper.rotate_half_step_ccw()
        
    except KeyboardInterrupt:
        print("\nMeasurement stopped by user")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        GPIO.cleanup()