from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import ollama
import json
import os

os.environ["OLLAMA_ACCELERATOR"] = "cuda"

has_printed_cuda = False

app = Flask(__name__, static_folder='static')
CORS(app, resources={r"/*": {"origins": "https://markoviandevelopments.com"}})

CHAT_FILE = "chat_history.json"

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

    # Generate response using DeepSeek-R1
    response = ollama.generate(
        model="deepseek-r1:7b",
        prompt=user_input
    )['response']

    # Store DeepSeek's response
    chat_history.append({"role": "assistant", "message": response})
    save_chat_history()

    return jsonify({"response": response, "history": chat_history})


@app.route('/history', methods=['GET'])
def get_history():
    return jsonify({"history": chat_history})

@app.route('/clear', methods=['POST'])
def clear_chat():
    global chat_history
    chat_history = []  # Clear chat history
    save_chat_history()  # Overwrite file with empty chat
    return jsonify({"message": "Chat history cleared."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True)
