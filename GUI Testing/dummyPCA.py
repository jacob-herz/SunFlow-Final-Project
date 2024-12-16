import time
import random

class DummyPCA9685Controller:
    def __init__(self):
        print("Dummy PCA9685Controller initialized")
        self.all_leds = []

    def set_pwm(self, channel, on, off):
        print(f"Dummy set_pwm called: channel={channel}, on={on}, off={off}")

    def reset(self):
        print("Dummy reset called")

    def master_off(self):
        print("Dummy master_off called")

    def create_led(self, channel):
        led = DummyLED(self, channel)
        self.all_leds.append(led)
        return led

    def create_rgb_led(self, channels):
        return DummyRGBLED(self, channels)

    def create_batch_led(self, channels):
        return DummyBatchLED([self.create_led(channel) for channel in channels])

    def create_light_show(self):
        return DummyLEDShow(self)

    def all_off(self):
        print("Dummy all_off called")

    def all_on(self):
        print("Dummy all_on called")

class DummyLED:
    def __init__(self, controller, channel):
        self.controller = controller
        self.channel = channel

    def set_brightness(self, brightness):
        print(f"Dummy LED {self.channel} brightness set to {brightness}")

    def breathe(self, duration=15, steps=100):
        print(f"Dummy LED {self.channel} breathe effect: duration={duration}, steps={steps}")

    def pulse(self, duration=1, steps=50):
        print(f"Dummy LED {self.channel} pulse effect: duration={duration}, steps={steps}")

class DummyRGBLED:
    def __init__(self, controller, channels):
        self.controller = controller
        self.channels = channels

    def set_color(self, r, g, b):
        print(f"Dummy RGB LED {self.channels} color set to R:{r}, G:{g}, B:{b}")

    def set_color_hex(self, hex_color):
        print(f"Dummy RGB LED {self.channels} color set to hex: {hex_color}")

    def set_white_brightness(self, brightness):
        print(f"Dummy RGB LED {self.channels} white brightness set to {brightness}")

    def breathe_single_color(self, hex_color, duration=5, steps=100):
        print(f"Dummy RGB LED {self.channels} breathe single color: {hex_color}, duration={duration}, steps={steps}")

    def color_cycle(self, duration=10, steps=200):
        print(f"Dummy RGB LED {self.channels} color cycle: duration={duration}, steps={steps}")

    def breathe_color_wheel(self, duration=10, steps=200):
        print(f"Dummy RGB LED {self.channels} breathe color wheel: duration={duration}, steps={steps}")

class DummyBatchLED:
    def __init__(self, leds):
        self.leds = leds

    def set_brightness(self, brightness):
        print(f"Dummy Batch LED brightness set to {brightness}")

    def breathe(self, duration=5, steps=100):
        print(f"Dummy Batch LED breathe effect: duration={duration}, steps={steps}")

    def chase(self, duration=5, steps=20):
        print(f"Dummy Batch LED chase effect: duration={duration}, steps={steps}")

class DummyLEDShow:
    def __init__(self, controller):
        self.controller = controller
        self.blade_leds = [controller.create_led(pin) for pin in range(5)]
        self.rgb_leds = [controller.create_rgb_led([i, i+1, i+2]) for i in range(0, 6, 3)]
        self.moss_leds = [controller.create_led(pin) for pin in range(8, 12)]
        self.center_led = controller.create_led(0)

    def all_on(self):
        print("Dummy LED Show: All LEDs turned on")

    def all_off(self):
        print("Dummy LED Show: All LEDs turned off")

    def blade_spin(self, duration=15):
        print(f"Dummy LED Show: Blade spin effect for {duration} seconds")

    def blade_chase(self, duration=15, tail_length=2):
        print(f"Dummy LED Show: Blade chase effect for {duration} seconds with tail length {tail_length}")

    def rgb_breathe_color_wheel(self, duration=10):
        print(f"Dummy LED Show: RGB breathe color wheel effect for {duration} seconds")

    def rgb_color_wheel_tandem(self, duration=10, steps=200):
        print(f"Dummy LED Show: RGB color wheel tandem effect for {duration} seconds with {steps} steps")

    def rgb_breathe_single_color(self, hex_color, duration=5, steps=100):
        print(f"Dummy LED Show: RGB breathe single color effect with color {hex_color} for {duration} seconds")

    def rgb_single_color(self, hex_color, brightness=50):
        print(f"Dummy LED Show: RGB single color set to {hex_color} with brightness {brightness}")

    def moss_twinkle(self, duration=10):
        print(f"Dummy LED Show: Moss twinkle effect for {duration} seconds")

    def moss_breathe(self, duration, steps=200):
        print(f"Dummy LED Show: Moss breathe effect for {duration} seconds with {steps} steps")

    def alternating_blink(self, duration=15):
        print(f"Dummy LED Show: Alternating blink effect for {duration} seconds")

    def run_light_show(self, show_name, duration=15, color=None):
        print(f"Dummy LED Show: Running light show '{show_name}' for {duration} seconds")
        if color:
            print(f"Color parameter: {color}")

if __name__ == "__main__":
    controller = DummyPCA9685Controller()
    led_show = controller.create_light_show()

    print("Testing dummy LED show functions:")
    led_show.all_off()
    led_show.all_on()
    led_show.blade_chase(duration=5, tail_length=3)
    led_show.rgb_single_color('#32a852')
    led_show.moss_twinkle(duration=10)
    led_show.alternating_blink(duration=5)
    led_show.run_light_show("Custom Show", duration=20, color="#FF00FF")
