import re
import uuid
from flask import Blueprint, request, jsonify
from app import bucket

image_bp = Blueprint('image', __name__)


@image_bp.route('', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image part"}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Generate a unique filename
    blob = bucket.blob(f"pois/{uuid.uuid4()}-{file.filename}")
    blob.upload_from_file(file, content_type=file.content_type)

    # Make it public
    blob.make_public()

    return jsonify({"url": blob.public_url})


@image_bp.route('', methods=['DELETE'])
def delete_image():
    try:
        data = request.get_json()
        if not data or "url" not in data:
            return jsonify({"error": "No image URL provided"}), 400

        image_url = data["url"]

        # Adjusted regex for your URL format
        match = re.search(r"/pois/(.+)", image_url)
        if not match:
            return jsonify({"error": "Invalid Firebase URL"}), 400

        file_path = "pois/" + match.group(1)

        blob = bucket.blob(file_path)

        if not blob.exists():
            return jsonify({"error": "File not found"}), 404

        blob.delete()

        return jsonify({"message": "File deleted successfully", "path": file_path}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


