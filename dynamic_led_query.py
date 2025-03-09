import json
import os
import time
import threading
from queue import Queue
from flask import Flask, jsonify
import eventlet  # Import eventlet first
eventlet.monkey_patch()  # Apply monkey patching before other imports
from flask_socketio import SocketIO, emit

app = Flask(__name__, static_url_path="/leds/static")
app.config["APPLICATION_ROOT"] = "/leds"
socketio = SocketIO(app, cors_allowed_origins="*")  # Enable CORS for WebSocket

led_pattern_data = {
    "pattern_type": "static",
    "generated_at": None,
    "data": {"frames": [[[0, 0, 0] for _ in range(10)]], "frame_rate": 0.1},
    "validation_status": "no_valid_pattern"
}
pattern_lock = threading.Lock()
emit_queue = Queue()

def background_emitter():
    while True:
        event, data = emit_queue.get()
        socketio.emit(event, data, namespace="/", broadcast=True)
        print(f"Emitted WebSocket pattern: {data['pattern']}")
        emit_queue.task_done()

threading.Thread(target=background_emitter, daemon=True).start()

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
                            emit_queue.put(("led_pattern_update", {"pattern": led_pattern_data["data"]}))
                            print(f"Queued WebSocket pattern: {led_pattern_data['data']}")
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

threading.Thread(target=update_led_pattern, daemon=True).start()

@app.route("/led_pattern", methods=["GET"])
def get_led_pattern():
    with pattern_lock:
        return jsonify(led_pattern_data)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5048, debug=False)