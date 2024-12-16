
# fake motor stuff
class MockNema17:
    def __init__(self, A1_pin, A2_pin, B1_pin, B2_pin, sleep_pin):
        self.A1 = A1_pin
        self.A2 = A2_pin
        self.B1 = B1_pin
        self.B2 = B2_pin
        self.sleep_pin = sleep_pin

    def rotate_full_step(self, rpm):
        print(f"Rotating full step at {rpm} RPM")

    def rotate_full_step_ccw(self, rpm):
        print(f"Rotating full step CCW at {rpm} RPM")

    def rotate_half_step(self, rpm):
        print(f"Rotating half step at {rpm} RPM")

    def rotate_half_step_ccw(self, rpm):
        print(f"Rotating half step CCW at {rpm} RPM")

    def stop(self):
        print("Motor stopped")


class DummyMCP9808:
    def __init__(self, i2c_addr=0x18):
        self.i2c_addr = i2c_addr
        self.temperature = 25.0  # Default temperature in Celsius
        self.critical_temp = 35.0  # Default critical temperature
        self.resolution = 0.0625  # Default resolution

    def configure(self, config_value=0):
        print(f'Dummy sensor configured with value: {bin(config_value)}')

    def read_temperature(self):
        return int(self.temperature)

    def threebit_read_temperature(self):
        return round(self.temperature, 3)

    def set_critical_temperature(self, temp_c):
        self.critical_temp = temp_c
        print(f'Critical temperature set to {temp_c}°C')

    def set_resolution(self, resolution=0.0625):
        self.resolution = resolution
        print(f'Resolution set to {resolution}°C')

    # Additional method to simulate temperature changes
    def set_temperature(self, temp):
        self.temperature = temp
