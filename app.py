from flask import Flask, render_template, request, jsonify
import mysql.connector
from dotenv import load_dotenv
import os
from datetime import datetime

# Laad configuratie uit .env
load_dotenv()

# Configuratie
DB_HOST = os.getenv("DB_HOST", "newyork.mysql.database.azure.com")
DB_NAME = os.getenv("DB_NAME", "reservations")
DB_USER = os.getenv("DB_USER", "dbadmin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Q#604664456957uf")

app = Flask(__name__)


def create_connection():
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            ssl_disabled=False
        )
        return connection
    except mysql.connector.Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

@app.route('/')
def admin_page():
    connection = create_connection()
    if connection is None:
        return "Kan geen verbinding maken met de database", 500

    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM logboek ORDER BY tijdstip DESC")
    logboek = cursor.fetchall()
    connection.close()

    return render_template('admin.html', logboek=logboek)

@app.route('/guest', methods=['GET', 'POST'])
def guest_page():
    if request.method == 'GET':
        return render_template('guest.html')

    if request.method == 'POST':
        data = request.json
        kenteken = data.get("kenteken")
        if not kenteken:
            return jsonify({"status": "failed", "message": "Kenteken is verplicht"}), 400

        connection = create_connection()
        if connection is None:
            return jsonify({"status": "failed", "message": "Kan geen verbinding maken met de database"}), 500

        cursor = connection.cursor(dictionary=True)

     
        cursor.execute("SELECT gastnaam FROM kentekens WHERE kenteken = %s", (kenteken,))
        result = cursor.fetchone()

        if not result:
            connection.close()
            return jsonify({"status": "failed", "message": "Kenteken niet toegestaan"}), 403

        gastnaam = result['gastnaam']

       
        cursor.execute("SELECT actie FROM logboek WHERE kenteken = %s ORDER BY tijdstip DESC LIMIT 1", (kenteken,))
        laatste_actie = cursor.fetchone()

        nieuwe_actie = "binnengekomen" if not laatste_actie or laatste_actie["actie"] == "vertrokken" else "vertrokken"

      
        cursor.execute(
            "INSERT INTO logboek (kenteken, gastnaam, actie, tijdstip) VALUES (%s, %s, %s, %s)",
            (kenteken, gastnaam, nieuwe_actie, datetime.now())
        )
        connection.commit()
        connection.close()

        return jsonify({"status": "success", "message": f"Actie gelogd: {gastnaam} is {nieuwe_actie}"}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
