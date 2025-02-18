from flask import Flask, jsonify
import json
import threading
import time

'''
Note that this program is a subset of what led_query_webserver does
'''


app = Flask(__name__)

# Global variable to store the LED pattern
led_pattern = []

def update_led_pattern():
    """Reads the JSON file every 5 seconds and updates the global led_pattern variable if valid."""
    global led_pattern
    while True:
        try:
            with open("led_pattern.json", "r") as file:
                data = json.load(file)
                if isinstance(data, list) and len(data) == 10:  # Ensure it's a list of length 10
                    led_pattern = data
        except (json.JSONDecodeError, FileNotFoundError, IOError):
            pass  # If reading fails, keep the old data

        time.sleep(5)  # Wait for 5 seconds before checking again

# Start the background thread
thread = threading.Thread(target=update_led_pattern, daemon=True)
thread.start()

@app.route("/led_pattern", methods=["GET"])
def get_led_pattern():
    return jsonify(led_pattern)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5048)
