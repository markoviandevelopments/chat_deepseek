from flask import Flask, jsonify
import json
import threading
import time

'''
Note that this program is a subset of what led_query_webserver does.
'''

app = Flask(__name__)

# Global variable to store the LED pattern
led_pattern = []
pattern_lock = threading.Lock()  # Ensures thread safety

def update_led_pattern():
    """Reads the JSON file every 5 seconds and updates the global led_pattern variable if valid."""
    global led_pattern
    while True:
        try:
            with open("led_pattern.json", "r", encoding="utf-8") as file:
                data = json.load(file)
                
                # Validate that data is a list of 10 RGB tuples
                if isinstance(data, list) and len(data) == 10 and all(isinstance(item, list) and len(item) == 3 for item in data):
                    with pattern_lock:
                        led_pattern = data  # Only update if valid
        except (json.JSONDecodeError, FileNotFoundError, IOError) as e:
            print(f"LED Pattern File Read Error: {e}")  # Debugging info

        for _ in range(5):
            time.sleep(0.5)


# Start the background thread
thread = threading.Thread(target=update_led_pattern, daemon=True)
thread.start()

@app.route("/led_pattern", methods=["GET"])
def get_led_pattern():
    with pattern_lock:
        return jsonify(led_pattern if led_pattern else [[0, 0, 0]] * 10)  # Default pattern if empty

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5048)






