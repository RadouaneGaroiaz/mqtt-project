import paho.mqtt.client as mqtt

# Callback function when client connects
def on_connect(client, userdata, flags, reason_code, properties=None):
    print(f"Connected with result code {reason_code}")
    client.subscribe("exo1")

# Callback function when a message is received
def on_message(client, userdata, msg):
    try:
        # Decode the payload and split into a list of numbers
        message = msg.payload.decode('utf-8')
        numbers = message.split(',')
        numbers = [int(num) for num in numbers]
        
        # Calculate the sum
        result = sum(numbers)
        print(f"Received numbers: {numbers}, Sum: {result}")
        
        # Publish the result
        client.publish("exo1_result", str(result), qos=1)
    except Exception as e:
        print(f"Error processing message: {e}")

# Create MQTT client and set callback functions
mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_message = on_message

# Connect to the MQTT broker
mqttc.connect("51.38.185.58", 1883, 60)

# Start the MQTT client loop
mqttc.loop_forever()
