from flask import Blueprint, request, jsonify
from supabase import create_client
from datetime import datetime
import random
import os

# IMPORTANT: import the MODULE, not the variable
import routes.batch as batch_state

# 🔗 Blockchain automation imports
from routes.hash_readings import hash_reading
from routes.merkle_tree import merkle_root
from routes.blockchain import store_merkle_root_on_chain

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

# -------------------------------
# In-memory buffer (PER BATCH)
# -------------------------------
sensor_buffer = []
buffer_batch_id = None   # tracks which batch the buffer belongs to
BATCH_SIZE = 5           # automation trigger


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
        active_batch = batch_state.current_batch

        # 🔴 HARD BLOCK if no active batch
        if not active_batch:
            return jsonify({
                "error": "No active batch. Farmer must create a batch first."
            }), 400

        global sensor_buffer, buffer_batch_id

        # 🔁 Reset buffer if batch changed
        if buffer_batch_id != active_batch:
            sensor_buffer.clear()
            buffer_batch_id = active_batch

        # Build full reading
        reading = {
            "airTemp": data.get("airTemp"),
            "humidity": data.get("humidity"),
            "soilMoisture": data.get("soilMoisture"),
            "npk": data.get("npk"),
            "soilPH": round(random.uniform(6.0, 7.0), 2),
            "timestamp": datetime.utcnow().isoformat()
        }

        # 1️⃣ Add to in-memory buffer
        sensor_buffer.append(reading)
        print(f"📦 Buffer size: {len(sensor_buffer)} | Batch: {active_batch}")

        # 2️⃣ Store raw reading (off-chain)
        supabase.table("harvest_data").insert({
            "batch_id": active_batch,
            "sensor_data": [reading],
            "merkle_root": "PENDING",
            "blockchain_tx": "PENDING",
            "network": "sepolia",
            "ph_source": "simulated"
        }).execute()

        blockchain_result = None

        # 3️⃣ AUTOMATION: commit batch to blockchain
        if len(sensor_buffer) >= BATCH_SIZE:
            print("🔗 Batch full → generating Merkle root")

            hashes = [hash_reading(r) for r in sensor_buffer]
            root = merkle_root(hashes)

            tx_hash = store_merkle_root_on_chain(
                active_batch,
                "0x" + root.replace("0x", "")
            )

            print("✅ Merkle root committed")
            print("🧱 Root:", root)
            print("🔗 Tx:", tx_hash)

            # Store committed batch snapshot
            supabase.table("harvest_data").insert({
                "batch_id": active_batch,
                "sensor_data": sensor_buffer,
                "merkle_root": "0x" + root,
                "blockchain_tx": tx_hash,
                "network": "sepolia",
                "ph_source": "simulated"
            }).execute()

            sensor_buffer.clear()
            blockchain_result = {
                "batch_id": active_batch,
                "merkle_root": root,
                "tx_hash": tx_hash
            }

        return jsonify({
            "message": "Sensor data received",
            "active_batch": active_batch,
            "buffer_size": len(sensor_buffer),
            "blockchain_commit": blockchain_result
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
            .order("id", desc=True) \
            .limit(1) \
            .execute()

        if not response.data:
            return jsonify({"error": "No sensor data available"}), 404

        row = response.data[0]
        sensor = row["sensor_data"][0]

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
            .execute()

        return jsonify(response.data), 200

    except Exception as e:
        return jsonify({
            "error": "Failed to fetch batch sensor data",
            "details": str(e)
        }), 500


# =========================================================
# GET: Buffer status (debug)
# GET /api/sensors/buffer
# =========================================================
@sensors_bp.route("/buffer", methods=["GET"])
def get_buffer_status():
    return jsonify({
        "buffer_count": len(sensor_buffer),
        "buffer_batch": buffer_batch_id,
        "active_batch": batch_state.current_batch,
        "buffer_preview": sensor_buffer[-3:]
    }), 200
