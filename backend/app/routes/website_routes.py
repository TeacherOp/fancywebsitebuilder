"""
Website Routes.

API endpoints for website operations and preview serving.
"""
from flask import Blueprint, jsonify, send_from_directory, abort, Response
from pathlib import Path

from app.config import Config
from app.services.website_service import website_service

website_bp = Blueprint("websites", __name__)


@website_bp.route("/websites", methods=["GET"])
def list_websites():
    """List all generated websites."""
    websites = website_service.list_websites()
    return jsonify({"websites": websites})


@website_bp.route("/websites/<website_id>", methods=["GET"])
def get_website(website_id: str):
    """Get website metadata."""
    website = website_service.get_website(website_id)
    if not website:
        return jsonify({"error": "Website not found"}), 404
    return jsonify(website)


@website_bp.route("/websites/<website_id>/preview", methods=["GET"])
@website_bp.route("/websites/<website_id>/preview/<path:filepath>", methods=["GET"])
def preview_website(website_id: str, filepath: str = "index.html"):
    """
    Serve website files for iframe preview.

    - /preview serves index.html (with base tag injected)
    - /preview/styles.css serves styles.css
    - /preview/assets/image.png serves assets/image.png

    This allows relative paths in HTML to work correctly.
    """
    website_dir = Config.WEBSITES_DIR / website_id

    if not website_dir.exists():
        return jsonify({"error": "Website not found"}), 404

    # Security check: prevent directory traversal
    try:
        full_path = (website_dir / filepath).resolve()
        if not str(full_path).startswith(str(website_dir.resolve())):
            abort(403)
    except (ValueError, RuntimeError):
        abort(400)

    if not full_path.exists():
        abort(404)

    # For HTML files, inject base tag so relative paths work
    if filepath.endswith(".html"):
        html_content = full_path.read_text(encoding="utf-8")
        base_url = f"/api/websites/{website_id}/preview/"
        # Inject base tag after <head>
        if "<head>" in html_content:
            html_content = html_content.replace(
                "<head>",
                f'<head>\n    <base href="{base_url}">'
            )
        return Response(html_content, mimetype="text/html")

    # For other files, serve directly
    file_dir = full_path.parent
    filename = full_path.name
    return send_from_directory(file_dir, filename)


@website_bp.route("/websites/<website_id>/files/<path:filepath>", methods=["GET"])
def serve_file(website_id: str, filepath: str):
    """
    Serve any website file (HTML, CSS, JS, images).

    Handles both root files and nested paths like assets/image.png.
    """
    website_dir = Config.WEBSITES_DIR / website_id

    if not website_dir.exists():
        abort(404)

    # Security check: prevent directory traversal
    try:
        full_path = (website_dir / filepath).resolve()
        if not str(full_path).startswith(str(website_dir.resolve())):
            abort(403)
    except (ValueError, RuntimeError):
        abort(400)

    if not full_path.exists():
        abort(404)

    # Determine the directory and filename
    file_dir = full_path.parent
    filename = full_path.name

    return send_from_directory(file_dir, filename)


@website_bp.route("/websites/<website_id>/pages", methods=["GET"])
def list_pages(website_id: str):
    """List all HTML pages in a website."""
    website_dir = Config.WEBSITES_DIR / website_id

    if not website_dir.exists():
        return jsonify({"error": "Website not found"}), 404

    pages = []
    for file_path in website_dir.glob("*.html"):
        pages.append({
            "filename": file_path.name,
            "url": f"/api/websites/{website_id}/files/{file_path.name}"
        })

    return jsonify({"pages": pages})
