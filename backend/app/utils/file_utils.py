"""
File Utilities.

Helper functions for reading and writing JSON files.
"""
import json
from pathlib import Path
from typing import Any, Dict, Optional


def read_json(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Read a JSON file and return its contents.

    Args:
        file_path: Path to the JSON file

    Returns:
        Parsed JSON data or None if file doesn't exist or is invalid
    """
    if not file_path.exists():
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading {file_path}: {e}")
        return None


def write_json(file_path: Path, data: Dict[str, Any]) -> bool:
    """
    Write data to a JSON file.

    Args:
        file_path: Path to the JSON file
        data: Data to write

    Returns:
        True if successful, False otherwise
    """
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except IOError as e:
        print(f"Error writing {file_path}: {e}")
        return False


def read_text(file_path: Path) -> Optional[str]:
    """
    Read a text file and return its contents.

    Args:
        file_path: Path to the text file

    Returns:
        File contents or None if file doesn't exist
    """
    if not file_path.exists():
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except IOError as e:
        print(f"Error reading {file_path}: {e}")
        return None


def write_text(file_path: Path, content: str) -> bool:
    """
    Write text to a file.

    Args:
        file_path: Path to the file
        content: Text content to write

    Returns:
        True if successful, False otherwise
    """
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except IOError as e:
        print(f"Error writing {file_path}: {e}")
        return False
