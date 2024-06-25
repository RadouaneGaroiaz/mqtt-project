import time
import json
import paho.mqtt.client as mqtt

def on_publish(client, userdata, mid, reason_code, properties):
    # reason_code and properties will only be present in MQTTv5. It's always unset in MQTTv3
    try:
        userdata.remove(mid)
    except KeyError:
        print("error")

unacked_publish = set()
mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_publish = on_publish

mqttc.user_data_set(unacked_publish)
mqttc.connect("51.38.185.58")
mqttc.loop_start()

# Our application produces some messages
message = {
    "temperature": 25,
}
message_json = json.dumps(message)

msg_info = mqttc.publish("exo1", message_json, qos=1)
unacked_publish.add(msg_info.mid)

# Wait for all messages to be published
while len(unacked_publish):
    time.sleep(0.1)

msg_info.wait_for_publish()

mqttc.disconnect()
mqttc.loop_stop()
