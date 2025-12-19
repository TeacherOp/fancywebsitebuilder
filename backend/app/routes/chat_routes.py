"""
Chat Routes.

API endpoints for chat operations.
"""
import json
import queue
import threading
from flask import Blueprint, request, jsonify, send_from_directory, Response
from werkzeug.utils import secure_filename

from app.config import Config
from app.services.chat_service import chat_service
from app.services.main_chat_service import main_chat_service
from app.services.brand_service import brand_service

chat_bp = Blueprint("chats", __name__)

ALLOWED_EXTENSIONS = {"png", "webp", "jpg", "jpeg", "svg", "ico", "gif", "txt", "md"}


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def process_resource_background(chat_id: str, filename: str):
    """Background task to process a resource."""
    try:
        brand_service.process_resource(chat_id, filename)
        print(f"Processed resource: {filename}")
    except Exception as e:
        print(f"Error processing resource {filename}: {e}")


@chat_bp.route("/chats", methods=["GET"])
def list_chats():
    """List all chats."""
    chats = chat_service.list_chats()
    return jsonify({"chats": chats})


@chat_bp.route("/chats", methods=["POST"])
def create_chat():
    """Create a new chat."""
    data = request.get_json() or {}
    title = data.get("title", "New Chat")

    chat = chat_service.create_chat(title=title)
    return jsonify(chat), 201


@chat_bp.route("/chats/<chat_id>", methods=["GET"])
def get_chat(chat_id: str):
    """Get a chat with messages."""
    chat = chat_service.get_chat(chat_id)
    if not chat:
        return jsonify({"error": "Chat not found"}), 404
    return jsonify(chat)


@chat_bp.route("/chats/<chat_id>", methods=["DELETE"])
def delete_chat(chat_id: str):
    """Delete a chat."""
    success = chat_service.delete_chat(chat_id)
    if not success:
        return jsonify({"error": "Failed to delete chat"}), 500
    return jsonify({"success": True})


@chat_bp.route("/chats/<chat_id>/messages", methods=["POST"])
def send_message(chat_id: str):
    """
    Send a message and get AI response.

    Request body:
        {"message": "User's message text"}

    Returns:
        {"user_message": {...}, "assistant_message": {...}}
    """
    chat = chat_service.get_chat(chat_id)
    if not chat:
        return jsonify({"error": "Chat not found"}), 404

    data = request.get_json()
    if not data or not data.get("message"):
        return jsonify({"error": "Message is required"}), 400

    user_message_text = data["message"]

    try:
        user_msg, assistant_msg = main_chat_service.send_message(
            chat_id=chat_id,
            user_message_text=user_message_text
        )

        updated_chat = chat_service.get_chat(chat_id)

        return jsonify({
            "user_message": user_msg,
            "assistant_message": assistant_msg,
            "website_id": updated_chat.get("website_id") if updated_chat else None
        })

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"Error processing message: {e}")
        return jsonify({"error": "Failed to process message"}), 500


@chat_bp.route("/chats/<chat_id>/messages/stream", methods=["POST"])
def send_message_stream(chat_id: str):
    """
    Send a message and stream progress updates via SSE.

    Request body:
        {"message": "User's message text"}

    Returns:
        SSE stream with progress events and final response
    """
    chat = chat_service.get_chat(chat_id)
    if not chat:
        return jsonify({"error": "Chat not found"}), 404

    data = request.get_json()
    if not data or not data.get("message"):
        return jsonify({"error": "Message is required"}), 400

    user_message_text = data["message"]

    # Queue for passing progress events from agent to SSE generator
    progress_queue: queue.Queue = queue.Queue()

    def progress_callback(event: dict):
        """Called by agent to report progress."""
        progress_queue.put(event)

    def run_chat():
        """Run the chat in a separate thread."""
        try:
            user_msg, assistant_msg = main_chat_service.send_message(
                chat_id=chat_id,
                user_message_text=user_message_text,
                progress_callback=progress_callback
            )

            updated_chat = chat_service.get_chat(chat_id)

            # Send final result
            progress_queue.put({
                "type": "complete",
                "user_message": user_msg,
                "assistant_message": assistant_msg,
                "website_id": updated_chat.get("website_id") if updated_chat else None
            })
        except Exception as e:
            print(f"Error in streaming message: {e}")
            progress_queue.put({
                "type": "error",
                "error": str(e)
            })

    def generate():
        """SSE generator yielding progress events."""
        # Start the chat processing in a separate thread
        thread = threading.Thread(target=run_chat)
        thread.start()

        while True:
            try:
                # Wait for next event (timeout to keep connection alive)
                event = progress_queue.get(timeout=30)

                # Format as SSE
                yield f"data: {json.dumps(event)}\n\n"

                # Stop if complete or error
                if event.get("type") in ("complete", "error"):
                    break

            except queue.Empty:
                # Send keepalive ping
                yield f"data: {json.dumps({'type': 'ping'})}\n\n"

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# ============== Resource/Asset Endpoints ==============

