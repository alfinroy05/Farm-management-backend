from flask import Flask
from flask_cors import CORS

# Import blueprints
from routes.auth import auth_bp
from routes.sensors import sensors_bp
from routes.predict import predict_bp
from routes.blockchain import blockchain_bp
from routes.trace import trace_bp

app = Flask(__name__)
CORS(app)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix="/api")
app.register_blueprint(sensors_bp, url_prefix="/api/sensors")
app.register_blueprint(predict_bp, url_prefix="/api")
app.register_blueprint(blockchain_bp, url_prefix="/api")
app.register_blueprint(trace_bp, url_prefix="/api")

# Test route
@app.route("/")
def home():
    return {"message": "AgriChain Backend is Running"}

if __name__ == "__main__":
    app.run(debug=True)
