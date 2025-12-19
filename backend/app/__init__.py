"""
Flask Application Factory.

Creates and configures the Flask application with CORS support
and registers all route blueprints.
"""
from flask import Flask
from flask_cors import CORS

from app.config import Config


def create_app():
    """
    Create and configure the Flask application.

    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)

    # Enable CORS for React frontend
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "http://localhost:5173"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # Register blueprints
    from app.routes.chat_routes import chat_bp
    from app.routes.website_routes import website_bp

    app.register_blueprint(chat_bp, url_prefix="/api")
    app.register_blueprint(website_bp, url_prefix="/api")

    # Ensure data directories exist
    Config.ensure_directories()

    return app
