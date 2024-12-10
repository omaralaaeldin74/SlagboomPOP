from flask import Flask, request, jsonify
import mysql.connector
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)  # CORS toestaan voor alle routes

# Database configuratie (vervang de placeholders door je eigen gegevens)
DB_HOST = "newyork.mysql.database.azure.com"
DB_NAME = "reservations"
DB_USER = "dbadmin"  # Bijvoorbeeld "dbadmin@jouw-database-host"
DB_PASSWORD = "Q#604664456957uf"  # Vervang dit door je echte wachtwoord

# Helper: Maak een databaseverbinding
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return connection
    except mysql.connector.Error as e:
        print(f"Fout bij verbinding maken: {e}")
        raise e

# Helper: Valideer API Key
CONFIG2_FILE = "config2.json"

def validate_api_key():
    try:
        with open(CONFIG2_FILE, "r") as file:
            config = json.load(file)
        api_key = request.headers.get("X-API-KEY")
        if api_key and api_key == config.get("api_key"):
            return True
        else:
            return False
    except FileNotFoundError:
        return False

# API: Handle Slagboom
@app.route('/slagboom', methods=['POST'])

def handle_slagboom():
    if not validate_api_key():
        return jsonify({"status": "failed", "message": "Ongeldige API-sleutel"}), 403

    data = request.json
    kenteken = data.get("kenteken")

    if not kenteken:
        return jsonify({"status": "failed", "message": "Kenteken is verplicht"}), 400

    connection = get_db_connection()
    if not connection:
        return jsonify({"status": "failed", "message": "Databaseverbinding mislukt"}), 500

    cursor = connection.cursor(dictionary=True)

    try:
        # Controleer of het kenteken bestaat
        cursor.execute("SELECT * FROM kentekens WHERE kenteken = %s", (kenteken,))
        kenteken_data = cursor.fetchone()

        if not kenteken_data:
            return jsonify({"status": "failed", "message": "Kenteken niet gevonden"}), 404

        # Controleer de laatste actie van dit kenteken
        cursor.execute(
            "SELECT actie FROM logboek WHERE kenteken = %s ORDER BY tijdstip DESC LIMIT 1",
            (kenteken,)
        )
        last_entry = cursor.fetchone()

        # Bepaal de volgende actie (binnenkomst of vertrek)
        actie = "binnengekomen" if not last_entry or last_entry["actie"] == "vertrokken" else "vertrokken"

        # Voeg een nieuwe logboekvermelding toe
        cursor.execute(
            "INSERT INTO logboek (kenteken, actie, tijdstip) VALUES (%s, %s, NOW())",
            (kenteken, actie)
        )
        connection.commit()

        return jsonify({"status": "success", "message": f"Kenteken {kenteken} is succesvol {actie}."}), 200
    except Exception as e:
        print(f"Fout tijdens verwerking: {e}")
        return jsonify({"status": "failed", "message": str(e)}), 500
    finally:
        cursor.close()
        connection.close()

# API: Ophalen van het logboek
@app.route('/logboek', methods=['GET'])
def get_logbook():
    if not validate_api_key():
        return jsonify({"status": "failed", "message": "Ongeldige API-sleutel"}), 403

    connection = get_db_connection()
    if not connection:
        return jsonify({"status": "failed", "message": "Databaseverbinding mislukt"}), 500

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM logboek ORDER BY tijdstip DESC")
        logbook_entries = cursor.fetchall()
        return jsonify(logbook_entries), 200
    except Exception as e:
        print(f"Fout bij ophalen logboek: {e}")
        return jsonify({"status": "failed", "message": str(e)}), 500
    finally:
        cursor.close()
        connection.close()

if __name__ == '__main__':
    app.run(debug=True, port=4000)  # API draait op poort 4000
