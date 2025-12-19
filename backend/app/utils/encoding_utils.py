"""
Encoding utilities for handling images and files.

Provides functions for base64 encoding/decoding and image metadata extraction.
"""
import base64
import mimetypes
from pathlib import Path
from typing import Dict, Optional, Tuple
from PIL import Image


def get_mime_type(filepath: Path) -> str:
    """
    Get MIME type for a file.

    Args:
        filepath: Path to the file

    Returns:
        MIME type string (e.g., 'image/png')
    """
    mime_type, _ = mimetypes.guess_type(str(filepath))
    if mime_type is None:
        # Default fallbacks based on extension
        ext = filepath.suffix.lower()
        mime_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".svg": "image/svg+xml",
            ".ico": "image/x-icon",
            ".txt": "text/plain",
            ".md": "text/markdown",
        }
        mime_type = mime_map.get(ext, "application/octet-stream")
    return mime_type


def encode_image_to_base64(filepath: Path) -> str:
    """
    Encode an image file to base64 string.

    Args:
        filepath: Path to the image file

    Returns:
        Base64 encoded string
    """
    with open(filepath, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def get_image_metadata(filepath: Path) -> Dict:
    """
    Extract metadata from an image file.

    Args:
        filepath: Path to the image file

    Returns:
        Dict with width, height, format, file_size, mime_type
    """
    metadata = {
        "filename": filepath.name,
        "file_size_bytes": filepath.stat().st_size,
        "mime_type": get_mime_type(filepath),
    }

    # Try to get image dimensions
    try:
        with Image.open(filepath) as img:
            metadata["width"] = img.width
            metadata["height"] = img.height
            metadata["format"] = img.format
            metadata["mode"] = img.mode  # RGB, RGBA, etc.
    except Exception:
        # Not a valid image or unsupported format (e.g., SVG)
        metadata["width"] = None
        metadata["height"] = None
        metadata["format"] = filepath.suffix.upper().lstrip(".")
        metadata["mode"] = None

    return metadata


def prepare_image_for_claude(filepath: Path) -> Dict:
    """
    Prepare an image for sending to Claude API.

    Args:
        filepath: Path to the image file

    Returns:
        Dict in Claude's image content block format
    """
    mime_type = get_mime_type(filepath)
    base64_data = encode_image_to_base64(filepath)

    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": mime_type,
            "data": base64_data,
        }
    }


def read_text_file(filepath: Path, max_chars: int = 50000) -> str:
    """
    Read a text file with optional truncation.

    Args:
        filepath: Path to the text file
        max_chars: Maximum characters to read

    Returns:
        File contents as string
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read(max_chars)
            if len(content) == max_chars:
                content += "\n... [truncated]"
            return content
    except UnicodeDecodeError:
        # Try with different encoding
        with open(filepath, "r", encoding="latin-1") as f:
            content = f.read(max_chars)
            if len(content) == max_chars:
                content += "\n... [truncated]"
            return content


def is_image_file(filepath: Path) -> bool:
    """Check if file is an image based on extension."""
    return filepath.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico"}


def is_text_file(filepath: Path) -> bool:
    """Check if file is a text file based on extension."""
    return filepath.suffix.lower() in {".txt", ".md", ".text", ".markdown"}
