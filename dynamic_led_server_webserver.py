from flask import Flask, request, jsonify, redirect, url_for
from flask_socketio import SocketIO, emit
import os
import requests
import re
import json
import datetime
import ast
from flask_cors import CORS
import mysql.connector
import threading
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_url_path="/leds/static")
app.config["APPLICATION_ROOT"] = "/leds"

socketio = SocketIO(app, cors_allowed_origins="https://markovianchats.duckdns.org")

CORS(app)

API_URL = "http://50.188.120.138:5049/api/deepseek"
LAST_RESULT = {"status": "No request yet", "timestamp": None, "raw_output": "", "think_content": ""}
ANIMATION_DATA = {"frames": [], "frame_rate": 0.1, "type": "static"}  # Frames and rate in seconds
animation_lock = threading.Lock()

db_config = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "log_user"),
    "password": os.getenv("DB_PASSWORD", "Not$erp011"),
    "database": os.getenv("DB_NAME", "client_logs_db")
}

def get_db_connection():
    try:
        return mysql.connector.connect(**db_config)
    except mysql.connector.Error as e:
        logger.error(f"Database Connection Error: {e}")
        return None

def query_api(user_prompt, temperature=0.7):
    params = {"prompt": user_prompt, "temperature": temperature}
    try:
        response = requests.get(API_URL, params=params, timeout=10)  # Add timeout
        response.raise_for_status()
        return response.json().get("response", "").strip() or "No response received."
    except requests.RequestException as e:
        logger.error(f"API Request Error: {e}")
        return f"Error: {e}"
    
def emit_animation():
    """Background task to emit animation frames via WebSocket."""
    global ANIMATION_DATA
    while True:
        with animation_lock:
            if ANIMATION_DATA["frames"]:
                if ANIMATION_DATA["type"] == "static":
                    socketio.emit("led_update", {"pattern": ANIMATION_DATA["frames"][0]})
                    logger.debug(f"Emitted static frame: {ANIMATION_DATA['frames'][0]}")
                    socketio.sleep(5)
                elif ANIMATION_DATA["type"] == "animated":
                    for frame in ANIMATION_DATA["frames"]:
                        socketio.emit("led_update", {"pattern": frame})
                        logger.debug(f"Emitted animated frame: {frame}")
                        socketio.sleep(ANIMATION_DATA["frame_rate"])
            else:
                socketio.sleep(1)

socketio.start_background_task(emit_animation)

