import json
import datetime
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import paho.mqtt.client as mqtt

load_dotenv()

client = MongoClient(os.getenv('MongoUrl'))
db = client['Mqtt-project']

def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with result code {reason_code}")
    client.subscribe([
        ("room1/topic", 0),
        ("room2/topic", 0),
        ("kitchen/topic", 0),
    ])

def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.payload))
    try:
        payload = json.loads(msg.payload.decode('utf-8'))
        payload['timestamp'] = datetime.datetime.now().isoformat()
        sensor_id = msg.topic.split("/")[0]
        collection = db[f'sensor_{sensor_id}']
        payload['position'] = sensor_id
        collection.insert_one(payload)
        print("Inserted data into MongoDB")
    except Exception as e:
        print(f"Error inserting into MongoDB: {e}")

def setup_mqtt_client():
    mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqttc.on_connect = on_connect
    mqttc.on_message = on_message
    mqttc.connect(os.getenv('MQTT_BROKER'), int(os.getenv('MQTT_PORT')), 60)
    return mqttc
