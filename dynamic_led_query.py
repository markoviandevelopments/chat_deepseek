import asyncio
import websockets
import json
import os
import time
import threading

# Global state for LED pattern data
led_pattern_data = {
    "pattern_type": "static",
    "generated_at": None,
    "data": {"frames": [[[0, 0, 0] for _ in range(10)]], "frame_rate": 0.1},
    "validation_status": "no_valid_pattern"
}
pattern_lock = threading.Lock()
clients = set()  # Set to track connected WebSocket clients

def update_led_pattern():
    """Background thread to monitor led_pattern.json and update clients."""
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
                            pattern_to_send = (
                                led_pattern_data["data"]["frames"][0] if "frames" in led_pattern_data["data"]
                                else led_pattern_data["data"]
                            )
                            if (isinstance(pattern_to_send, list) and len(pattern_to_send) == 10 and
                                all(isinstance(frame, list) and len(frame) == 3 and all(0 <= v <= 255 for v in frame) for frame in pattern_to_send)):
                                # Use asyncio.run to send from a non-async context
                                asyncio.run(send_to_clients({"pattern": pattern_to_send}))
                                print(f"Sent WebSocket pattern: {pattern_to_send}")
                            else:
                                print(f"Invalid pattern format: {pattern_to_send}")
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
        time.sleep(1)  # Check every second

async def handler(websocket, path):
    """Handle individual WebSocket connections."""
    global clients
    clients.add(websocket)
    print(f"Client connected: {websocket.remote_address}")
    try:
        await websocket.wait_closed()  # Keep connection open until client disconnects
    except Exception as e:
        print(f"WebSocket Handler Error: {e}")
    finally:
        clients.remove(websocket)
        print(f"Client disconnected: {websocket.remote_address}")

async def send_to_clients(message):
    """Send a message to all connected WebSocket clients."""
    if clients:
        tasks = [asyncio.create_task(client.send(json.dumps(message))) for client in clients]
        await asyncio.gather(*tasks, return_exceptions=True)

# Start the background thread to monitor the JSON file
threading.Thread(target=update_led_pattern, daemon=True).start()

# Start the WebSocket server
async def main():
    server = await websockets.serve(handler, "0.0.0.0", 5048)
    print("Starting WebSocket server on 0.0.0.0:5048")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())