@app.route("/leds", methods=["GET", "POST"])
def index():
    global LAST_RESULT, ANIMATION_DATA

    if request.method == "POST":
        request_data = request.get_json() if request.is_json else request.form
        theme = request_data.get("theme")
        temp = float(request_data.get("temperature", 0.7))
        pattern_type = request_data.get("pattern_type", "static")

        if not theme:
            return jsonify({"error": "Theme is required"}), 400
        
        prompt_templates = {
            "static": (
                f'Generate exactly 10 RGB tuples as a Python list that fully embodies the theme "{theme}". '
                f'Each color must be highly representative of this theme, avoiding unnecessary variety. '
                f'If the theme is known for specific colors (e.g., camouflage = shades of green/brown), ensure the output maintains that consistency. '
                f'Do NOT introduce unrelated colors—every color must strongly reinforce the theme. '
                f'Repeat colors when appropriate rather than adding extra variety. '
                f'Return ONLY the list, with NO extra text, formatting, explanations, or symbols. '
                f'The response must strictly be formatted as: @[[R, G, B], [R, G, B], ..., [R, G, B]].'
            ),
            "animated": (
                f'Generate an LED animation sequence for the theme "{theme}". '
                f'Return a Python dict with: '
                f'- "frames": a list of at least 5 frames, each frame being a list of exactly 10 RGB tuples ([R, G, B]), '
                f'  where colors strongly embody the theme with smooth transitions or dynamic patterns (e.g., waves, pulses). '
                f'- "frame_rate": a float (seconds per frame, between 0.05 and 1.0) to control animation speed. '
                f'Ensure all colors reinforce the theme consistently. '
                f'Return ONLY the dict, formatted as: @{{"frames": [[[...], [...]], ...], "frame_rate": float}}.'
            )
        }
        user_prompt = prompt_templates.get(pattern_type, "static")

        ip_address = request.remote_addr
        result = query_api(user_prompt, temperature=temp)
        raw_result = result

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        led_data, status = None, "Fail"

        # Extract <think> section if present (for logging or display)
        think_match = re.search(r'<think>.*?</think>', raw_result, re.DOTALL)
        think_content = think_match.group(0) if think_match else "No thinking process provided."
        logger.debug(f"Thinking process: {think_content}")

        # Clean result by removing <think> to focus on the list
        cleaned_result = re.sub(r'<think>.*?</think>', '', raw_result, flags=re.DOTALL).strip()

        if pattern_type == "static":
            match = re.search(r"@\[.*?\]", cleaned_result, re.DOTALL)
            if match:
                try:
                    raw_list = match.group(0)[1:]  # Remove '@'
                    logger.debug(f"Raw list from API: {raw_list}")
                    parsed_data = ast.literal_eval(raw_list)
                    logger.debug(f"Parsed data: {parsed_data}")
                    # Handle the extra nesting level (list of one list)
                    if isinstance(parsed_data, list) and len(parsed_data) == 1:
                        inner_list = parsed_data[0]
                    else:
                        inner_list = parsed_data
                    # Flatten the list if it contains pairs of tuples
                    flat_list = []
                    for item in inner_list:
                        if isinstance(item, list) and len(item) == 2 and all(len(t) == 3 for t in item):
                            flat_list.extend(item)  # Unpack [red_tuple, pink_tuple] into individual tuples
                        elif len(item) == 3 and all(0 <= v <= 255 for v in item):
                            flat_list.append(item)  # Single tuple
                        else:
                            logger.warning(f"Invalid item in inner list: {item}")
                    logger.debug(f"Flattened list: {flat_list}")
                    if len(flat_list) == 10 and all(len(t) == 3 and all(0 <= v <= 255 for v in t) for t in flat_list):
                        led_data = flat_list
                        status = "Pass"
                        with animation_lock:
                            ANIMATION_DATA = {"frames": [led_data], "frame_rate": 0.1, "type": "static"}
                    else:
                        led_data = f"Validation Error: Expected exactly 10 RGB tuples with values 0-255, got {len(flat_list)}"
                        logger.error(led_data)
                except Exception as e:
                    led_data = f"Parsing Error: {e}"
                    logger.error(led_data)
            else:
                led_data = "Format Error: No valid static pattern found"
                logger.error(f"No match found in cleaned result: {cleaned_result}")
                
        elif pattern_type == "animated":
            match = re.search(r'@\{.*"frames":\s*\[.*\],\s*"frame_rate":\s*[0-1]?\.\d+\}', cleaned_result, re.DOTALL)
            if match:
                try:
                    led_data = ast.literal_eval(match.group(0)[1:])  # Remove '@'
                    frames, frame_rate = led_data["frames"], led_data["frame_rate"]
                    if (len(frames) >= 5 and 
                        all(len(f) == 10 and all(len(c) == 3 and all(0 <= v <= 255 for v in c) for c in f) for f in frames) and 
                        0.05 <= frame_rate <= 1.0):
                        status = "Pass"
                        with animation_lock:
                            ANIMATION_DATA = {"frames": frames, "frame_rate": frame_rate, "type": "animated"}
                    else:
                        led_data = "Validation Error: Invalid frames or frame_rate"
                except Exception as e:
                    led_data = f"Parsing Error: {e}"
            else:
                led_data = "Format Error: No valid animation data found"

        logger.debug(f"Writing to led_pattern.json: {json.dumps({
            'pattern_type': pattern_type,
            'generated_at': timestamp,
            'data': led_data if status == "Pass" else None,
            'validation_status': status,
            'think_content': think_content if think_content != "No thinking process provided." else None
        }, indent=4)}")

        with open("led_pattern.json", "w") as json_file:
            json.dump({
                "pattern_type": pattern_type,
                "generated_at": timestamp,
                "data": led_data if status == "Pass" else None,
                "validation_status": status,
                "think_content": think_content if think_content != "No thinking process provided." else None
            }, json_file, indent=4)

        # Update LAST_RESULT with think_content
        LAST_RESULT = {
            "status": status,
            "timestamp": timestamp,
            "raw_output": raw_result,
            "pattern_type": pattern_type,
            "think_content": think_content if think_content != "No thinking process provided." else None,
            "data": led_data if status == "Pass" else None
        }

        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO led_history (timestamp, prompt, theme, temperature, ip_address, pattern_generated, 
                                                pattern_type, api_response_length, status, raw_output, think_content)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (timestamp, user_prompt, theme, temp, ip_address,
                        json.dumps(led_data) if led_data else None, pattern_type,
                        len(raw_result), status, raw_result,
                        think_content if think_content != "No thinking process provided." else None)
                    )
                conn.commit()
            except mysql.connector.Error as e:
                logger.error(f"Database Insert Error: {e}")
            finally:
                conn.close()

        return jsonify(LAST_RESULT)

    return jsonify(LAST_RESULT)

@app.route('/')
def redirect_to_leds():
    try:
        return app.send_static_file('led_app.html')  # Serve the frontend
    except FileNotFoundError:
        return jsonify({"error": "Frontend file led_app.html not found in static folder"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5047, debug=True)