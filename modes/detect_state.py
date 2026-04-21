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
import json
import lcd_helper


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

def feedback_monitor():
    
    count = 0
    
    while True:
        
        if config.feedback_monitor_on:

            with config.i2c_lock:
                state = grovepi.digitalRead(config.button)

            if state == 0:
                    
                count += 1

            print(count)

            if count >= 2:
                
                config.item_flagged = True
                config.feedback_monitor_on = False
                count = 0

        else:
            time.sleep(0.01)   

def feedback_message(class_name, score):
    
    setRGB(255,155,0)
    lcd_helper.scroll_message_two_lines(f"User flagged as incorrect", f"Logging Data - Score: {score:.2f}")
    return


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
    
    class_ids = [class_id for class_id, _ in preds]
    most_common_class = Counter(class_ids).most_common(1)[0][0]
    
    scores_for_class = [score for class_id, score in preds if class_id == most_common_class]
    avg_score = sum(scores_for_class) / len(scores_for_class)
    
    return most_common_class, avg_score

def send_to_thingsboard(data):
    config.client.publish("v1/devices/me/telemetry", json.dumps(data), qos=1)

#MAIN LOOP

def detect_waste(picam2):


    light_val = grovepi.analogRead(config.light_sens)
    print(light_val)

    while light_val <= 150:

        with config.i2c_lock:
            setRGB(255,0,0)
            setText("Warning!\nLight too low!")
        
        time.sleep(0.5)

        light_val = grovepi.analogRead(config.light_sens)

    time.sleep(1)
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
            preds.append((class_id, score))
        else:
            print("NONE FOUND")
        
    if not preds:
        time.sleep(1)
        setText("No Predictions")
        print("No Predictions")	
        return
                
    final_class, avg_score = majority_vote(preds)

    class_name = CLASSES[final_class]

    config.feedback_monitor_on = True

    if avg_score < 0.75:
         
        with config.i2c_lock:
            setRGB(255,165,0)
            setText(f"Caution\nConfidence Low")
            
        time.sleep(1)
        
        with config.i2c_lock:
            setText(f"Detected:\n{class_name}")

        time.sleep(4)

        if config.item_flagged:
             
            feedback_message(class_name, avg_score)

            del images
            del preds

            config.feedback_monitor_on = False
            config.item_flagged = False

            return
        

        data = {"waste_type": class_name}

        send_to_thingsboard(data)

        del images
        del preds

        config.feedback_monitor_on = False
            
        
    elif avg_score < 0.5:
         
        with config.i2c_lock:
            setRGB(255,0,0)
            lcd_helper.scroll_message_two_lines("Warning! Confidence very low.", "Please read packaging for further guidance or place item in your general waste bin.")
            
        time.sleep(0.5)
        
        data = {"waste_type": "GENERAL WASTE"}

        del images
        del preds

        config.feedback_monitor_on = False

        time.sleep(5)
         
    else:    
        print(f"Final: {class_name} with average score {avg_score:.2f}")

        with config.i2c_lock:
            setRGB(0,255,0)
            setText(f"Detected:\n{class_name}")

        time.sleep(5)

        if config.item_flagged:
                 
            feedback_message(class_name, avg_score)

            del images
            del preds

            config.feedback_monitor_on = False
            config.item_flagged = False

            return

        data = {"waste_type": class_name}

        send_to_thingsboard(data)

        del images
        del preds

        config.feedback_monitor_on = False

		
        
def detect_mode(picam2):

    while True:
        if config.detect_mode_running:
            print("Start Running:" + str(config.start_screen_running))
            print("Detect Mode Running:" + str(config.detect_mode_running))

            picam2.start()

            # Display "Press button to start"
            with config.i2c_lock:
                
                grovepi.digitalWrite(config.button_led, 1)  # Turn LED on
                
                setRGB(0, 0, 255)  # Blue
                setText("     DETECT     ")
                time.sleep(3)
                setText("Ready!\nPress Button")

            timeout = time.time()

            # Wait for the next button press
            while grovepi.digitalRead(config.button) == 1:

                if time.time() - timeout > 10:
                    with config.i2c_lock:
                        setRGB(255,255,0)
                        setText("Exiting\nDetect Mode")
                        time.sleep(3)
                    picam2.stop()
                    config.detect_mode_running = False
                    config.start_screen_running = True
                    break
                
                time.sleep(0.05)

            # Start inference loop with 15-second timeout
            last_button_press = time.time()
            
            while True:
                button_state = grovepi.digitalRead(config.button)
                if button_state == 0:
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