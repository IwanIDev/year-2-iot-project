import sys
import os

sys.path.append(os.path.abspath("."))

import threading
from modes.detect_state import detect_mode, feedback_monitor
from modes.main_state import button_monitor, intitial_display
import grovepi
import config
import atexit
import signal
import sys
from picamera2 import Picamera2

# Camera

# Initialise the pi camera
picam2 = Picamera2()
picam2.configure(picam2.create_still_configuration())

# Helper functions to ensure that the camera is stopped on program closure

# If not handled correctly the camera will not initialise when this script is run again

def cleanup_camera():
    try:
        picam2.stop()
    except Exception:
        pass
    try:
        picam2.close()
    except Exception:
        pass

atexit.register(cleanup_camera)

def handle_exit(signum, frame):
    cleanup_camera()
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

# Initialises the input/output modes for the sensors
grovepi.pinMode(config.pir, "INPUT")

grovepi.pinMode(config.button_led, "OUTPUT")
grovepi.digitalWrite(config.button_led, 0)

grovepi.pinMode(config.button, "INPUT")

# Creates the threads 

start_thread = threading.Thread(target=intitial_display) 
monitor_thread = threading.Thread(target=button_monitor)
detect_thread = threading.Thread(target=detect_mode, args=(picam2,))
feedback_thread = threading.Thread(target=feedback_monitor)

# Starts the threads
start_thread.start()
monitor_thread.start()
detect_thread.start()
feedback_thread.start()



