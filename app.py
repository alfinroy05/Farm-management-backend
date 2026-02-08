from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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



from flask import request

@app.route("/sensor-data", methods=["POST"])
def sensor_data():
    data = request.json
    print("ESP32 DATA:", data)
    return {"message": "received"}, 200

# ---------------------------------
# Run Server
# ---------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)




