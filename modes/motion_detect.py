import grovepi
from grove_rgb_lcd import *  # For Grove RGB LCD
import time

# ----- Setup -----
pir = 2          # Motion sensor on D2
button_led = 3   # LED Button on D3

grovepi.pinMode(pir, "INPUT")
grovepi.pinMode(button_led, "INPUT")
grovepi.pinMode(button_led, "OUTPUT")  # For LED control

# Fake collection info
collection_type = ["General Waste", "Red Bag", "Blue Bag"]
collection_date = "01/04/2026"

# Scroll helper function
def scroll_message(message, color, delay=0.3):
    """Scroll text across LCD."""
    setRGB(*color)
    for i in range(len(message) - 16 + 1):
        setText(message[i:i+16])
        time.sleep(delay)

# ----- Main Loop -----
led_on = False

while True:
    try:
        motion = grovepi.digitalRead(pir)
        button_pressed = grovepi.digitalRead(button_led)
        
        if motion and not button_pressed:
            # Motion detected mode (green)
            grovepi.digitalWrite(button_led, 0)  # Ensure LED off
            led_on = False
            setRGB(0, 255, 0)  # Green
            message = f"Collection Date: {collection_date}\nBins: {', '.join(collection_type)}"
            
            # Scroll if message too long
            if len(message) > 16:
                scroll_message(message.replace("\n", " "), (0,255,0))
            else:
                setText(message)
            time.sleep(0.5)

        elif button_pressed:
            # Button pressed mode (blue)
            grovepi.digitalWrite(button_led, 1)  # Turn LED on
            led_on = True
            setRGB(0, 0, 255)  # Blue
            message = "DETECT"
            setText(message)
            time.sleep(0.5)

        else:
            # No motion, button not pressed → clear
            grovepi.digitalWrite(button_led, 0)
            led_on = False
            setText("")
            setRGB(0,0,0)
            time.sleep(0.2)

    except IOError:
        print("Error reading sensor")