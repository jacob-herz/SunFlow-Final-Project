import smbus2
import time
import math

class PCA9685Controller:
    # Register addresses for PCA9685
    MODE1 = 0x00
    LED0_ON_L = 0x06
    LED0_ON_H = 0x07
    LED0_OFF_L = 0x08
    LED0_OFF_H = 0x09
    PRESCALE = 0xFE

    def __init__(self, i2c_bus=1, address=0x40):
        self.bus = smbus2.SMBus(i2c_bus)
        self.address = address
        self.initialize()
        self.all_leds = []

    def initialize(self, freq=50):
        # Initialize the PCA9685 chip with a specific frequency
        self.bus.write_byte_data(self.address, self.MODE1, 0x00)
        time.sleep(0.005)
        prescale_value = int(25000000.0 / (4096 * freq) - 1)
        self.bus.write_byte_data(self.address, self.MODE1, 0x10)  # Sleep mode
        self.bus.write_byte_data(self.address, self.PRESCALE, prescale_value)
        self.bus.write_byte_data(self.address, self.MODE1, 0x00)
        time.sleep(0.005)
        self.bus.write_byte_data(self.address, self.MODE1, 0xA1)  # Auto-increment and restart

    def set_pwm(self, channel, on, off):
        # Set PWM values for a specific channel
        reg_base = self.LED0_ON_L + 4 * channel
        self.bus.write_byte_data(self.address, reg_base, on & 0xFF)
        self.bus.write_byte_data(self.address, reg_base + 1, on >> 8)
        self.bus.write_byte_data(self.address, reg_base + 2, off & 0xFF)
        self.bus.write_byte_data(self.address, reg_base + 3, off >> 8)

    def reset(self):
        # Reset all LEDs to 0 brightness
        for led in self.all_leds:
            led.set_brightness(0)

    class LED:
        def __init__(self, controller, channel):
            self.controller = controller
            self.channel = channel
            self.controller.all_leds.append(self)

        def set_brightness_old(self, brightness):
            # Set brightness for the LED (0-100%)
            duty_cycle = int((brightness) * 4095 / 100) # int(brightness * 65535 / 100)? from adafruit
            self.controller.set_pwm(self.channel, 0, duty_cycle)

        def set_brightness(self, brightness):
            if brightness <= 0:
                # Turn off the LED completely
                self.controller.set_pwm(self.channel, 0, 4096)
            elif brightness >= 100:
                # Turn on the LED at full brightness
                self.controller.set_pwm(self.channel, 4096, 0)
            else:
                # Normal case: set PWM duty cycle
                duty_cycle = int(brightness * 4095 / 100)
                self.controller.set_pwm(self.channel, 0, duty_cycle)

        def breathe(self, duration=5, steps=100):
            # Create a breathing effect for the LED
            for i in range(steps):
                brightness = (math.sin(i * math.pi / steps) + 1) / 2 * 100
                self.set_brightness(brightness)
                time.sleep(duration / steps)

        def pulse(self, duration=1, steps=50):
            # Create a quick pulse effect
            self.set_brightness(0)
            time.sleep(duration / 4)
            for i in range(steps):
                brightness = math.sin(i * math.pi / steps) * 100
                self.set_brightness(brightness)
                time.sleep(duration / (2 * steps))
            self.set_brightness(0)

    class RGBLED:
        def __init__(self, controller, red_channel, green_channel, blue_channel):
            self.red = controller.LED(controller, red_channel)
            self.green = controller.LED(controller, green_channel)
            self.blue = controller.LED(controller, blue_channel)

        def set_color(self, r, g, b):
            # Set RGB color (0-100 for each component)
            self.red.set_brightness(r)
            self.green.set_brightness(g)
            self.blue.set_brightness(b)

        def set_color_hex(self, hex_color):
            # Set RGB color using a hex string
            r = int(hex_color[1:3], 16) * 100 / 255
            g = int(hex_color[3:5], 16) * 100 / 255
            b = int(hex_color[5:7], 16) * 100 / 255
            self.set_color(r, g, b)

        def set_brightness(self, brightness):
            # Set brightness for all RGB components
            self.red.set_brightness(brightness)
            self.green.set_brightness(brightness)
            self.blue.set_brightness(brightness)

        def rgb_breathe(self, color, duration=5, steps=100):
            # Create a breathing effect with a specific color
            r, g, b = [int(color[i:i+2], 16) for i in (1, 3, 5)]
            for i in range(steps):
                brightness = (math.sin(i * math.pi / steps) + 1) / 2
                self.set_color(
                    r * brightness * 100 / 255,
                    g * brightness * 100 / 255,
                    b * brightness * 100 / 255
                )
                time.sleep(duration / steps)

        def color_cycle(self, duration=10, steps=200):
            # Cycle through the color wheel
            for i in range(steps):
                hue = i / steps
                r, g, b = [int(x * 255) for x in self.hsv_to_rgb(hue, 1, 1)]
                self.set_color(r * 100 / 255, g * 100 / 255, b * 100 / 255)
                time.sleep(duration / steps)

        @staticmethod
        def hsv_to_rgb(h, s, v):
            if s == 0.0:
                return (v, v, v)
            i = int(h * 6.0)
            f = (h * 6.0) - i
            p = v * (1.0 - s)
            q = v * (1.0 - s * f)
            t = v * (1.0 - s * (1.0 - f))
            i = i % 6
            if i == 0:
                return (v, t, p)
            if i == 1:
                return (q, v, p)
            if i == 2:
                return (p, v, t)
            if i == 3:
                return (p, q, v)
            if i == 4:
                return (t, p, v)
            if i == 5:
                return (v, p, q)

    class BatchLED:
        def __init__(self, leds):
            self.leds = leds

        def set_brightness(self, brightness):
            # Set brightness for all LEDs in the group
            for led in self.leds:
                led.set_brightness(brightness)

        def breathe(self, duration=5, steps=100):
            # Create a breathing effect for all LEDs in the group
            for i in range(steps):
                brightness = (math.sin(i * math.pi / steps) + 1) / 2 * 100
                self.set_brightness(brightness)
                time.sleep(duration / steps)

        def chase(self, duration=5, steps=20):
            # Create a chasing effect
            for _ in range(steps):
                for led in self.leds:
                    led.set_brightness(100)
                    time.sleep(duration / (steps * len(self.leds)))
                    led.set_brightness(0)

    def create_led(self, channel):
        return self.LED(self, channel)

    def create_rgb_led(self, red_channel, green_channel, blue_channel):
        return self.RGBLED(self, red_channel, green_channel, blue_channel)

    def create_batch_led(self, channels):
        return self.BatchLED([self.create_led(channel) for channel in channels])

    def all_off(self):
        for led in self.all_leds:
            led.set_brightness(0)

    def all_on(self):
        for led in self.all_leds:
            led.set_brightness(100)

    def sequential_on(self, delay=0.1):
        for led in self.all_leds:
            led.set_brightness(100)
            time.sleep(delay)

    def sequential_off(self, delay=0.1):
        for led in self.all_leds:
            led.set_brightness(0)
            time.sleep(delay)

# Example usage
if __name__ == "__main__":
    try:
        controller = PCA9685Controller()

        # Create and use a single LED
        led1 = controller.create_led(0)
        led1.set_brightness(50)
        time.sleep(1)
        led1.set_brightness(0)
        time.sleep(1)
        led1.breathe(duration=3)
        led1.pulse()

        # Create and use an RGB LED
        rgb_led1 = controller.create_rgb_led(1, 2, 3)
        rgb_led1.rgb_breathe("#FF0000", duration=3)
        time.sleep(1)
        rgb_led1.color_cycle(duration=5)

        rgb_led2 = controller.create_rgb_led(4, 5, 6)
        rgb_led2.set_color_hex("#00FF00")
        time.sleep(2)

        # Create and use a batch of LEDs
        batch_led = controller.create_batch_led([7, 8, 9, 10])
        batch_led.breathe(duration=3)
        batch_led.chase(duration=3)

        # Demonstrate all LEDs
        controller.all_on()
        time.sleep(2)
        controller.sequential_off()
        time.sleep(1)
        controller.sequential_on()
        time.sleep(1)
        controller.all_off()

        print("Test complete")

    except KeyboardInterrupt:
        controller.all_off()
        print('Exiting program')