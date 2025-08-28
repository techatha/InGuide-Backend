from flask import Blueprint, request, jsonify
from firebase_init import db, bucket
from google.cloud.firestore_v1 import GeoPoint

POIs_bp = Blueprint('POIs', __name__)

@POIs_bp.route('', methods=['GET'])
def get_POIs():
    building_id = request.args.get('building_id')
    floor = request.args.get('floor', type=int)

    if not building_id:
        return jsonify({"error": "Missing 'building_id' query parameter."}), 400
    if floor is None:
        return jsonify({"error": "Missing 'floor' query parameter."}), 400
    if db is None:
        return jsonify({"error": "Database not initialized."}), 500

    try:
        floor_query = db.collection('buildings').document(building_id)\
                        .collection('floors').where('floor', '==', floor)
        floor_docs = list(floor_query.stream())
        if not floor_docs:
            return jsonify({"error": f"Floor '{floor}' not found for building '{building_id}'."}), 404

        poi_snapshots = list(floor_docs[0].reference.collection('POIs').stream())
        pois = []
        for doc in poi_snapshots:
            d = doc.to_dict() or {}
            d['id'] = doc.id
            d['floor'] = floor
            for k, v in list(d.items()):
                if isinstance(v, GeoPoint):
                    d[k] = [v.latitude, v.longitude]
            pois.append(d)

        return jsonify(pois), 200
    except Exception as e:
        print(f"An error occurred during query: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@POIs_bp.route('/POI', methods=['GET'])   # <-- fixed leading slash
def get_POI():
    building_id = request.args.get('building_id')
    poi_id = request.args.get('poi_id')

    if not building_id:
        return jsonify({"error": "Missing 'building_id' query parameter."}), 400
    if not poi_id:
        return jsonify({"error": "Missing 'poi_id' query parameter."}), 400
    if db is None:
        return jsonify({"error": "Database not initialized."}), 500

    try:
        floors_ref = db.collection('buildings').document(building_id).collection('floors')
        for floor_doc in floors_ref.stream():
            current_floor = floor_doc.get('floor')
            poi_doc = floor_doc.reference.collection('POIs').document(poi_id).get()
            if poi_doc.exists:
                data = poi_doc.to_dict() or {}
                data['id'] = poi_doc.id
                data['floor'] = current_floor
                for k, v in list(data.items()):
                    if isinstance(v, GeoPoint):
                        data[k] = [v.latitude, v.longitude]
                return jsonify(data), 200

        return jsonify({"error": f"Cannot find poi id: {poi_id} for building {building_id}."}), 404
    except Exception as e:
        print(f"An error occurred during query: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
