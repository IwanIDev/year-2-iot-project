# Shared configuration and state variables
import threading
import paho.mqtt.client as mqtt
import json


collection_info = {}

def on_message(client, userdata, msg):
    
    payload = json.loads(msg.payload.decode())

    shared = payload.get("shared", {})

    collection_info.update(shared)

ACCESS_TOKEN = "aipiRandomToken69420"

client = mqtt.Client()
client.username_pw_set(ACCESS_TOKEN)

client.connect("thingsboard.cs.cf.ac.uk", 1883, 60)

client.on_message = on_message

client.subscribe("v1/devices/me/attributes")

start_screen_running = True
detect_mode_running = False
feedback_monitor_on = False
item_flagged = False


i2c_lock = threading.RLock()


# Hardware pins
pir = 2          # Motion sensor on D2
button_led = 3   # LED Button on D3
button = 4
light_sens = 0



