from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import os
from flask_cors import CORS

load_dotenv()

API_KEY = os.getenv("API_KEY")

app = Flask(__name__)
CORS(app)

def validate_api_key():
    api_key = request.headers.get('X-API-Key')
    if api_key != API_KEY:
        return jsonify({"message": "Unauthorized", "status": "failed"}), 401

@app.route('/guest', methods=['GET'])
def guest_page():
    validation_response = validate_api_key()
    if validation_response:
        return validation_response
    return render_template('guest.html')

@app.route('/admin', methods=['GET'])
def admin_page():
    validation_response = validate_api_key()
    if validation_response:
        return validation_response
    return render_template('admin.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
