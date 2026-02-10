from flask import Blueprint, jsonify, request
from supabase import create_client
import joblib
import numpy as np
import pandas as pd
import os

# -------------------------------
# Supabase Configuration (KEPT)
# -------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

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
    ML inference is performed on frontend-provided
    batch-specific sensor data.
    """

    # ------------------------------------
    # Read sensor data from frontend (FIX)
    # ------------------------------------
    data = request.json

    if not data:
        return jsonify({"error": "No input data received"}), 400

    try:
        # ------------------------------------
        # Prepare ML input
        # ------------------------------------
        input_features = pd.DataFrame([{
            "temperature": float(data.get("temperature", 0)),
            "humidity": float(data.get("humidity", 0)),
            "soilMoisture": float(data.get("soilMoisture", 0)),
            "ph": float(data.get("ph", 6.5)),   # simulated default
            "nitrogen": float(data.get("nitrogen", 0)),
            "phosphorus": float(data.get("phosphorus", 0)),
            "potassium": float(data.get("potassium", 0)),
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
            "data_source": "Frontend (Batch-Aware)",
            "prediction_type": "ML-based"
        }), 200

    except Exception as e:
        return jsonify({
            "error": "Prediction failed",
            "details": str(e)
        }), 500
