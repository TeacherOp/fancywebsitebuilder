"""
Claude Service.

Thin wrapper around the Anthropic API for Claude interactions.
Used by main chat and website agent services.
"""
from typing import Any, Dict, List, Optional
import anthropic

from app.config import Config


class ClaudeService:
    """
    Service class for Claude API interactions.

    Provides a clean interface for making API calls with
    different configurations (prompts, tools, temperature).
    """

    def __init__(self):
        """Initialize with lazy-loaded client."""
        self._client: Optional[anthropic.Anthropic] = None

    def _get_client(self) -> anthropic.Anthropic:
        """
        Get or create the Anthropic client.

        Returns:
            Anthropic client instance

        Raises:
            ValueError: If ANTHROPIC_API_KEY is not set
        """
        if self._client is None:
            if not Config.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY not found in environment")
            self._client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        return self._client

    def send_message(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send messages to Claude and get a response.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt
            model: Claude model to use (default from config)
            max_tokens: Maximum tokens in response (default from config)
            temperature: Sampling temperature (default from config)
            tools: Optional list of tool definitions
            tool_choice: Optional tool choice configuration

        Returns:
            Dict containing content_blocks, model, usage, stop_reason

        Raises:
            ValueError: If API key is not configured
            anthropic.APIError: If API call fails
        """
        client = self._get_client()

        # Use config defaults if not specified
        model = model or Config.CLAUDE_MODEL
        max_tokens = max_tokens or Config.CLAUDE_MAX_TOKENS
        temperature = temperature if temperature is not None else Config.CLAUDE_TEMPERATURE

        # Build API call parameters
        api_params = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages,
            "temperature": temperature,
        }

        if system_prompt:
            api_params["system"] = system_prompt

        if tools:
            api_params["tools"] = tools

        if tool_choice:
            api_params["tool_choice"] = tool_choice

        # Make API call
        response = client.messages.create(**api_params)

        return {
            "content_blocks": response.content,
            "model": response.model,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            "stop_reason": response.stop_reason,
        }


# Singleton instance
claude_service = ClaudeService()
