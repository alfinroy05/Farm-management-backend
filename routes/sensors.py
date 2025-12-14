from flask import Blueprint, request, jsonify

# Create Blueprint
sensors_bp = Blueprint("sensors", __name__)

# In-memory storage for latest sensor data
# (For demo / project purpose)
latest_sensor_data = {
    "temperature": "--",
    "humidity": "--",
    "soilMoisture": "--",
    "ph": "--",
    "nitrogen": "--",
    "phosphorus": "--",
    "potassium": "--",
    "rainfall": "--"
}

# ------------------------------------
# POST: Receive sensor data (ESP32 / Dummy)
# ------------------------------------
@sensors_bp.route("/", methods=["POST"])
def receive_sensor_data():
    """
    Expected JSON:
    {
        "temperature": 29,
        "humidity": 72,
        "soilMoisture": 45,
        "ph": 6.5,
        "nitrogen": 40,
        "phosphorus": 20,
        "potassium": 35,
        "rainfall": 3
    }
    """
    global latest_sensor_data

    data = request.json

    if not data:
        return jsonify({"error": "No sensor data received"}), 400

    # Update latest sensor data
    for key in latest_sensor_data:
        if key in data:
            latest_sensor_data[key] = data[key]

    return jsonify({
        "message": "Sensor data updated successfully",
        "data": latest_sensor_data
    }), 200


# ------------------------------------
# GET: Send latest sensor data to frontend
# ------------------------------------
@sensors_bp.route("/latest", methods=["GET"])
def get_latest_sensor_data():
    return jsonify(latest_sensor_data), 200
