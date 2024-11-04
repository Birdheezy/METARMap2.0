import paho.mqtt.client as mqtt
from mqtt_config import MQTT_BROKER, MQTT_PORT, MQTT_TOPIC_LED_CONTROL, MQTT_USERNAME, MQTT_PASSWORD
import subprocess

def turn_on_leds():
    print("Turning LEDs ON")
    subprocess.run(['sudo', 'systemctl', 'restart', 'metar.service'], check=True)

def turn_off_leds():
    print("Turning LEDs OFF")
    subprocess.run(['sudo', 'systemctl', 'stop', 'metar.service'], check=True)
    subprocess.run(['sudo', '/home/pi/metar/bin/python3', '/home/pi/blank.py'], check=True)

# MQTT setup
def on_connect(client, userdata, flags, rc, *args):
    print(f"Connected with result code {rc}")
    client.subscribe(MQTT_TOPIC_LED_CONTROL)

def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    print(f"Message received: {payload}")
    if payload == 'ON':
        turn_on_leds()
    elif payload == 'OFF':
        turn_off_leds()

# Initialize and start the MQTT client
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)

# Start the MQTT client loop to keep the script running
print("MQTT client loop started")
mqtt_client.loop_forever()  # This will block and keep the script alive
