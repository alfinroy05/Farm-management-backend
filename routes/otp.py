from flask import Blueprint, request, jsonify
import random
import time
from twilio.rest import Client
import os

otp_bp = Blueprint("otp", __name__)

# In-memory OTP store
otp_store = {}

# Twilio config
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH")
TWILIO_PHONE = os.getenv("TWILIO_PHONE")
FARMER_PHONE = os.getenv("FARMER_PHONE")

client = Client(TWILIO_SID, TWILIO_AUTH)

OTP_EXPIRY = 300  # 5 minutes

@otp_bp.route("/otp/send", methods=["POST"])
def send_otp():
    data = request.get_json()
    batch_id = data.get("batch_id")

    if not batch_id:
        return jsonify({"error": "Batch ID required"}), 400

    otp = random.randint(100000, 999999)

    otp_store[batch_id] = {
        "otp": str(otp),
        "expires": time.time() + OTP_EXPIRY
    }

    # Send SMS
    client.messages.create(
        body=f"AgriChain OTP for batch {batch_id}: {otp}",
        from_=TWILIO_PHONE,
        to=FARMER_PHONE
    )

    return jsonify({"message": "OTP sent"}), 200


@otp_bp.route("/otp/verify", methods=["POST"])
def verify_otp():
    data = request.get_json()
    batch_id = data.get("batch_id")
    otp = data.get("otp")

    record = otp_store.get(batch_id)

    if not record:
        return jsonify({"verified": False}), 400

    if time.time() > record["expires"]:
        otp_store.pop(batch_id)
        return jsonify({"verified": False, "error": "OTP expired"}), 400

    if record["otp"] != otp:
        return jsonify({"verified": False}), 400

    otp_store.pop(batch_id)
    return jsonify({"verified": True}), 200
