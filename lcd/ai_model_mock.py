#!/usr/bin/env python3
"""
Script to produce mock AI model output for testing the LCD display without needing to run the actual AI model.
Written by Iwan Ingman, 2026-03-09
"""

import random
import time

TEST_LABELS = [
    "CARDBOARD/PAPER",
    "GLASS",
    "METAL",
    "PLASTIC FILM",
    "PLASTIC BOTTLE",
    "FOOD WASTE"
]

def main():
    while True:
        label = random.choice(TEST_LABELS)
        print(label)
        time.sleep(5)

if __name__ == "__main__":
    main()