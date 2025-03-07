import json
import os
import time
import threading
from flask import Flask, jsonify

app = Flask(__name__, static_url_path="/leds/static")
app.config["APPLICATION_ROOT"] = "/leds"

led_pattern_data = {
    "pattern_type": "static",
    "generated_at": None,
    "data": {"frames": [[[0, 0, 0] for _ in range(10)]], "frame_rate": 0.1},
    "validation_status": "no_valid_pattern"
}
pattern_lock = threading.Lock()

def update_led_pattern():
    global led_pattern_data
    last_modified = 0
    while True:
        try:
            current_modified = os.path.getmtime("led_pattern.json")
            if current_modified > last_modified:
                with open("led_pattern.json", "r", encoding="utf-8") as file:
                    new_data = json.load(file)
                with pattern_lock:
                    if isinstance(new_data, dict) and new_data.get("validation_status") == "Pass":
                        led_pattern_data = new_data
                    else:
                        print("Invalid pattern data in led_pattern.json")
                last_modified = current_modified
        except Exception as e:
            print(f"LED Pattern Update Error: {e}")
        time.sleep(1)

threading.Thread(target=update_led_pattern, daemon=True).start()

@app.route("/led_pattern", methods=["GET"])
def get_led_pattern():
    with pattern_lock:
        return jsonify(led_pattern_data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5048, debug=False)