import paho.mqtt.client as mqtt
import json
import time
import base64
import os
import threading

# Path to config file
CONFIG_FILE = "mqtt_config.json"

class MQTTPublisher:
    def __init__(self):
        """Initialize the MQTT Publisher and read config once."""
        self.config = self.read_config()
        self.broker = self.config["broker_ip"]
        self.port = int(self.config["port"])
        self.topic = self.config["topic"]
        self.debug_enabled = self.config.get("debug", False)  # Read debug flag from config

        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_disconnect = self.on_disconnect
        self.is_connected = False
        self.reconnect_attempt = 0
        self.publish_queue = []  # Queue for messages to be published
        self._publish_thread = threading.Thread(target=self._process_publish_queue, daemon=True)
        self._publish_thread.start()

        self.connect_mqtt()

    def read_config(self):
        """Read MQTT broker details from the config file."""
        if not os.path.exists(CONFIG_FILE):
            print("Config file not found. Using default values.")
            return {"broker_ip": None, "port": None, "topic": "robot/data", "debug": False}

        with open(CONFIG_FILE, "r") as file:
            return json.load(file)

    def on_connect(self, client, userdata, flags, rc):
        """Handle MQTT connection."""
        if rc == 0:
            self.is_connected = True
            self.reconnect_attempt = 0
            if self.debug_enabled:
                print("Connected to MQTT Broker")
        else:
            print(f"Failed to connect to MQTT Broker. Return code: {rc}")

    def on_disconnect(self, client, userdata, rc):
        """Handle unexpected disconnections."""
        self.is_connected = False
        if rc != 0:
            print("Unexpected disconnection. Attempting to reconnect...")
            threading.Thread(target=self.reconnect_mqtt, daemon=True).start()

    def reconnect_mqtt(self):
        """Reconnect to MQTT broker with exponential backoff."""
        while not self.is_connected:
            try:
                self.reconnect_attempt += 1
                self.connect_mqtt()
                if self.is_connected:
                    if self.debug_enabled:
                        print("Reconnected successfully.")
                    return
                sleep_time = min(2**self.reconnect_attempt, 30)  # Exponential backoff (max 30 sec)
                if self.debug_enabled:
                    print(f"Reconnecting in {sleep_time} seconds...")
                time.sleep(sleep_time)
            except Exception as e:
                print(f"Reconnection failed: {e}")
                time.sleep(min(2**self.reconnect_attempt, 30))  # Retry with backoff

    def connect_mqtt(self):
        """Connect to the MQTT broker if not already connected."""
        if self.is_connected:
            return  # Already connected, no need to reconnect

        if not self.broker or not self.port:
            print("MQTT broker details are missing. Cannot connect.")
            return None

        try:
            if self.debug_enabled:
                print(f"Connecting to MQTT broker at {self.broker}:{self.port}...")
            self.mqtt_client.connect(self.broker, self.port, 60)
            self.mqtt_client.loop_start()  # Keeps MQTT connection alive
            time.sleep(1)  # Give it time to establish connection
        except Exception as e:
            print(f"Failed to connect to MQTT Broker: {e}")

    def _enqueue_publish(self, topic, message):
        """Enqueue a message to be published."""
        self.publish_queue.append((topic, message))

    def _process_publish_queue(self):
        """Process messages in the publish queue in a separate thread."""
        while True:
            if self.is_connected and self.publish_queue:
                topic, message = self.publish_queue.pop(0)
                try:
                    result = self.mqtt_client.publish(topic, json.dumps(message), qos=1)
                    # We don't block here
                    if self.debug_enabled:
                        print(f"Enqueued message published to {topic}")
                except Exception as e:
                    print(f"Exception during queued publish: {e}")
            time.sleep(0.1)  # Small delay to avoid busy-waiting

    def send_message(self, message):
        """General method to send a message."""
        if self.broker and self.port and self.topic:
            self._enqueue_publish(self.topic, message)
            return True
        else:
            print("MQTT broker details or topic not configured.")
            return False

    def send_solution(self, solution_string):
        """Send the solution string before solving starts (non-blocking)."""
        message = {
            "type": "solution",
            "solution": solution_string,
            "timestamp": int(time.time())
        }
        return self.send_message(message)

    def send_command(self, command, step, total_steps):
        """Send each command as it is executed (non-blocking)."""
        message = {
            "type": "command",
            "command": command,
            "step": step,
            "total_steps": total_steps,
            "timestamp": int(time.time())
        }
        return self.send_message(message)

    def send_status(self, robot_state):
        """Send robot status (non-blocking)."""
        message = {
            "type": "status",
            "robot_state": robot_state,
            "timestamp": int(time.time())
        }
        return self.send_message(message)

    def send_face_image(self, side, image_buffer):
        """Send each face image as scanned (non-blocking)."""
        encoded_string = base64.b64encode(image_buffer).decode('utf-8')
        message = {
            "type": "face",
            "side": side,
            "image_data": encoded_string,
            "timestamp": int(time.time())
        }
        return self.send_message(message)

    def send_image(self, image_path):
        """Send the final image after solving (non-blocking)."""
        try:
            with open(image_path, "rb") as img_file:
                encoded_string = base64.b64encode(img_file.read()).decode('utf-8')

            message = {
                "type": "image",
                "image_data": encoded_string,
                "timestamp": int(time.time())
            }
            return self.send_message(message)

        except FileNotFoundError:
            print(f"Error: Image file '{image_path}' not found!")
            return False

# Global instance of MQTTPublisher, reused in all modules
mqtt_publisher = MQTTPublisher()
