from flask import Flask, render_template, request, jsonify
import requests
import ast
import re
import json
import datetime

app = Flask(__name__)

API_URL = "http://50.188.120.138:5049/api/deepseek"  # Modify if necessary
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

        answer = data.get("response", "").strip()
        answer = re.sub(r"<think>.*?</think>", "", answer, flags=re.DOTALL).strip()

        return answer if answer else "No response received."
    
    except requests.RequestException as e:
        return f"Error: {e}"

@app.route("/", methods=["GET", "POST"])
def index():
    global LAST_RESULT

    if request.method == "POST":
        theme = request.form.get("theme")
        temp = float(request.form.get("temperature", 0.7))

        user_prompt = (
            f'Please generate a set of 2 dimensional arrays for the use of lighting up some LEDs. '
            f'Make the theme: {theme}. Each array should be IMMEDIATELY preceeded by an "@" symbol '
            f'and be 10 items long. Such as, for example, "@[[255, 255, 255], [225, 235, 115], ..., [0, 124, 42]]". '
            f'Value in each tuple should be between 0 and 255, inclusive. Ten tuples long a piece. Go China!'
        )

        result = query_api(user_prompt, temperature=temp)
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

        return jsonify({
            "led_pattern": led_pattern if status == "Pass" else None,
            "status": status,
            "timestamp": timestamp,
            "raw_output": result
        })

    return render_template("led_index.html", last_result=LAST_RESULT)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5047, debug=True)
