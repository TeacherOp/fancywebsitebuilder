"""
Application Entry Point.

Run the Flask development server.
"""
from app import create_app
from app.config import Config

app = create_app()

if __name__ == "__main__":
    # Validate configuration
    Config.validate()

    print("Starting Website Builder API...")
    print(f"Data directory: {Config.DATA_DIR}")
    print(f"Claude model: {Config.CLAUDE_MODEL}")
    print("")
    print("API Endpoints:")
    print("  GET  /api/chats              - List all chats")
    print("  POST /api/chats              - Create new chat")
    print("  GET  /api/chats/<id>         - Get chat with messages")
    print("  POST /api/chats/<id>/messages - Send message")
    print("  GET  /api/websites           - List all websites")
    print("  GET  /api/websites/<id>      - Get website metadata")
    print("  GET  /api/websites/<id>/preview - Preview website")
    print("")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
