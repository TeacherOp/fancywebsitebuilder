"""
Website Service.

Handles website file operations and metadata management.
"""
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import Config
from app.utils.file_utils import read_json, write_json, read_text, write_text


class WebsiteService:
    """
    Service class for website file management.
    """

    def _get_website_dir(self, website_id: str) -> Path:
        """Get path to website directory."""
        return Config.WEBSITES_DIR / website_id

    def _get_assets_dir(self, website_id: str) -> Path:
        """Get path to website assets directory."""
        return self._get_website_dir(website_id) / "assets"

    def _get_metadata_path(self, website_id: str) -> Path:
        """Get path to website metadata file."""
        return self._get_website_dir(website_id) / "metadata.json"

    def create_website(self, chat_id: str) -> Dict[str, Any]:
        """
        Create a new website.

        Args:
            chat_id: The associated chat ID

        Returns:
            Website metadata dict
        """
        website_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        website_dir = self._get_website_dir(website_id)
        website_dir.mkdir(parents=True, exist_ok=True)

        assets_dir = self._get_assets_dir(website_id)
        assets_dir.mkdir(parents=True, exist_ok=True)

        metadata = {
            "id": website_id,
            "chat_id": chat_id,
            "status": "generating",
            "created_at": now,
            "updated_at": now,
            "files": [],
            "images": [],
            "plan": None,
            "summary": None,
            "pages_created": [],
            "features_implemented": [],
        }

        write_json(self._get_metadata_path(website_id), metadata)

        return metadata

    def get_website(self, website_id: str) -> Optional[Dict[str, Any]]:
        """Get website metadata."""
        return read_json(self._get_metadata_path(website_id))

    def update_website(self, website_id: str, updates: Dict[str, Any]) -> bool:
        """Update website metadata."""
        metadata = self.get_website(website_id)
        if not metadata:
            return False

        for key, value in updates.items():
            metadata[key] = value
        metadata["updated_at"] = datetime.now().isoformat()

        return write_json(self._get_metadata_path(website_id), metadata)

    def list_websites(self) -> List[Dict[str, Any]]:
        """List all websites."""
        websites = []

        if not Config.WEBSITES_DIR.exists():
            return websites

        for website_dir in Config.WEBSITES_DIR.iterdir():
            if website_dir.is_dir():
                metadata = read_json(website_dir / "metadata.json")
                if metadata:
                    websites.append({
                        "id": metadata.get("id"),
                        "status": metadata.get("status"),
                        "site_name": metadata.get("plan", {}).get("site_name") if metadata.get("plan") else None,
                        "created_at": metadata.get("created_at"),
                        "pages_created": metadata.get("pages_created", []),
                    })

        # Sort by created_at descending
        websites.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        return websites

    def create_file(
        self,
        website_id: str,
        filename: str,
        content: str,
        images: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create or overwrite a website file.

        Replaces IMAGE_N placeholders with actual URLs.

        Args:
            website_id: The website ID
            filename: Name of the file
            content: File content
            images: List of image info dicts for placeholder replacement

        Returns:
            Result dict with success status
        """
        website_dir = self._get_website_dir(website_id)
        file_path = website_dir / filename

        # Replace image placeholders
        final_content = content
        if images:
            for image_info in images:
                placeholder = image_info.get("placeholder", "")
                url = image_info.get("url", "")
                if placeholder and url:
                    final_content = final_content.replace(
                        f'"{placeholder}"', f'"{url}"'
                    )
                    final_content = final_content.replace(
                        f"'{placeholder}'", f"'{url}'"
                    )

        success = write_text(file_path, final_content)

        if success:
            # Update metadata
            metadata = self.get_website(website_id)
            if metadata:
                files = metadata.get("files", [])
                if filename not in files:
                    files.append(filename)
                self.update_website(website_id, {"files": files})

        line_count = len(final_content.split("\n"))

        return {
            "success": success,
            "filename": filename,
            "lines": line_count,
            "chars": len(final_content)
        }

    def read_file(
        self,
        website_id: str,
        filename: str,
        start_line: int = None,
        end_line: int = None
    ) -> Dict[str, Any]:
        """
        Read a website file with smart context.

        Args:
            website_id: The website ID
            filename: Name of the file
            start_line: Starting line (1-indexed, optional)
            end_line: Ending line (1-indexed, optional)

        Returns:
            Result dict with file content
        """
        website_dir = self._get_website_dir(website_id)
        file_path = website_dir / filename

        content = read_text(file_path)
        if content is None:
            return {
                "success": False,
                "error": f"File '{filename}' does not exist"
            }

        lines = content.split("\n")
        total_lines = len(lines)

        # Small file: return all
        if total_lines < 100:
            return {
                "success": True,
                "filename": filename,
                "total_lines": total_lines,
                "content": content
            }

        # Large file, no range: return overview
        if start_line is None:
            first_50 = "\n".join(lines[:50])
            last_50 = "\n".join(lines[-50:])
            return {
                "success": True,
                "filename": filename,
                "total_lines": total_lines,
                "content": f"[Lines 1-50]\n{first_50}\n\n... [{total_lines - 100} lines omitted] ...\n\n[Lines {total_lines-49}-{total_lines}]\n{last_50}"
            }

        # Specific range with context
        context_start = max(0, start_line - 1 - 5)
        context_end = min(total_lines, (end_line or total_lines) + 5)

        range_content = "\n".join(lines[context_start:context_end])
        return {
            "success": True,
            "filename": filename,
            "total_lines": total_lines,
            "range": f"{context_start + 1}-{context_end}",
            "content": range_content
        }

    def update_file_lines(
        self,
        website_id: str,
        filename: str,
        start_line: int,
        end_line: int,
        new_content: str,
        images: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Replace a line range in a file.

        Args:
            website_id: The website ID
            filename: Name of the file
            start_line: Starting line (1-indexed)
            end_line: Ending line (1-indexed)
            new_content: New content to replace
            images: Image info for placeholder replacement

        Returns:
            Result dict
        """
        website_dir = self._get_website_dir(website_id)
        file_path = website_dir / filename

        content = read_text(file_path)
        if content is None:
            return {
                "success": False,
                "error": f"File '{filename}' does not exist"
            }

        lines = content.split("\n")

        if start_line < 1 or end_line > len(lines):
            return {
                "success": False,
                "error": f"Invalid line range. File has {len(lines)} lines."
            }

        # Replace image placeholders
        final_content = new_content
        if images:
            for image_info in images:
                placeholder = image_info.get("placeholder", "")
                url = image_info.get("url", "")
                if placeholder and url:
                    final_content = final_content.replace(
                        f'"{placeholder}"', f'"{url}"'
                    )

        # Replace lines
        new_lines = final_content.split("\n")
        lines[start_line - 1:end_line] = new_lines

        success = write_text(file_path, "\n".join(lines))

        return {
            "success": success,
            "message": f"Updated lines {start_line}-{end_line}"
        }

    def insert_code(
        self,
        website_id: str,
        filename: str,
        after_line: int,
        content: str,
        images: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Insert code after a specific line.

        Args:
            website_id: The website ID
            filename: Name of the file
            after_line: Line after which to insert (0 for beginning)
            content: Content to insert
            images: Image info for placeholder replacement

        Returns:
            Result dict
        """
        website_dir = self._get_website_dir(website_id)
        file_path = website_dir / filename

        file_content = read_text(file_path)
        if file_content is None:
            return {
                "success": False,
                "error": f"File '{filename}' does not exist"
            }

        lines = file_content.split("\n")

        if after_line < 0 or after_line > len(lines):
            return {
                "success": False,
                "error": f"Invalid line number. File has {len(lines)} lines."
            }

        # Replace image placeholders
        final_content = content
        if images:
            for image_info in images:
                placeholder = image_info.get("placeholder", "")
                url = image_info.get("url", "")
                if placeholder and url:
                    final_content = final_content.replace(
                        f'"{placeholder}"', f'"{url}"'
                    )

        # Insert new lines
        new_lines = final_content.split("\n")
        lines[after_line:after_line] = new_lines

        success = write_text(file_path, "\n".join(lines))

        return {
            "success": success,
            "message": f"Inserted {len(new_lines)} lines after line {after_line}"
        }

    def add_image(
        self,
        website_id: str,
        purpose: str,
        filename: str
    ) -> Dict[str, str]:
        """
        Record a generated image.

        Args:
            website_id: The website ID
            purpose: Image purpose
            filename: Image filename

        Returns:
            Image info dict with placeholder and URL
        """
        metadata = self.get_website(website_id)
        if not metadata:
            return {}

        images = metadata.get("images", [])
        index = len(images) + 1

        image_info = {
            "purpose": purpose,
            "filename": filename,
            "placeholder": f"IMAGE_{index}",
            "url": f"/api/websites/{website_id}/files/assets/{filename}"
        }

        images.append(image_info)
        self.update_website(website_id, {"images": images})

        return image_info


# Singleton instance
website_service = WebsiteService()
