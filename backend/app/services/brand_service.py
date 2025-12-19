"""
Brand Service.

Handles AI-powered analysis of brand resources (images, text files).
Generates brief and detailed summaries for use in website generation.
"""
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from app.config import Config
from app.services.claude_service import claude_service
from app.utils.file_utils import read_json, write_json
from app.utils.encoding_utils import (
    get_image_metadata,
    prepare_image_for_claude,
    read_text_file,
    is_image_file,
    is_text_file,
)


# Prompts for resource analysis
IMAGE_ANALYSIS_PROMPT = """Analyze this image as a brand asset for website building. Provide:

1. **Brief Summary** (1-2 sentences): What is this image? (logo, photo, icon, illustration, etc.)

2. **Detailed Analysis**:
   - Type: (logo, photograph, icon, illustration, pattern, etc.)
   - Subject: What does it depict?
   - Colors: Primary colors visible (list hex codes if identifiable)
   - Style: (minimal, bold, vintage, modern, corporate, playful, etc.)
   - Suggested Usage: Where this could be used on a website (hero, header, background, icon, etc.)
   - Quality Notes: Any observations about resolution, transparency, etc.

Format your response as JSON:
{
    "brief_summary": "...",
    "detailed": {
        "type": "...",
        "subject": "...",
        "colors": ["#hex1", "#hex2"],
        "style": "...",
        "suggested_usage": ["hero", "header"],
        "quality_notes": "..."
    }
}"""

TEXT_ANALYSIS_PROMPT = """Analyze this text content as brand guidelines or documentation for website building. Provide:

1. **Brief Summary** (1-2 sentences): What information does this contain?

2. **Detailed Analysis**:
   - Content Type: (brand guidelines, copy text, about content, product description, etc.)
   - Key Information: Important details extracted
   - Brand Voice: Tone and style if apparent
   - Colors Mentioned: Any color codes or names
   - Fonts Mentioned: Any typography specifications
   - Actionable Items: Specific instructions or requirements

Format your response as JSON:
{
    "brief_summary": "...",
    "detailed": {
        "content_type": "...",
        "key_information": ["..."],
        "brand_voice": "...",
        "colors_mentioned": ["..."],
        "fonts_mentioned": ["..."],
        "actionable_items": ["..."]
    }
}

Here is the text content:
---
"""


