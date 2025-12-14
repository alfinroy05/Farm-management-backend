from flask import Blueprint, request, jsonify
import random

# Create Blueprint
predict_bp = Blueprint("predict", __name__)

# ------------------------------------
# POST: Crop Health Prediction API
# ------------------------------------
@predict_bp.route("/predict", methods=["POST"])
def predict_crop_health():
    """
    Expected JSON from frontend:
    {
        "temperature": 29,
        "humidity": 72,
        "soilMoisture": 45,
        "ph": 6.5,
        "nitrogen": 40,
        "phosphorus": 20,
        "potassium": 35
    }
    """

    data = request.json

    if not data:
        return jsonify({"error": "No input data received"}), 400

    # ----------------------------
    # Dummy ML Logic (for project)
    # ----------------------------

    temperature = float(data.get("temperature", 0))
    soil_moisture = float(data.get("soilMoisture", 0))
    humidity = float(data.get("humidity", 0))

    # Crop health logic (simple rule-based)
    if soil_moisture < 30 or temperature > 35:
        crop_health = "Poor"
    elif soil_moisture < 45:
        crop_health = "Moderate"
    else:
        crop_health = "Healthy"

    # Disease risk logic
    if humidity > 80:
        disease_risk = "High"
    elif humidity > 60:
        disease_risk = "Medium"
    else:
        disease_risk = "Low"

    # Weather impact (random for demo)
    weather_impact = random.choice([
        "Low Risk",
        "Moderate Risk",
        "Favorable"
    ])

    # ----------------------------
    # Response to frontend
    # ----------------------------
    return jsonify({
        "crop_health": crop_health,
        "disease_risk": disease_risk,
        "weather_impact": weather_impact
    }), 200
