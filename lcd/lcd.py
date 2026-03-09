#!/usr/bin/env python3
"""
LCD display module.
Model predictions are received via STDIN and displayed on the LCD screen.
Colours are also used to indicate the type of waste detected.
Written by Iwan Ingman, 2026-03-09
"""

import time

import smbus
import RPi.GPIO as GPIO
rev = GPIO.RPI_REVISION
if rev == 2 or rev == 3:
    bus = smbus.SMBus(1)
else:
    bus = smbus.SMBus(0)

DISPLAY_RGB_ADDR = 0x62 # RGB display address
DISPLAY_TEXT_ADDR = 0x3e # Text display address

WASTE_TYPES = {
    "CARDBOARD/PAPER": (255, 255, 255),  # White
    "GLASS": (0, 255, 255),  # Cyan
    "METAL": (128, 128, 128),  # Gray
    "PLASTIC FILM": (255, 0, 255),  # Magenta
    "PLASTIC BOTTLE": (0, 255, 0),  # Green
    "FOOD WASTE": (255, 165, 0)  # Orange
}

def textCommand(cmd: int) -> None:
    """
    Send a command byte to the LCD text display.
    cmd: The command byte to send
    """
    bus.write_byte_data(DISPLAY_TEXT_ADDR,0x80,cmd)

def setText(text: str) -> None:
    """
    Set the text to be displayed on the LCD screen. Supports up to 2 lines of 16 characters each.
    text: The string to display, with optional newline character to separate lines.
    """
    textCommand(0x01) # clear display
    time.sleep(.05)
    textCommand(0x08 | 0x04) # display on, no cursor
    textCommand(0x28) # 2 lines
    time.sleep(.05)
    count = 0
    row = 0
    for c in text:
        if c == '\n' or count == 16:
            count = 0
            row += 1
            if row == 2:
                break
            textCommand(0xc0)
            if c == '\n':
                continue
        count += 1
        bus.write_byte_data(DISPLAY_TEXT_ADDR,0x40,ord(c))
 

def setRGB(r: int, g: int, b: int) -> None:
    """
    Set the backlight colour of the LCD display.
    r, g, b: 0-255 values for red, green, blue components
    """
    bus.write_byte_data(DISPLAY_RGB_ADDR,0,0)
    bus.write_byte_data(DISPLAY_RGB_ADDR,1,0)
    bus.write_byte_data(DISPLAY_RGB_ADDR,0x08,0xaa)
    bus.write_byte_data(DISPLAY_RGB_ADDR,4,r)
    bus.write_byte_data(DISPLAY_RGB_ADDR,3,g)
    bus.write_byte_data(DISPLAY_RGB_ADDR,2,b)

def main():
    prediction = ""
    while True:
        try:
            prediction = prediction + input()
            print(f"Received prediction: {prediction}")
            line = prediction.strip()
            if line in WASTE_TYPES:
                setText(line)
                r, g, b = WASTE_TYPES[line]
                setRGB(r, g, b)
            else:
                setText("UNKNOWN\n" + line[:16])
                setRGB(255, 0, 0) # Red for unknown
            prediction = ""
        except EOFError:
            break

if __name__ == "__main__":
    main()