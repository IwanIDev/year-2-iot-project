import time
import grovepi
from grove_rgb_lcd import *  # For Grove RGB LCD
import config

def scroll_message_two_lines(message1, message2, delay=0.3):
    """Scroll text across LCD."""
    

    message1 = message1 + " " * 16
    message2 = message2 + " " * 16
    
    max_len = max(len(message1), len(message2))
    
    for i in range(max_len - 15):
        
        text = message1[i:i+16] + "\n" + message2[i:i+16]

        with config.i2c_lock:
            setText(text)
        
        time.sleep(delay)