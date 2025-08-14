from flask import Flask
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, storage, firestore

try:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'inguide-se953499.appspot.com'
    })
    print("Firebase Admin SDK initialized successfully!")
except Exception as e:
    print(f"Error initializing Firebase Admin SDK: {e}")

db = firestore.client()
bucket = storage.bucket()

app = Flask(__name__)
CORS(app)

# Blueprints
from blueprints.model import model_bp
from blueprints.beacon import beacon_bp
from blueprints.floors import floors_bp

app.register_blueprint(model_bp, url_prefix='/model')
app.register_blueprint(beacon_bp, url_prefix='/beacon')
app.register_blueprint(floors_bp, url_prefix='/floors')

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        ssl_context=('localhost+4.pem', 'localhost+4-key.pem'),
        debug=True
    )
