import board
import time
from adafruit_pca9685 import PCA9685

# Create an I2C bus interface and a PCA9685 instance
i2c = board.I2C()
pca = PCA9685(i2c)
pca.frequency = 60

# Test all channels by turning them on and off
for channel in range(16):
    pca.channels[channel].duty_cycle = 0xFFFF  # Set to full brightness
    time.sleep(0.5)
    pca.channels[channel].duty_cycle = 0      # Turn off
    time.sleep(0.5)

print("Test complete")
