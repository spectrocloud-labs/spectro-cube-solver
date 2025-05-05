import os
import time
import requests

BASE_URL = os.getenv("ROBOT_API_URL", "http://192.168.88.101:8000")

scramb_cycle = 0
solv_cycle = 0

def safe_post(url, json_data):
    """Try sending POST until it succeeds (with retries)."""
    while True:
        try:
            response = requests.post(url, json=json_data, timeout=5)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            print(f"[Retry] Failed to send to {url}: {e}")
            time.sleep(3)

def get_robot_status():
    """Get the current status of the robot (idle, scrambling, solving)."""
    try:
        response = requests.get(f"{BASE_URL}/status", timeout=5)
        response.raise_for_status()
        data = response.json()
        return data.get("status")
    except requests.RequestException as e:
        print(f"Failed to get status: {e}")
        return None

try:
    while True:
        # Wait for the robot to be idle before sending a scramble request
        while True:
            status = get_robot_status()
            if status == "idle":
                break
            print(f"Robot status: {status}. Waiting to scramble...")
            time.sleep(30)

        scramb_cycle += 1
        print(f"\n🔄 Sending scramble cycle {scramb_cycle}...")
        resp = safe_post(f"{BASE_URL}/scramble", {"scramb_cycle": scramb_cycle})
        print(f"✅ Scramble Response: {resp.status_code} {resp.text}")
        time.sleep(10)

        # Wait for the robot to be idle before sending a solve request
        while True:
            status = get_robot_status()
            if status == "idle":
                break
            print(f"Robot status: {status}. Waiting to solve...")
            time.sleep(30)

        solv_cycle += 1
        print(f"\n🔄 Sending solve cycle {solv_cycle}...")
        resp = safe_post(f"{BASE_URL}/solve", {"solv_cycle": solv_cycle})
        print(f"✅ Solve Response: {resp.status_code} {resp.text}")
        time.sleep(10)

except KeyboardInterrupt:
    print("Stopped by user.")
