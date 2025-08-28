from flask import Flask
from flask_cors import CORS

# move firebase init out to avoid circulars
from firebase_init import db, bucket  # noqa: F401 (ensures they’re initialized)

app = Flask(__name__)
CORS(app)

# Blueprints
from blueprints.model import model_bp
from blueprints.beacon import beacon_bp
from blueprints.floors import floors_bp
from blueprints.POIs import POIs_bp
from blueprints.building import building_bp
from blueprints.paths import paths_bp

app.register_blueprint(model_bp, url_prefix='/model')
app.register_blueprint(beacon_bp, url_prefix='/beacon')
app.register_blueprint(floors_bp, url_prefix='/floors')
app.register_blueprint(POIs_bp, url_prefix='/POIs')
app.register_blueprint(building_bp, url_prefix='/buildings')
app.register_blueprint(paths_bp, url_prefix='/paths')

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        ssl_context=('localhost+4.pem', 'localhost+4-key.pem'),
        debug=True,
    )
