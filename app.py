from flask import Flask, jsonify, request
from flask_cors import CORS
import random

app = Flask(__name__)
CORS(app)   # ✅ allow frontend access

# ----------------------------
# Test API (check connection)
# ----------------------------
@app.route("/api/test", methods=["GET"])
def test_api():
    return jsonify({"message": "Frontend connected to backend"})


# ----------------------------
# LOGIN API (Role-based)
# ----------------------------
@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    role = data.get("role")

    return jsonify({
        "message": "Login successful",
        "role": role
    })


# ----------------------------
# SENSOR DATA APIs
# ----------------------------
latest_sensor_data = {}

@app.route("/api/sensors", methods=["POST"])
def receive_sensor_data():
    global latest_sensor_data
    latest_sensor_data = request.json
    return jsonify({"message": "Sensor data received successfully"})

@app.route("/api/sensors/latest", methods=["GET"])
def get_latest_sensor_data():
    return jsonify(latest_sensor_data)


# ----------------------------
# ML PREDICTION API (Dummy)
# ----------------------------
@app.route("/api/predict", methods=["POST"])
def predict():
    data = request.json

    result = {
        "crop_health": "Healthy",
        "disease_risk": f"{random.randint(5,15)}%",
        "weather_impact": "Low Risk"
    }

    return jsonify(result)


# ----------------------------
# BLOCKCHAIN / QR API (Dummy)
# ----------------------------
@app.route("/api/harvest/store", methods=["POST"])
def store_harvest():
    data = request.json

    batch_id = "BATCH-" + str(random.randint(1000, 9999))
    tx_hash = "0x" + str(random.getrandbits(128))

    return jsonify({
        "batchId": batch_id,
        "txHash": tx_hash
    })


# ----------------------------
# TRACEABILITY API
# ----------------------------
@app.route("/api/trace/<batch_id>", methods=["GET"])
def trace(batch_id):
    return jsonify({
        "batchId": batch_id,
        "crop": "Tomato",
        "farmer": "John Mathew",
        "location": "Kerala",
        "harvestDate": "2025-02-10",
        "verified": True
    })


# ----------------------------
# RUN SERVER
# ----------------------------
if __name__ == "__main__":
    app.run(debug=True)
