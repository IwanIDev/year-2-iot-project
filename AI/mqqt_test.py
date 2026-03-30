import paho.mqtt.client as mqtt
import json
import time

ACCESS_TOKEN = "aipiRandomToken69420"


client = mqtt.Client()
client.username_pw_set(ACCESS_TOKEN)


client.connect("thingsboard.cs.cf.ac.uk", 1883, 60)
client.loop_start()

time.sleep(3)


data = {"waste_type": "HARD-PLASTC"}
client.publish("v1/devices/me/telemetry", json.dumps(data), qos=1)

time.sleep(5)