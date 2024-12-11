from flask import Flask, request, jsonify
from datetime import datetime
import json
from flask_cors import CORS
app = Flask(__name__)
CORS(app) 
CONFIG2_FILE = "config2.json"
DB_FILE = "db.json"
def load_config(file_path):
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"{file_path} not found. Ensure the file exists.")
        return {}
    except json.JSONDecodeError:
        print(f"Error decoding {file_path}. Check for syntax errors.")
        return {}
CONFIG2 = load_config(CONFIG2_FILE)
def validate_api_key():
    api_key = request.headers.get("X-API-KEY")
    expected_key = CONFIG2.get("api_key")
    if not expected_key:
        print("API key is not properly loaded from config2.json")
        return False
    if not api_key:
        print("API key is missing in the request header")
        return False
    if api_key != expected_key:
        print(f"Invalid API key provided: {api_key}")
        return False
    return True
def read_database():
    try:
        with open(DB_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"{DB_FILE} not found. Creating a new database file.")
        write_database({"logboek": [], "kentekens": {}})
        return {"logboek": [], "kentekens": {}}
    except json.JSONDecodeError as e:
        print(f"Error decoding {DB_FILE}: {e}")
        return {"logboek": [], "kentekens": {}}
def write_database(data):
    with open(DB_FILE, "w") as file:
        json.dump(data, file, indent=4)
def read_logbook():
    db = read_database()
    return db.get("logboek", [])
def write_log_entry(entry):
    db = read_database()
    logbook = db.get("logboek", [])
    logbook.append(entry)
    db["logboek"] = logbook
    write_database(db)
def read_license_plates():
    db = read_database()
    return db.get("kentekens", {})
SLAGBOOM_STATUS = {
    "binnenkomst": "closed",
    "vertrek": "closed"
}
@app.route('/slagboom', methods=['POST'])
def handle_slagboom():
    if not validate_api_key():
        return jsonify({"status": "failed", "message": "Ongeldige API-sleutel"}), 403
    data = request.json
    kenteken = data.get("kenteken")
    if not kenteken:
        return jsonify({"status": "failed", "message": "Kenteken is verplicht"}), 400
    
    logboek = read_logbook()
    actie = "binnengekomen"
   
    for entry in reversed(logboek):
        if entry["kenteken"] == kenteken and entry["actie"] == "binnengekomen":
            actie = "vertrokken"
            break
    kentekens = read_license_plates()
    gastnaam = kentekens.get(kenteken)
    if gastnaam:
        SLAGBOOM_STATUS["binnenkomst" if actie == "binnengekomen" else "vertrek"] = "opened"
        log_entry = {
            "gastnaam": gastnaam,
            "kenteken": kenteken,
            "actie": actie,
            "tijdstip": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        write_log_entry(log_entry)
        return jsonify({"status": "success", "message": f"{gastnaam} is succesvol {actie}."}), 200
    return jsonify({"status": "failed", "message": "Ongeldig kenteken"}), 403
@app.route('/logboek', methods=['GET'])
def logboek():
    if not validate_api_key():
        return jsonify({"status": "failed", "message": "Ongeldige API-sleutel"}), 403
    return jsonify(read_logbook())
if __name__ == '__main__':
    app.run(debug=True, port=4000)  