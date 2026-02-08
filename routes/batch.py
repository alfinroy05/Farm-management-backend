from flask import Blueprint, request, jsonify
from datetime import datetime
import time
from supabase import create_client
import os

# ✅ UNIQUE blueprint name
batch_bp = Blueprint("batch_routes", __name__)

# ---------------------------------
# Supabase Configuration
# ---------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------------------------
# In-memory active batch
# ---------------------------------
current_batch = None


# =========================================================
# POST: Create New Batch
# =========================================================
@batch_bp.route("/batch/create", methods=["POST"])
def create_batch():
    global current_batch
    print("✅ /batch/create called")

    data = request.get_json(silent=True) or {}

    try:
        # Close previous batch if exists
        if current_batch:
            supabase.table("batches").update({
                "status": "COMPLETED",
                "end_date": datetime.utcnow().isoformat()
            }).eq("batch_id", current_batch).execute()

        batch_id = f"BATCH_{int(time.time())}"
        current_batch = batch_id

        supabase.table("batches").insert({
            "batch_id": batch_id,
            "crop": data.get("crop", "Unknown Crop"),
            "location": data.get("location", "Unknown Location"),
            "start_date": datetime.utcnow().isoformat(),
            "status": "ACTIVE"
        }).execute()

        return jsonify({
            "message": "New batch created successfully",
            "batch_id": batch_id
        }), 200

    except Exception as e:
        return jsonify({
            "error": "Batch creation failed",
            "details": str(e)
        }), 500


# =========================================================
# GET: Current Active Batch
# =========================================================
@batch_bp.route("/batch/current", methods=["GET"])
def get_current_batch():
    return jsonify({
        "current_batch": current_batch
    }), 200


# =========================================================
# GET: All Batches (Dashboard dropdown)
# =========================================================
@batch_bp.route("/batch/all", methods=["GET"])
def get_all_batches():
    try:
        response = supabase.table("batches") \
            .select("batch_id, crop, location, status, start_date") \
            .order("start_date", desc=True) \
            .execute()

        return jsonify(response.data), 200

    except Exception as e:
        return jsonify({
            "error": "Failed to fetch batches",
            "details": str(e)
        }), 500


# =========================================================
# GET: Finalized Batches (QR / Consumer)
# =========================================================
@batch_bp.route("/batch/finalized", methods=["GET"])
def get_finalized_batches():
    try:
        response = supabase.table("batches") \
            .select("batch_id, status") \
            .eq("status", "FINALIZED") \
            .execute()

        return jsonify(response.data), 200

    except Exception as e:
        return jsonify({
            "error": "Failed to fetch finalized batches",
            "details": str(e)
        }), 500


# =========================================================
# INTERNAL HELPER (NO ROUTE)
# =========================================================
def _finalize_batch_with_blockchain(batch_id):
    from routes.hash_readings import hash_reading
    from routes.merkle_tree import merkle_root
    from routes.blockchain import store_merkle_root_on_chain

    # Fetch sensor readings
    data = supabase.table("harvest_data") \
        .select("sensor_data") \
        .eq("batch_id", batch_id) \
        .execute()

    readings = []
    for row in data.data:
        readings.extend(row["sensor_data"])

    if not readings:
        raise Exception("No sensor data found")

    # Build Merkle tree
    hashes = [hash_reading(r) for r in readings]
    root = merkle_root(hashes)

    # Store on blockchain
    tx_hash = store_merkle_root_on_chain(
        batch_id,
        "0x" + root.replace("0x", "")
    )

    # ✅ ONLY update status in batches table
    supabase.table("batches").update({
    "status": "FINALIZED",
    "end_date": datetime.utcnow().isoformat(),
    "merkle_root": "0x" + root,
    "blockchain_tx": tx_hash
}).eq("batch_id", batch_id).execute()

    return root, tx_hash


# =========================================================
# POST: Finalize Batch (HARVEST DONE)
# =========================================================
@batch_bp.route("/batch/finalize", methods=["POST"])
def finalize_batch():
    global current_batch

    if not current_batch:
        return jsonify({
            "error": "No active batch to finalize"
        }), 400

    try:
        batch_id = current_batch
        root, tx_hash = _finalize_batch_with_blockchain(batch_id)

        # Clear active batch
        current_batch = None

        return jsonify({
            "message": "Batch finalized successfully",
            "batch_id": batch_id,
            "merkle_root": root,
            "tx_hash": tx_hash
        }), 200

    except Exception as e:
        return jsonify({
            "error": "Failed to finalize batch",
            "details": str(e)
        }), 500