@chat_bp.route("/chats/<chat_id>/assets", methods=["POST"])
def upload_asset(chat_id: str):
    """
    Upload a brand asset (image/text) to the chat.

    Files are saved to the raw folder and queued for AI processing.
    Returns immediately with status 'pending'.
    """
    chat = chat_service.get_chat(chat_id)
    if not chat:
        return jsonify({"error": "Chat not found"}), 404

    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed. Supported: PNG, WebP, JPG, SVG, ICO, GIF, TXT, MD"}), 400

    # Secure the filename
    filename = secure_filename(file.filename)

    # Save to raw folder via brand service
    file_data = file.read()
    resource = brand_service.save_raw_resource(chat_id, filename, file_data)

    # Start background processing
    thread = threading.Thread(
        target=process_resource_background,
        args=(chat_id, filename)
    )
    thread.daemon = True
    thread.start()

    return jsonify({
        "filename": resource["filename"],
        "status": resource["status"],
        "type": resource["type"],
        "url": f"/api/chats/{chat_id}/assets/raw/{filename}"
    }), 201


@chat_bp.route("/chats/<chat_id>/assets", methods=["GET"])
def list_assets(chat_id: str):
    """List all resources/assets for a chat with their processing status."""
    chat = chat_service.get_chat(chat_id)
    if not chat:
        return jsonify({"error": "Chat not found"}), 404

    resources = brand_service.list_resources(chat_id)

    # Format for frontend
    assets = []
    for r in resources:
        assets.append({
            "filename": r["filename"],
            "type": r["type"],
            "status": r["status"],
            "url": f"/api/chats/{chat_id}/assets/raw/{r['filename']}",
            "brief_summary": r.get("brief_summary"),
            "metadata": r.get("metadata", {}),
        })

    return jsonify({"assets": assets})


@chat_bp.route("/chats/<chat_id>/assets/raw/<filename>", methods=["GET"])
def get_raw_asset(chat_id: str, filename: str):
    """Serve a raw (original) asset file."""
    raw_dir = Config.CHATS_DIR / chat_id / "assets" / "raw"

    if not raw_dir.exists():
        return jsonify({"error": "Asset not found"}), 404

    return send_from_directory(raw_dir, filename)


@chat_bp.route("/chats/<chat_id>/assets/processed/<filename>", methods=["GET"])
def get_processed_asset(chat_id: str, filename: str):
    """Serve a processed analysis file."""
    processed_dir = Config.CHATS_DIR / chat_id / "assets" / "processed"

    if not processed_dir.exists():
        return jsonify({"error": "Asset not found"}), 404

    return send_from_directory(processed_dir, filename)


@chat_bp.route("/chats/<chat_id>/assets/<filename>", methods=["GET"])
def get_asset(chat_id: str, filename: str):
    """
    Serve an asset file (backward compatibility).

    Checks raw folder first, then assets root.
    """
    raw_dir = Config.CHATS_DIR / chat_id / "assets" / "raw"
    assets_dir = Config.CHATS_DIR / chat_id / "assets"

    # Check raw folder first
    if (raw_dir / filename).exists():
        return send_from_directory(raw_dir, filename)

    # Fall back to assets root (backward compatibility)
    if (assets_dir / filename).exists():
        return send_from_directory(assets_dir, filename)

    return jsonify({"error": "Asset not found"}), 404


@chat_bp.route("/chats/<chat_id>/resources/<filename>", methods=["GET"])
def get_resource_details(chat_id: str, filename: str):
    """Get detailed information about a specific resource."""
    resource = brand_service.get_resource(chat_id, filename)

    if not resource:
        return jsonify({"error": "Resource not found"}), 404

    return jsonify(resource)


@chat_bp.route("/chats/<chat_id>/resources/<filename>/reprocess", methods=["POST"])
def reprocess_resource(chat_id: str, filename: str):
    """Manually trigger reprocessing of a resource."""
    resource = brand_service.get_resource(chat_id, filename)

    if not resource:
        return jsonify({"error": "Resource not found"}), 404

    # Start background processing
    thread = threading.Thread(
        target=process_resource_background,
        args=(chat_id, filename)
    )
    thread.daemon = True
    thread.start()

    return jsonify({"status": "processing", "message": "Reprocessing started"})


# ============== Brand Guidelines Endpoints ==============

@chat_bp.route("/chats/<chat_id>/brand-guidelines", methods=["PUT"])
def update_brand_guidelines(chat_id: str):
    """
    Update brand guidelines for a chat.

    Request body:
        {"brand_guidelines": "Text describing brand colors, fonts, style..."}
    """
    chat = chat_service.get_chat(chat_id)
    if not chat:
        return jsonify({"error": "Chat not found"}), 404

    data = request.get_json() or {}
    brand_guidelines = data.get("brand_guidelines", "")

    success = chat_service.update_brand_guidelines(chat_id, brand_guidelines)
    if not success:
        return jsonify({"error": "Failed to update brand guidelines"}), 500

    return jsonify({"success": True, "brand_guidelines": brand_guidelines})


@chat_bp.route("/chats/<chat_id>/brand-guidelines", methods=["GET"])
def get_brand_guidelines(chat_id: str):
    """Get brand guidelines for a chat."""
    chat = chat_service.get_chat(chat_id)
    if not chat:
        return jsonify({"error": "Chat not found"}), 404

    return jsonify({"brand_guidelines": chat.get("brand_guidelines", "")})
