import sys

sys.path.append("/home/pi/Dexter/GrovePi/Software/Python")

import grovepi

#if on d3 led is pin 3 and button is 4

button_led = 4  # LED Button on D3

grovepi.pinMode(button_led, "INPUT")


while True:

    print(grovepi.digitalRead(button_led))

