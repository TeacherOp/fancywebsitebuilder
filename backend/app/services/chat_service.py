"""
Chat Service.

Handles CRUD operations for chats. Each chat has:
- An entry in the index file (metadata)
- A separate JSON file with full message history
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.config import Config
from app.utils.file_utils import read_json, write_json


class ChatService:
    """
    Service class for chat CRUD operations.

    Manages chat index and individual chat files.
    """

    def __init__(self):
        """Initialize the chat service."""
        self.index_path = Config.CHATS_DIR / "index.json"

    def _load_index(self) -> Dict[str, Any]:
        """Load the chat index or create if missing."""
        data = read_json(self.index_path)
        if data is None:
            data = {"chats": [], "last_updated": datetime.now().isoformat()}
            write_json(self.index_path, data)
        return data

    def _save_index(self, data: Dict[str, Any]) -> bool:
        """Save the chat index."""
        data["last_updated"] = datetime.now().isoformat()
        return write_json(self.index_path, data)

    def _get_chat_path(self, chat_id: str):
        """Get path to individual chat file."""
        return Config.CHATS_DIR / f"{chat_id}.json"

    def list_chats(self) -> List[Dict[str, Any]]:
        """
        List all chats with metadata.

        Returns:
            List of chat metadata dicts (id, title, created_at, etc.)
        """
        index = self._load_index()
        return index.get("chats", [])

    def get_chat(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a chat with its messages.

        Args:
            chat_id: The chat UUID

        Returns:
            Chat data with messages or None if not found
        """
        chat_path = self._get_chat_path(chat_id)
        return read_json(chat_path)

    def create_chat(self, title: str = "New Chat") -> Dict[str, Any]:
        """
        Create a new chat.

        Args:
            title: Initial chat title

        Returns:
            The created chat data
        """
        chat_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        # Create chat data
        chat_data = {
            "id": chat_id,
            "title": title,
            "created_at": now,
            "updated_at": now,
            "message_count": 0,
            "messages": [],
            "website_id": None,  # Will be set when website is generated
        }

        # Save chat file
        chat_path = self._get_chat_path(chat_id)
        write_json(chat_path, chat_data)

        # Update index
        index = self._load_index()
        index["chats"].insert(0, {
            "id": chat_id,
            "title": title,
            "created_at": now,
            "updated_at": now,
            "message_count": 0,
        })
        self._save_index(index)

        return chat_data

    def update_chat(self, chat_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update chat metadata.

        Args:
            chat_id: The chat UUID
            updates: Fields to update (title, website_id, etc.)

        Returns:
            True if successful
        """
        chat_data = self.get_chat(chat_id)
        if not chat_data:
            return False

        # Update chat file
        for key, value in updates.items():
            if key != "messages":  # Don't update messages via this method
                chat_data[key] = value
        chat_data["updated_at"] = datetime.now().isoformat()

        chat_path = self._get_chat_path(chat_id)
        write_json(chat_path, chat_data)

        # Update index entry
        index = self._load_index()
        for chat in index["chats"]:
            if chat["id"] == chat_id:
                for key, value in updates.items():
                    if key in ["title", "message_count", "website_id"]:
                        chat[key] = value
                chat["updated_at"] = chat_data["updated_at"]
                break
        self._save_index(index)

        return True

    def delete_chat(self, chat_id: str) -> bool:
        """
        Delete a chat.

        Args:
            chat_id: The chat UUID

        Returns:
            True if successful
        """
        # Delete chat file
        chat_path = self._get_chat_path(chat_id)
        if chat_path.exists():
            chat_path.unlink()

        # Remove from index
        index = self._load_index()
        index["chats"] = [c for c in index["chats"] if c["id"] != chat_id]
        self._save_index(index)

        return True

    def sync_to_index(self, chat_id: str) -> bool:
        """
        Sync chat data to index (for message count updates).

        Args:
            chat_id: The chat UUID

        Returns:
            True if successful
        """
        chat_data = self.get_chat(chat_id)
        if not chat_data:
            return False

        return self.update_chat(chat_id, {
            "message_count": chat_data.get("message_count", 0)
        })


# Singleton instance
chat_service = ChatService()
