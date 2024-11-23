import customtkinter as ctk
from typing_extensions import Literal
import RPi.GPIO as GPIO
import tkinter.messagebox as messagebox
import random
import threading
import time
from NEMA17mod1 import Nema17  # Import the Nema17 class from the driver file
import multiprocessing

'''
this one is straight from perplexity so no guarantees!
good luck!
'''

def get_temp():
    return round(25 + 5 * random.random(), 2)

class WindmillGUI:
    def __init__(self, master):
        self.master = master
        master.title("Windmill Control")
        
        # Initialize the Nema17 motor
        self.motor = Nema17(A1_pin=17, A2_pin=18, B1_pin=27, B2_pin=22, sleep_pin=23)
        
        self.motor_settings = {
            'rpm': 10.0,
            'direction': 'CW',
            'step_mode': 'Full'
        }

        self.on = False  # Define 'on' here
      
        frame = ctk.CTkFrame(master, corner_radius=20)
        frame.pack(padx=30, pady=30, fill="both", expand=True)

        # Temperature label
        self.temp_label = ctk.CTkLabel(frame, text=f"Temperature: {get_temp()}", font=("Comic Sans MS", 18))
        self.temp_label.pack(pady=20)

        # Motor speed control
        speed_frame = ctk.CTkFrame(frame)
        speed_frame.pack(pady=20, fill="x")

        ctk.CTkLabel(speed_frame, text="Motor Speed (RPM):", font=("Helvetica", 14)).pack(side="left", padx=(0, 10))

        self.speed_var = ctk.StringVar(value="60.0")
        self.speed_entry = ctk.CTkEntry(speed_frame, textvariable=self.speed_var, width=50)
        self.speed_entry.pack(side="left", padx=(0, 10))

        # Update slider command to also update entry field
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
        self.power_switch = ctk.CTkSwitch(power_frame, text="Off/On", variable=self.power_var, command=self.toggle_power)
        self.power_switch.pack(side="left", padx=10)

        # Status display
        self.status_var = ctk.StringVar(value="Motor Stopped")
        self.status_label = ctk.CTkLabel(frame, textvariable=self.status_var, font=("Helvetica", 12, "bold"))
        self.status_label.pack(pady=10)

    def update_speed_entry(self,value):
       try:
           value=float(value) 
           if value <= 150 and value >= 1:
               self.speed_slider.set(value) 
               self.speed_var.set(f"{value:.2f}")  # Update entry field with the slider value
           else:
               raise ValueError("Invalid input")
       except ValueError:
           messagebox.showerror("Error","Please enter a valid number between (1-150)")

    def show_error_message(self,message):
       messagebox.showerror("Error" , message)

    def apply_changes(self):
        if not self.power_var.get():
           self.show_error_message("Turn on the power to apply changes.")
           return

        try:
            rpm = float(self.speed_var.get())
            direction = self.direction_var.get()
            step_mode = self.step_mode_var.get()
            
            if rpm < 1 or rpm > 150:
                raise ValueError("RPM must be between 1-150")
            
            with threading.Lock():
                print('Applying changes...')
                self.motor_settings['rpm'] = rpm
                self.motor_settings['direction'] = direction
                self.motor_settings['step_mode'] = step_mode
                
            if hasattr(self, 'motor_process') and self.motor_process.is_alive():
                self.motor_process.terminate()  # Terminate previous motor process
            
            self.motor.sleep()
            print("Motor sleeping...")
            self.start_motor()
        
            status = f"RPM: {rpm:.2f}, Direction: {direction}, Mode: {step_mode}"
            messagebox.showinfo("Success", status)
            
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def toggle_power(self):
        self.on = self.power_var.get()  # Update 'on' based on switch state
        if self.on:
            print('Motor ON')
            self.start_motor()
            self.status_var.set("Motor Running")
        else:
            print('Motor OFF')
            if hasattr(self, 'motor_process') and self.motor_process.is_alive():
                self.motor_process.terminate()  # Ensure motor process is terminated
                print("Motor process terminated.")
            self.motor.sleep()
            self.status_var.set("Motor Stopped")

    def start_motor(self):
        print('Starting motor...')
        
        # Start motor in a separate process
        if not hasattr(self, 'motor_process') or not self.motor_process.is_alive():
            self.motor_process = multiprocessing.Process(target=self.run_motor)
            self.motor_process.start()

    def run_motor(self):
        rpm = self.motor_settings['rpm']
        direction = self.motor_settings['direction']
        
        print(f"Running motor at {rpm} RPM in {direction} direction.")
        
        while self.on:  
            if direction == "CW":
                if self.motor_settings['step_mode'] == "Full":
                    self.motor.rotate_full_step(rpm)
                else:
                    self.motor.rotate_half_step(rpm)
            else:  
                if self.motor_settings['step_mode'] == "Full":
                    self.motor.rotate_full_step_ccw(rpm)
                else:
                    self.motor.rotate_half_step_ccw(rpm)


if __name__ == "__main__":
    try:
        GPIO.setmode(GPIO.BCM)  # Set GPIO mode (BCM or BOARD)
        
        root = ctk.CTk()
        gui = WindmillGUI(root)
        root.mainloop()
       
    except KeyboardInterrupt:
       print('Exiting program')
       
    finally:
       GPIO.cleanup()  # Clean up GPIO on exit
