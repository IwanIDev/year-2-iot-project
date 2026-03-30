import paho.mqtt.client as mqtt
import json
import time

ACCESS_TOKEN = "your_token_here"

def on_connect(client, userdata, flags, rc):
    print("Connected with result code:", rc)

client = mqtt.Client()
client.username_pw_set(ACCESS_TOKEN)



client.on_connect = on_connect

client.connect("thingsboard.cs.cf.ac.uk", 1883, 60)
client.loop_start()

time.sleep(3)

while True:
    data = {"test": 123}
    result = client.publish("v1/devices/me/telemetry", json.dumps(data), qos=1)
    print("Publish result:", result)
    time.sleep(5)