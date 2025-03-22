from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
import os
from dotenv import load_dotenv
from flask import send_from_directory

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Change this to a secure value!

# Load environment variables
load_dotenv()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

FLEETS_FILE = "fleets.json"

# Function to load fleet data
def load_fleets():
    try:
        with open(FLEETS_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# Function to save fleet data
def save_fleets(fleets):
    with open(FLEETS_FILE, "w") as file:
        json.dump(fleets, file, indent=4)

# -------------------- Routes --------------------


@app.route('/fleets.json')
def serve_fleets():
    return send_from_directory('.', 'fleets.json') 

# Home page (Public search page)
@app.route("/")
def home():
    return render_template("index.html")

# Admin login page
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password")

        if password == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("admin"))
        else:
            return render_template("login.html", error="Invalid password!")

    return render_template("login.html")

# Admin Fleet Editor Page (Protected)
@app.route("/admin")
def admin():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template("admin.html")

# API - Get Fleet Data
@app.route("/api/fleets", methods=["GET"])
def get_fleets():
    return jsonify(load_fleets())

# API - Add a new fleet entry
@app.route("/api/add_fleet", methods=["POST"])
def add_fleet():
    if not session.get("logged_in"):
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    if not request.is_json:
        return jsonify({"success": False, "error": "Invalid JSON format"}), 400

    fleet = request.get_json()
    
    # Ensure fleet has necessary fields
    required_fields = ["fleetNumber", "reg", "previousReg", "vehicleType", "livery", "operator"]
    if not all(field in fleet for field in required_fields):
        return jsonify({"success": False, "error": "Missing fields"}), 400

    fleets = load_fleets()
    fleets.append(fleet)
    save_fleets(fleets)
    
    return jsonify({"success": True, "message": "Fleet added successfully"})

# API - Update an existing fleet entry
@app.route("/api/update_fleet", methods=["POST"])
def update_fleet():
    if not session.get("logged_in"):
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    if not request.is_json:
        return jsonify({"success": False, "error": "Invalid JSON format"}), 400

    data = request.get_json()
    index = data.get("index")
    updated_fleet = data.get("updatedFleet")

    if index is None or updated_fleet is None:
        return jsonify({"success": False, "error": "Missing index or fleet data"}), 400

    fleets = load_fleets()
    if not (0 <= index < len(fleets)):
        return jsonify({"success": False, "error": "Fleet not found"}), 404

    fleets[index] = updated_fleet
    save_fleets(fleets)
    
    return jsonify({"success": True, "message": "Fleet updated successfully"})

# API - Delete a fleet entry
@app.route("/api/delete_fleet", methods=["POST"])
def delete_fleet():
    if not session.get("logged_in"):
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    if not request.is_json:
        return jsonify({"success": False, "error": "Invalid JSON format"}), 400

    data = request.get_json()
    index = data.get("index")

    if index is None:
        return jsonify({"success": False, "error": "Missing index"}), 400

    fleets = load_fleets()
    if not (0 <= index < len(fleets)):
        return jsonify({"success": False, "error": "Fleet not found"}), 404

    del fleets[index]
    save_fleets(fleets)
    
    return jsonify({"success": True, "message": "Fleet deleted successfully"})

# API - Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
