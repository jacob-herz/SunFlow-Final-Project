#!/usr/bin/env python3
"""
MCP9808 Temperature Sensor Driver for Python 3.x.x

Revised by: Ran Yang, September 2024

Pin Configuration for Raspberry Pi 4:
- Vdd to GPIO1 (3.3V)
- Gnd to any GPIO ground
- SCL to GPIO3
- SDA to GPIO2
- Alert to a user-defined GPIO pin (can be left floating)
- A0, A1, and A2 define the chip's address. Max 8 chips (0b000 to 0b111) can be used simultaneously.
  Floating all address pins results in address 0b000.
"""

import smbus2

class MCP9808:

    DEFAULT_ADDRESS = 0x18
    REG_CONFIG = 0x01
    REG_TEMPERATURE = 0x05
    REG_TCRITICAL = 0x04
    REG_RESOLUTION = 0x08

    def __init__(self, i2c_addr=DEFAULT_ADDRESS):
        self.i2c_addr = i2c_addr
        self.bus = smbus2.SMBus(1)

    def configure(self, config_value=0):

        config_value = self._swap_bytes(config_value)
        self.bus.write_word_data(self.i2c_addr, self.REG_CONFIG, config_value)
        read_config = self._swap_bytes(self.bus.read_word_data(self.i2c_addr, self.REG_CONFIG))
        print(f'Temperature sensor configured as: {bin(read_config)}')


    def read_temperature(self):
        temphex = self.bus.read_word_data(self.i2c_addr, self.REG_TEMPERATURE)
        #convert from big-endian to little-endian
        temphex = ((temphex & 0x00ff) << 8) + ((temphex & 0xff00) >> 8)      
        #Mask out the flag bits
        temphex = temphex & 0x1fff       
        #the sign bit
        sign = (temphex & 0x1000) >> 12      
        # Mask out the sign bit
        temphex = temphex & 0xfff       
        # Extract upper 8 bits
        integer_part = temphex >> 4
        
        if sign:
            return integer_part - 256
        else:
            return integer_part
    
    def threebit_read_temperature(self):
        """Read temperature with exactly 0.125°C resolution using 3 fractional bits."""
        # Read the 16-bit temperature register from the sensor
        temphex = self.bus.read_word_data(self.i2c_addr, self.REG_TEMPERATURE)

        # Convert from big-endian to little-endian
        temphex = ((temphex & 0x00ff) << 8) + ((temphex & 0xff00) >> 8)      

        # Mask out the 3 flag bits (keep only the lower 13 bits)
        temphex = temphex & 0x1fff       

        # exrtact the sign bit (bit 12 indicates whether the temperature is negative)
        sign = (temphex & 0x1000) >> 12

        # Mask out the sign bit (keep only the temperature data)
        temphex = temphex & 0xfff
        
        # Extract the integer part (upper 8 bits)
        integer_part = temphex >> 4  # Right shift by 4 to get the integer part
        
        # Extract the fractional part (lower 4 bits) but only use the top 3 bits for 0.125°C resolution
        fractional_part = (temphex & 0xF) >> 1  # Shift right by 1 to discard the least significant bit

        # Combine the integer part and the 3-bit fractional part
        # Divide the fractional part by 8 to get 0.125°C resolution (since 2^3 = 8)
        temperature = integer_part + (fractional_part / 8.0)

        # If the sign bit was set, adjust the temperature for negative values using two's complement
        if sign:
            return temperature - 256  # For negative temperatures subtract 256
        else:
            return temperature
   

    def set_critical_temperature(self, temp_c):

        temp_encoded = self._encode_temperature(temp_c)
        self._write_word(self.REG_TCRITICAL, temp_encoded)

    def set_resolution(self, resolution=0.0625):

        resolution_map = {0.5: 0, 0.25: 1, 0.125: 2, 0.0625: 3}
        self.bus.write_byte_data(self.i2c_addr, self.REG_RESOLUTION, resolution_map.get(resolution, 3))

    def _swap_bytes(self, value):

        return ((value & 0xFF) << 8) | ((value & 0xFF00) >> 8)

    def _write_word(self, reg, value):
        """Write a 16-bit word to the specified register."""
        self.bus.write_word_data(self.i2c_addr, reg, self._swap_bytes(value))

    def _encode_temperature(self, temp_c):
        """Encode temperature for writing to registers."""
        if temp_c < 0:
            return (int(abs(temp_c) * 16) & 0xFFF) ^ 0x1FFF + 1
        return int(temp_c * 16) & 0xFFF
