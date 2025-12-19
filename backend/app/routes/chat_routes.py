"""
Chat Routes.

API endpoints for chat operations.
"""
from flask import Blueprint, request, jsonify

from app.services.chat_service import chat_service
from app.services.main_chat_service import main_chat_service

chat_bp = Blueprint("chats", __name__)


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
    # Validate chat exists
    chat = chat_service.get_chat(chat_id)
    if not chat:
        return jsonify({"error": "Chat not found"}), 404

    # Get message from request
    data = request.get_json()
    if not data or not data.get("message"):
        return jsonify({"error": "Message is required"}), 400

    user_message_text = data["message"]

    try:
        # Process message and get AI response
        user_msg, assistant_msg = main_chat_service.send_message(
            chat_id=chat_id,
            user_message_text=user_message_text
        )

        # Get updated chat for website_id
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
