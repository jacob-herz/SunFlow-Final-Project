import smbus2
import time

'''
use this file to troubleshoot RPI issues with smbus
'''

# Define I2C bus and PCA9685 address
I2C_BUS = 1  # I2C bus number (1 for Raspberry Pi)
PCA9685_ADDRESS = 0x40  # Default I2C address

# Registers
MODE1 = 0x00
LED0_ON_L = 0x06
LED0_ON_H = 0x07
LED0_OFF_L = 0x08
LED0_OFF_H = 0x09
PRESCALE = 0xFE  # For setting PWM frequency

# Initialize I2C bus
bus = smbus2.SMBus(I2C_BUS)

# Set up PCA9685
def initialize_pca9685():
    bus.write_byte_data(PCA9685_ADDRESS, MODE1, 0x00)  # Reset PCA9685
    time.sleep(0.005)  # Wait for oscillator
    bus.write_byte_data(PCA9685_ADDRESS, MODE1, 0x10)  # Enter sleep mode
    bus.write_byte_data(PCA9685_ADDRESS, PRESCALE, 0x79)  # Set prescale for 60Hz
    bus.write_byte_data(PCA9685_ADDRESS, MODE1, 0x00)  # Exit sleep mode
    time.sleep(0.005)
    bus.write_byte_data(PCA9685_ADDRESS, MODE1, 0xA1)  # Enable auto-increment

# Set PWM duty cycle
def set_pwm(channel, on, off):
    reg_base = LED0_ON_L + 4 * channel
    bus.write_byte_data(PCA9685_ADDRESS, reg_base, on & 0xFF)
    bus.write_byte_data(PCA9685_ADDRESS, reg_base + 1, on >> 8)
    bus.write_byte_data(PCA9685_ADDRESS, reg_base + 2, off & 0xFF)
    bus.write_byte_data(PCA9685_ADDRESS, reg_base + 3, off >> 8)

# Initialize and set PWM
initialize_pca9685()
set_pwm(0, 0, 2048)  # Set channel 0 to 50% duty cycle (2048/4096)

print("Channel 0 set to 50% duty cycle.")
