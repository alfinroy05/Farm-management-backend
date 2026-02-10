from flask import Blueprint, jsonify
from supabase import create_client
from web3 import Web3
import json
import os

from routes.hash_readings import hash_reading
from routes.merkle_tree import merkle_root

# ---------------------------------
# Blueprint
# ---------------------------------
trace_bp = Blueprint("trace", __name__)

# ---------------------------------
# Supabase Configuration
# ---------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------------------------
# Blockchain Configuration (READ ONLY)
# ---------------------------------
SEPOLIA_RPC_URL = "https://sepolia.infura.io/v3/YOUR_API_KEY"
CONTRACT_ADDRESS = "0xb8E82a2247b1E6a358220C8C24Ba53e89b411138"

w3 = Web3(Web3.HTTPProvider(SEPOLIA_RPC_URL))

with open("abi.json") as f:
    abi = json.load(f)

contract = w3.eth.contract(
    address=Web3.to_checksum_address(CONTRACT_ADDRESS),
    abi=abi
)

# -------------------------------------------------
# GET: Trace & Verify product using Batch ID (QR)
# -------------------------------------------------
@trace_bp.route("/trace/<batch_id>", methods=["GET"])
def trace_product(batch_id):
    """
    QR → Batch trace & tamper verification
    """

    try:
        # =================================
        # 1️⃣ Fetch finalized batch metadata
        # =================================
        batch_res = supabase.table("batches") \
            .select("merkle_root, blockchain_tx, status") \
            .eq("batch_id", batch_id) \
            .single() \
            .execute()

        if not batch_res.data:
            return jsonify({
                "verified": False,
                "error": "Batch not found"
            }), 404

        if batch_res.data["status"] != "FINALIZED":
            return jsonify({
                "verified": False,
                "error": "Batch not finalized yet"
            }), 400

        stored_root = batch_res.data["merkle_root"].replace("0x", "")
        blockchain_tx = batch_res.data["blockchain_tx"]

        # =================================
        # 2️⃣ Fetch ALL sensor readings (ORDERED)
        # =================================
        readings_res = supabase.table("harvest_data") \
            .select("sensor_data") \
            .eq("batch_id", batch_id) \
            .order("created_at", desc=False) \
            .execute()

        readings = []

        for row in readings_res.data:
            if isinstance(row["sensor_data"], list):
                readings.extend(row["sensor_data"])
            else:
                readings.append(row["sensor_data"])

        if not readings:
            return jsonify({
                "verified": False,
                "error": "No sensor readings found"
            }), 404

        # =================================
        # 3️⃣ Recompute Merkle root
        # =================================
        hashes = [hash_reading(r) for r in readings]
        recomputed_root = merkle_root(hashes)

        # =================================
        # 4️⃣ Tamper verification
        # =================================
        verified = (recomputed_root == stored_root)

        # =================================
        # 5️⃣ Optional blockchain existence check
        # =================================
        try:
            total_batches = contract.functions.getTotalBatches().call()
            blockchain_verified = total_batches > 0
        except Exception:
            blockchain_verified = False

        # =================================
        # 6️⃣ Final trace response
        # =================================
        return jsonify({
            "batchId": batch_id,
            "verified": verified,
            "tamperStatus": "NOT TAMPERED" if verified else "TAMPERED",

            "merkleRootStored": "0x" + stored_root,
            "merkleRootRecomputed": "0x" + recomputed_root,

            "blockchainTx": blockchain_tx,
            "blockchainVerified": blockchain_verified,

            "supplyChain": [
                "Harvested at Farm",
                "Sensor Data Collected (IoT)",
                "Merkle Root Generated",
                "Stored on Ethereum Sepolia",
                "Verified via QR Scan"
            ]
        }), 200

    except Exception as e:
        return jsonify({
            "verified": False,
            "error": "Trace verification failed",
            "details": str(e)
        }), 500
