from flask import Flask, jsonify
import json

app = Flask(__name__)

# Load the LED pattern from file
with open("led_pattern.json", "r") as file:
    led_pattern = json.load(file)

@app.route("/led_pattern", methods=["GET"])
def get_led_pattern():
    return jsonify(led_pattern)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5048)