import os
import paho.mqtt.client as mqtt
import asyncio
import websockets
import json

# MQTT Configuration
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_TOPIC = "robot/data"

# Websocket Configuration
WEBSOCKET_HOST = "0.0.0.0"
WEBSOCKET_PORT = 8765

connected_websockets = set()
current_cycle_data = []  # To store messages within the current cycle
latest_status = {}  # To store the latest status message (if any)
main_event_loop = None  # To store the main asyncio event loop

def on_connect(client, userdata, flags, rc):
    """Callback when MQTT client connects."""
    if rc == 0:
        print("Connected to MQTT broker")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"Connection to MQTT broker failed with code {rc}")

def on_message(client, userdata, msg):
    """Callback when MQTT message is received."""
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        if main_event_loop and not main_event_loop.is_closed():
            asyncio.run_coroutine_threadsafe(process_and_send(payload), main_event_loop)
        else:
            print("Main event loop not initialized or closed. Cannot process MQTT message.")
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error processing MQTT message: {e}")

async def process_and_send(message):
    """Processes the MQTT message and sends it to websockets."""
    global current_cycle_data
    global latest_status
    current_cycle_data.append(message)  # Store the message

    if message.get("type") == "status" and message.get("robot_state") == "Scrambling":
        current_cycle_data = [message]  # Start a new cycle

    if message.get("type") == "status":
        latest_status = message  # Update the latest status

    await send_to_websockets(message)

async def send_to_websockets(message):
    """Sends data to all connected websockets immediately."""
    if not connected_websockets:
        print("No connected websockets.")
        return

    message_str = json.dumps(message)

    for websocket in connected_websockets.copy():
        try:
            await websocket.send(message_str)
        except websockets.exceptions.ConnectionClosed:
            print("Websocket connection closed.")
            connected_websockets.discard(websocket)
        except Exception as e:
            print(f"Error sending to websocket: {e}")
            connected_websockets.discard(websocket)

async def websocket_handler(websocket):
    """Handles websocket connections."""
    connected_websockets.add(websocket)
    print(f"Websocket connected: {websocket}")

    # Send the latest status to the newly connected client
    if latest_status:
        try:
            status_message_str = json.dumps(latest_status)
            await websocket.send(status_message_str)
            print(f"Sent latest status to new websocket: {websocket}")
        except websockets.exceptions.ConnectionClosed:
            print("Websocket connection closed before sending latest status.")
            connected_websockets.remove(websocket)
        except Exception as e:
            print(f"Error sending latest status to websocket {websocket}: {e}")
            connected_websockets.remove(websocket)

    # Send the current cycle data to the newly connected client
    if current_cycle_data:
        try:
            for data in current_cycle_data:
                await websocket.send(json.dumps(data))
            print("Sent current cycle data to new client.")
        except websockets.exceptions.ConnectionClosed:
            print("Websocket connection closed before sending current cycle data.")
            connected_websockets.remove(websocket)
        except Exception as e:
            print(f"Error sending current cycle data to websocket: {e}")
            connected_websockets.remove(websocket)

    try:
        await websocket.wait_closed()
    except Exception as e:
        print(f"Websocket error: {e}")
    finally:
        connected_websockets.remove(websocket)
        print(f"Websocket disconnected: {websocket}")

async def start_servers():
    """Main function to start MQTT and websocket servers."""
    global main_event_loop
    main_event_loop = asyncio.get_event_loop()  # Get the main event loop

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, 1883, 60)
    client.loop_start()

    async with websockets.serve(websocket_handler, WEBSOCKET_HOST, WEBSOCKET_PORT):
        print(f"Websocket server started on ws://{WEBSOCKET_HOST}:{WEBSOCKET_PORT}")
        await asyncio.Future()
