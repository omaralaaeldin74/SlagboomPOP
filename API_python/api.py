from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine, text
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# Azure Key Vault configuratie
try:
    vault_url = "https://abudhabi.vault.azure.net/" 
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=vault_url, credential=credential)

    # Geheimen ophalen uit Key Vault
    DB_HOST = client.get_secret("DB_HOST").value
    DB_NAME = client.get_secret("DB_NAME").value
    DB_USER = client.get_secret("DB_USER").value
    DB_PASSWORD = client.get_secret("DB_PASSWORD").value
    API_KEY = client.get_secret("API_KEY").value
except Exception as e:
    raise RuntimeError(f"Fout bij het ophalen van geheimen uit Azure Key Vault: {e}")

# SQLAlchemy Engine met pyodbc
connection_string = f"mssql+pyodbc://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}?driver=ODBC+Driver+17+for+SQL+Server"
engine = create_engine(connection_string)

# Flask app
app = Flask(__name__)
CORS(app)

# Functie om API-sleutel te valideren
def check_api_key():
    api_key = request.headers.get("X-API-Key")
    if not api_key or api_key != API_KEY:
        return jsonify({"status": "failed", "message": "Unauthorized"}), 401
    return None

@app.route('/api/slagboom', methods=['POST'])
def handle_slagboom():
    validation_response = check_api_key()
    if validation_response:
        return validation_response

    data = request.json
    kenteken = data.get("kenteken")
    if not kenteken:
        return jsonify({"status": "failed", "message": "Kenteken is verplicht"}), 400

    try:
        with engine.connect() as conn:
            # Controleer kenteken
            result = conn.execute(
                text("SELECT KentekenID, EigenaarNaam FROM dbo.Kentekens WHERE Kenteken = :kenteken"),
                {"kenteken": kenteken}
            ).fetchone()

            if not result:
                return jsonify({"status": "failed", "message": f"Kenteken {kenteken} is niet toegestaan"}), 403

            kenteken_id, eigenaar_naam = result

            # Controleer laatste actie
            laatste_actie = conn.execute(
                text("SELECT Actie FROM dbo.Logboek WHERE KentekenID = :kenteken_id ORDER BY Tijdstip DESC"),
                {"kenteken_id": kenteken_id}
            ).fetchone()

            nieuwe_actie = "binnengekomen" if not laatste_actie or laatste_actie[0] == "vertrokken" else "vertrokken"

            # Voeg nieuwe actie toe
            conn.execute(
                text(
                    "INSERT INTO dbo.Logboek (KentekenID, EigenaarNaam, Actie, Tijdstip) "
                    "VALUES (:kenteken_id, :eigenaar_naam, :actie, GETDATE())"
                ),
                {"kenteken_id": kenteken_id, "eigenaar_naam": eigenaar_naam, "actie": nieuwe_actie}
            )

            return jsonify({"status": "success", "message": f"{eigenaar_naam} is succesvol {nieuwe_actie}."}), 200

    except Exception as e:
        return jsonify({"status": "failed", "message": f"Fout bij verwerking: {e}"}), 500

@app.route('/api/logboek', methods=['GET'])
def logboek():
    validation_response = check_api_key()
    if validation_response:
        return validation_response

    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT l.LogboekID, k.Kenteken, l.EigenaarNaam, l.Actie, l.Tijdstip "
                    "FROM dbo.Logboek l LEFT JOIN dbo.Kentekens k ON l.KentekenID = k.KentekenID "
                    "ORDER BY l.Tijdstip DESC"
                )
            ).fetchall()

            logboek = [
                {
                    "logboek_id": row[0],
                    "kenteken": row[1],
                    "eigenaar_naam": row[2],
                    "actie": row[3],
                    "tijdstip": row[4].strftime('%Y-%m-%d %H:%M:%S')
                }
                for row in result
            ]

            return jsonify(logboek)

    except Exception as e:
        return jsonify({"status": "failed", "message": f"Fout bij ophalen logboek: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=4000)
