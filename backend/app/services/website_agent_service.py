"""
Website Agent Service.

AI agent for generating complete websites using an agentic loop pattern.
"""
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from app.config import Config
from app.services.claude_service import claude_service
from app.services.website_service import website_service
from app.services.imagen_service import imagen_service
from app.tools.tool_definitions import (
    get_website_agent_tools,
    WEBSITE_AGENT_SYSTEM_PROMPT,
)
from app.utils.parsing_utils import (
    is_tool_use,
    extract_tool_use_blocks,
    serialize_content_blocks,
)
from app.utils.file_utils import write_json


class WebsiteAgentService:
    """
    Website generation agent with multi-step file operations workflow.
    """

    MAX_ITERATIONS = Config.WEBSITE_AGENT_MAX_ITERATIONS

    def generate_website(
        self,
        chat_id: str,
        direction: str,
        resources: List[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        """
        Run the agent to generate a website.

        Args:
            chat_id: Associated chat ID
            direction: User's requirements and design preferences
            resources: Optional list of user-uploaded brand resources
            progress_callback: Optional callback for progress updates

        Returns:
            Result dict with website info or error
        """
        resources = resources or []

        def emit_progress(event_type: str, **kwargs):
            """Emit a progress event if callback is provided."""
            if progress_callback:
                progress_callback({"type": event_type, **kwargs})
        execution_id = str(uuid.uuid4())
        started_at = datetime.now().isoformat()

        # Create website
        website = website_service.create_website(chat_id)
        website_id = website["id"]

        tools = get_website_agent_tools()

        # Build initial user message
        user_message = f"""Create a professional website based on the following direction:

{direction}

Please create a complete website following the workflow:
1. Plan the website structure, pages, features, and design system
2. Generate any images needed (photos/illustrations only)
3. Create all files iteratively (HTML pages, CSS, JS)
4. Ensure navigation and footer are consistent across all pages
5. Finalize when all files are complete"""

        # Add resources section if available
        if resources:
            resources_section = "\n\n## Available Brand Resources\n"
            resources_section += "Use these user-provided assets in the website:\n\n"
            for r in resources:
                resources_section += f"- **{r.get('filename')}** ({r.get('type')})\n"
                resources_section += f"  Summary: {r.get('brief_summary', 'No description')}\n"
                resources_section += f"  URL: {r.get('raw_url')}\n\n"
            user_message += resources_section

        messages = [{"role": "user", "content": user_message}]

        total_input_tokens = 0
        total_output_tokens = 0

        print(f"[WebsiteAgent] Starting (website_id: {website_id[:8]})")
        emit_progress("agent_started", website_id=website_id)

        for iteration in range(1, self.MAX_ITERATIONS + 1):
            print(f"  Iteration {iteration}/{self.MAX_ITERATIONS}")
            emit_progress("iteration_start", iteration=iteration, max_iterations=self.MAX_ITERATIONS)

            response = claude_service.send_message(
                messages=messages,
                system_prompt=WEBSITE_AGENT_SYSTEM_PROMPT,
                tools=tools,
                tool_choice={"type": "any"},
            )

            total_input_tokens += response["usage"]["input_tokens"]
            total_output_tokens += response["usage"]["output_tokens"]

            # Serialize and add assistant response
            content_blocks = response.get("content_blocks", [])
            serialized_content = serialize_content_blocks(content_blocks)
            messages.append({"role": "assistant", "content": serialized_content})

            # Process tool calls
            tool_results = []

            for block in content_blocks:
                block_type = self._get_attr(block, "type")

                if block_type == "tool_use":
                    tool_name = self._get_attr(block, "name", "")
                    tool_input = self._get_attr(block, "input", {})
                    tool_id = self._get_attr(block, "id", "")

                    print(f"    Tool: {tool_name}")

                    # Build tool details for progress
                    tool_details = self._get_tool_details(tool_name, tool_input)
                    emit_progress(
                        "tool_start",
                        iteration=iteration,
                        tool_name=tool_name,
                        tool_details=tool_details
                    )

                    result = self._handle_tool(
                        website_id, tool_name, tool_input
                    )

                    # Check for termination
                    if tool_name == "finalize_website":
                        final_result = self._finalize(
                            website_id, tool_input, iteration,
                            total_input_tokens, total_output_tokens
                        )

                        print(f"  Completed in {iteration} iterations")
                        emit_progress(
                            "agent_completed",
                            iterations=iteration,
                            website_id=website_id,
                            pages_created=final_result.get("pages_created", [])
                        )

                        self._save_execution(
                            execution_id, website_id, messages,
                            final_result, started_at
                        )

                        return final_result

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": result
                    })

            # Add tool results to messages
            if tool_results:
                messages.append({"role": "user", "content": tool_results})

        # Max iterations reached
        print(f"  Max iterations reached ({self.MAX_ITERATIONS})")

        error_result = {
            "success": False,
            "website_id": website_id,
            "error": f"Agent reached maximum iterations ({self.MAX_ITERATIONS})",
            "iterations": self.MAX_ITERATIONS,
            "usage": {
                "input_tokens": total_input_tokens,
                "output_tokens": total_output_tokens
            }
        }

        website_service.update_website(website_id, {
            "status": "error",
            "error": error_result["error"]
        })

        self._save_execution(
            execution_id, website_id, messages, error_result, started_at
        )

        return error_result

    def _handle_tool(
        self,
        website_id: str,
        tool_name: str,
        tool_input: Dict[str, Any]
    ) -> str:
        """Handle a tool call and return result string."""

        if tool_name == "plan_website":
            return self._handle_plan(website_id, tool_input)

        elif tool_name == "generate_website_image":
            return self._handle_image(website_id, tool_input)

        elif tool_name == "read_file":
            return self._handle_read(website_id, tool_input)

        elif tool_name == "create_file":
            return self._handle_create(website_id, tool_input)

        elif tool_name == "update_file_lines":
            return self._handle_update(website_id, tool_input)

        elif tool_name == "insert_code":
            return self._handle_insert(website_id, tool_input)

        return f"Unknown tool: {tool_name}"

    def _handle_plan(
        self,
        website_id: str,
        tool_input: Dict[str, Any]
    ) -> str:
        """Handle plan_website tool."""
        site_name = tool_input.get("site_name", "Untitled")
        pages = tool_input.get("pages", [])

        print(f"      Planning: {site_name} ({len(pages)} pages)")

        website_service.update_website(website_id, {
            "plan": tool_input,
            "status": "planning"
        })

        return (
            f"Website plan saved. Site: '{site_name}', "
            f"Pages: {len(pages)}, "
            f"Features: {len(tool_input.get('features', []))}"
        )

    def _handle_image(
        self,
        website_id: str,
        tool_input: Dict[str, Any]
    ) -> str:
        """Handle generate_website_image tool."""
        purpose = tool_input.get("purpose", "unknown")
        image_prompt = tool_input.get("image_prompt", "")
        aspect_ratio = tool_input.get("aspect_ratio", "16:9")

        print(f"      Generating image: {purpose}")

        assets_dir = website_service._get_assets_dir(website_id)

        result = imagen_service.generate_image(
            prompt=image_prompt,
            output_dir=assets_dir,
            filename_prefix=purpose,
            aspect_ratio=aspect_ratio
        )

        if not result.get("success"):
            return f"Error generating image: {result.get('error', 'Unknown error')}"

        filename = result["filename"]

        # Record image
        image_info = website_service.add_image(website_id, purpose, filename)

        return (
            f"Image generated for '{purpose}'. "
            f"Use placeholder '{image_info.get('placeholder')}' in your HTML."
        )

    def _handle_read(
        self,
        website_id: str,
        tool_input: Dict[str, Any]
    ) -> str:
        """Handle read_file tool."""
        filename = tool_input.get("filename", "")
        start_line = tool_input.get("start_line")
        end_line = tool_input.get("end_line")

        result = website_service.read_file(
            website_id, filename, start_line, end_line
        )

        if not result.get("success"):
            return result.get("error", "Error reading file")

        return f"File: {filename} ({result.get('total_lines')} lines)\n\n{result.get('content')}"

    def _handle_create(
        self,
        website_id: str,
        tool_input: Dict[str, Any]
    ) -> str:
        """Handle create_file tool."""
        filename = tool_input.get("filename", "")
        content = tool_input.get("content", "")

        print(f"      Creating: {filename}")

        # Get images for placeholder replacement
        metadata = website_service.get_website(website_id)
        images = metadata.get("images", []) if metadata else []

        result = website_service.create_file(
            website_id, filename, content, images
        )

        if not result.get("success"):
            return f"Error creating file: {filename}"

        return (
            f"File '{filename}' created successfully "
            f"({result.get('lines')} lines, {result.get('chars')} characters)"
        )

    def _handle_update(
        self,
        website_id: str,
        tool_input: Dict[str, Any]
    ) -> str:
        """Handle update_file_lines tool."""
        filename = tool_input.get("filename", "")
        start_line = tool_input.get("start_line", 1)
        end_line = tool_input.get("end_line", 1)
        new_content = tool_input.get("new_content", "")

        metadata = website_service.get_website(website_id)
        images = metadata.get("images", []) if metadata else []

        result = website_service.update_file_lines(
            website_id, filename, start_line, end_line, new_content, images
        )

        if not result.get("success"):
            return result.get("error", "Error updating file")

        return result.get("message", "File updated")

    def _handle_insert(
        self,
        website_id: str,
        tool_input: Dict[str, Any]
    ) -> str:
        """Handle insert_code tool."""
        filename = tool_input.get("filename", "")
        after_line = tool_input.get("after_line", 0)
        content = tool_input.get("content", "")

        metadata = website_service.get_website(website_id)
        images = metadata.get("images", []) if metadata else []

        result = website_service.insert_code(
            website_id, filename, after_line, content, images
        )

        if not result.get("success"):
            return result.get("error", "Error inserting code")

        return result.get("message", "Code inserted")

    def _finalize(
        self,
        website_id: str,
        tool_input: Dict[str, Any],
        iterations: int,
        input_tokens: int,
        output_tokens: int
    ) -> Dict[str, Any]:
        """Handle finalize_website tool."""
        summary = tool_input.get("summary", "")
        pages_created = tool_input.get("pages_created", [])
        features_implemented = tool_input.get("features_implemented", [])

        website_service.update_website(website_id, {
            "status": "ready",
            "summary": summary,
            "pages_created": pages_created,
            "features_implemented": features_implemented,
            "completed_at": datetime.now().isoformat(),
            "iterations": iterations,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens
            }
        })

        return {
            "success": True,
            "website_id": website_id,
            "summary": summary,
            "pages_created": pages_created,
            "features_implemented": features_implemented,
            "iterations": iterations,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens
            }
        }

    def _save_execution(
        self,
        execution_id: str,
        website_id: str,
        messages: List[Dict[str, Any]],
        result: Dict[str, Any],
        started_at: str
    ) -> None:
        """Save agent execution log."""
        execution_log = {
            "execution_id": execution_id,
            "website_id": website_id,
            "messages": messages,
            "result": result,
            "started_at": started_at,
            "completed_at": datetime.now().isoformat()
        }

        log_path = Config.AGENTS_DIR / f"{execution_id}.json"
        write_json(log_path, execution_log)

    def _get_attr(self, block: Any, attr: str, default: Any = None) -> Any:
        """Get attribute from block (dict or object)."""
        if isinstance(block, dict):
            return block.get(attr, default)
        return getattr(block, attr, default)

    def _get_tool_details(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """Get human-readable details for a tool call."""
        if tool_name == "plan_website":
            site_name = tool_input.get("site_name", "Untitled")
            pages = tool_input.get("pages", [])
            return f"Planning: {site_name} ({len(pages)} pages)"

        elif tool_name == "generate_website_image":
            purpose = tool_input.get("purpose", "unknown")
            return f"Generating image: {purpose}"

        elif tool_name == "create_file":
            filename = tool_input.get("filename", "")
            return f"Creating: {filename}"

        elif tool_name == "update_file_lines":
            filename = tool_input.get("filename", "")
            return f"Updating: {filename}"

        elif tool_name == "insert_code":
            filename = tool_input.get("filename", "")
            return f"Inserting code: {filename}"

        elif tool_name == "read_file":
            filename = tool_input.get("filename", "")
            return f"Reading: {filename}"

        elif tool_name == "finalize_website":
            return "Finalizing website"

        return tool_name


# Singleton instance
website_agent_service = WebsiteAgentService()
