import smbus2
import time
import random
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

    def master_off(self):
        # Set all channels (0-15) to off
        for channel in range(16):
            self.set_pwm(channel, 0, 4096)  # 4096 represents fully off for PCA9685

    def start_light_show(self, show_name, duration=5):
        self.led_show.start_show(show_name, duration)

    def stop_light_show(self):
        self.led_show.stop_show()

    class LED:
        def __init__(self, controller, channel):
            self.controller = controller
            self.channel = channel
            self.controller.all_leds.append(self)

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


        def set_rgb_brightness(self, brightness):
            '''this is for rgb
            brightness is from 0-255 instead of 0-100'''
            if brightness <= 0:
                # Turn off the LED completely
                self.controller.set_pwm(self.channel, 0, 4096)
            elif brightness >= 255:
                # Turn on the LED at full brightness
                self.controller.set_pwm(self.channel, 4096, 0)
            else:
                # Normal case: set PWM duty cycle
                duty_cycle = int(brightness * 4095 / 100)
                self.controller.set_pwm(self.channel, 0, duty_cycle)

        def breathe(self, duration=15, steps=100):
            # Create a breathing effect for the LED
            start = time.time()
            while (time.time() - start) < duration:
                for i in range(steps):
                    brightness = (math.sin(i * math.pi / steps) + 1) / 2 * 100
                    self.set_brightness(brightness)
                    time.sleep(duration / (steps * 2))  # Adjusted sleep time
                for i in range(steps, 0, -1):
                    brightness = (math.sin(i * math.pi / steps) + 1) / 2 * 100
                    self.set_brightness(brightness)
                    time.sleep(duration / (steps * 2))  # Adjusted sleep time
                
                if (time.time() - start) >= duration:
                    break

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
        def __init__(self, controller, channels):
            # channels is a list [r, g, b]
            # Initialize an RGB LED
            self.red = controller.LED(controller, channels[0])
            self.green = controller.LED(controller, channels[1])
            self.blue = controller.LED(controller, channels[2])

        def set_color(self, r, g, b):
            # Set RGB color (0-255 for each component)
            self.red.set_rgb_brightness(r)
            self.green.set_rgb_brightness(g)
            self.blue.set_rgb_brightness(b)

        def set_color_hex(self, hex_color):
            # Set RGB color using a hex string
            # converts to 0-255 as desired
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            print(f'setting colors to {r}, {g}, {b}')
            self.set_color(r, g, b)

        def set_white_brightness(self, brightness):
            # Set brightness for all RGB components from 0-100
            self.red.set_brightness(brightness)
            self.green.set_brightness(brightness)
            self.blue.set_brightness(brightness)

        def breathe_single_color(self, hex_color, duration=5, steps=100):
            r, g, b = [int(hex_color[i:i+2], 16) for i in (1, 3, 5)]
            for i in range(steps):
                brightness = ((math.sin(i * math.pi / steps) + 1) / 2) * 255 # set scaled brightness from 0-255
                self.red.set_brightness(r)
                self.green.set_brightness(g)
                self.blue.set_brightness(b)
                time.sleep(duration / steps)

        def color_cycle(self, duration=10, steps=200):
            # Cycle through the color wheel
            for i in range(steps):
                hue = i / steps
                r, g, b = [int(x * 255) for x in self.hsv_to_rgb(hue, 1, 1)]
                self.set_color(r * 100 / 255, g * 100 / 255, b * 100 / 255)
                time.sleep(duration / steps)

        def breathe_color_wheel(self, duration=10, steps=200):
            for i in range(steps):
                hue = i / steps
                r, g, b = [int(x * 255) for x in self.hsv_to_rgb(hue, 1, 1)]
                brightness = (math.sin(i * math.pi / steps) + 1) / 2
                self.set_color(
                    r * brightness * 100 / 255,
                    g * brightness * 100 / 255,
                    b * brightness * 100 / 255
                )
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
        
        def rgb_breathe_single_color(self, hex_color, duration=5, steps=100):
            r, g, b = [int(hex_color[i:i+2], 16) for i in (1, 3, 5)]
            print('set color')
            for i in range(steps):
                brightness = (math.sin(i * math.pi / steps) + 1) / 2
                print(f'brightness set to {brightness}')
                for rgb_led in self.rgb_leds:
                    rgb_led.set_color(
                        r * brightness,
                        g * brightness,
                        b * brightness
                    )
                    dur1 = time.sleep(0.1)
                    print(f'slept for {dur1} inside rgb loop')
                dur2 = 0.5
                time.sleep(dur2)
                print(f'slept for {dur2} outside rgb loop')
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

    def create_rgb_led(self, channels):
        return self.RGBLED(self, channels)

    def create_batch_led(self, channels):
        return self.BatchLED([self.create_led(channel) for channel in channels])
    
    def create_light_show(self):
        return self.LEDShow(self)

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

    class LEDShow:
        def __init__(self, controller):
            self.controller = controller
            # Updated pin assignments
            self.blade_led_pins = [1, 11, 12, 13, 14]  # 5 blade LEDs
            self.center_pin = 0 # 1 center LED
            self.rgb_led_pins = [[5, 6, 7], [8, 9, 10]]  # 2 RGB LEDs
            self.moss_led_pins = [2, 3, 4, 15]  # 4 moss LEDs

            # Create LED objects
            self.blade_leds = [controller.create_led(pin) for pin in self.blade_led_pins]
            self.rgb_leds = [controller.create_rgb_led(pins) for pins in self.rgb_led_pins]
            self.moss_leds = [controller.create_led(pin) for pin in self.moss_led_pins]
            self.center_led = controller.create_led(self.center_pin)

        def all_on(self):
            """Turn on all LEDs."""
            for led in self.blade_leds + self.moss_leds:
                led.set_brightness(100)
            for rgb in self.rgb_leds:
                rgb.set_color_hex('#f23fe3') # default is pink

        def all_off(self):
            """Turn off all LEDs."""
            for led in self.blade_leds + self.moss_leds:
                led.set_brightness(0)
            for rgb in self.rgb_leds:
                rgb.set_color(0, 0, 0)

        def center_led_breathe(self, duration=5, steps=200):
            self.center_led.breathe(duration, steps)

        def center_led_toggle(self, state):
            self.center_led.set_brightness(100 if state else 0)

        def center_led_on(self):
            self.center_led.set_brightness(100)

        def center_led_off(self):
            self.center_led.set_brightness(0)


        def blade_spin(self, duration=15):
            """Create a chasing effect on the windmill blades."""
            start = time.time()
            steps = len(self.blade_leds)
            delay = 0.25  # Adjust this value for desired speed
            
            while (time.time() - start) <= duration:
                for i in range(steps):
                    self.blade_leds[i].set_brightness(100)
                    time.sleep(delay)
                    self.blade_leds[i].set_brightness(0)

        def blade_chase(self, duration=15, tail_length=2):
            """Create a chasing effect on the windmill blades with a tail."""
            steps = len(self.blade_leds)
            step_duration = duration / (steps * 2)  # Adjust for a complete rotation

            start = time.time()
            while (time.time()-start) <= duration:
                for _ in range(int(duration / step_duration)):
                    for i in range(steps):
                        # Turn off all LEDs
                        for led in self.blade_leds:
                            led.set_brightness(0)
                        
                        # Light up the tail
                        for j in range(tail_length):
                            index = (i - j) % steps
                            brightness = 100 - (j * (100 // tail_length))
                            self.blade_leds[index].set_brightness(brightness)
                        
                        time.sleep(step_duration)


        def rgb_breathe_color_wheel(self, duration=10):
            for rgb in self.rgb_leds:
                rgb.breathe_color_wheel(duration)
        
        @staticmethod
        def show_hsv_to_rgb(h, s, v):
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

        def rgb_color_wheel_tandem(self, duration=10, steps=200):
            for i in range(steps):
                hue = i / steps
                r, g, b = [int(x * 255) for x in self.show_hsv_to_rgb(hue, 1, 1)]
                for rgb in self.rgb_leds:
                    rgb.set_color(r * 100 / 255, g * 100 / 255, b * 100 / 255)
                time.sleep(duration / steps)

        def rgb_breathe_single_color(self, hex_color, duration=5, steps=100):
            r, g, b = [int(hex_color[i:i+2], 16) for i in (1, 3, 5)]
            print('set color')
            for i in range(steps):
                brightness = (math.sin(i * math.pi / steps) + 1) / 2
                print(f'brightness set to {brightness}')
                for rgb_led in self.rgb_leds:
                    rgb_led.set_color(
                        r * brightness,
                        g * brightness,
                        b * brightness
                    )
                    dur1 = time.sleep(0.1)
                    print(f'slept for {dur1} inside rgb loop')
                dur2 = 0.5
                time.sleep(dur2)
                print(f'slept for {dur2} outside rgb loop')


        def rgb_single_color(self, hex_color, brightness = 50):
            r, g, b = [int(hex_color[i:i+2], 16) for i in (1, 3, 5)]
            b2 = brightness/100
            for rgb_led in self.rgb_leds:
                rgb_led.set_color(
                    r * b2,
                    g * b2,
                    b * b2)
                
        def rgb_off(self, hex_color, brightness = 50):
            r, g, b = [int(hex_color[i:i+2], 16) for i in (1, 3, 5)]
            b2 = brightness/100
            start = time.time()
            for rgb_led in self.rgb_leds:
                rgb_led.set_color(
                    r * b2,
                    g * b2,
                    b * b2)

        
        def moss_twinkle(self, duration=10):
            """Twinkle effect on moss garden LEDs with random brightness, sleep time, and LED selection."""
            end_time = time.time() + duration
            while time.time() < end_time:
                # Select a random LED to twinkle
                led = random.choice(self.moss_leds)
                
                # Set a random brightness for the selected LED
                brightness = random.randint(0, 100)
                led.set_brightness(brightness)
                
                # Set a random sleep time between 0.05 and 0.5 seconds
                sleep_time = random.uniform(0.05, 0.5)
                time.sleep(sleep_time)


        def moss_breathe(self, duration, steps = 200):
            start = time.time()
            while(time.time() - start) <= duration:
                for i in range(steps):
                    for led in self.moss_leds:
                        brightness = (math.sin(i * math.pi / steps) + 1) / 2 * 100
                        led.set_brightness(brightness)
                        time.sleep(0.1)  # Adjusted sleep time
                for i in range(steps, 0, -1):
                    for led in self.moss_leds:
                        brightness = (math.sin(i * math.pi / steps) + 1) / 2 * 100
                        led.set_brightness(brightness)
                        time.sleep(0.1)  # Adjusted sleep time
                
                if (time.time() - start) >= duration:
                    continue


        def alternating_blink(self, duration=15):
            start = time.time()
            while (time.time() - start) <= duration:
                for i in range(2):
                    for j in range(0, len(self.blade_leds), 2):
                        self.blade_leds[j+i].set_brightness(100)
                        self.blade_leds[j+1-i].set_brightness(0)
                    time.sleep(0.33)

        def test_individual_channels(self, duration=5):
            """
            Light up each channel individually for a specified duration.
            This helps in identifying which LED is connected to which PCA channel.
            """
            # Turn off all LEDs first
            self.all_off()
            
            # Test all channels (0-15)
            for channel in range(16):
                print(f"Testing channel {channel}")
                self.controller.set_pwm(channel, 0, 4095)  # Turn on the channel at full brightness
                time.sleep(duration)
                self.controller.set_pwm(channel, 0, 0)  # Turn off the channel
                time.sleep(0.5)  # Short pause between channels

        def test(self, channel):
            """
            Light up each channel individually for a specified duration.
            This helps in identifying which LED is connected to which PCA channel.
            """
            # Turn off all LEDs first
            self.all_off()
            print(f'testing channel {channel}')
            self.controller.set_pwm(channel, 0, 4095)  # Turn on the channel at full brightness

            print(f"test {channel} complete")

        def run_light_show(self, show_name, duration=15, color=None):
            """Run a specific light show by name for 15 seconds"""

            if show_name == "all on":
                self.all_on()
            elif show_name == "all off":
                self.all_off()
            elif show_name == "blade chase":
                self.blade_chase(duration)
            elif show_name == "rgb fade":
                self.rgb_color_wheel_tandem(duration)
            elif show_name == "moss twinkle":
                self.moss_twinkle(duration)
            elif show_name == "alternating blink":
                self.alternating_blink(duration)
            elif show_name == "rgb single color":
                if color:
                    self.rgb_single_color(color, duration)
                else:
                    self.rgb_single_color('#f23fe3', duration) # default is pink
            else:
                pass
            self.all_on()



if __name__ == "__main__":
    try:
        controller = PCA9685Controller()
        led_show = controller.LEDShow(controller)  # Use controller.LEDShow instead of just LEDShow
        controller.all_off()
        
        
        print("Testing all off...")
        led_show.all_off()
        #time.sleep(1)

        # Run the channel test which will print out the channel being tested and leave that channel on for 5 seconds
        #led_show.test_individual_channels()
        #led_show.test(10)

        
        print("Testing all on...")
        led_show.all_on()
        time.sleep(2)
        led_show.all_off()
        time.sleep(1)

        ("Testing blade spin...")
        led_show.blade_spin(duration=5)
        time.sleep(1)

        print("Testing blade chase...")
        led_show.blade_chase(duration=5, tail_length=3)
        time.sleep(1)

        print("Testing RGB breathe color wheel...")
        led_show.rgb_single_color('#32a852')
        time.sleep(1)

        print("Testing moss twinkle...")
        led_show.moss_twinkle(duration=10)
        time.sleep(1)

        print("Testing alternating blink...")
        led_show.alternating_blink(duration=5)
        time.sleep(1)

        
        #print("Test complete")
        #led_show.all_off()

    except KeyboardInterrupt:
        led_show.all_off()
        print('Exiting program')