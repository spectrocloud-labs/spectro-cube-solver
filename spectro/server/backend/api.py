from fastapi import FastAPI
from websocket_server import data_store  # ✅ Import shared data

app = FastAPI()

@app.get("/latest_solution")
def get_latest_solution():
    return {"status": "success", "solution": data_store["solution"]} if data_store["solution"] else {"status": "error", "message": "No solution received yet."}

@app.get("/latest_command")
def get_latest_command():
    return {"status": "success", "command": data_store["command"]} if data_store["command"] else {"status": "error", "message": "No command received yet."}

@app.get("/latest_image")
def get_latest_image():
    return {"status": "success", "image": data_store["image"]} if data_store["image"] else {"status": "error", "message": "No image received yet."}
