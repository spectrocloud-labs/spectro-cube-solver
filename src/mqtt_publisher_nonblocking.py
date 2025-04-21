import paho.mqtt.client as mqtt
import json
import time
import base64
import os
import queue
import threading
import atexit

# Path to config file
CONFIG_FILE = "mqtt_config.json"
LOG_FILE = "mqtt_failures.log"

# Global MQTT client instance
mqtt_client = None
is_connected = False  # Track connection status
message_queue = queue.Queue()  # Message queue for non-blocking publishing
shutdown_event = threading.Event()  # Event to handle shutdown

def read_config():
    """Read broker IP and port from the config file."""
    if not os.path.exists(CONFIG_FILE):
        print("Config file not found. Using default values.")
        return {"broker_ip": None, "port": None, "topic": "robot/data"}
    
    with open(CONFIG_FILE, "r") as file:
        return json.load(file)

def log_failure(message):
    """Log failed MQTT messages to a file."""
    with open(LOG_FILE, "a") as log_file:
        log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Failed to publish: {json.dumps(message)}\n")

def on_connect(client, userdata, flags, rc):
    """Callback for when the client connects to the broker."""
    global is_connected
    if rc == 0:
        is_connected = True
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

def on_publish(client, userdata, mid):
    """Callback for when a message is published successfully."""
    print(f"Message {mid} published successfully.")

def reconnect_mqtt():
    """Reconnect to MQTT broker with exponential backoff."""
    global mqtt_client
    attempt = 1
    while not is_connected:
        try:
            connect_mqtt()
            if is_connected:
                print("Reconnected successfully.")
                return
            time.sleep(min(2**attempt, 30))  # Exponential backoff (max 30 sec)
            attempt += 1
        except Exception as e:
            print(f"Reconnection failed: {e}")
            time.sleep(min(2**attempt, 30))  # Retry with backoff

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
        return

    if mqtt_client is None:
        mqtt_client = mqtt.Client()
        mqtt_client.on_connect = on_connect
        mqtt_client.on_disconnect = on_disconnect
        mqtt_client.on_publish = on_publish

    try:
        print(f"Connecting to MQTT broker at {broker}:{port}...")
        mqtt_client.connect(broker, int(port), 60)
        mqtt_client.loop_start()  # ✅ Starts MQTT in background
    except Exception as e:
        print(f"Failed to connect to MQTT broker: {e}")

def message_worker():
    """Background worker thread to process the message queue."""
    while not shutdown_event.is_set():
        try:
            topic, message = message_queue.get(timeout=1)  # Wait for a message with timeout
        except queue.Empty:
            continue  # No message, check shutdown_event again
        
        while not is_connected:  # Wait until connected
            print("MQTT is not connected. Holding messages in queue...")
            connect_mqtt()  # Ensure it attempts to reconnect
            time.sleep(2)  # Keep checking connection status

        success = publish_message(topic, message)
        if not success:
            log_failure(message)  # Log failed messages
            message_queue.put((topic, message))  # Requeue message for retry
        message_queue.task_done()

# Start the worker thread (Only runs once)
worker_thread = threading.Thread(target=message_worker, daemon=True)
worker_thread.start()

def publish_message(topic, message):
    """Publish message asynchronously if MQTT is connected."""
    if not is_connected:
        return False  # Skip publishing if not connected

    try:
        result = mqtt_client.publish(topic, json.dumps(message), qos=1)  # QoS 1 ensures delivery
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"Published message to {topic}: {message}")
            return True
        else:
            print(f"Publish failed with error code {result.rc}")
            return False
    except Exception as e:
        print(f"Exception during publish: {e}")
        return False

def queue_message(topic, message):
    """Add a message to the queue for the worker to process."""
    message_queue.put((topic, message))

def send_solution(solution_string):
    """Send the solution string before solving starts."""
    config = read_config()
    message = {
        "type": "solution",
        "solution": solution_string,
        "timestamp": int(time.time())
    }
    queue_message(config["topic"], message)

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
    queue_message(config["topic"], message)

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
        queue_message(config["topic"], message)

    except FileNotFoundError:
        print(f"Error: Image file '{image_path}' not found!")

def shutdown_handler():
    """Ensure all messages in the queue are sent before exiting."""
    print("Waiting for all messages to be published before exiting...")
    shutdown_event.set()  # Signal worker thread to stop
    message_queue.join()  # Wait until all messages are processed
    print("All messages have been published. Exiting now.")

# Register shutdown_handler to run on program exit
atexit.register(shutdown_handler)
