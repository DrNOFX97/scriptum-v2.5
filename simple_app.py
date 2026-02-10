"""
Minimal Flask app for testing Render deployment.
"""
from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'message': 'Minimal app running',
        'port': os.environ.get('PORT', 'not set')
    })

@app.route('/')
def home():
    return jsonify({'message': 'Hello from Scriptum minimal API'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)
