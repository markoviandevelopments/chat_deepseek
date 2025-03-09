import asyncio
import websockets
import json
import os
import time
import threading

led_pattern_data = {
    "pattern_type": "static",
    "generated_at": None,
    "data": {"frames": [[[0, 0, 0] for _ in range(10)]], "frame_rate": 0.1},
    "validation_status": "no_valid_pattern"
}
pattern_lock = threading.Lock()
clients = set()

def update_led_pattern():
    global led_pattern_data
    last_modified = 0
    while True:
        try:
            if os.path.exists("led_pattern.json"):
                current_modified = os.path.getmtime("led_pattern.json")
                if current_modified > last_modified:
                    with open("led_pattern.json", "r", encoding="utf-8") as file:
                        new_data = json.load(file)
                    with pattern_lock:
                        if (isinstance(new_data, dict) and 
                            new_data.get("validation_status") == "Pass" and 
                            new_data.get("data") is not None):
                            led_pattern_data = new_data
                            pattern_to_send = led_pattern_data["data"]
                            if led_pattern_data["pattern_type"] == "static":
                                # Static: wrap as single pattern
                                if (isinstance(pattern_to_send, list) and len(pattern_to_send) == 10 and
                                    all(isinstance(frame, list) and len(frame) == 3 and all(0 <= v <= 255 for v in frame) for frame in pattern_to_send)):
                                    pattern_to_send = {"pattern": pattern_to_send}
                                else:
                                    print(f"Invalid static pattern format: {pattern_to_send}")
                                    continue
                            # Animated: send full data (frames and frame_rate)
                            asyncio.run(send_to_clients(pattern_to_send))
                            print(f"Sent WebSocket data: {pattern_to_send}")
                        else:
                            print(f"Invalid pattern data: {new_data}")
                            led_pattern_data = {
                                "pattern_type": "static",
                                "generated_at": None,
                                "data": {"frames": [[[0, 0, 0] for _ in range(10)]], "frame_rate": 0.1},
                                "validation_status": "invalid_pattern"
                            }
                    last_modified = current_modified
            else:
                print("led_pattern.json not found")
        except Exception as e:
            print(f"LED Pattern Update Error: {e}")
        time.sleep(1)

async def handler(websocket, path):
    global clients
    clients.add(websocket)
    print(f"Client connected: {websocket.remote_address}")
    try:
        await websocket.wait_closed()
    except Exception as e:
        print(f"WebSocket Handler Error: {e}")
    finally:
        clients.remove(websocket)
        print(f"Client disconnected: {websocket.remote_address}")

async def send_to_clients(message):
    if clients:
        tasks = [asyncio.create_task(client.send(json.dumps(message))) for client in clients]
        await asyncio.gather(*tasks, return_exceptions=True)

async def main():
    server = await websockets.serve(handler, "0.0.0.0", 5048)
    print("Starting WebSocket server on 0.0.0.0:5048")
    await server.wait_closed()

threading.Thread(target=update_led_pattern, daemon=True).start()

if __name__ == "__main__":
    asyncio.run(main())