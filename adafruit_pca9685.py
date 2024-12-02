# SPDX-FileCopyrightText: 2016 Radomir Dopieralski for Adafruit Industries
# SPDX-FileCopyrightText: 2017 Scott Shawcroft for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_pca9685`
====================================================

Driver for the PCA9685 PWM control IC. Its commonly used to control servos, leds and motors.

.. seealso:: The `Adafruit CircuitPython Motor library
    <https://github.com/adafruit/Adafruit_CircuitPython_Motor>`_ can be used to control the PWM
    outputs for specific uses instead of generic duty_cycle adjustments.

* Author(s): Scott Shawcroft
edited by Julia Rodrigues

Implementation Notes
--------------------

**Hardware:**

* Adafruit `16-Channel 12-bit PWM/Servo Driver - I2C interface - PCA9685
  <https://www.adafruit.com/product/815>`_ (Product ID: 815)

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the ESP8622 and M0-based boards:
  https://github.com/adafruit/circuitpython/releases
* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
* Adafruit's Register library: https://github.com/adafruit/Adafruit_CircuitPython_Register

Adafruit-Blinka
sudo apt-get update
sudo apt-get install python3-pip
adafruit-circuitpython-register
adafruit-circuitpython-busdevice
pip3 install adafruit-circuitpython-pca9685 
pip3 install adafruit-circuitpython-busdevice

