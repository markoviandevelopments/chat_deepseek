import requests
import re
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

# Forward requests to the local api_deepseek server
API_URL = "http://localhost:5049/api/deepseek"

@app.route("/api/deepseek", methods=["GET"])
def query_api():
    prompt = request.args.get("prompt")
    temperature = float(request.args.get("temperature", 0.7))

    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400

    try:
        response = requests.get(API_URL, params={"prompt": prompt, "temperature": temperature}, timeout=10)
        response.raise_for_status()
        data = response.json()
        answer = data.get("response", "").strip()
        answer = re.sub(r"<think>.*?</think>", "", answer, flags=re.DOTALL).strip()
        return jsonify({"response": answer})
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5049, debug=False)