from flask import Blueprint, request, jsonify
from app import db, bucket  # Assuming 'bucket' is from GCS
from google.cloud.firestore import GeoPoint

POIs_bp = Blueprint('POIs', __name__)


@POIs_bp.route('/<building_id>/<floor_id>', methods=['GET'])
def get_POIs(building_id, floor_id):
    if not building_id:
        return jsonify({"error": "Missing 'building_id' parameter."}), 400
    if not floor_id:
        return jsonify({"error": "Missing 'floor_id' parameter."}), 400
    if db is None:
        return jsonify({"error": "Database not initialized."}), 500

    try:
        # Correctly get the floor document
        floor_doc_ref = db.collection('buildings').document(building_id).collection('floors').document(floor_id)
        floor_doc = floor_doc_ref.get()

        if not floor_doc.exists:
            return jsonify({"error": f"Floor '{floor_id}' not found for building '{building_id}'."}), 404

        POIs_ref = floor_doc_ref.collection('POIs')
        POIs_docs = POIs_ref.stream()

        POIs = []
        for doc in POIs_docs:
            poi_data = doc.to_dict()
            poi_data['id'] = doc.id
            poi_data['floor'] = floor_doc.get('floor')  # Use the floor_doc
            for key, value in poi_data.items():
                if isinstance(value, GeoPoint):
                    poi_data[key] = [value.latitude, value.longitude]
            POIs.append(poi_data)

        return jsonify(POIs), 200

    except Exception as e:
        print(f"An error occurred during query: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@POIs_bp.route('/<building_id>/<floor_id>', methods=['POST'])
def add_poi(building_id, floor_id):
    try:
        data = request.get_json()
        if not data or 'id' not in data:
            return jsonify({"error": "Each POI must have an 'id'."}), 400

        poi_id = data['id']
        poi_copy = data.copy()
        poi_copy.pop('id')

        if 'location' in poi_copy and isinstance(poi_copy['location'], list) and len(poi_copy['location']) == 2:
            poi_copy['location'] = GeoPoint(poi_copy['location'][0], poi_copy['location'][1])

        poi_ref = db.collection('buildings').document(building_id)\
            .collection('floors').document(floor_id)\
            .collection('POIs').document(poi_id)
        poi_ref.set(poi_copy)

        return jsonify({"status": "success", "message": f"POI {poi_id} added."}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    except Exception as e:
        print(f"An error occurred during query: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@POIs_bp.route('/<building_id>/<floor_id>/<poi_id>', methods=['PATCH'])
def update_poi(building_id, floor_id, poi_id):
    if not building_id:
        return jsonify({"error": "Missing 'building_id' parameter."}), 400
    if not floor_id:
        return jsonify({"error": "Missing 'floor_id' parameter."}), 400
    if not poi_id:
        return jsonify({"error": "Missing 'poi_id' parameter."}), 400
    if db is None:
        return jsonify({"error": "Database not initialized."}), 500

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is empty"}), 400

        # Example expected payload: {"location": [13.7563, 100.5018]}
        update_data = {}
        if 'location' in data and isinstance(data['location'], list) and len(data['location']) == 2:
            update_data['location'] = GeoPoint(data['location'][0], data['location'][1])

        # Update POI doc
        poi_ref = db.collection('buildings').document(building_id).collection('floors').document(floor_id).collection('POIs').document(poi_id)
        poi_ref.update(update_data)

        return jsonify({"status": "success", "message": f"POI {poi_id} updated successfully."}), 200

    except Exception as e:
        print(f"Error updating POI: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@POIs_bp.route('/<building_id>/<floor_id>/<poi_id>', methods=['DELETE'])
def delete_poi(building_id, floor_id, poi_id):
    try:
        poi_ref = db.collection('buildings').document(building_id)\
            .collection('floors').document(floor_id)\
            .collection('POIs').document(poi_id)

        if not poi_ref.get().exists:
            return jsonify({"error": f"POI {poi_id} not found"}), 404

        poi_ref.delete()
        return jsonify({"status": "success", "message": f"POI {poi_id} deleted."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@POIs_bp.route('POI_info/<building_id>/<poi_id>', methods=['GET'])
def get_POI(building_id, poi_id):
    if not building_id:
        return jsonify({"error": "Missing 'building_id' query parameter."}), 400
    if not poi_id:
        return jsonify({"error": "Missing 'poi_id' query parameter."}), 400
    if db is None:
        return jsonify({"error": "Database not initialized."}), 500

    try:
        # Query across all floors for the given POI
        floor_query = db.collection('buildings').document(building_id).collection('floors')
        for floor_doc in floor_query.stream():
            poi_doc_ref = floor_doc.reference.collection('POIs').document(poi_id)
            poi_snapshot = poi_doc_ref.get()
            if poi_snapshot.exists:
                query_result = poi_snapshot.to_dict()
                query_result['id'] = poi_snapshot.id
                query_result['floor'] = floor_doc.get('floor')
                for key, value in query_result.items():
                    if isinstance(value, GeoPoint):
                        query_result[key] = [value.latitude, value.longitude]
                return jsonify(query_result), 200

        # If the loop finishes without finding the POI
        return jsonify({"error": f"Cannot find poi id: {poi_id} for building {building_id}."}), 404

    except Exception as e:
        print(f"An error occurred during query: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# ===================== NEW: RECOMMENDED POIs ENDPOINTS =====================


@POIs_bp.route('/<building_id>/<floor_id>/<poi_id>/recommended', methods=['PATCH'])
def set_recommended(building_id, floor_id, poi_id):
    """
    Toggle the 'recommended' flag for a single POI on a floor.
    Body: {"value": true|false}
    """
    try:
        payload = request.get_json() or {}
        if 'value' not in payload:
            return jsonify({"error": "Body must include {'value': true|false}"}), 400

        # Ensure the POI exists first
        poi_ref = db.collection('buildings').document(building_id) \
            .collection('floors').document(floor_id) \
            .collection('POIs').document(poi_id)

        snap = poi_ref.get()
        if not snap.exists:
            return jsonify({"error": f"POI {poi_id} not found"}), 404

        poi_ref.update({'recommended': bool(payload['value'])})
        return jsonify({
            "status": "success",
            "message": f"POI {poi_id} recommended = {bool(payload['value'])}"
        }), 200

    except Exception as e:
        print(f"Error setting recommended: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@POIs_bp.route('/<building_id>/<floor_id>/recommended', methods=['GET'])
def list_recommended_on_floor(building_id, floor_id):
    """
    List only recommended POIs for a given floor.
    """
    try:
        floor_doc_ref = db.collection('buildings').document(building_id) \
            .collection('floors').document(floor_id)
        floor_doc = floor_doc_ref.get()

        if not floor_doc.exists:
            return jsonify({"error": f"Floor '{floor_id}' not found for building '{building_id}'."}), 404

        pois_ref = floor_doc_ref.collection('POIs')
        pois_docs = pois_ref.where('recommended', '==', True).stream()

        results = []
        for doc in pois_docs:
            poi = doc.to_dict()
            poi['id'] = doc.id
            poi['floor'] = floor_doc.get('floor')
            # convert GeoPoint → [lat, lng] (keep same style as your GET)
            for k, v in list(poi.items()):
                if isinstance(v, GeoPoint):
                    poi[k] = [v.latitude, v.longitude]
            results.append(poi)

        return jsonify(results), 200

    except Exception as e:
        print(f"Error listing recommended POIs: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@POIs_bp.route('/<building_id>/recommended', methods=['GET'])
def list_recommended_in_building(building_id):
    """
    (Optional) List recommended POIs across ALL floors in a building.
    """
    try:
        floors_ref = db.collection('buildings').document(building_id).collection('floors')
        results = []

        for floor_doc in floors_ref.stream():
            pois_ref = floor_doc.reference.collection('POIs')
            for poi_doc in pois_ref.where('recommended', '==', True).stream():
                poi = poi_doc.to_dict()
                poi['id'] = poi_doc.id
                poi['floor'] = floor_doc.get('floor')
                for k, v in list(poi.items()):
                    if isinstance(v, GeoPoint):
                        poi[k] = [v.latitude, v.longitude]
                results.append(poi)

        return jsonify(results), 200

    except Exception as e:
        print(f"Error listing building recommended POIs: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
# =================== END NEW: RECOMMENDED POIs ENDPOINTS ====================
