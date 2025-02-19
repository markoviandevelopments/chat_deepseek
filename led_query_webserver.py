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
            f'Please generate an array for me to use to light up my individually addressable led strip in accordance 
            with the following theme: {theme}. The array should be formatted as follows, notice the nested rgb value tuples 
            as well as the "@" symbol. For use with WS2812B leds. They are RGB, not GRB. Keep that in mind alongside the 
            theme ({theme}), which should be weighted heavily. Example formatting (of course, the variables should be 
            filled in with actual values that bare no corolation to those presented here in your response): 
            @[[n, i, c], [b, f, g], ..., [w, b, b]]. There should be 100 tuples in your list. Thank you!'
        )

        result = query_api(user_prompt, temperature=temp)
        raw_result = result
        result = re.sub(r"<think>.*?</think>", "", result, flags=re.DOTALL).strip()
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
            "raw_output": raw_result
        })

    return render_template("led_index.html", last_result=LAST_RESULT)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5047, debug=True)
