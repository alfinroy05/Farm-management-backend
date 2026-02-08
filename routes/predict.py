from flask import Blueprint, jsonify
from supabase import create_client
import joblib
import numpy as np
import pandas as pd   # ✅ ADDED
import os

# -------------------------------
# Supabase Configuration
# -------------------------------
SUPABASE_URL = "https://cxpusibdyaxtkgxgenvu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN4cHVzaWJkeWF4dGtneGdlbnZ1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjYzMTY1OTgsImV4cCI6MjA4MTg5MjU5OH0.2RUYwpK6n_4XC6iqzK1fJricYeEA93wJ9cgzAEFKhLk"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Create Blueprint
predict_bp = Blueprint("predict", __name__)

# -------------------------------
# Load ML Models (ONCE)
# -------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

crop_health_model = joblib.load(
    os.path.join(BASE_DIR, "ml/crop_health_model.pkl")
)

disease_model = joblib.load(
    os.path.join(BASE_DIR, "ml/disease_model.pkl")
)

health_encoder = joblib.load(
    os.path.join(BASE_DIR, "ml/crop_health_encoder.pkl")
)

disease_encoder = joblib.load(
    os.path.join(BASE_DIR, "ml/disease_risk_encoder.pkl")
)

# ------------------------------------
# POST: Crop Health Prediction API
# ------------------------------------
@predict_bp.route("/predict", methods=["POST"])
def predict_crop_health():
    """
    Frontend triggers prediction.
    Latest sensor data is fetched automatically from Supabase.
    """

    # ------------------------------------
    # Fetch latest sensor data from Supabase
    # ------------------------------------
    response = (
        supabase
        .table("sensor_data")
        .select("*")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if not response.data:
        return jsonify({"error": "No sensor data available"}), 404

    sensor = response.data[0]

    try:
        # ------------------------------------
        # Prepare ML input (FIXED ✅)
        # ------------------------------------
        input_features = pd.DataFrame([{
            "temperature": float(sensor.get("temperature", 0)),
            "humidity": float(sensor.get("humidity", 0)),
            "soilMoisture": float(sensor.get("soilMoisture", 0)),
            "ph": float(sensor.get("ph", 0)),
            "nitrogen": float(sensor.get("nitrogen", 0)),
            "phosphorus": float(sensor.get("phosphorus", 0)),
            "potassium": float(sensor.get("potassium", 0)),
        }])

        # ------------------------------------
        # ML Predictions
        # ------------------------------------
        crop_health_pred = crop_health_model.predict(input_features)
        disease_pred = disease_model.predict(input_features)

        crop_health = health_encoder.inverse_transform(crop_health_pred)[0]
        disease_risk = disease_encoder.inverse_transform(disease_pred)[0]

        # ------------------------------------
        # Advisory Logic
        # ------------------------------------
        advisory = []

        if crop_health == "Poor":
            advisory.append("Soil nutrients and moisture need immediate attention.")

        if disease_risk == "High":
            advisory.append("High disease risk detected. Preventive action advised.")

        if not advisory:
            advisory.append("Crop condition is healthy. Maintain current practices.")

        # ------------------------------------
        # Response to frontend
        # ------------------------------------
        return jsonify({
            "crop_health": crop_health,
            "disease_risk": disease_risk,
            "advisory": advisory,
            "data_source": "Supabase (Auto)",
            "prediction_type": "ML-based"
        }), 200

    except Exception as e:
        return jsonify({
            "error": "Prediction failed",
            "details": str(e)
        }), 500
