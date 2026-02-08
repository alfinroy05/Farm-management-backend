from flask import Blueprint, request, jsonify
from supabase import create_client
from datetime import datetime
import os

# -------------------------------
# Supabase Configuration
# -------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------------------
# Create Blueprint
# -------------------------------
sensors_bp = Blueprint("sensors", __name__)

# =========================================================
# POST: Receive sensor data (ESP32 / Simulator)
# POST /api/sensors/sensor-data
# =========================================================
@sensors_bp.route("/sensor-data", methods=["POST"])
def receive_sensor_data():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No sensor data received"}), 400

    try:
        # 🔐 ALWAYS resolve ACTIVE batch from DATABASE
        batch_res = supabase.table("batches") \
            .select("batch_id, status") \
            .eq("status", "ACTIVE") \
            .order("start_date", desc=True) \
            .limit(1) \
            .execute()

        if not batch_res.data:
            return jsonify({
                "error": "No active batch. Create a batch first."
            }), 400

        active_batch_id = batch_res.data[0]["batch_id"]

        # ✅ Build canonical sensor reading
        reading = {
            "airTemp": data.get("airTemp") or data.get("temperature"),
            "humidity": data.get("humidity"),
            "soilMoisture": data.get("soilMoisture") or data.get("soil_moisture"),
            "npk": data.get("npk") or {
                "N": data.get("nitrogen"),
                "P": data.get("phosphorus"),
                "K": data.get("potassium")
            },
            "soilPH": data.get("soilPH"),  # optional
            "timestamp": datetime.utcnow().isoformat()
        }

        # 🔒 Store reading OFF-CHAIN (cloud only)
        supabase.table("harvest_data").insert({
            "batch_id": active_batch_id,
            "sensor_data": reading,
            "merkle_root": "PENDING",
            "blockchain_tx": "PENDING",
            "network": "sepolia",
            "ph_source": "simulated"
        }).execute()

        print("✅ Sensor data stored under batch:", active_batch_id)

        return jsonify({
            "message": "Sensor data received",
            "active_batch": active_batch_id
        }), 200

    except Exception as e:
        return jsonify({
            "error": "Failed to process sensor data",
            "details": str(e)
        }), 500


# =========================================================
# GET: Latest sensor data (ACTIVE batch)
# GET /api/sensors/latest
# =========================================================
@sensors_bp.route("/latest", methods=["GET"])
def get_latest_sensor():
    try:
        response = supabase.table("harvest_data") \
            .select("*") \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()

        if not response.data:
            return jsonify({"error": "No sensor data available"}), 404

        row = response.data[0]
        sensor = row["sensor_data"]

        return jsonify({
            "batch_id": row["batch_id"],
            "airTemp": sensor.get("airTemp"),
            "humidity": sensor.get("humidity"),
            "soilMoisture": sensor.get("soilMoisture"),
            "soilPH": sensor.get("soilPH"),
            "npk": sensor.get("npk"),
            "timestamp": sensor.get("timestamp"),
            "merkle_root": row["merkle_root"],
            "blockchain_tx": row["blockchain_tx"],
            "network": row.get("network")
        }), 200

    except Exception as e:
        return jsonify({
            "error": "Failed to fetch latest sensor data",
            "details": str(e)
        }), 500


# =========================================================
# GET: Sensor data for a specific batch (VIEW MODE)
# GET /api/sensors/batch/<batch_id>
# =========================================================
@sensors_bp.route("/batch/<batch_id>", methods=["GET"])
def get_sensor_data_by_batch(batch_id):
    try:
        response = supabase.table("harvest_data") \
            .select("*") \
            .eq("batch_id", batch_id) \
            .order("created_at", desc=False) \
            .execute()

        return jsonify(response.data), 200

    except Exception as e:
        return jsonify({
            "error": "Failed to fetch batch sensor data",
            "details": str(e)
        }), 500
