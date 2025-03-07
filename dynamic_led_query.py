from flask import Flask, jsonify
import json
import threading
import time

app = Flask(__name__)

# Initialize with a default pattern
led_pattern_data = {
    "pattern_type": "static",
    "generated_at": None,
    "data": {"frames": [[[0, 0, 0]] * 10], "frame_rate": 0.1},  # Default static frame
    "validation_status": "no_valid_pattern"
}
pattern_lock = threading.Lock()

def update_led_pattern():
    """Poll led_pattern.json and update the global led_pattern_data."""
    global led_pattern_data
    while True:
        try:
            with open("led_pattern.json", "r", encoding="utf-8") as file:
                new_data = json.load(file)
                
            with pattern_lock:
                pattern_type = new_data.get("pattern_type")
                validation_status = new_data.get("validation_status", "unknown")
                generated_at = new_data.get("generated_at")
                data = new_data.get("data")

                if pattern_type == "static" and validation_status == "Pass":
                    if (isinstance(data, list) and len(data) == 10 and 
                        all(isinstance(c, list) and len(c) == 3 and all(0 <= v <= 255 for v in c) for c in data)):
                        led_pattern_data = {
                            "pattern_type": "static",
                            "generated_at": generated_at,
                            "data": {"frames": [data], "frame_rate": 0.1},  # Wrap as single frame
                            "validation_status": validation_status
                        }
                elif pattern_type == "animated" and validation_status == "Pass":
                    if (isinstance(data, dict) and "frames" in data and "frame_rate" in data and
                        len(data["frames"]) >= 5 and 
                        all(len(f) == 10 and all(len(c) == 3 and all(0 <= v <= 255 for v in c) for c in f) for f in data["frames"]) and
                        0.05 <= data["frame_rate"] <= 1.0):
                        led_pattern_data = {
                            "pattern_type": "animated",
                            "generated_at": generated_at,
                            "data": {"frames": data["frames"], "frame_rate": data["frame_rate"]},
                            "validation_status": validation_status
                        }
                # Invalid data keeps the previous state or defaults if uninitialized
        except (json.JSONDecodeError, FileNotFoundError, IOError, TypeError) as e:
            print(f"LED Pattern File Read Error: {e}")
        
        time.sleep(1)  # Poll every second

thread = threading.Thread(target=update_led_pattern, daemon=True)
thread.start()

@app.route("/led_pattern", methods=["GET"])
def get_led_pattern():
    """Serve the current pattern data as JSON."""
    with pattern_lock:
        return jsonify({
            "pattern_type": led_pattern_data["pattern_type"],
            "generated_at": led_pattern_data["generated_at"],
            "frames": led_pattern_data["data"]["frames"],
            "frame_rate": led_pattern_data["data"]["frame_rate"],
            "validation_status": led_pattern_data["validation_status"]
        })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5048)