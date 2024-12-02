# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

# Outputs a 50% duty cycle PWM single on the 0th channel.
# Connect an LED and resistor in series to the pin
# to visualize duty cycle changes and its impact on brightness.

'''
Adafruit-Blinka
adafruit-circuitpython-register
adafruit-circuitpython-busdevice
pip3 install adafruit-circuitpython-pca9685
'''

import board
import time
from adafruit_pca9685 import PCA9685

# Create I2C bus interface and PCA9685 instance
i2c = board.I2C()
pca = PCA9685(i2c)
pca.frequency = 60

# Define LED channels
led1 = pca.channels[0]
led2 = pca.channels[1]
led3 = pca.channels[2]
rgb_red = pca.channels[3]
rgb_green = pca.channels[4]
rgb_blue = pca.channels[5]

# Test regular LEDs
print("Testing regular LEDs")
for led in [led1, led2, led3]:
    led.duty_cycle = 32768  # Set to 50% brightness
    time.sleep(1)
    led.duty_cycle = 0       # Turn off
    time.sleep(0.5)

# Test RGB LED colors
print("Testing RGB LED")
colors = [(100, 0, 0), (0, 100, 0), (0, 0, 100), (100, 100, 0), (100, 0, 100), (0, 100, 100), (100, 100, 100)]
for color in colors:
    rgb_red.duty_cycle = int(color[0] * 65535 / 100)
    rgb_green.duty_cycle = int(color[1] * 65535 / 100)
    rgb_blue.duty_cycle = int(color[2] * 65535 / 100)
    time.sleep(1)

# Turn off RGB LED
rgb_red.duty_cycle = rgb_green.duty_cycle = rgb_blue.duty_cycle = 0

print("Test complete")