import sys
import os



sys.path.append(os.path.abspath("."))

import threading
from modes.detect_state import detect_mode
from modes.main_state import button_monitor, intitial_display
import grovepi
import config
import atexit
import signal
import sys
from picamera2 import Picamera2

# Camera
picam2 = Picamera2()
picam2.configure(picam2.create_still_configuration())

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


grovepi.pinMode(config.pir, "INPUT")

grovepi.pinMode(config.button_led, "OUTPUT")
grovepi.digitalWrite(config.button_led, 0)

grovepi.pinMode(config.button_led, "INPUT")


start_thread = threading.Thread(target=intitial_display, args=(f"Next Collection Date {config.collection_date}", f"Bins Taken: {config.collection_type}", 0.3)) 
monitor_thread = threading.Thread(target=button_monitor)
detect_thread = threading.Thread(target=detect_mode, args=(picam2,))

start_thread.start()
monitor_thread.start()
detect_thread.start()



