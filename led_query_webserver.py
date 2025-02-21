from flask import Flask, render_template, request, jsonify, redirect
import requests
import ast
import re
import json
import datetime

app = Flask(__name__, static_url_path="/leds/static")
app.config["APPLICATION_ROOT"] = "/leds"

API_URL = "http://50.188.120.138:5049/api/deepseek"
LAST_RESULT = {"status": "No request yet", "timestamp": None, "raw_output": ""}

def query_api(user_prompt, temperature=0.7):
    params = {
        "prompt": user_prompt,
        "temperature": temperature
    }
    
    try:
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip() or "No response received."
    
    except requests.RequestException as e:
        return f"Error: {e}"

@app.route("/leds", methods=["GET", "POST"])
def index():
    global LAST_RESULT

    if request.method == "POST":
        # Handle both JSON and Form Data Requests
        if request.is_json:
            request_data = request.json
            theme = request_data.get("theme")
            temp = float(request_data.get("temperature", 0.7))
        else:
            theme = request.form.get("theme")
            temp = float(request.form.get("temperature", 0.7))

        if not theme:
            return jsonify({"error": "Theme is required"}), 400

        user_prompt = (
            f'Please generate an array of RGB tuples that aesthetically embody the theme "{theme}". '
            f'Values must be between 0-255. The array should be prefixed with "@", and contain exactly 10 RGB tuples. '
            f'Absolutely NO COMMENTS. Serve the role of a robot which has no other task than outputting this sequence, '
            f'and include no other text. '
        )

        result = query_api(user_prompt, temperature=temp)
        raw_result = result
        result_cleaned = result.replace("\n", "").replace(" ", "")

        indexx = result_cleaned.find("@[")
        status = "Fail"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        led_pattern = None

        if indexx != -1:
            for i in range(2, 1000):
                if result_cleaned[(indexx + i) : (indexx + i + 2)] == "]]":
                    break

            list_str = result_cleaned[(indexx + 1):(i + indexx + 2)]
            try:
                led_pattern = ast.literal_eval(list_str)
                if len(led_pattern) == 10 and all(len(item) == 3 for item in led_pattern):
                    with open("led_pattern.json", "w") as json_file:
                        json.dump(led_pattern, json_file, indent=4)
                    status = "Pass"
            except Exception as e:
                led_pattern = f"Parsing Error: {str(e)}"

        LAST_RESULT = {"status": status, "timestamp": timestamp, "raw_output": result}

        response_data = {
            "led_pattern": led_pattern if status == "Pass" else None,
            "status": status,
            "timestamp": timestamp,
            "raw_output": raw_result
        }

        accept_header = request.headers.get("Accept", "")
        if "text/html" in accept_header or "application/x-www-form-urlencoded" in request.content_type:
            return redirect("https://markoviandevelopments.com/other_projects/led_app/led_app.html")

        # **ESP or API Request → Return JSON**
        return jsonify(response_data)

    return render_template("led_index.html", last_result=LAST_RESULT)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5047, debug=True)
