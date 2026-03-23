import cv2
import numpy as np
from picamera2 import Picamera2
import subprocess
import time
import os
import tensorflow as tf
from collections import Counter

from grove_rgb_lcd import setText, setRGB


#GPIO Setup



#Load Model

MODEL_PATH = "/home/pi/AI/iot-group-project/AI/model.tflite"
IMG_SIZE = (224, 224)

CLASSES = ["CARDBOARD-PAPER", "FOOD", "GENERAL WASTE", "GLASS", "HARD PLASTIC", "METAL", "SOFT PLASTIC"]

CONF_THRESHOLD = 0.5

interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

input_index = input_details[0]["index"]
output_index = output_details[0]["index"]

input_dtype = input_details[0]["index"]

#Takes 10 photos 
picam2 = Picamera2()
picam2.configure(picam2.create_still_configuration())
picam2.start()

def capture_image():

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
		img = img.astype(np.float32)
	elif input_dtype == np.uint8:
		img = img.astype(np.uint8)
	else:
		img = img.astype(input_dtype)
		
	img = np.expand_dims(img, axis=0)
	
	return img
	
	
#Runs inference on 1 image

def run_inference(img_tensor):

    input_tensor = pre_process(img_tensor)
    
    interpreter.set_tensor(input_index, input_tensor)
    
    interpreter.get_tensor(output_index)[0]
    
    probs = interpreter.get_tensor(output_index)[0]
    
    probs = output.astype(np.float32)
    
    pred_idx = int(np.argmax(probs))
    
    confidence = float(probs[pred_idx])
    
    return pred_idx, confidence
	
	

	
def majority_vote(preds):
	return Counter(preds).most_common(1)[0][0]
	
#MAIN LOOP



print("System ready. Press the button")

while True:
	time.sleep(0.05)
	setRGB(0, 50, 255)
	setText("Ready...")
	
	input("Press Enter to capture")
	print("Button Pressed")
	time.sleep(0.05)
	setRGB(255,165,0)
	setText("Capturing...")
		
	images = capture_image()
	
	print("Images captured")
	
	
	preds = []
	for img in images:
		print("Running Inference")
		img_tensor = pre_process(img)
		if img_tensor is None:
			print("NONE")
			continue
		
		class_id, score = run_inference(img_tensor)
		if class_id is not None:
			print(f"class = {class_id} ({CLASSES[class_id]}) score={score:.2f}")
			preds.append(class_id)
		else:
			print("NONE FOUND")
		
	if not preds:
		time.sleep(0.05)
		setText("No Predictions")
		print("No Predictions")	
		continue
				
	final_class = majority_vote(preds)
		
	class_name = CLASSES[final_class]
		
	print("Final: ", class_name)
	
	time.sleep(0.05)
	setRGB(0,255,0)
	setText(f"Detected:\n{class_name}")
	
	del images
	del preds
		
	
	time.sleep(5)
			

