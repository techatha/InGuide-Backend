from flask import Blueprint, request, jsonify
from app import db

nav_graph_bp = Blueprint('nav_graph', __name__)


@nav_graph_bp.route('/<building_id>/<floor_id>', methods=['POST'])
def save_or_update_navigation_graph(building_id, floor_id):
    if db is None:
        return jsonify({"error": "Database not initialized."}), 500

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required."}), 400

        # Reference to the floor document
        floor_ref = db.collection('buildings').document(building_id).collection('floors').document(floor_id)

        # Check if floor exists
        if not floor_ref.get().exists:
            return jsonify({"error": f"Floor '{floor_id}' not found in building '{building_id}'."}), 404

        # Update the graph field
        floor_ref.update({
            "graph": data,
        })

        return jsonify({"message": "Navigation graph saved successfully."}), 200

    except Exception as e:
        print(f"Error saving navigation graph: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@nav_graph_bp.route('/<building_id>/<floor_id>', methods=['GET'])
def get_navigation_graph(building_id, floor_id):
    if db is None:
        return jsonify({"error": "Database not initialized."}), 500

    try:
        floor_ref = db.collection('buildings').document(building_id).collection('floors').document(floor_id)
        doc = floor_ref.get()

        if not doc.exists:
            return jsonify({"error": f"Floor '{floor_id}' not found in building '{building_id}'."}), 404

        floor_data = doc.to_dict()
        graph = floor_data.get("graph")

        if not graph:
            return jsonify({"error": "No navigation graph found for this floor."}), 404

        return jsonify(graph), 200

    except Exception as e:
        print(f"Error fetching navigation graph: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
