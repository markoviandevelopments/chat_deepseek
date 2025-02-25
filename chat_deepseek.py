from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import ollama
import json
import os
import mysql.connector
import re

os.environ["OLLAMA_ACCELERATOR"] = "cuda"

has_printed_cuda = False

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "log_user"),
    "password": os.getenv("DB_PASSWORD", "Not$erp011"),
    "database": os.getenv("DB_NAME", "client_logs_db")
}

app = Flask(__name__, static_folder='static')
CORS(app, resources={r"/*": {"origins": "https://markoviandevelopments.com"}})

CHAT_FILE = "chat_history.json"

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# Load chat history from file (if exists)
def load_chat_history():
    if os.path.exists(CHAT_FILE):
        with open(CHAT_FILE, "r") as f:
            return json.load(f)
    return []

# Save chat history to file
def save_chat_history():
    with open(CHAT_FILE, "w") as f:
        json.dump(chat_history, f, indent=4)

def log_chat_message(session_id, user_ip, user_agent, role, message, context=None):
    db = get_db_connection()
    cursor = db.cursor()

    query = """
    INSERT INTO chat_logs (session_id, user_ip, user_agent, role, message, context)
    VALUES (%s, %s, %s, %s, %s, %s);
    """
    cursor.execute(query, (session_id, user_ip, user_agent, role, message, context))
    db.commit()

    cursor.close()
    db.close()

# Initialize chat history
chat_history = load_chat_history()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])

def chat():
    global has_printed_cuda
    global chat_history

    user_input = request.json.get('message', '')
    session_id = request.json.get('session_id', 'default')
    user_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent')

    if not user_input:
        return jsonify({"error": "Empty message"}), 400

    # Print CUDA status
    if not has_printed_cuda:
        cuda_status = os.environ.get("OLLAMA_ACCELERATOR", "Not set")
        print(f"🔥 CUDA Status: OLLAMA_ACCELERATOR={cuda_status}")
        has_printed_cuda = True

    # Add user's message immediately
    chat_history.append({"role": "user", "message": user_input})
    save_chat_history()

        # Log user's message
    log_chat_message(session_id, user_ip, user_agent, "user", user_input)

    # Generate response using DeepSeek-R1
    response = ollama.generate(
        model="deepseek-r1:7b",
        prompt=user_input
    )['response']

    # Store DeepSeek's response
    chat_history.append({"role": "assistant", "message": response})
    save_chat_history()

    filtered_response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()

    log_chat_message(session_id, user_ip, user_agent, "assistant", response)

    return jsonify({"response": filtered_response, "history": chat_history})


@app.route('/history', methods=['GET'])
def get_history():
    session_id = request.args.get('session_id', 'default')

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    query = "SELECT role, message, timestamp FROM chat_logs WHERE session_id = %s ORDER BY timestamp;"
    cursor.execute(query, (session_id,))
    chat_history = cursor.fetchall()

    cursor.close()
    db.close()

    return jsonify({"history": chat_history})

@app.route('/sessions', methods=['GET'])
def list_sessions():
    db = get_db_connection()
    cursor = db.cursor()

    query = "SELECT DISTINCT session_id FROM chat_logs;"
    cursor.execute(query)
    sessions = [row[0] for row in cursor.fetchall()]

    cursor.close()
    db.close()

    return jsonify({"sessions": sessions})

@app.route('/new_session', methods=['POST'])
def new_session():
    session_id = request.json.get('session_id')
    if not session_id:
        return jsonify({"error": "Session name required"}), 400

    db = get_db_connection()
    cursor = db.cursor()

    query = "INSERT INTO chat_logs (session_id, user_ip, user_agent, role, message) VALUES (%s, %s, %s, %s, %s);"
    cursor.execute(query, (session_id, "system", "server", "system", f"Session {session_id} created"))
    db.commit()

    cursor.close()
    db.close()

    return jsonify({"success": True})

@app.route('/clear', methods=['POST'])
def clear_chat():
    session_id = request.json.get('session_id', 'default')

    db = get_db_connection()
    cursor = db.cursor()

    query = "DELETE FROM chat_logs WHERE session_id = %s;"
    cursor.execute(query, (session_id,))
    db.commit()

    cursor.close()
    db.close()

    return jsonify({"message": f"Chat history cleared for session {session_id}."})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True)
