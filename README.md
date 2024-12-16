# SolarZaan: SunFlow
PHYS351 Final Project Fall 2024
Jacob Herz, Josh Levin, Julia Rodrigues

- Fully functional model "windmill" with LEDs, stepper motor, USB speaker, solar charging circuit, and temperature sensor. All drivers are included here. Interface with a GUI through a Raspberry Pi 4.
- Tested on Raspberry Pi 4 running Python 3.7.3
- no external dependencies besides libraries to install as listed below

**Installation and Setup Instructions**

Upon first time Raspberry Pi setup run this line in the terminal:
pip3 install customtkinter RPi.GPIO math numpy smbus2 pygame

**wiring**
*Stepper motor driver into RPi*
GPIO setup:
A1 out --> GPIO 17
A2 out --> GPIO 18
B1 out --> GPIO 27
B2 out --> GPIO 22
SLP --> GPIO 23

*smbus lines*
SDA --> GPIO 2
SCL --> GPIO 3

Ground rail from white breakout board --> RPI GND

**Usage**
- Download all files from the 'Final Working Files' folder onto the RPi
- save each file individually
- connect the RPi to a shared wifi network
- establish remote connection to the RPi using RealVNCViewer
- run 'GUI_test_v7.6.py' to start the GUI


**Troubleshooting**
- run each mod file individually to test components
- ensure path directories are correct for mp3 files

