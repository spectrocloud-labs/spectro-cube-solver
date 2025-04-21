import paho.mqtt.client as mqtt
import json
import time
import base64
import os
import threading

# Path to config file
CONFIG_FILE = "mqtt_config.json"

# Global MQTT client instance
mqtt_client = None
is_connected = False  # Track connection status
reconnect_attempt = 0  # Track reconnect attempts

def read_config():
    """Read broker IP and port from the config file."""
    if not os.path.exists(CONFIG_FILE):
        print("Config file not found. Using default values.")
        return {"broker_ip": None, "port": None, "topic": "robot/data"}
    
    with open(CONFIG_FILE, "r") as file:
        return json.load(file)

def on_connect(client, userdata, flags, rc):
    """Callback for when the client connects to the broker."""
    global is_connected, reconnect_attempt
    if rc == 0:
        is_connected = True
        reconnect_attempt = 0  # Reset reconnect attempts
        print("Connected to MQTT broker successfully.")
    else:
        print(f"Failed to connect to MQTT broker. Return code: {rc}")

def on_disconnect(client, userdata, rc):
    """Callback for when the client disconnects."""
    global is_connected
    is_connected = False
    if rc != 0:
        print("Unexpected disconnection. Attempting to reconnect...")
        threading.Thread(target=reconnect_mqtt, daemon=True).start()

def reconnect_mqtt():
    """Reconnect to MQTT broker with exponential backoff."""
    global mqtt_client, is_connected, reconnect_attempt
    while not is_connected:
        try:
            reconnect_attempt += 1
            connect_mqtt()
            if is_connected:
                print("Reconnected successfully.")
                return
            sleep_time = min(2**reconnect_attempt, 30)  # Exponential backoff (max 30 sec)
            print(f"Reconnecting in {sleep_time} seconds...")
            time.sleep(sleep_time)
        except Exception as e:
            print(f"Reconnection failed: {e}")
            time.sleep(min(2**reconnect_attempt, 30))  # Retry with backoff

def connect_mqtt():
    """Connect to the MQTT broker if not already connected."""
    global mqtt_client, is_connected

    if is_connected:
        return  # Already connected, no need to reconnect

    config = read_config()
    broker = config["broker_ip"]
    port = config["port"]

    if not broker or not port:
        print("MQTT broker details are missing. Cannot connect.")
        return None

    if mqtt_client is None:
        mqtt_client = mqtt.Client()
        mqtt_client.on_connect = on_connect
        mqtt_client.on_disconnect = on_disconnect

    try:
        print(f"Connecting to MQTT broker at {broker}:{port}...")
        mqtt_client.connect(broker, int(port), 60)
        mqtt_client.loop_start()  # ✅ Keeps MQTT connection alive
        time.sleep(1)  # Give it time to establish connection
        return mqtt_client
    except Exception as e:
        print(f"Failed to connect to MQTT broker: {e}")
        return None

def publish_message(topic, message):
    """Publish message and ensure connection before sending."""
    connect_mqtt()  # Ensure connection before publishing

    if not is_connected:
        print("Cannot publish: No connection to MQTT broker. Retrying...")
        while not is_connected:  # Wait until reconnected
            time.sleep(1)
        print("Reconnected, retrying publish.")

    try:
        result = mqtt_client.publish(topic, json.dumps(message), qos=1)
        result.wait_for_publish()  # Block until the message is published
        print(f"Published message to {topic}")
        return True
    except Exception as e:
        print(f"Exception during publish: {e}")
        return False

def send_solution(solution_string):
    """Send the solution string before solving starts."""
    config = read_config()
    message = {
        "type": "solution",
        "solution": solution_string,
        "timestamp": int(time.time())
    }
    return publish_message(config["topic"], message)

def send_command(command, step, total_steps):
    """Send each command as it is executed."""
    config = read_config()
    message = {
        "type": "command",
        "command": command,
        "step": step,
        "total_steps": total_steps,
        "timestamp": int(time.time())
    }
    return publish_message(config["topic"], message)

def send_face_image(side, image_buffer):
    """Send each face image as scanned."""
    config = read_config()
    encoded_string = base64.b64encode(image_buffer).decode('utf-8')
    message = {
        "type": "face",
        "side": side,
        "image_data": encoded_string ,
        "timestamp": int(time.time())
    }
    return publish_message(config["topic"], message)

def send_image(image_path):
    """Send the final image after solving."""
    try:
        with open(image_path, "rb") as img_file:
            encoded_string = base64.b64encode(img_file.read()).decode('utf-8')

        config = read_config()
        message = {
            "type": "image",
            "image_data": encoded_string,
            "timestamp": int(time.time())
        }
        return publish_message(config["topic"], message)

    except FileNotFoundError:
        print(f"Error: Image file '{image_path}' not found!")
        return False

