import threading
import asyncio
import uvicorn
from websocket_server import start_servers

if __name__ == "__main__":

    #  Start WebSockets + MQTT in the same asyncio loop
    asyncio.run(start_servers())  #  Runs both inside one thread
