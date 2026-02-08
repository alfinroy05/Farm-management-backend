from flask import Blueprint, jsonify
from web3 import Web3
import os
import json
from datetime import datetime
from supabase import create_client

from routes.hash_readings import hash_reading
from routes.merkle_tree import merkle_root

# ---------------------------------
# Blueprint
# ---------------------------------
blockchain_bp = Blueprint("blockchain", __name__)

# ---------------------------------
# Supabase Configuration
# ---------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------------------------
# Blockchain Configuration (Sepolia)
# ---------------------------------
SEPOLIA_RPC_URL = os.getenv("SEPOLIA_RPC_URL")
CONTRACT_ADDRESS = "0xb8E82a2247b1E6a358220C8C24Ba53e89b411138"

WALLET_ADDRESS = os.getenv("WALLET_ADDRESS")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

w3 = Web3(Web3.HTTPProvider(SEPOLIA_RPC_URL))

with open("abi.json") as f:
    abi = json.load(f)

contract = w3.eth.contract(
    address=Web3.to_checksum_address(CONTRACT_ADDRESS),
    abi=abi
)

# =========================================================
# CORE FUNCTION (USED BY AUTOMATION)
# =========================================================
def store_merkle_root_on_chain(batch_id: str, merkle_root_hex: str) -> str:
    clean_root = merkle_root_hex.replace("0x", "")
    data_hash = "0x" + clean_root

    nonce = w3.eth.get_transaction_count(WALLET_ADDRESS)

    tx = contract.functions.addHarvest(
        batch_id,
        "CROP",
        "LOCATION",
        data_hash,
        0,
        True,
        Web3.to_checksum_address(WALLET_ADDRESS)
    ).build_transaction({
        "from": WALLET_ADDRESS,
        "nonce": nonce,
        "gas": 500000,
        "gasPrice": w3.to_wei("10", "gwei")
    })

    signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return "0x" + receipt.transactionHash.hex().replace("0x", "")


# =========================================================
# READ-ONLY: Blockchain Logs
# =========================================================
@blockchain_bp.route("/logs", methods=["GET"])
def blockchain_logs():
    response = supabase.table("harvest_data") \
        .select("*") \
        .like("merkle_root", "0x%") \
        .order("created_at", desc=True) \
        .execute()

    seen = set()
    logs = []

    for row in response.data:
        if row["batch_id"] not in seen:
            seen.add(row["batch_id"])
            logs.append({
                "batch_id": row["batch_id"],
                "tx_hash": row["blockchain_tx"],
                "timestamp": row["created_at"]
            })

    return jsonify(logs), 200

# =========================================================
# HELPER: Verify using COMMITTED SNAPSHOT (no route)
# =========================================================
def verify_using_snapshot(batch_id: str):
    response = supabase.table("harvest_data") \
        .select("*") \
        .eq("batch_id", batch_id) \
        .neq("merkle_root", "PENDING") \
        .limit(1) \
        .execute()

    if not response.data:
        return None, "No committed snapshot found"

    row = response.data[0]

    stored_root = row["merkle_root"].replace("0x", "")
    sensor_data = row["sensor_data"]

    hashes = [hash_reading(r) for r in sensor_data]
    recomputed = merkle_root(hashes)

    return stored_root == recomputed, {
        "stored": "0x" + stored_root,
        "recomputed": "0x" + recomputed
    }

# =========================================================
# MAIN VERIFY ROUTE (SINGLE SOURCE OF TRUTH)
# =========================================================
@blockchain_bp.route("/verify/<batch_id>", methods=["GET"])
def verify_batch(batch_id):
    try:
        # 1️⃣ Fetch committed snapshot (NOT pending)
        response = supabase.table("harvest_data") \
            .select("sensor_data, merkle_root, blockchain_tx") \
            .eq("batch_id", batch_id) \
            .neq("merkle_root", "PENDING") \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()

        if not response.data:
            return jsonify({
                "error": "No committed batch found"
            }), 404

        row = response.data[0]

        stored_root = row["merkle_root"]
        sensor_data = row["sensor_data"]
        tx_hash = row["blockchain_tx"]

        if not stored_root or not sensor_data:
            return jsonify({
                "error": "Incomplete batch data"
            }), 400

        # 2️⃣ Recompute Merkle root
        hashes = [hash_reading(r) for r in sensor_data]
        recomputed_root = "0x" + merkle_root(hashes).replace("0x", "")

        verified = stored_root.lower() == recomputed_root.lower()

        return jsonify({
            "batch_id": batch_id,
            "verified": verified,
            "stored_merkle_root": stored_root,
            "recomputed_merkle_root": recomputed_root,
            "tx_hash": tx_hash
        }), 200

    except Exception as e:
        return jsonify({
            "error": "Verification failed",
            "details": str(e)
        }), 500

