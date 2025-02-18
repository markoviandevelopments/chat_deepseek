from flask import Flask, request, jsonify, make_response
import ollama
import os

app = Flask(__name__)

# Force CUDA acceleration for Ollama
os.environ["OLLAMA_ACCELERATOR"] = "cuda"

MODEL_NAME = "deepseek-r1:7b"

@app.route('/api/deepseek', methods=['GET', 'POST'])
def deepseek():
    """Handle GET and POST requests for DeepSeek."""
    
    if request.method == 'POST':
        data = request.get_json(silent=True) or request.form
        prompt = data.get('prompt', '')
        temperature = float(data.get('temperature', 0.7))  # Default to 0.7 if not provided
    else:
        prompt = request.args.get('prompt', '')
        temperature = float(request.args.get('temperature', 0.7))  # Default to 0.7 if not provided

    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400

    try:
        # Generate response from DeepSeek with temperature adjustment
        response = ollama.generate(
            model=MODEL_NAME,
            prompt=prompt,
            options={"temperature": temperature}  # Set temperature
        )
        return jsonify({'response': response['response']})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5049)
