import sys
import os

sys.path.append("/home/pi/Dexter/GrovePi/Software/Python")
sys.path.append(os.path.abspath("."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'web-app'))

# Now import from bin_lookup
from bin_lookup.council_bins import wales_bins  # or specific imports
from bin_lookup.waste_to_bin import bin_waste

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



#Loads the tflite model

MODEL_PATH = "/home/pi/AI/iot-group-project/classifier/model.tflite"
IMG_SIZE = (224, 224)

# Initialises the classes the model was trained on
CLASSES = ["CARDBOARD-PAPER", "FOOD", "GENERAL WASTE", "GLASS", "HARD PLASTIC", "METAL", "SOFT PLASTIC"]

# Initialises the interpreter
interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)

# Allocates the memory for the input and output tensors
interpreter.allocate_tensors()

# Gets the expected input and output  the model was trained on
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Gets the indexes of where data must go and be retrived
input_index = input_details[0]["index"]
output_index = output_details[0]["index"]

# Gets the expected data type for the input
input_dtype = input_details[0]["dtype"]


# This is a monitor function that listens for 2 button presses after a prediction has been made
# so the user can flag it as incorrect

def feedback_monitor():
    
    count = 0
    
    while True:
        
        if config.feedback_monitor_on:

            with config.i2c_lock:
                state = grovepi.digitalRead(config.button)

            if state == 0:
                    
                count += 1


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

# Captures 10 images using the raspberry pi's camerea and appends them to a list
def capture_image(picam2):

    images = []
    for i in range(10):
        frame = picam2.capture_array()
        images.append(frame)
        time.sleep(0.1)

    return images

# This function applies the necessary pre_processing to each captured frame
def pre_process(frame):
	
	if frame is None:
		return None
	
    # Changes the image from BGR to RGB format
	frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
	
    # Resiszes the frames to 224x224 as that is what the model was trained on

	frame = cv2.resize(frame, IMG_SIZE, interpolation=cv2.INTER_AREA)
	
    # Sets the data type of the frame to that exoected of the model

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

    # Pre processes the image
	input_tensor = pre_process(img_tensor)

    # Feeds the processed image into the model
	interpreter.set_tensor(input_index, input_tensor)

    # Runs the models inference
	interpreter.invoke()

    # Gets the output array which contains the probabilities for each waste type

	probs = interpreter.get_tensor(output_index)[0]

    # Ensures the probabilties are in float 32 format
	probs = probs.astype(np.float32)

    # Gets the index of the class with the larges probability
	pred_idx = int(np.argmax(probs))

    # Returns the confidence score of the class
	confidence = float(probs[pred_idx])

	return pred_idx, confidence
	
	

	
def majority_vote(preds):
    
    # Gets every predicted class for each image

    class_ids = [class_id for class_id, _ in preds]

    # Finds the most common class
    most_common_class = Counter(class_ids).most_common(1)[0][0]
    
    # Collects all the scores for the most common class
    scores_for_class = [score for class_id, score in preds if class_id == most_common_class]

    # Calculates the average score
    avg_score = sum(scores_for_class) / len(scores_for_class)
    
    return most_common_class, avg_score

def send_to_thingsboard(data):

    # Publishes the detected class to the devices telemetry
    config.client.publish("v1/devices/me/telemetry", json.dumps(data), qos=1)

#MAIN LOOP

def detect_waste(picam2):

    # Reads the light sensor
    light_val = grovepi.analogRead(config.light_sens)

    # If the light is too low
    while light_val <= 150:

        # Keep looping and warn the user until it has increased
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

    # Captures the images
    images = capture_image(picam2)

    print("Images captured")

    preds = []
    
    # For each image
    for img in images:
        print("Running Inference")
        
        # Run inference on the image
        class_id, score = run_inference(img)

        # If a class is returned
        if class_id is not None:
            print(f"class = {class_id} ({CLASSES[class_id]}) score={score:.2f}")

            # Add its Id and Score to the list

            preds.append((class_id, score))
        else:
            print("NONE FOUND")
        
    if not preds:
        time.sleep(1)
        setText("No Predictions")
        print("No Predictions")	
        return
    
    # Gets the most common class and its average score
    final_class, avg_score = majority_vote(preds)

    #Uses the class id to get the correct class name
    class_name = CLASSES[final_class]

    # Starts the feedback monitor
    config.feedback_monitor_on = True

    #Gets the users council from thingsboard to provide bin suggestions
    council = config.collection_info.get('council').lower()

    # Parses the class name into the correct dictionary key
    bin_parsed = bin_waste.get(class_name)

    # If the average confidence is below 0.75 warn the user
    if avg_score < 0.75:
         
        with config.i2c_lock:
            setRGB(255,165,0)
            setText(f"Caution\nConfidence Low")
            
        time.sleep(1)
        
        with config.i2c_lock:
            setText(f"Detected:\n{class_name}")

        time.sleep(2)
        
        # Suggest the correct bin
        with config.i2c_lock:
            setText(f"Bin:\n{wales_bins.get(council,{}).get(bin_parsed)}")

        time.sleep(3)

        # If the user presses the button twice, flag it and dont send the data to thingsboard
        if config.item_flagged:
            
            # Display feedback message
            feedback_message(class_name, avg_score)

            # Delete the images and predictions
            del images
            del preds

            # Turn of the feedback monitor
            config.feedback_monitor_on = False
            config.item_flagged = False

            return
        
        # Formats the data
        data = {"waste_type": class_name}

        # Sends it to thingsboard
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

        time.sleep(2)
        
        with config.i2c_lock:
            setText(f"Bin:\n{wales_bins.get(council).get(bin_parsed)}")

        time.sleep(3)

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
           
            
            # Starts the pi's camera
            picam2.start()

            # Display "Press button to start"
            with config.i2c_lock:
                
                grovepi.digitalWrite(config.button_led, 1)  # Turn LED on
                
                setRGB(0, 0, 255)  # Blue
                setText("     DETECT     ")
                time.sleep(3)
                setText("Ready!\nPress Button")

            # Gets the current time
            timeout = time.time()

            # Wait for the next button press
            while grovepi.digitalRead(config.button) == 1:
                
                # If 10 seconds has passed and there has been no button press
                if time.time() - timeout > 10:

                    # Exit the loop
                    with config.i2c_lock:
                        setRGB(255,255,0)
                        setText("Exiting\nDetect Mode")
                        time.sleep(3)
                    picam2.stop()
                    config.detect_mode_running = False
                    config.start_screen_running = True
                    break
                
                time.sleep(0.05)

            # Checks if detect mode is running so it doesnt enter detect mode after inactivuty
            if not config.detect_mode_running:
                continue
            
            
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