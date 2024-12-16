import customtkinter as ctk
#import RPi.GPIO as GPIO
import tkinter.messagebox as messagebox
import threading
import time
#from NEMA17mod2 import Nema17  # Import the Nema17 class from the driver file
#from MockMod import MockNema17 as Nema17
#from MockMod import DummyMCP9808 as MCP9808
#from MCP9808mod5 import MCP9808
import multiprocessing
#from PCA9685mod2 import PCA9685Controller #, LEDShow #LED, RGBLED?
from dummyPCA import DummyPCA9685Controller as PCA9685Controller
from musicmod import MusicPlayer
import queue



'''
Version 7.4 updates
- dummy classes


GPIO setup:
A1 in --> GPIO 17
A2 in --> GPIO 18
B1 in --> GPIO 27
B2 in --> GPIO 22
SLP --> GPIO 23
tie grounds
'''

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


# define processes here, not inside GUI to prevent lockup

def temperature_monitor(queue):
    temp_sensor = DummyMCP9808()
    while True:
        try:
            temperature = temp_sensor.threebit_read_temperature()
            queue.put(temperature)
            time.sleep(2)
        except Exception as e:
            print(f"Error reading temperature: {e}")
            time.sleep(1)

def music_control_process(queue):
    try:
        player = MusicPlayer()
        while True:
            command = queue.get()
            if command == "EXIT":
                player.stop()
                player.cleanup()
                break
            elif command.startswith("LOAD:"):
                filename = command.split(":")[1]
                player.load_song(filename)
            elif command == "PLAY":
                player.play()
            elif command == "PAUSE":
                player.pause()
            elif command.startswith("VOLUME:"):
                volume = float(command.split(":")[1])
                player.set_volume(volume)
    except Exception as e:
        print(f"Error in music process: {e}")
    finally:
        player.cleanup()


def led_control_process(queue):
    controller = PCA9685Controller()
    led_show = controller.create_light_show()
    led_show.all_off()
    
    while True:
        command = queue.get()
        if command == "EXIT":
            led_show.all_off()
            break
        elif command == "MASTER_ON":
            led_show.all_on()
        elif command == "MASTER_OFF":
            led_show.all_off()
        elif command.startswith("SHOW:"):
            show_name = command.split(":")[1]
            led_show.run_light_show(show_name, duration=15)
            led_show.all_on()  # Return to all LEDs on after the show