class BrandService:
    """Service for analyzing brand resources with AI."""

    def __init__(self):
        self.model = Config.CLAUDE_MODEL

    def _get_assets_dir(self, chat_id: str) -> Path:
        """Get the assets directory for a chat."""
        return Config.CHATS_DIR / chat_id / "assets"

    def _get_raw_dir(self, chat_id: str) -> Path:
        """Get the raw assets directory."""
        raw_dir = self._get_assets_dir(chat_id) / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        return raw_dir

    def _get_processed_dir(self, chat_id: str) -> Path:
        """Get the processed assets directory."""
        processed_dir = self._get_assets_dir(chat_id) / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        return processed_dir

    def _get_index_path(self, chat_id: str) -> Path:
        """Get the resources index file path."""
        return self._get_assets_dir(chat_id) / "index.json"

    def _load_index(self, chat_id: str) -> Dict:
        """Load the resources index."""
        index_path = self._get_index_path(chat_id)
        data = read_json(index_path)
        if data is None:
            data = {"resources": [], "last_updated": datetime.now().isoformat()}
            write_json(index_path, data)
        return data

    def _save_index(self, chat_id: str, data: Dict) -> bool:
        """Save the resources index."""
        data["last_updated"] = datetime.now().isoformat()
        return write_json(self._get_index_path(chat_id), data)

    def save_raw_resource(self, chat_id: str, filename: str, file_data: bytes) -> Dict:
        """
        Save a raw resource file and create an index entry.

        Returns the resource entry with status 'pending'.
        """
        raw_dir = self._get_raw_dir(chat_id)
        filepath = raw_dir / filename

        # Save file
        with open(filepath, "wb") as f:
            f.write(file_data)

        # Determine resource type
        if is_image_file(filepath):
            resource_type = "image"
            metadata = get_image_metadata(filepath)
        elif is_text_file(filepath):
            resource_type = "text"
            metadata = {
                "filename": filename,
                "file_size_bytes": filepath.stat().st_size,
            }
        else:
            resource_type = "unknown"
            metadata = {"filename": filename}

        # Create resource entry
        resource = {
            "id": filename.rsplit(".", 1)[0] + "_" + datetime.now().strftime("%Y%m%d%H%M%S"),
            "filename": filename,
            "type": resource_type,
            "status": "pending",  # pending, processing, ready, error
            "raw_path": f"raw/{filename}",
            "processed_path": None,
            "metadata": metadata,
            "brief_summary": None,
            "created_at": datetime.now().isoformat(),
            "processed_at": None,
        }

        # Add to index
        index = self._load_index(chat_id)
        # Remove any existing entry with same filename
        index["resources"] = [r for r in index["resources"] if r["filename"] != filename]
        index["resources"].append(resource)
        self._save_index(chat_id, index)

        return resource

    def process_resource(self, chat_id: str, filename: str) -> Optional[Dict]:
        """
        Process a resource with AI analysis.

        Args:
            chat_id: The chat ID
            filename: The resource filename

        Returns:
            Updated resource entry or None if failed
        """
        index = self._load_index(chat_id)
        resource = next((r for r in index["resources"] if r["filename"] == filename), None)

        if not resource:
            return None

        # Update status to processing
        resource["status"] = "processing"
        self._save_index(chat_id, index)

        raw_path = self._get_raw_dir(chat_id) / filename

        try:
            if resource["type"] == "image":
                analysis = self._analyze_image(raw_path)
            elif resource["type"] == "text":
                analysis = self._analyze_text(raw_path)
            else:
                analysis = {"brief_summary": "Unknown file type", "detailed": {}}

            # Save processed analysis
            processed_filename = f"{resource['id']}_analysis.json"
            processed_path = self._get_processed_dir(chat_id) / processed_filename
            write_json(processed_path, analysis)

            # Update resource entry
            resource["status"] = "ready"
            resource["processed_path"] = f"processed/{processed_filename}"
            resource["brief_summary"] = analysis.get("brief_summary", "")
            resource["detailed_analysis"] = analysis.get("detailed", {})
            resource["processed_at"] = datetime.now().isoformat()

        except Exception as e:
            print(f"Error processing resource {filename}: {e}")
            resource["status"] = "error"
            resource["error"] = str(e)

        self._save_index(chat_id, index)
        return resource

    def _analyze_image(self, filepath: Path) -> Dict:
        """Analyze an image using Claude Vision."""
        image_content = prepare_image_for_claude(filepath)

        messages = [
            {
                "role": "user",
                "content": [
                    image_content,
                    {"type": "text", "text": IMAGE_ANALYSIS_PROMPT}
                ]
            }
        ]

        response = claude_service.send_message(
            messages=messages,
            system_prompt="You are a brand asset analyst. Analyze images for website building purposes. Always respond with valid JSON.",
            max_tokens=1000,
        )

        # Extract text from response (claude_service returns dict with content_blocks)
        response_text = ""
        for block in response.get("content_blocks", []):
            if hasattr(block, "text"):
                response_text = block.text
                break

        # Parse JSON response
        try:
            # Handle markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]

            return json.loads(response_text.strip())
        except json.JSONDecodeError:
            return {
                "brief_summary": response_text[:200],
                "detailed": {"raw_response": response_text}
            }

    def _analyze_text(self, filepath: Path) -> Dict:
        """Analyze a text file."""
        content = read_text_file(filepath)

        messages = [
            {
                "role": "user",
                "content": TEXT_ANALYSIS_PROMPT + content
            }
        ]

        response = claude_service.send_message(
            messages=messages,
            system_prompt="You are a brand guidelines analyst. Extract useful information for website building. Always respond with valid JSON.",
            max_tokens=1500,
        )

        # Extract text from response (claude_service returns dict with content_blocks)
        response_text = ""
        for block in response.get("content_blocks", []):
            if hasattr(block, "text"):
                response_text = block.text
                break

        # Parse JSON response
        try:
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]

            return json.loads(response_text.strip())
        except json.JSONDecodeError:
            return {
                "brief_summary": response_text[:200],
                "detailed": {"raw_response": response_text}
            }

    def get_resource(self, chat_id: str, filename: str) -> Optional[Dict]:
        """Get a specific resource by filename."""
        index = self._load_index(chat_id)
        return next((r for r in index["resources"] if r["filename"] == filename), None)

    def list_resources(self, chat_id: str) -> List[Dict]:
        """List all resources for a chat."""
        index = self._load_index(chat_id)
        return index.get("resources", [])

    def get_ready_resources(self, chat_id: str) -> List[Dict]:
        """Get all processed (ready) resources for a chat."""
        resources = self.list_resources(chat_id)
        return [r for r in resources if r["status"] == "ready"]

    def get_resources_summary(self, chat_id: str) -> str:
        """
        Get a formatted summary of all ready resources for system prompts.

        Returns a string suitable for including in chat system messages.
        """
        resources = self.get_ready_resources(chat_id)

        if not resources:
            return ""

        lines = ["## Available Brand Resources\n"]

        for r in resources:
            resource_type = r.get("type", "unknown")
            brief = r.get("brief_summary", "No description")
            metadata = r.get("metadata", {})

            if resource_type == "image":
                dims = ""
                if metadata.get("width") and metadata.get("height"):
                    dims = f" ({metadata['width']}x{metadata['height']})"
                lines.append(f"- **{r['filename']}**{dims}: {brief}")
                lines.append(f"  - Raw: `/api/chats/{chat_id}/assets/{r['raw_path']}`")
            else:
                lines.append(f"- **{r['filename']}**: {brief}")

        return "\n".join(lines)

    def get_resources_for_agent(self, chat_id: str) -> List[Dict]:
        """
        Get resources in format suitable for website agent.

        Returns list of resource objects with paths and summaries.
        """
        resources = self.get_ready_resources(chat_id)

        agent_resources = []
        for r in resources:
            agent_resources.append({
                "filename": r["filename"],
                "type": r["type"],
                "brief_summary": r.get("brief_summary", ""),
                "raw_url": f"/api/chats/{chat_id}/assets/raw/{r['filename']}",
                "metadata": r.get("metadata", {}),
                "detailed_analysis": r.get("detailed_analysis", {}),
            })

        return agent_resources


# Singleton instance
brand_service = BrandService()
