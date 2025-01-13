from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# Azure Key Vault configuratie
try:
    vault_url = "https://abudhabi.vault.azure.net/"
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=vault_url, credential=credential)
    API_KEY = client.get_secret("API_KEY").value
except Exception as e:
    raise RuntimeError(f"Fout bij het ophalen van geheimen uit Azure Key Vault: {e}")

# Flask-app configuratie
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Functie om API-sleutel te valideren
def validate_api_key():
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        app.logger.warning("Geen API-sleutel ontvangen in headers!")
        return jsonify({"message": "Unauthorized: No API key provided", "status": "failed"}), 401
    if api_key != API_KEY:
        app.logger.warning(f"Ongeldige API-sleutel ontvangen: {api_key}")
        return jsonify({"message": "Unauthorized: Invalid API key", "status": "failed"}), 401

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
