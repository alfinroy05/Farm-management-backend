from flask import Blueprint, request, jsonify
from datetime import datetime
import time
from supabase import create_client
import os

# ================================
# Blueprint
# ================================
batch_bp = Blueprint("batch_routes", __name__)

# ================================
# Supabase Configuration
# ================================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ================================
# In-memory active batch (UI helper)
# ================================
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
        # Close any ACTIVE batch in DB
        supabase.table("batches").update({
            "status": "COMPLETED",
            "end_date": datetime.utcnow().isoformat()
        }).eq("status", "ACTIVE").execute()

        batch_id = f"BATCH_{int(time.time())}"
        current_batch = batch_id  # UI helper only

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
    try:
        res = supabase.table("batches") \
            .select("batch_id") \
            .eq("status", "ACTIVE") \
            .order("start_date", desc=True) \
            .limit(1) \
            .execute()

        return jsonify({
            "current_batch": res.data[0]["batch_id"] if res.data else None
        }), 200

    except Exception:
        return jsonify({"current_batch": None}), 200


# =========================================================
# GET: All Batches
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
# GET: Finalized Batches
# =========================================================
@batch_bp.route("/batch/finalized", methods=["GET"])
def get_finalized_batches():
    try:
        response = supabase.table("batches") \
            .select("batch_id, status, merkle_root, blockchain_tx") \
            .eq("status", "FINALIZED") \
            .execute()

        return jsonify(response.data), 200

    except Exception as e:
        return jsonify({
            "error": "Failed to fetch finalized batches",
            "details": str(e)
        }), 500


# =========================================================
# INTERNAL: Finalize Batch (Merkle + Blockchain)
# =========================================================
def _finalize_batch_with_blockchain(batch_id):
    from routes.hash_readings import hash_reading
    from routes.merkle_tree import merkle_root
    from routes.blockchain import store_merkle_root_on_chain

    # Fetch readings in insertion order
    response = supabase.table("harvest_data") \
        .select("sensor_data") \
        .eq("batch_id", batch_id) \
        .order("created_at", desc=False) \
        .execute()

    readings = []

    for row in response.data:
        if isinstance(row["sensor_data"], list):
            readings.extend(row["sensor_data"])  # ✅ FLATTEN
        else:
            readings.append(row["sensor_data"])

    if not readings:
        raise Exception("No sensor data found for batch")

    # Build Merkle tree
    hashes = [hash_reading(r) for r in readings]
    root = merkle_root(hashes)

    tx_hash = store_merkle_root_on_chain(
        batch_id,
        "0x" + root
    )

    # Update batch metadata
    supabase.table("batches").update({
        "status": "FINALIZED",
        "end_date": datetime.utcnow().isoformat(),
        "merkle_root": "0x" + root,
        "blockchain_tx": tx_hash
    }).eq("batch_id", batch_id).execute()

    # Update all readings
    supabase.table("harvest_data").update({
        "merkle_root": "0x" + root,
        "blockchain_tx": tx_hash
    }).eq("batch_id", batch_id).execute()

    return root, tx_hash


# =========================================================
# POST: Finalize Batch
# =========================================================
@batch_bp.route("/batch/finalize", methods=["POST"])
def finalize_batch():
    data = request.get_json()
    batch_id = data.get("batch_id")

    if not batch_id:
        return jsonify({"error": "Batch ID is required"}), 400

    try:
        batch = supabase.table("batches") \
            .select("status") \
            .eq("batch_id", batch_id) \
            .single() \
            .execute()

        if not batch.data:
            return jsonify({"error": "Batch not found"}), 404

        if batch.data["status"] != "ACTIVE":
            return jsonify({"error": "Batch is not active"}), 400

        root, tx_hash = _finalize_batch_with_blockchain(batch_id)

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
