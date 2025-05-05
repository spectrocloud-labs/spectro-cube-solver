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

try:
    while True:
        scramb_cycle += 1
        print(f"\n🔄 Sending scramble cycle {scramb_cycle}...")
        resp = safe_post(f"{BASE_URL}/scramble", {"scramb_cycle": scramb_cycle})
        print(f"✅ Scramble Response: {resp.status_code} {resp.text}")

        time.sleep(5)

        solv_cycle += 1
        print(f"\n🔄 Sending solve cycle {solv_cycle}...")
        resp = safe_post(f"{BASE_URL}/solve", {"solv_cycle": solv_cycle})
        print(f"✅ Solve Response: {resp.status_code} {resp.text}")

        time.sleep(5)

except KeyboardInterrupt:
    print("Stopped by user.")

