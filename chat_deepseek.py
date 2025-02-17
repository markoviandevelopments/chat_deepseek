from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import ollama

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

chat_history = []  # Store messages globally

@app.route('/')
def home():
    return render_template('index.html')  # Serve the chat UI

@app.route('/chat', methods=['POST'])
def chat():
    global chat_history

    user_input = request.json.get('message', '')

    if not user_input:
        return jsonify({"error": "Empty message"}), 400

    # Generate response using DeepSeek-R1
    response = ollama.generate(
        model="deepseek-r1:7b",
        prompt=user_input
    )['response']

    # Store conversation
    chat_history.append({"role": "user", "message": user_input})
    chat_history.append({"role": "assistant", "message": response})

    return jsonify({"response": response, "history": chat_history})

@app.route('/clear', methods=['POST'])
def clear_chat():
    global chat_history
    chat_history = []  # Clear chat history
    return jsonify({"message": "Chat history cleared."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True)
