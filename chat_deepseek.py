from flask import Flask, request, jsonify
from flask_cors import CORS
import ollama
import json
import os

app = Flask(__name__)
CORS(app)

CHAT_FILE = "chat_sessions.json"

# Load stored sessions from file
def load_chat_sessions():
    if os.path.exists(CHAT_FILE):
        with open(CHAT_FILE, "r") as f:
            return json.load(f)
    return {}

# Save sessions to file
def save_chat_sessions():
    with open(CHAT_FILE, "w") as f:
        json.dump(chat_sessions, f, indent=4)

# Initialize chat session storage
chat_sessions = load_chat_sessions()

@app.route('/chat', methods=['POST'])
def chat():
    session_id = request.json.get('session_id', 'default')
    user_input = request.json.get('message', '')

    if not user_input:
        return jsonify({"error": "Empty message"}), 400

    # Ensure session exists
    if session_id not in chat_sessions:
        chat_sessions[session_id] = []

    # Retrieve the last 15 exchanges (adjustable for token limit)
    session_chat = chat_sessions[session_id][-15:]  
    formatted_history = "\n".join([f"{msg['role']}: {msg['message']}" for msg in session_chat])

    # Construct prompt with history
    full_prompt = f"""
    The following is an ongoing conversation. Here is the recent chat history:
    {formatted_history}

    User: {user_input}
    Assistant:
    """

    # Generate response from DeepSeek R1
    response = ollama.generate(model="deepseek-r1:7b", prompt=full_prompt)['response']

    # Store the conversation
    chat_sessions[session_id].append({"role": "user", "message": user_input})
    chat_sessions[session_id].append({"role": "assistant", "message": response})
    save_chat_sessions()

    return jsonify({"response": response, "history": chat_sessions[session_id]})

@app.route('/history', methods=['GET'])
def get_history():
    session_id = request.args.get('session_id', 'default')
    return jsonify({"history": chat_sessions.get(session_id, [])})

@app.route('/clear', methods=['POST'])
def clear_chat():
    session_id = request.json.get('session_id', 'default')
    chat_sessions[session_id] = []  # Clear chat history for that session
    save_chat_sessions()
    return jsonify({"message": "Chat history cleared."})

@app.route('/sessions', methods=['GET'])
def get_sessions():
    return jsonify({"sessions": list(chat_sessions.keys())})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True)
