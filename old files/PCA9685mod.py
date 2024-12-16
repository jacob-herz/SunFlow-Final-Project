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
        # Initialize the PCA9685 controller
        self.bus = smbus2.SMBus(i2c_bus)
        self.address = address
        self.initialize()
        self.all_leds = []

    def initialize(self):
        # Initialize the PCA9685 chip
        self.bus.write_byte_data(self.address, self.MODE1, 0x00)
        time.sleep(0.005)
        self.bus.write_byte_data(self.address, self.MODE1, 0x10)
        self.bus.write_byte_data(self.address, self.PRESCALE, 0x79)
        self.bus.write_byte_data(self.address, self.MODE1, 0x00)
        time.sleep(0.005)
        self.bus.write_byte_data(self.address, self.MODE1, 0xA1)

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
            # Initialize a single LED
            self.controller = controller
            self.channel = channel
            self.controller.all_leds.append(self)

        def set_brightness(self, brightness):
            # Set brightness for the LED (0-100%)
            duty_cycle = int(brightness * 4095 / 100)
            self.controller.set_pwm(self.channel, 0, duty_cycle)

        def breathe(self, duration=5, steps=100):
            # Create a breathing effect for the LED
            for i in range(steps):
                brightness = (math.sin(i * math.pi / steps) + 1) / 2 * 100
                self.set_brightness(brightness)
                time.sleep(duration / steps)

    class RGBLED:
        def __init__(self, controller, red_channel, green_channel, blue_channel):
            # Initialize an RGB LED
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

    class BatchLED:
        def __init__(self, leds):
            # Initialize a group of LEDs
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

    def create_led(self, channel):
        # Create a single LED object
        return self.LED(self, channel)

    def create_rgb_led(self, red_channel, green_channel, blue_channel):
        # Create an RGB LED object
        return self.RGBLED(self, red_channel, green_channel, blue_channel)

    def create_batch_led(self, channels):
        # Create a BatchLED object for multiple LEDs
        return self.BatchLED([self.create_led(channel) for channel in channels])

    def all_off(self):
        # Turn off all LEDs
        for led in self.all_leds:
            led.set_brightness(0)

# Example usage
if __name__ == "__main__":
    try:
        controller = PCA9685Controller()

        # Create and use a single LED
        led1 = controller.create_led(0)
        led1.set_brightness(50)
        time.sleep(3)
        led1.set_brightness(0)
        time.sleep(3)
        led1.breathe(duration=3)

        # Create and use an RGB LED
        rgb_led1 = controller.create_rgb_led(4, 5, 6)
        rgb_led1.rgb_breathe("#FF0000", duration=3)
        time.sleep(1)

        rgb_led2 = controller.create_rgb_led(8, 9, 10)
        rgb_led2.rgb_breathe("#00FF00", duration=3)

        # Set RGB color and brightness
        rgb_led1.set_color_hex("#0000FF")
        rgb_led1.set_brightness(50)
        time.sleep(3)

        # Reset all LEDs
        controller.reset()
        time.sleep(2)

        # Turn off all LEDs
        controller.all_off()

        print("Test complete")

    except KeyboardInterrupt:
        controller.all_off()
        print('Exiting program')
