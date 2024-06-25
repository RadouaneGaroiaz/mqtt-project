import time
import json
import paho.mqtt.client as mqtt

def on_publish(client, userdata, mid, reason_code, properties=None):
    try:
        userdata.remove(mid)
    except KeyError:
        print("error")

unacked_publish = set()

mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_publish = on_publish

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    
    # Our application produces some messages
    message = [2, 5, 6]
    message_json = json.dumps(message)
    
    msg_info = client.publish("exo1", message_json, qos=1)
    unacked_publish.add(msg_info.mid)

mqttc.on_connect = on_connect

mqttc.connect("51.38.185.58", 1883, 60)
mqttc.loop_start()

# Wait for all messages to be published
while len(unacked_publish):
    time.sleep(0.1)

mqttc.disconnect()
mqttc.loop_stop()
