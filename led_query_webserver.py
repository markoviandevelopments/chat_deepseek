from flask import Flask, render_template, request, jsonify, redirect
import requests
import re
import json
import datetime
import ast
from flask_cors import CORS

app = Flask(__name__, static_url_path="/leds/static")
app.config["APPLICATION_ROOT"] = "/leds"

CORS(app)

API_URL = "http://50.188.120.138:5049/api/deepseek"
LAST_RESULT = {"status": "No request yet", "timestamp": None, "raw_output": ""}

def query_api(user_prompt, temperature=0.7):
    params = {"prompt": user_prompt, "temperature": temperature}

    try:
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
        data = response.json()

        print("=== RAW API RESPONSE ===")
        print(data)
        print("=======================")

        return data.get("response", "").strip() or "No response received."
    
    except requests.RequestException as e:
        print("API Request Error:", e)
        return f"Error: {e}"

@app.route("/leds", methods=["GET", "POST"])
def index():
    global LAST_RESULT

    if request.method == "POST":
        # Handle both JSON and Form Data Requests
        request_data = request.get_json() if request.is_json else request.form
        theme = request_data.get("theme")
        temp = float(request_data.get("temperature", 0.7))

        if not theme:
            return jsonify({"error": "Theme is required"}), 400

        user_prompt = (
            f'Generate exactly 10 RGB tuples as a Python list that fully embodies the theme "{theme}". '
            f'Each color must be highly representative of this theme, avoiding unnecessary variety. '
            f'If the theme is known for specific colors (e.g., camouflage = shades of green/brown), ensure the output maintains that consistency. '
            f'Do NOT introduce unrelated colors—every color must strongly reinforce the theme. '
            f'Repeat colors when appropriate rather than adding extra variety. '
            f'Return ONLY the list, with NO extra text, formatting, explanations, or symbols. '
        )


        result = query_api(user_prompt, temperature=temp)
        raw_result = result

        # Extract list of RGB values
        match = re.search(r"\[\s*\[\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\](?:\s*,\s*\[\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\]){9}\s*\]", result)

        status = "Fail"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        led_pattern = None

        if match:
            list_str = match.group()
            try:
                led_pattern = ast.literal_eval(list_str)  # Convert to Python list
                if len(led_pattern) == 10 and all(isinstance(color, list) and len(color) == 3 for color in led_pattern):
                    status = "Pass"

                    # Write to JSON file
                    with open("led_pattern.json", "w") as json_file:
                        json.dump(led_pattern, json_file, indent=4)
                else:
                    led_pattern = "Validation Error: Expected exactly 10 RGB tuples."
            except (SyntaxError, ValueError) as e:
                led_pattern = f"Parsing Error: {str(e)}"
        else:
            led_pattern = "Format Error: Could not find valid RGB pattern."

        LAST_RESULT = {"status": status, "timestamp": timestamp, "raw_output": result}

        response_data = {
            "led_pattern": led_pattern if status == "Pass" else None,
            "status": status,
            "timestamp": timestamp,
            "raw_output": raw_result,
            "formatted_output": json.dumps(led_pattern, indent=4) if status == "Pass" else None,
            "metadata": {
                "theme": theme,
                "temperature": temp,
                "api_response_length": len(raw_result)
            }
        }

        # Redirect for HTML requests
        accept_header = request.headers.get("Accept", "")
        if "text/html" in accept_header or "application/x-www-form-urlencoded" in request.content_type:
            return redirect("https://markoviandevelopments.com/other_projects/led_app/led_app.html")

        return jsonify(response_data)

    return render_template("led_index.html", last_result=LAST_RESULT)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5047, debug=True)
