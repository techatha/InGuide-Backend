from flask import Blueprint, request, jsonify
from app import bucket

floors_bp = Blueprint('floors', __name__)


@floors_bp.route('/getFloorPlan', methods=['GET'])
def get_floor_plan():
    file_name = request.args.get('floor')
    if not file_name:
        # Return a 400 Bad Request error if the 'fileName' parameter is missing.
        return jsonify({"error": "Missing 'fileName' query parameter."}), 400
    try:
        blob = bucket.blob(file_name)
        if not blob.exists():
            return jsonify({"error": f"File '{file_name}' not found."}), 404
        url = blob.public_url
        return jsonify({"url": url}), 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error."}), 500
