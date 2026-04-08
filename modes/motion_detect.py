import sys
import os

sys.path.append("/home/pi/Dexter/GrovePi/Software/Python")
sys.path.append(os.path.abspath("."))

import threading
from classifier.cameratest import detect_waste
import grovepi
from grove_rgb_lcd import *  # For Grove RGB LCD
import time

button_pressed_flag = False
start_screen_running = True
detect_mode_running = False

i2c_lock = threading.RLock()

# ----- Setup -----
pir = 2          # Motion sensor on D2
button_led = 3   # LED Button on D3


grovepi.pinMode(pir, "INPUT")
grovepi.pinMode(button_led, "INPUT")


grovepi.digitalWrite(button_led, 0)

# Fake collection info
collection_type = "General Waste, Red Bag, Blue Bag"
collection_date = "01/04/2026"



#Button Monitor

def button_monitor():
    
    global start_screen_running, detect_mode_running

    while True:

        with i2c_lock:
            state = grovepi.digitalRead(button_led)

        if state == 1:
            start_screen_running = False
            detect_mode_running = True
        
        time.sleep(0.05)


# Scroll helper function
def scroll_message_two_lines(message1, message2, delay=0.3):
    """Scroll text across LCD."""
    
    global start_screen_running, detect_mode_running

    message1 = message1 + " " * 16
    message2 = message2 + " " * 16
    
    max_len = max(len(message1), len(message2))
    
    for i in range(max_len - 15):

        if not start_screen_running:
            break
        
        text = message1[i:i+16] + "\n" + message2[i:i+16]

        with i2c_lock:
            setText(text)
        
        time.sleep(delay)

def intitial_display(message1, message2, delay):
    
    global start_screen_running, detect_mode_running
    
    while True:
        if start_screen_running:
            with i2c_lock:
                motion = grovepi.digitalRead(pir)
                
            if motion:
                # Motion detected mode (green)888

                with i2c_lock:
                    grovepi.digitalWrite(button_led, 0)  # Ensure LED off
                    setRGB(0, 255, 0)  # Green

                scroll_message_two_lines(message1, message2, delay)
                
                time.sleep(0.5)

            else:
                with i2c_lock:
                    grovepi.digitalWrite(button_led, 0)
                    setText("")
                    setRGB(0,0,0)
                
                time.sleep(0.2)
        else:
            time.sleep(0.1)
   

def detect_mode():
    
    global start_screen_running, detect_mode_running

    while True:
        
        if detect_mode_running:
            with i2c_lock:
                motion = grovepi.digitalRead(pir)
                grovepi.digitalWrite(button_led, 1)  # Turn LED on
                
                setRGB(0, 0, 255)  # Blue
                message = "     DETECT     "
                setText(message)
            
            time.sleep(3)
            
            with i2c_lock:
                motion = grovepi.digitalRead(pir)

            if motion == 0:
                detect_mode_running = False
                start_screen_running = True
        
        else:
            with i2c_lock:
                detect_waste()
            detect_mode_running = False
            start_screen_running = True



start_thread = threading.Thread(target=intitial_display, args=(f"Next Collection Date {collection_date}", f"Bins Taken: {collection_type}", 0.3)) 
monitor_thread = threading.Thread(target=button_monitor)
detect_thread = threading.Thread(target=detect_mode)

start_thread.start()
monitor_thread.start()
detect_thread.start()



            
            
        
      