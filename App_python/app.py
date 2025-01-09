from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import os
from flask_cors import CORS

# Laad omgevingsvariabelen
load_dotenv()

# Haal API-sleutel uit .env
API_KEY = os.getenv("API_KEY")

# Controleer of de API-sleutel geladen is
if not API_KEY:
    raise ValueError("API_KEY ontbreekt in .env bestand!")

# Flask-app configuratie
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Pas "*" aan voor specifieke origins indien nodig

# Functie om API-sleutel te valideren
def validate_api_key():
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        app.logger.warning("Geen API-sleutel ontvangen in headers!")
        return jsonify({"message": "Unauthorized: No API key provided", "status": "failed"}), 401
    if api_key != API_KEY:
        app.logger.warning(f"Ongeldige API-sleutel ontvangen: {api_key}")
        return jsonify({"message": "Unauthorized: Invalid API key", "status": "failed"}), 401

# Logging voor debugging
@app.before_request
def log_request_info():
    app.logger.info(f"Ontvangen headers: {request.headers}")

# Routes
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
