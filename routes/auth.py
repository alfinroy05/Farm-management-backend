from flask import Blueprint, request, jsonify

# Create Blueprint for authentication
auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Expected JSON from frontend:
    {
        "role": "farmer" | "store" | "consumer",
        "email": "user@example.com",
        "password": "password"
    }
    """

    data = request.json

    role = data.get("role")
    email = data.get("email")

    # Basic validation
    if not role:
        return jsonify({"error": "Role is required"}), 400

    # Dummy authentication logic (for project/demo)
    # In real systems, password & DB verification happens here

    return jsonify({
        "message": "Login successful",
        "role": role,
        "email": email
    }), 200
