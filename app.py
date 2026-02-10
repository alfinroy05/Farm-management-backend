from flask import Flask, request
from flask_cors import CORS
from dotenv import load_dotenv
import os
from supabase import create_client

# ---------------------------------
# Load environment variables
# ---------------------------------
load_dotenv()

# ---------------------------------
# Supabase Client (NEW – minimal)
# ---------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------------------------
# Import Blueprints (ONLY ONCE)
# ---------------------------------
from routes.auth import auth_bp
from routes.sensors import sensors_bp
from routes.predict import predict_bp
from routes.blockchain import blockchain_bp
from routes.trace import trace_bp
from routes.batch import batch_bp

# ---------------------------------
# Create Flask App
# ---------------------------------
app = Flask(__name__)
CORS(app)

# ---------------------------------
# Register Blueprints (ONLY ONCE)
# ---------------------------------
app.register_blueprint(auth_bp, url_prefix="/api")
app.register_blueprint(sensors_bp, url_prefix="/api/sensors")
app.register_blueprint(predict_bp, url_prefix="/api")
app.register_blueprint(blockchain_bp, url_prefix="/api/blockchain")
app.register_blueprint(trace_bp, url_prefix="/api")
app.register_blueprint(batch_bp, url_prefix="/api")
from routes.otp import otp_bp
app.register_blueprint(otp_bp, url_prefix="/api")

# ---------------------------------
# Health Check
# ---------------------------------
@app.route("/")
def home():
    return {"message": "AgriChain Backend is Running"}

@app.route("/routes")
def list_routes():
    return {
        "routes": [str(rule) for rule in app.url_map.iter_rules()]
    }

# ---------------------------------
# ESP32 → CLOUD INGESTION (UPDATED)
# ---------------------------------

from datetime import datetime

@app.route("/sensor-data", methods=["POST"])
def sensor_data():
    data = request.json
    print("ESP32 DATA:", data)

    # 🔹 STEP 1: Find ACTIVE batch
    active_batch = supabase.table("batches") \
        .select("batch_id") \
        .eq("status", "ACTIVE") \
        .limit(1) \
        .execute()

    if active_batch.data:
        batch_id = active_batch.data[0]["batch_id"]
    else:
        batch_id = "NO_BATCH"

    # 🔹 STEP 2: Build sensor payload
    sensor_payload = {
        "airTemp": data.get("temperature"),
        "humidity": data.get("humidity"),
        "soilMoisture": data.get("soil_moisture"),
        "npk": {
            "N": data.get("nitrogen"),
            "P": data.get("phosphorus"),
            "K": data.get("potassium")
        },
        "timestamp": datetime.utcnow().isoformat()
    }

    # 🔹 STEP 3: Insert into harvest_data
    response = supabase.table("harvest_data").insert({
        "batch_id": batch_id,
        "sensor_data": sensor_payload,
        "merkle_root": "PENDING",
        "blockchain_tx": "PENDING",
        "network": "sepolia"
    }).execute()

    print("ACTIVE BATCH USED:", batch_id)
    print("SUPABASE RESPONSE:", response)

    return {"status": "stored", "batch_id": batch_id}, 200



# ---------------------------------
# Run Server
# ---------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
