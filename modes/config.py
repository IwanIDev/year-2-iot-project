# Shared configuration and state variables
import threading
import paho.mqtt.client as mqtt
import json
import ssl

# Initialises the dictionary to hold the shared attribute data from thingsboard
collection_info = {}

# Defines the on message function that is called when shared attributes are updates in thingsboard

def on_message(client, userdata, msg):
    
    # Parses the json payload
    payload = json.loads(msg.payload.decode())

    #Appends the data to the dictionary
    if "shared" in payload:
        collection_info.update(payload["shared"])
    else:
        collection_info.update(payload)

# Defines an on connect fucntion that requests the shared attribute data on device startup as 
# the pi will not recieve updates automatically

def on_connect(client, userdata, flags, rc):

    client.subscribe("v1/devices/me/attributes")

    client.publish(
        "v1/devices/me/attributes/request/1",
        json.dumps({
            "sharedKeys": "bins,collection_date,council"
        })
    )

# Devices access token
ACCESS_TOKEN = "aipiRandomToken69420"

# Defines the mqtt client
client = mqtt.Client()
client.username_pw_set(ACCESS_TOKEN)

client.on_connect = on_connect 
client.on_message = on_message


client.connect("thingsboard.cs.cf.ac.uk", 1883)


client.loop_start()

# Initialises the mode flags
start_screen_running = True
detect_mode_running = False
feedback_monitor_on = False
item_flagged = False

# Defines the thread lock to be used when a funtion is accessing the sensors/lcd
i2c_lock = threading.RLock()


# Hardware pins
pir = 2          # Motion sensor on D2
button_led = 3   # LED on D3
button = 4 #Button on D4
light_sens = 0 # Light sensor on A0

