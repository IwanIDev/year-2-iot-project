import sys
import os

sys.path.append("/home/pi/Dexter/GrovePi/Software/Python")
sys.path.append(os.path.abspath("."))

import threading
from modes.detect_state import detect_mode
import grovepi
from grove_rgb_lcd import *  # For Grove RGB LCD
import time
import tensorflow as tf
from collections import Counter
import config


#Button Monitor

def button_monitor():


    while True:

        if config.start_screen_running:

            with config.i2c_lock:
                state = grovepi.digitalRead(config.button)
                
            
            if state == 0:
                config.start_screen_running = False
                config.detect_mode_running = True
        
            time.sleep(0.05)
        
        else: 
            time.sleep(0.05)

# Scroll helper function
def scroll_message_two_lines(message1, message2, delay=0.3):
    """Scroll text across LCD."""
    

    message1 = message1 + " " * 16
    message2 = message2 + " " * 16
    
    max_len = max(len(message1), len(message2))
    
    for i in range(max_len - 15):

        if not config.start_screen_running:
            break
        
        text = message1[i:i+16] + "\n" + message2[i:i+16]

        with config.i2c_lock:
            setText(text)
        
        time.sleep(delay)

def intitial_display():
    
    while True:
        if config.start_screen_running:

            message1 = f"Bins Taken: {config.collection_info.get("bins")}"
            message2 = f"Next Collection Date {config.collection_info.get("collection_date")}"

            #print("Start Running:" + str(config.start_screen_running))
            #print("Detect Mode Running:" + str(config.detect_mode_running))
            
            with config.i2c_lock:
                motion = grovepi.digitalRead(config.pir)
                
            if motion:
                # Motion detected mode (green)888

                with config.i2c_lock:
                    grovepi.digitalWrite(config.button_led, 0)  # Ensure LED off
                    setRGB(0, 255, 0)  # Green

                scroll_message_two_lines(message1, message2, delay)
                
                time.sleep(0.5)

            else:
                with config.i2c_lock:
                    grovepi.digitalWrite(config.button_led, 0)
                    setText("")
                    setRGB(0,0,0)
                
                time.sleep(0.2)
        else:
            time.sleep(0.1)
   








            
            
        
      