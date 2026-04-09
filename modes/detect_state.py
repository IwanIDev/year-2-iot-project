import sys
import os

sys.path.append("/home/pi/Dexter/GrovePi/Software/Python")
sys.path.append(os.path.abspath("."))

import threading
import grovepi
from grove_rgb_lcd import *  # For Grove RGB LCD
import time
from picamera2 import Picamera2
import cv2
import numpy as np
import tensorflow as tf
from collections import Counter
import config


#Load Model

MODEL_PATH = "/home/pi/AI/iot-group-project/classifier/model.tflite"
IMG_SIZE = (224, 224)

CLASSES = ["CARDBOARD-PAPER", "FOOD", "GENERAL WASTE", "GLASS", "HARD PLASTIC", "METAL", "SOFT PLASTIC"]

CONF_THRESHOLD = 0.5

interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

input_index = input_details[0]["index"]
output_index = output_details[0]["index"]

input_dtype = input_details[0]["dtype"]

def capture_image(picam2):

    images = []
    for i in range(10):
        frame = picam2.capture_array()
        images.append(frame)
        time.sleep(0.1)

    return images
	
def pre_process(frame):
	
	if frame is None:
		return None
	
	frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
	
	frame = cv2.resize(frame, IMG_SIZE, interpolation=cv2.INTER_AREA)
	
	if input_dtype == np.float32:
		frame = frame.astype(np.float32)
	elif input_dtype == np.uint8:
		frame = frame.astype(np.uint8)
	else:
		frame = frame.astype(input_dtype)
		
	img = np.expand_dims(frame, axis=0)
	
	return img
	
	
#Runs inference on 1 image

def run_inference(img_tensor):

	input_tensor = pre_process(img_tensor)

	interpreter.set_tensor(input_index, input_tensor)

	interpreter.invoke()

	interpreter.get_tensor(output_index)[0]

	probs = interpreter.get_tensor(output_index)[0]

	probs = probs.astype(np.float32)

	pred_idx = int(np.argmax(probs))

	confidence = float(probs[pred_idx])

	return pred_idx, confidence
	
	

	
def majority_vote(preds):
	return Counter(preds).most_common(1)[0][0]



#MAIN LOOP

def detect_waste(picam2):


    light_val = grovepi.analogRead(config.light_sens)
    print(light_val)

    while light_val <= 40:

        with config.i2c_lock:
            setRGB(255,0,0)
            setText("Warning!\nLight too low!")
        
        time.sleep(0.5)

        light_val = grovepi.analogRead(config.light_sens)

    time.sleep(2)
    print("System ready. Running Inference")


    with config.i2c_lock:
        setRGB(255,165,0)
        setText("Capturing...")

        
    images = capture_image(picam2)

    print("Images captured")


    preds = []
    for img in images:
        print("Running Inference")
        
        class_id, score = run_inference(img)

        if class_id is not None:
            print(f"class = {class_id} ({CLASSES[class_id]}) score={score:.2f}")
            preds.append(class_id)
        else:
            print("NONE FOUND")
        
    if not preds:
        time.sleep(1)
        setText("No Predictions")
        print("No Predictions")	
        return
                
    final_class = majority_vote(preds)
        
    class_name = CLASSES[final_class]
        
    print("Final: ", class_name)

    with config.i2c_lock:
        setRGB(0,255,0)
        setText(f"Detected:\n{class_name}")

    del images
    del preds

    time.sleep(5)
		
        
def detect_mode(picam2):

    while True:
        if config.detect_mode_running:
            print("Start Running:" + str(config.start_screen_running))
            print("Detect Mode Running:" + str(config.detect_mode_running))

            picam2.start()

            # Display "Press button to start"
            with config.i2c_lock:
                grovepi.pinMode(config.button_led, "OUTPUT")
                grovepi.digitalWrite(config.button_led, 1)  # Turn LED on

                grovepi.pinMode(config.button_led, "INPUT")  # Set back to input to detect presses
                
                setRGB(0, 0, 255)  # Blue
                setText("     DETECT     ")
                time.sleep(3)
                setText("Ready!\nPress Button")

            # Wait for the next button press
            while grovepi.digitalRead(config.button_led) == 0:
                print(grovepi.digitalRead(config.button_led))
                time.sleep(0.05)

            # Start inference loop with 15-second timeout
            last_button_press = time.time()
            
            while True:
                button_state = grovepi.digitalRead(config.button_led)
                print(button_state)
                if button_state == 1:
                    last_button_press = time.time()
                    detect_waste(picam2)
                else:
                    with config.i2c_lock:
                        setRGB(0,0,255)
                        setText("Ready!\nPress Button")
                    if time.time() - last_button_press > 15:
                        break
                time.sleep(0.1)

            with config.i2c_lock:
                setRGB(255,255,0)
                setText("Exiting\nDetect Mode")
                time.sleep(3)
            picam2.stop()
            config.detect_mode_running = False
            config.start_screen_running = True
        else:
            time.sleep(0.1)