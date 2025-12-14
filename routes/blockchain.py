from flask import Blueprint, request, jsonify
import uuid
import datetime

# Create Blueprint
blockchain_bp = Blueprint("blockchain", __name__)

# In-memory storage (simulating blockchain ledger)
# In real deployment → Ethereum / Smart Contract
blockchain_ledger = {}

# -------------------------------------------------
# POST: Store Harvest Data + Generate QR (Batch ID)
# -------------------------------------------------
@blockchain_bp.route("/harvest/store", methods=["POST"])
def store_harvest():
    """
    Expected JSON from frontend (GenerateQR.jsx):
    {
        "cropName": "Tomato",
        "variety": "Hybrid",
        "harvestDate": "2025-02-10",
        "location": "Kerala",
        "farmerName": "John Mathew"
    }
    """

    data = request.json

    if not data:
        return jsonify({"error": "No harvest data received"}), 400

    # Generate unique batch ID
    batch_id = "BATCH-" + uuid.uuid4().hex[:8].upper()

    # Generate dummy blockchain transaction hash
    tx_hash = "0x" + uuid.uuid4().hex

    # Timestamp
    timestamp = datetime.datetime.utcnow().isoformat()

    # Store data (simulating immutable blockchain storage)
    blockchain_ledger[batch_id] = {
        "batchId": batch_id,
        "txHash": tx_hash,
        "timestamp": timestamp,
        "cropName": data.get("cropName"),
        "variety": data.get("variety"),
        "harvestDate": data.get("harvestDate"),
        "location": data.get("location"),
        "farmerName": data.get("farmerName"),
        "status": "Harvested"
    }

    return jsonify({
        "message": "Harvest data stored on blockchain",
        "batchId": batch_id,
        "txHash": tx_hash
    }), 200


# -------------------------------------------------
# GET: Fetch All Blockchain Records (Farmer/Store)
# -------------------------------------------------
@blockchain_bp.route("/blockchain/logs", methods=["GET"])
def get_blockchain_logs():
    """
    Used in Blockchain.jsx
    """
    return jsonify(list(blockchain_ledger.values())), 200
