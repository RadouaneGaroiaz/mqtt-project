import network
import time
from machine import Pin
import dht
import ujson
from umqtt.simple import MQTTClient

# MQTT Server Parameters
MQTT_CLIENT_ID = "G1"
MQTT_BROKER = "51.38.185.58"
MQTT_USER = ""
MQTT_PASSWORD = ""
MQTT_TOPIC = "kitchen/topic"
STATUS = "Disconnected"

# Pin setup
sensor = dht.DHT22(Pin(15))
led = Pin(23, Pin.OUT)  # Pin D23 as output for LED

# Initialize LED to off
led.value(0)

def mqtt_callback(topic, msg):
    global led
    print("Received MQTT message on topic {}: {}".format(topic, msg))
    if msg == b"ledOn":
        print("Turning LED ON")
        led.value(1)  # Turn LED on
    elif msg == b"ledOff":
        print("Turning LED OFF")
        led.value(0)  # Turn LED off
    else:
        print("Unknown command")

def connect_wifi():
    print("Connecting to WiFi", end="")
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect('Wokwi-GUEST', '')
    while not sta_if.isconnected():
        print(".", end="")
        time.sleep(0.1)
    print(" Connected!")

def main():
    global STATUS
    connect_wifi()

    print("Connecting to MQTT server... ", end="")
    client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, user=MQTT_USER, password=MQTT_PASSWORD)

    # Set the callback function
    client.set_callback(mqtt_callback)

    client.connect()
    client.subscribe(MQTT_TOPIC)
    print("Connected!")
    STATUS = "Connected"

    prev_weather = ""
    while True:
        print("Measuring weather conditions... ", end="")
        sensor.measure()
        message = ujson.dumps({
            "status": STATUS,
            "data": {
                "temp": sensor.temperature(),
                "humidity": sensor.humidity(),
            }
        })
        if message != prev_weather:
            print("Updated!")
            print("Reporting to MQTT topic {}: {}".format(MQTT_TOPIC, message))
            client.publish(MQTT_TOPIC, message)
            prev_weather = message
        else:
            print("No change")

        # Check for incoming MQTT messages
        client.check_msg()

        time.sleep(5)

if __name__ == "__main__":
    main()
