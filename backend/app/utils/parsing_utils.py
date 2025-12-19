"""
Claude Response Parsing Utilities.

Helpers for parsing Claude API responses, extracting tool calls,
and building message content blocks.
"""
from typing import Any, Dict, List, Optional


def is_tool_use(response: Dict[str, Any]) -> bool:
    """
    Check if the response contains tool use.

    Args:
        response: Claude API response

    Returns:
        True if response has tool_use stop reason
    """
    return response.get("stop_reason") == "tool_use"


def extract_text(response: Dict[str, Any]) -> str:
    """
    Extract text content from Claude response.

    Args:
        response: Claude API response

    Returns:
        Concatenated text from all text blocks
    """
    content_blocks = response.get("content_blocks", [])
    text_parts = []

    for block in content_blocks:
        block_type = _get_block_attr(block, "type")
        if block_type == "text":
            text = _get_block_attr(block, "text", "")
            if text:
                text_parts.append(text)

    return "\n".join(text_parts)


def extract_tool_use_blocks(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract tool_use blocks from Claude response.

    Args:
        response: Claude API response

    Returns:
        List of tool use dictionaries with id, name, input
    """
    content_blocks = response.get("content_blocks", [])
    tool_blocks = []

    for block in content_blocks:
        block_type = _get_block_attr(block, "type")
        if block_type == "tool_use":
            tool_blocks.append({
                "id": _get_block_attr(block, "id", ""),
                "name": _get_block_attr(block, "name", ""),
                "input": _get_block_attr(block, "input", {})
            })

    return tool_blocks


def serialize_content_blocks(content_blocks: List[Any]) -> List[Dict[str, Any]]:
    """
    Serialize Claude content blocks for storage.

    Converts Anthropic SDK objects to plain dicts.

    Args:
        content_blocks: List of content blocks from Claude response

    Returns:
        List of serialized content block dicts
    """
    serialized = []

    for block in content_blocks:
        block_type = _get_block_attr(block, "type")

        if block_type == "text":
            serialized.append({
                "type": "text",
                "text": _get_block_attr(block, "text", "")
            })
        elif block_type == "tool_use":
            serialized.append({
                "type": "tool_use",
                "id": _get_block_attr(block, "id", ""),
                "name": _get_block_attr(block, "name", ""),
                "input": _get_block_attr(block, "input", {})
            })

    return serialized


def build_tool_result(tool_use_id: str, result: str, is_error: bool = False) -> Dict[str, Any]:
    """
    Build a single tool_result content block.

    Args:
        tool_use_id: The ID from the tool_use block
        result: The tool execution result
        is_error: Whether the tool execution failed

    Returns:
        Tool result content block
    """
    block = {
        "type": "tool_result",
        "tool_use_id": tool_use_id,
        "content": result
    }
    if is_error:
        block["is_error"] = True
    return block


def build_tool_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Build tool_result content blocks for multiple tool calls.

    Args:
        results: List of dicts with tool_use_id, result, is_error

    Returns:
        List of tool result content blocks
    """
    return [
        build_tool_result(
            r["tool_use_id"],
            r["result"],
            r.get("is_error", False)
        )
        for r in results
    ]


def _get_block_attr(block: Any, attr: str, default: Any = None) -> Any:
    """
    Get attribute from a block (handles both dict and object).

    Args:
        block: Content block (dict or object)
        attr: Attribute name
        default: Default value if not found

    Returns:
        Attribute value
    """
    if isinstance(block, dict):
        return block.get(attr, default)
    return getattr(block, attr, default)
