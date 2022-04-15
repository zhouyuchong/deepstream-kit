import json
import paho.mqtt.client as mqtt
import json


def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("deepstream")


def on_message(client, userdata, msg):
    # msg.payload = msg.payload.decode("utf-8")
    print(str(msg.payload) + "\n\n")
    # print("json format:", json.loads(msg.payload))
    # except:
        # print("something wrong:" +  ":" + str(msg.payload))
    

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("localhost", 1883, 60)
client.loop_forever()