from flask import Blueprint, request, jsonify
from app import db, bucket
from google.cloud.firestore import GeoPoint

POIs_bp = Blueprint('POIs', __name__)


@POIs_bp.route('', methods=['GET'])
def get_POIs():
    building_id = request.args.get('building_id')
    floor = int(request.args.get('floor'))
    if not building_id:
        return jsonify({"error": "Missing 'building_id' query parameter."}), 400
    if not floor:
        return jsonify({"error": "Missing 'floor' query parameter."}), 400
    if db is None:
        return jsonify({"error": "Database not initialized."}), 500

    try:

        floor_query = db.collection('buildings').document(building_id).collection('floors').where('floor', '==', floor)
        floor_docs = list(floor_query.stream())
        if not floor_docs:
            return jsonify({"error": f"Floor '{floor}' not found for building '{building_id}'."}), 404

        floor_doc_ref = floor_docs[0].reference
        POIs_ref = floor_doc_ref.collection('POIs')
        POIs_docs = list(POIs_ref.stream())
        POIs = []
        for doc in POIs_docs:
            log_data = doc.to_dict()
            log_data['id'] = doc.id
            for key, value in log_data.items():
                if isinstance(value, GeoPoint):
                    log_data[key] = [value.latitude, value.longitude]
            POIs.append(log_data)

        return jsonify(POIs), 200

    except Exception as e:
        print(f"An error occurred during query: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
