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


@image_bp.route('/delete-image', methods=['DELETE'])
def delete_image():
    try:
        data = request.get_json()
        image_url = data.get("url")

        if not image_url:
            return jsonify({"error": "No image URL provided"}), 400

        # Extract filename from Firebase URL
        # Example: https://firebasestorage.googleapis.com/v0/b/inguide-se953499.appspot.com/o/floorplans%2Fmyimg.png?alt=media
        match = re.search(r"/o/(.+)\?alt=media", image_url)
        if not match:
            return jsonify({"error": "Invalid Firebase URL"}), 400

        file_path = match.group(1).replace("%2F", "/")  # decode `%2F` → `/`

        # Get bucket and blob
        blob = bucket.blob(file_path)

        if not blob.exists():
            return jsonify({"error": "File not found"}), 404

        # Delete file
        blob.delete()

        return jsonify({"message": "File deleted successfully", "path": file_path}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