class WindmillGUI:
    def __init__(self, master):
        self.master = master
        master.title("Windmill Control")
        
        # Initialize the Nema17 motor
        self.motor = MockNema17(A1_pin=17, A2_pin=18, B1_pin=27, B2_pin=22, sleep_pin=23)
        
        self.motor_settings = {
            'rpm': 10.0,
            'direction': 'CW',
            'step_mode': 'Full'
        }

        self.on = False  # Define 'on' here

        # initialize multiprocessing for temperature sensor
        self.temp_queue = multiprocessing.Queue()
        self.temp_process = multiprocessing.Process(target=temperature_monitor, args=(self.temp_queue,))
        self.temp_process.start()
        
        self.master.after(100, self.update_temperature) # update temperature from queue after 100ms
        
        # initialize multiprocessing for LED control
        self.led_queue = multiprocessing.Queue()
        self.led_process = multiprocessing.Process(target=led_control_process, args=(self.led_queue,))
        self.led_process.start()

        # initialize music stuff
        self.music_queue = multiprocessing.Queue()
        self.music_process = multiprocessing.Process(target=music_control_process, args=(self.music_queue,))
        self.music_process.start()


        # Bind the closing event
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

        frame = ctk.CTkFrame(master, corner_radius=20)
        frame.pack(padx=30, pady=30, fill="both", expand=True)

        # Temperature label
        self.temp_label = ctk.CTkLabel(frame, text=f"Temperature: None", font=("Helvetica", 24))
        self.temp_label.pack(pady=20)

        # Motor speed control
        speed_frame = ctk.CTkFrame(frame)
        speed_frame.pack(pady=20, fill="x")

        ctk.CTkLabel(speed_frame, text="Motor Speed (RPM):", font=("Helvetica", 14)).pack(side="left", padx=(0, 10))

        self.speed_var = ctk.StringVar(value="10.0")
        self.speed_entry = ctk.CTkEntry(speed_frame, textvariable=self.speed_var, width=50)
        self.speed_entry.pack(side="left", padx=(0, 10))

        # Update slider command to also update entry field
        self.speed_slider = ctk.CTkSlider(speed_frame, from_=1, to=100, command=self.update_speed_entry)
        self.speed_slider.pack(side="left", padx=(0, 10), expand=True)

        # Direction control
        direction_frame = ctk.CTkFrame(frame)
        direction_frame.pack(pady=20, fill="x")

        ctk.CTkLabel(direction_frame, text="Direction:", font=("Helvetica", 18)).pack(side="left", padx=(0, 10))

        self.direction_var = ctk.StringVar(value="CW")
        ctk.CTkRadioButton(direction_frame, text="CW", variable=self.direction_var, value="CW").pack(side="left", padx=10)
        ctk.CTkRadioButton(direction_frame, text="CCW", variable=self.direction_var, value="CCW").pack(side="left", padx=10)

        # Step mode control
        step_mode_frame = ctk.CTkFrame(frame)
        step_mode_frame.pack(pady=20, fill="x")

        ctk.CTkLabel(step_mode_frame, text="Step Mode:", font=("Helvetica", 18)).pack(side="left", padx=(0, 10))

        self.step_mode_var = ctk.StringVar(value="Full")
        ctk.CTkRadioButton(step_mode_frame, text="Full", variable=self.step_mode_var, value="Full").pack(side="left", padx=10)
        ctk.CTkRadioButton(step_mode_frame, text="Half", variable=self.step_mode_var, value="Half").pack(side="left", padx=10)

        # Apply Changes button
        self.apply_button = ctk.CTkButton(frame, text="Apply Motor Changes", command=self.apply_changes)
        self.apply_button.pack(pady=20)

        # Power control
        power_frame = ctk.CTkFrame(frame)
        power_frame.pack(pady=20, fill="x")

        ctk.CTkLabel(power_frame, text="Motor Power:", font=("Helvetica", 18)).pack(side="left", padx=(0, 10))

        self.power_var = ctk.BooleanVar(value=False)
        self.power_switch = ctk.CTkSwitch(power_frame, text="Off/On", variable=self.power_var, command=self.toggle_power)
        self.power_switch.pack(side="left", padx=10)


        # Master LED control

        # LED frame
        led_frame = ctk.CTkFrame(frame)
        led_frame.pack(pady=20, fill="x")
        
        ctk.CTkLabel(led_frame, text="LED Control:", font=("Helvetica", 18)).pack(side="left", padx=(0, 10))
        self.led_master_var = ctk.BooleanVar(value=False)
        self.led_master_switch = ctk.CTkSwitch(led_frame, text="All LEDs Off/On", variable=self.led_master_var, command=self.toggle_led_master)
        self.led_master_switch.pack(side="left", padx=10)
        
        # LED show selection
        self.led_show_options = ["all On", "blade chase", "rgb Fade", "moss Twinkle", "moss Breathe"]
        self.led_show_var = ctk.StringVar(value=self.led_show_options[0])
        self.led_show_dropdown = ctk.CTkOptionMenu(
            led_frame,
            values=self.led_show_options,
            variable=self.led_show_var,
            command=self.start_led_show
        )
        self.led_show_dropdown.pack(side="left", padx=10)

        # Safety Mode control
        safety_frame = ctk.CTkFrame(frame)
        safety_frame.pack(pady=20, fill="x")
        ctk.CTkLabel(safety_frame, text="Safety Mode:", font=("Helvetica", 14)).pack(side="left", padx=(0, 10))
        self.safety_mode = ctk.BooleanVar(value=True)  # Default to safety on
        ctk.CTkRadioButton(safety_frame, text="On", variable=self.safety_mode, value=True).pack(side="left", padx=10)
        ctk.CTkRadioButton(safety_frame, text="Off", variable=self.safety_mode, value=False).pack(side="left", padx=10)

        # Music Control Section
        music_frame = ctk.CTkFrame(frame)
        music_frame.pack(pady=20, fill="x")
        ctk.CTkLabel(music_frame, text="Music Control:", font=("Helvetica", 14)).pack(side="left", padx=(0, 10))

        # Song Selection Dropdown
        self.song_options = ["dutchmusic", "walkingonsunshine", "kahoot", "soak_up_the_sun", "Ik_Hou_Van_Holland", "you_are_my_sunshine"]
        self.song_var = ctk.StringVar(value=self.song_options[0])
        self.song_dropdown = ctk.CTkOptionMenu(
            music_frame, 
            values=self.song_options,
            variable=self.song_var,
            command=self.song_selected
        )
        self.song_dropdown.pack(side="left", padx=5)

        # Play/Pause and Stop Buttons
        self.music_is_playing = False  # Track playing state
        self.play_pause_button = ctk.CTkButton(
            music_frame, 
            text="Play", 
            command=self.toggle_play_pause
        )
        self.play_pause_button.pack(side="left", padx=5)

        self.stop_music_button = ctk.CTkButton(
            music_frame, 
            text="Stop", 
            command=self.stop_music
        )
        self.stop_music_button.pack(side="left", padx=5)        


        ctk.CTkLabel(music_frame, text="Music Volume:", font=("Helvetica", 14)).pack(side="left", padx=(0, 10))

        # Volume Slider
        self.volume_slider = ctk.CTkSlider(
            music_frame, 
            from_=0, 
            to=1, 
            command=self.change_volume
        )
        self.volume_slider.set(1.0)
        self.volume_slider.pack(side="left", padx=10, expand=True)

        # Music status
        self.music_status_var = ctk.StringVar(value="No song playing")
        self.music_status = ctk.CTkLabel(
            music_frame, 
            textvariable=self.music_status_var, 
            font=("Helvetica", 12)
        )
        self.music_status.pack(side="left", padx=10)

        # Motor Status display
        self.status_var = ctk.StringVar(value="Motor Stopped")
        self.status_label = ctk.CTkLabel(frame, textvariable=self.status_var, font=("Helvetica", 12, "bold"))
        self.status_label.pack(pady=10)

    ##########################################################
    '''begin class methods/functions to use within the GUI'''
    ##########################################################

    # Music Methods
    def toggle_play_pause(self):
        if not self.music_is_playing:  # Changed from is_playing to music_is_playing
            self.music_queue.put("PLAY")
            self.play_pause_button.configure(text="Pause")
            self.music_is_playing = True
            self.music_status_var.set(f"Playing: {self.song_var.get()}")
        else:
            self.music_queue.put("PAUSE")
            self.play_pause_button.configure(text="Play")
            self.music_is_playing = False
            self.music_status_var.set("Paused")

    def stop_music(self):
        try:
            while True:
                self.music_queue.get_nowait()
        except:
            pass
        self.music_queue.put("STOP")
        self.play_pause_button.configure(text="Play")
        self.is_playing = False
        self.music_status_var.set("No song playing")

    def song_selected(self, choice):
        self.music_queue.put(f"LOAD:{choice}.mp3")
        if self.is_playing:
            self.music_status_var.set(f"Playing: {choice}")

    def play_music(self):
        self.music_queue.put("PLAY")
        
    def pause_music(self):
        self.music_queue.put("PAUSE")
        
    def change_volume(self, value):
        self.music_queue.put(f"VOLUME:{value}")

    # LED methods
    def toggle_led_master(self):
        if self.led_master_var.get():
            self.led_queue.put("MASTER_ON")
        else:
            self.led_queue.put("MASTER_OFF")

    def start_led_show(self, choice):
        self.led_queue.put(f"SHOW:{choice}")


    # Motor control methods
    def update_speed_entry(self,value):
       try:
           value=float(value) 
           if value <= 100 and value >= 1:
               self.speed_slider.set(value) 
               self.speed_var.set(f"{value:.2f}")  # Update entry field with the slider value
           else:
               raise ValueError("Invalid input")
       except ValueError:
           messagebox.showerror("Error","Please enter a valid number between (1-100)")

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
            
            if rpm < 1 or rpm > 100:
                raise ValueError("RPM must be between 1-100")
            
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
            #messagebox.showinfo("Success", status) # do you still need to double click to apply changes?
            print(f'starting motor {status}')
            
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    # toggle motor power
    def toggle_power(self):
        '''
        toggle power binds to the power switch for motor. if on, the motor will start using the updated data,
        this means if you turn on the motor without clicking 'apply changes', the motor will not have updated
        status information like rpm, direction, and step size
        '''


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
            self.motor.sleep_main_motor()
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
        
        self.motor.wake()
        print('motor awake. All pins set to 0, sleep on HIGH')

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
    
    def sleep_main_motor(self):
        '''
        separate, more fancy than the NEMA17mod sleep function
        checks if there is a motor attribute at all before going to town
        '''
        if hasattr(self, 'motor'):
            self.motor.sleep()
            print("Motor sleeping and all motor pins set to OFF...")

    # Temperature MCP9808 methods
    def update_temperature(self):
        try:
            temperature = self.temp_queue.get_nowait()
            self.temp_label.configure(text=f"Temperature: {temperature:.2f}°C")
            
            # Check temperature safety
            if temperature > 32.0:
                self.raise_temperature_flag(temperature)
                
        except queue.Empty:
            pass
        finally:
            self.master.after(100, self.update_temperature)

    def raise_temperature_flag(self, temperature):
        if self.safety_mode.get():
            self.show_emergency_dialog(f"EMERGENCY: Temperature Critical!\nCurrent: {temperature:.1f}°C\nThreshold: 32.0°C")
        else:
            messagebox.showwarning("Temperature Warning", 
                "Temperature exceeds safety threshold!\nPlease consider closing the application.")

    def show_emergency_dialog(self, message):
        dialog = ctk.CTkToplevel(self.master)
        dialog.title("Emergency Stop")
        dialog.geometry("400x300")
        dialog.transient(self.master)
        dialog.grab_set()
        
        countdown_var = ctk.StringVar(value="10")
        
        ctk.CTkLabel(dialog, text=message, 
                    font=("Helvetica", 14, "bold"), 
                    text_color="red").pack(pady=20)
        
        countdown_label = ctk.CTkLabel(dialog, 
                                    textvariable=countdown_var,
                                    font=("Helvetica", 24, "bold"),
                                    text_color="red")
        countdown_label.pack(pady=10)
        
        def countdown(seconds):
            if seconds > 0 and dialog.winfo_exists():
                countdown_var.set(str(seconds))
                dialog.after(1000, lambda: countdown(seconds - 1))
            elif seconds == 0 and dialog.winfo_exists():
                dialog.destroy()
                self.emergency_shutdown()
        
        def override():
            self.safety_mode.set(False)
            dialog.destroy()
        
        # Add the override button
        ctk.CTkButton(dialog, 
                    text="Override Safety",
                    command=override,
                    fg_color="orange",
                    hover_color="dark orange").pack(pady=10)
        
        # Start countdown
        countdown(15)

    def emergency_shutdown(self):
        try:
            # Stop motor
            if hasattr(self, 'motor_process') and self.motor_process.is_alive():
                self.motor_process.terminate()
            self.motor.sleep_main_motor()
            
            # Stop music and clear queue
            try:
                while True:
                    self.music_queue.get_nowait()
            except queue.Empty:
                pass
            self.music_queue.put("STOP")
            self.play_pause_button.configure(text="Play")
            self.music_is_playing = False
            
            # Turn off LEDs
            self.led_queue.put("LED:0")
            self.led_var.set(False)
            
            # Update GUI state
            self.power_var.set(False)
            self.status_var.set("Emergency Stop Activated")
            
            # Close GUI
            self.on_closing()
        except Exception as e:
            print(f"Error during emergency shutdown: {e}")
            self.master.destroy()


    # big methods for closing GUI
    def on_closingOLD(self):
        '''
        Function to kill the GUI and sleep the GPIO pins
        you should not hear any ringing from the motor after you close the window --
        this means the motor is completely off and receiving no power if it is silent
        '''
        print('begin closing protocol...')
        if hasattr(self, 'temp_process') and self.temp_process.is_alive():
            self.temp_process.terminate()
        
        if hasattr(self, 'motor_process') and self.motor_process.is_alive():
            print('detected motor process running...')
            self.motor_process.terminate()
            print('terminated motor process.')
        self.sleep_main_motor()
        print('all motor pins off.')
        self.led_queue.put("EXIT")
        self.led_process.join()
        self.master.destroy()
        print('destroyed master')

    # newer method to kill GUI
    def on_closing(self):
        '''
        Function to kill the GUI and sleep the GPIO pins
        you should not hear any ringing from the motor after you close the window --
        this means the motor is completely off and receiving no power if it is silent
        '''

        try:
            if hasattr(self, 'motor_process') and self.motor_process.is_alive():
                self.motor_process.terminate()
            
            if self.running:
                self.running = False
                if self.motor_thread:
                    self.motor_thread.join()
            
            self.sleep_main_motor()
            print('all motor pins off.')
            # Add music cleanup
            self.music_queue.put("EXIT")
            self.music_process.join()
            
            self.led_queue.put("EXIT")
            self.led_process.join()
            self.master.quit()
        except Exception as e:
            print(f"Error during closing: {e}")
        finally:
            try:
                self.master.destroy()
            except:
                pass


if __name__ == "__main__":
    try:
        #GPIO.setwarnings(False)
        #GPIO.setmode(GPIO.BCM)  # Set GPIO mode (BCM or BOARD)
        #GPIO.cleanup()
        #GPIO.setwarnings(True)
        root = ctk.CTk()
        gui = WindmillGUI(root)
        root.protocol("WM_DELETE_WINDOW", gui.on_closing)  # Bind the closing event
        root.mainloop()
    except KeyboardInterrupt:
        print('Exiting program')
    finally:
        print('Closed GUI')