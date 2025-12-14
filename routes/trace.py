from flask import Blueprint, jsonify

# Create Blueprint
trace_bp = Blueprint("trace", __name__)

# IMPORTANT:
# This must match the same in-memory ledger used in blockchain.py
# For demo purposes, we re-create a shared reference.
# In real projects, this would come from blockchain / database.

from routes.blockchain import blockchain_ledger


# -------------------------------------------------
# GET: Trace product using Batch ID (QR Scan)
# -------------------------------------------------
@trace_bp.route("/trace/<batch_id>", methods=["GET"])
def trace_product(batch_id):
    """
    Called after scanning QR code.
    URL example:
    /api/trace/BATCH-9A3F2C1D
    """

    # Check if batch exists
    if batch_id not in blockchain_ledger:
        return jsonify({
            "error": "Invalid Batch ID",
            "verified": False
        }), 404

    record = blockchain_ledger[batch_id]

    # Construct traceability response
    trace_response = {
        "batchId": record["batchId"],
        "cropName": record["cropName"],
        "variety": record["variety"],
        "farmerName": record["farmerName"],
        "location": record["location"],
        "harvestDate": record["harvestDate"],
        "txHash": record["txHash"],
        "timestamp": record["timestamp"],
        "status": record["status"],
        "verified": True,
        "supplyChain": [
            "Harvested at Farm",
            "Quality Checked",
            "Packed for Distribution",
            "Transported to Store",
            "Available for Consumer"
        ]
    }

    return jsonify(trace_response), 200
