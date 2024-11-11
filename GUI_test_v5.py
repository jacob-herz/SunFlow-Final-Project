import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
import random
import threading
import time

def get_temp():
    return round(25 + 5*random.random(), 2)

class MockNema17:
    def __init__(self, A1_pin, A2_pin, B1_pin, B2_pin):
        self.A1 = A1_pin
        self.A2 = A2_pin
        self.B1 = B1_pin
        self.B2 = B2_pin

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

class WindmillGUI:
    def __init__(self, master):
        self.master = master
        master.title("Windmill Control")
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.motor = MockNema17(A1_pin=17, A2_pin=18, B1_pin=27, B2_pin=22)
        self.running = False
        self.motor_thread = None

        frame = ctk.CTkFrame(master, corner_radius=20)
        frame.pack(padx=30, pady=30, fill="both", expand=True)

        # Temperature label
        self.temp_label = ctk.CTkLabel(frame, text=f"Temperature: {get_temp()}", font=("Helvetica", 18))
        self.temp_label.pack(pady=20)

        # Motor speed control
        speed_frame = ctk.CTkFrame(frame)
        speed_frame.pack(pady=20, fill="x")
        ctk.CTkLabel(speed_frame, text="Motor Speed (RPM):", font=("Helvetica", 14)).pack(side="left", padx=(0, 10))
        self.speed_var = ctk.StringVar(value="60.0")
        self.speed_entry = ctk.CTkEntry(speed_frame, textvariable=self.speed_var, width=50)
        self.speed_entry.pack(side="left", padx=(0, 10))
        self.speed_slider = ctk.CTkSlider(speed_frame, from_=1, to=150, command=self.update_speed_entry)
        self.speed_slider.pack(side="left", padx=(0, 10), expand=True)

        # Direction control
        direction_frame = ctk.CTkFrame(frame)
        direction_frame.pack(pady=20, fill="x")
        ctk.CTkLabel(direction_frame, text="Direction:", font=("Helvetica", 14)).pack(side="left", padx=(0, 10))
        self.direction_var = ctk.StringVar(value="CW")
        ctk.CTkRadioButton(direction_frame, text="CW", variable=self.direction_var, value="CW").pack(side="left", padx=10)
        ctk.CTkRadioButton(direction_frame, text="CCW", variable=self.direction_var, value="CCW").pack(side="left", padx=10)

        # Step mode control
        step_mode_frame = ctk.CTkFrame(frame)
        step_mode_frame.pack(pady=20, fill="x")
        ctk.CTkLabel(step_mode_frame, text="Step Mode:", font=("Helvetica", 14)).pack(side="left", padx=(0, 10))
        self.step_mode_var = ctk.StringVar(value="Full")
        ctk.CTkRadioButton(step_mode_frame, text="Full", variable=self.step_mode_var, value="Full").pack(side="left", padx=10)
        ctk.CTkRadioButton(step_mode_frame, text="Half", variable=self.step_mode_var, value="Half").pack(side="left", padx=10)

        # Apply Changes button
        self.apply_button = ctk.CTkButton(frame, text="Apply Changes", command=self.apply_changes)
        self.apply_button.pack(pady=20)

        # Power control
        power_frame = ctk.CTkFrame(frame)
        power_frame.pack(pady=20, fill="x")
        ctk.CTkLabel(power_frame, text="Power:", font=("Helvetica", 14)).pack(side="left", padx=(0, 10))
        self.power_var = ctk.BooleanVar(value=False)
        ctk.CTkSwitch(power_frame, text="On/Off", variable=self.power_var, command=self.toggle_power).pack(side="left", padx=10)

        # Status display
        self.status_var = ctk.StringVar(value="Motor Stopped")
        self.status_label = ctk.CTkLabel(frame, textvariable=self.status_var, font=("Helvetica", 12, "bold"))
        self.status_label.pack(pady=10)

        # Bind events
        self.speed_entry.bind("<Return>", lambda event: self.update_slider(self.speed_entry, self.speed_slider, "Motor speed"))

    def update_speed_entry(self, value):
        self.speed_var.set(f"{float(value):.1f}")

    def update_slider(self, entry, slider, control_name):
        try:
            value = float(entry.get())
            if 1 <= value <= 150:
                slider.set(value)
            else:
                self.show_error_message(f"{control_name} must be between 1 and 100.")
                entry.delete(0, ctk.END)
                entry.insert(0, str(slider.get()))
        except ValueError:
            self.show_error_message(f"Invalid input for {control_name}. Please enter a number between 1 and 100.")
            entry.delete(0, ctk.END)
            entry.insert(0, str(slider.get()))

    def show_error_message(self, message):
        CTkMessagebox(title="Error", message=message, icon="cancel")

    def apply_changes(self):
        rpm = float(self.speed_var.get())
        direction = self.direction_var.get()
        step_mode = self.step_mode_var.get()

        if step_mode == "Full":
            if direction == "CW":
                self.motor.rotate_full_step(rpm)
            else:
                self.motor.rotate_full_step_ccw(rpm)
        else:  # Half step
            if direction == "CW":
                self.motor.rotate_half_step(rpm)
            else:
                self.motor.rotate_half_step_ccw(rpm)

        self.update_status(rpm, direction, step_mode)

    def update_status(self, rpm, direction, step_mode):
        status = f"RPM: {rpm:.1f}, Direction: {direction}, Mode: {step_mode}"
        self.status_var.set(status)

    def toggle_power(self):
        if self.power_var.get():
            self.running = True
            self.motor_thread = threading.Thread(target=self.run_motor)
            self.motor_thread.start()
            self.status_var.set("Motor Running")
            self.apply_changes()  # Apply initial settings when turning on
        else:
            self.running = False
            if self.motor_thread:
                self.motor_thread.join()
            self.motor.stop()
            self.status_var.set("Motor Stopped")

    def run_motor(self):
        while self.running:
            # Motor continues to run with the last applied settings
            time.sleep(0.01)

if __name__ == "__main__":
    root = ctk.CTk()
    gui = WindmillGUI(root)
    root.mainloop()
