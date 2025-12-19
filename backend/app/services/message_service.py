"""
Message Service.

Handles message persistence within chats.
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.config import Config
from app.utils.file_utils import read_json, write_json
from app.utils.parsing_utils import build_tool_result


class MessageService:
    """
    Service class for message operations within chats.
    """

    def _get_chat_path(self, chat_id: str):
        """Get path to chat file."""
        return Config.CHATS_DIR / f"{chat_id}.json"

    def _load_chat(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """Load chat data."""
        return read_json(self._get_chat_path(chat_id))

    def _save_chat(self, chat_id: str, data: Dict[str, Any]) -> bool:
        """Save chat data."""
        return write_json(self._get_chat_path(chat_id), data)

    def get_messages(self, chat_id: str) -> List[Dict[str, Any]]:
        """
        Get all messages from a chat.

        Args:
            chat_id: The chat UUID

        Returns:
            List of message dicts
        """
        chat_data = self._load_chat(chat_id)
        if not chat_data:
            return []
        return chat_data.get("messages", [])

    def add_message(
        self,
        chat_id: str,
        role: str,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Add a message to a chat.

        Args:
            chat_id: The chat UUID
            role: Message role ('user' or 'assistant')
            content: Message content (string or list of content blocks)
            metadata: Optional metadata (model, tokens, etc.)

        Returns:
            The created message or None if chat not found
        """
        chat_data = self._load_chat(chat_id)
        if not chat_data:
            return None

        # Create message
        message = {
            "id": str(uuid.uuid4()),
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }

        if metadata:
            message.update(metadata)

        # Append to messages
        chat_data["messages"].append(message)
        chat_data["updated_at"] = datetime.now().isoformat()
        chat_data["message_count"] = len(chat_data["messages"])

        self._save_chat(chat_id, chat_data)

        return message

    def add_user_message(self, chat_id: str, content: str) -> Optional[Dict[str, Any]]:
        """Add a user text message."""
        return self.add_message(chat_id, "user", content)

    def add_assistant_message(
        self,
        chat_id: str,
        content: str,
        model: Optional[str] = None,
        tokens: Optional[Dict[str, int]] = None,
        error: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Add an assistant text message with metadata."""
        metadata = {}
        if model:
            metadata["model"] = model
        if tokens:
            metadata["tokens"] = tokens
        if error:
            metadata["error"] = True

        return self.add_message(chat_id, "assistant", content, metadata)

    def add_tool_result_message(
        self,
        chat_id: str,
        tool_use_id: str,
        result: str,
        is_error: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Add a tool result message.

        Args:
            chat_id: The chat UUID
            tool_use_id: The ID from the tool_use block
            result: The tool execution result
            is_error: Whether the tool execution failed

        Returns:
            The created message
        """
        content = [build_tool_result(tool_use_id, result, is_error)]
        return self.add_message(chat_id, "user", content)

    def build_api_messages(self, chat_id: str) -> List[Dict[str, str]]:
        """
        Build message array for Claude API call.

        Args:
            chat_id: The chat UUID

        Returns:
            List of message dicts ready for Claude API
        """
        messages = self.get_messages(chat_id)
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in messages
        ]


# Singleton instance
message_service = MessageService()