sudo apt-get install -y i2c-tools python3-smbus
sudo raspi-config
i2cdetect -y 1
"""

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_PCA9685.git"

import time
import math
import busio

from adafruit_register.i2c_struct import UnaryStruct
from adafruit_register.i2c_struct_array import StructArray
from adafruit_bus_device import i2c_device
from typing import Union
from typing import List

try:
    from typing import Optional, Type
    from types import TracebackType
    from busio import I2C
except ImportError:
    pass


class PWMChannel:
    """A single PCA9685 channel that matches the :py:class:`~pwmio.PWMOut` API.

    :param PCA9685 pca: The PCA9685 object
    :param int index: The index of the channel
    """

    def __init__(self, pca: "PCA9685", index: int):
        self._pca = pca
        self._index = index

    @property
    def frequency(self) -> float:
        """The overall PWM frequency in Hertz (read-only).
        A PWMChannel's frequency cannot be set individually.
        All channels share a common frequency, set by PCA9685.frequency."""
        return self._pca.frequency

    @frequency.setter
    def frequency(self, _):
        raise NotImplementedError("frequency cannot be set on individual channels")

    @property
    def duty_cycle(self) -> int:
        """16 bit value that dictates how much of one cycle is high (1) versus low (0). 0xffff will
        always be high, 0 will always be low and 0x7fff will be half high and then half low.
        """
        pwm = self._pca.pwm_regs[self._index]
        if pwm[0] == 0x1000:
            return 0xFFFF
        if pwm[1] == 0x1000:
            return 0x0000
        return (pwm[1] << 4)* 100 / 65535 # return the duty cycle as a float from 0-100

    @duty_cycle.setter
    def duty_cycle(self, value: Union[int, float]) -> None:
        # Convert to float if it's an int
        float_value = float(value)
        
        if not 0.0 <= float_value <= 100.0:
            raise ValueError(f"Out of range: value {float_value} not 0.0 <= value <= 100.0")
        
        # Convert percentage to 16-bit value
        int_value = int(float_value * 65535 / 100)
        
        if int_value == 65535:
            self._pca.pwm_regs[self._index] = (0x1000, 0)
        elif int_value == 0:
            self._pca.pwm_regs[self._index] = (0, 0x1000)
        else:
            self._pca.pwm_regs[self._index] = (0, int_value >> 4)

    def breathe(self, step: Union[int, float] = 1.0, delay: float = 0.01) -> None:
        """Create a breathing effect by smoothly increasing and decreasing brightness.
        
        :param float step: The increment size for brightness changes (0.1 to 100)
        :param float delay: The delay between brightness changes in seconds
        """
        # Increase brightness
        for brightness in range(0, 101, int(step)):
            self.duty_cycle = float(brightness)
            time.sleep(delay)
            
        # Decrease brightness
        for brightness in range(100, -1, -int(step)):
            self.duty_cycle = float(brightness)
            time.sleep(delay)


    _SINE_TABLE = {
        i: 50 * (math.sin(i * math.pi / 100) + 1) 
        for i in range(101)
    }

    def breathe_sin(self, step: Union[int, float] = 1, delay: float = 0.01) -> None:
        """Create a breathing effect using pre-calculated sine values.
        
        :param float step: The increment size for brightness changes (1 to 100)
        :param float delay: The delay between brightness changes in seconds
        """
        # Increase brightness using lookup table
        for i in range(0, 101, int(step)):
            self.duty_cycle = float(self._SINE_TABLE[i])
            time.sleep(delay)
            
        # Decrease brightness by reversing through the table
        for i in range(100, -1, -int(step)):
            self.duty_cycle = float(self._SINE_TABLE[i])
            time.sleep(delay)


class PCAChannels:  # pylint: disable=too-few-public-methods
    """Lazily creates and caches channel objects as needed. Treat it like a sequence.

    :param PCA9685 pca: The PCA9685 object
    """

    def __init__(self, pca: "PCA9685") -> None:
        self._pca = pca
        self._channels = [None] * len(self)

    def __len__(self) -> int:
        return 16

    def __getitem__(self, index: int) -> PWMChannel:
        if not self._channels[index]:
            self._channels[index] = PWMChannel(self._pca, index)
        return self._channels[index]


class PCA9685:
    """
    Initialise the PCA9685 chip at ``address`` on ``i2c_bus``.

    The internal reference clock is 25mhz but may vary slightly with environmental conditions and
    manufacturing variances. Providing a more precise ``reference_clock_speed`` can improve the
    accuracy of the frequency and duty_cycle computations. See the ``calibration.py`` example for
    how to derive this value by measuring the resulting pulse widths.

    :param ~busio.I2C i2c_bus: The I2C bus which the PCA9685 is connected to.
    :param int address: The I2C address of the PCA9685.
    :param int reference_clock_speed: The frequency of the internal reference clock in Hertz.
    """

    # Registers:
    mode1_reg = UnaryStruct(0x00, "<B")
    mode2_reg = UnaryStruct(0x01, "<B")
    prescale_reg = UnaryStruct(0xFE, "<B")
    pwm_regs = StructArray(0x06, "<HH", 16)

    def __init__(
        self,
        i2c_bus: I2C,
        *,
        address: int = 0x40,
        reference_clock_speed: int = 25000000,
    ) -> None:
        self.i2c_device = i2c_device.I2CDevice(i2c_bus, address)
        self.channels = PCAChannels(self)
        """Sequence of 16 `PWMChannel` objects. One for each channel."""
        self.reference_clock_speed = reference_clock_speed
        """The reference clock speed in Hz."""
        self.reset()

    def reset(self) -> None:
        """Reset the chip."""
        self.mode1_reg = 0x00  # Mode1

    @property
    def frequency(self) -> float:
        """The overall PWM frequency in Hertz."""
        prescale_result = self.prescale_reg
        if prescale_result < 3:
            raise ValueError(
                "The device pre_scale register (0xFE) was not read or returned a value < 3"
            )
        return self.reference_clock_speed / 4096 / (prescale_result + 1)

    @frequency.setter
    def frequency(self, freq: float) -> None:
        if not 40 <= freq <= 1000:
            raise ValueError(f"Frequency {freq} Hz is out of the supported range (40-1000 Hz)")
        
        prescale = int(self.reference_clock_speed / 4096.0 / freq + 0.5) - 1
        if prescale < 3:
            raise ValueError("PCA9685 cannot output at the given frequency")
        
        old_mode = self.mode1_reg
        self.mode1_reg = (old_mode & 0x7F) | 0x10  # Mode 1, sleep
        self.prescale_reg = prescale
        self.mode1_reg = old_mode
        time.sleep(0.005)
        self.mode1_reg = old_mode | 0xA0  # Mode 1, autoincrement on

    @property
    def pwm_batch(self):
        return [channel.duty_cycle for channel in self.channels]

    @pwm_batch.setter
    def pwm_batch(self, values: List[float]) -> None:
        if len(values) != len(self.channels):
            raise ValueError(f"Expected {len(self.channels)} values, got {len(values)}")

        for i, value in enumerate(values):
            if not 0 <= value <= 100:
                raise ValueError(f"Out of range: value {value} not 0 <= value <= 100")
            
            int_value = int(value * 4095 / 100)  # Convert 0-100 to 0-4095
            
            if int_value == 4095:
                self.pwm_regs[i] = (0x1000, 0)
            elif int_value == 0:
                self.pwm_regs[i] = (0, 0x1000)
            else:
                self.pwm_regs[i] = (0, int_value)

    def create_rgb_led(self, red_channel, green_channel, blue_channel):
        return RGBLED(self, red_channel, green_channel, blue_channel)

    def __enter__(self) -> "PCA9685":
        return self

    def __exit__(
        self,
        exception_type: Optional[Type[type]],
        exception_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        self.deinit()

    def deinit(self) -> None:
        """Stop using the pca9685."""
        self.reset()


class LED:
    def __init__(self, pca, channel):
        self.channel = pca.channels[channel]
    
    def set_brightness(self, brightness):
        # Convert 0-100 to 0-65535
        self.channel.duty_cycle = int(brightness * 65535 / 100)
    
    def breathe(self, duration=5, steps=100):
        for i in range(steps):
            brightness = (math.sin(i * math.pi / steps) + 1) / 2 * 100
            self.set_brightness(brightness)
            time.sleep(duration / steps)

class RGBLED:
    def __init__(self, pca, red_channel, green_channel, blue_channel):
        self.red = pca.channels[red_channel]
        self.green = pca.channels[green_channel]
        self.blue = pca.channels[blue_channel]

    def set_color(self, r, g, b):
        self.red.duty_cycle = r
        self.green.duty_cycle = g
        self.blue.duty_cycle = b

    def set_color_hex(self, hex_color):
        r = int(hex_color[1:3], 16) * 100 / 255
        g = int(hex_color[3:5], 16) * 100 / 255
        b = int(hex_color[5:7], 16) * 100 / 255
        self.set_color(r, g, b)

    def rgb_breathe(self, color, duration=5, steps=100):
        r, g, b = [int(color[i:i+2], 16) for i in (1, 3, 5)]
        for i in range(steps):
            brightness = (math.sin(i * math.pi / steps) + 1) / 2
            self.set_color(
                r * brightness * 100 / 255,
                g * brightness * 100 / 255,
                b * brightness * 100 / 255
            )
            time.sleep(duration / steps)

class LEDBatch:
    def __init__(self, leds):
        self.leds = leds

    def set_brightness(self, brightness):
        for led in self.leds:
            led.set_brightness(brightness)

    def breathe(self, duration=5, steps=100):
        for i in range(steps):
            brightness = (math.sin(i * math.pi / steps) + 1) / 2 * 100
            self.set_brightness(brightness)
            time.sleep(duration / steps)