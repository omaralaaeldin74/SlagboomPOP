from flask import Flask, request, jsonify
from flask_cors import CORS  
from datetime import datetime
import pyodbc
from dotenv import load_dotenv
import os

load_dotenv()

# Flask app
app = Flask(__name__)
CORS(app)  


def create_connection():
    try:
        connection = pyodbc.connect(
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={os.getenv('DB_HOST')};"
            f"DATABASE={os.getenv('DB_NAME')};"
            f"UID={os.getenv('DB_USER')};"
            f"PWD={os.getenv('DB_PASSWORD')};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
            f"Connection Timeout=30;"
        )
        print("Succesvolle databaseverbinding.")
        return connection
    except pyodbc.Error as e:
        print(f"Fout bij verbinden met de database: {e}")
        return None


def check_api_key():
    api_key = request.headers.get("X-API-Key")
    if api_key != os.getenv("API_KEY"):
        print("Ongeldige API-key.")
        return False
    return True

@app.route('/api/slagboom', methods=['POST'])
def handle_slagboom():
    if not check_api_key():
        return jsonify({"status": "failed", "message": "Unauthorized"}), 401

    data = request.json
    kenteken = data.get("kenteken")
    if not kenteken:
        return jsonify({"status": "failed", "message": "Kenteken is verplicht"}), 400

    connection = create_connection()
    if connection is None:
        return jsonify({"status": "failed", "message": "Kan geen verbinding maken met de database"}), 500

    try:
        cursor = connection.cursor()

        cursor.execute("SELECT KentekenID, EigenaarNaam FROM dbo.Kentekens WHERE Kenteken = ?", kenteken)
        result = cursor.fetchone()

        if not result:
            return jsonify({"status": "failed", "message": f"Kenteken {kenteken} is niet toegestaan"}), 403

        kenteken_id, eigenaar_naam = result

        
        cursor.execute("SELECT Actie FROM dbo.Logboek WHERE KentekenID = ? ORDER BY Tijdstip DESC", kenteken_id)
        laatste_actie = cursor.fetchone()

        nieuwe_actie = "binnengekomen" if not laatste_actie or laatste_actie[0] == "vertrokken" else "vertrokken"

       
        cursor.execute(
            "INSERT INTO dbo.Logboek (KentekenID, EigenaarNaam, Actie, Tijdstip) VALUES (?, ?, ?, ?)",
            (kenteken_id, eigenaar_naam, nieuwe_actie, datetime.now())
        )
        connection.commit()

        return jsonify({"status": "success", "message": f"{eigenaar_naam} is succesvol {nieuwe_actie}."}), 200

    except Exception as e:
        return jsonify({"status": "failed", "message": f"Fout bij verwerking: {e}"}), 500
    finally:
        connection.close()

@app.route('/api/logboek', methods=['GET'])
def logboek():
    if not check_api_key():
        return jsonify({"status": "failed", "message": "Unauthorized"}), 401

    connection = create_connection()
    if connection is None:
        return jsonify({"status": "failed", "message": "Kan geen verbinding maken met de database"}), 500

    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT l.LogboekID, k.Kenteken, l.EigenaarNaam, l.Actie, l.Tijdstip
            FROM dbo.Logboek l
            LEFT JOIN dbo.Kentekens k ON l.KentekenID = k.KentekenID
            ORDER BY l.Tijdstip DESC
        """)
        logboek = cursor.fetchall()

        return jsonify([
            {
                "logboek_id": row[0],
                "kenteken": row[1],
                "eigenaar_naam": row[2],
                "actie": row[3],
                "tijdstip": row[4].strftime('%Y-%m-%d %H:%M:%S')
            }
            for row in logboek
        ])

    except Exception as e:
        print(f"Fout bij ophalen logboek: {e}")
        return jsonify({"status": "failed", "message": "Fout bij ophalen logboek"}), 500
    finally:
        connection.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=4000)

