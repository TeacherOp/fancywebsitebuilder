"""
Main Chat Service.

Orchestrates chat message processing with AI responses.
Triggers website agent when user wants to generate a website.
"""
from typing import Any, Callable, Dict, Optional, Tuple

from app.services.claude_service import claude_service
from app.services.message_service import message_service
from app.services.chat_service import chat_service
from app.services.brand_service import brand_service
from app.tools.tool_definitions import get_main_chat_tools, MAIN_CHAT_SYSTEM_PROMPT
from app.utils.parsing_utils import (
    is_tool_use,
    extract_text,
    extract_tool_use_blocks,
    serialize_content_blocks,
)


class MainChatService:
    """
    Service class for orchestrating chat conversations.

    Handles the message flow between user, Claude, and tools.
    """

    MAX_TOOL_ITERATIONS = 10

    def _build_system_prompt(self, chat_id: str) -> str:
        """
        Build system prompt with brand resources and guidelines.

        Args:
            chat_id: The chat UUID

        Returns:
            System prompt string with resources appended
        """
        system_prompt = MAIN_CHAT_SYSTEM_PROMPT

        # Add brand guidelines
        chat = chat_service.get_chat(chat_id)
        if chat and chat.get("brand_guidelines"):
            system_prompt += f"\n\n## User's Brand Guidelines\n{chat['brand_guidelines']}"

        # Add resources summary
        resources_summary = brand_service.get_resources_summary(chat_id)
        if resources_summary:
            system_prompt += f"\n\n{resources_summary}"

        return system_prompt

    def send_message(
        self,
        chat_id: str,
        user_message_text: str,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Process a user message and get AI response.

        Flow:
        1. Store user message
        2. Call Claude with tools
        3. If tool_use: execute tool, send result, call again
        4. When text response: store and return

        Args:
            chat_id: The chat UUID
            user_message_text: The user's message text
            progress_callback: Optional callback for progress updates

        Returns:
            Tuple of (user_message_dict, assistant_message_dict)
        """
        # Store callback for use in tool execution
        self._progress_callback = progress_callback
        # Step 1: Store user message
        user_msg = message_service.add_user_message(chat_id, user_message_text)

        # Step 2: Get tools and build dynamic system prompt
        tools = get_main_chat_tools()
        system_prompt = self._build_system_prompt(chat_id)

        try:
            # Step 3: Build messages and call Claude
            api_messages = message_service.build_api_messages(chat_id)

            response = claude_service.send_message(
                messages=api_messages,
                system_prompt=system_prompt,
                tools=tools,
            )

            # Step 4: Handle tool use loop
            iteration = 0
            accumulated_text_parts = []

            while is_tool_use(response) and iteration < self.MAX_TOOL_ITERATIONS:
                iteration += 1

                tool_use_blocks = extract_tool_use_blocks(response)
                if not tool_use_blocks:
                    break

                # Extract text from this response
                response_text = extract_text(response)
                if response_text.strip():
                    accumulated_text_parts.append(response_text)

                # Store the assistant's tool_use response
                serialized_content = serialize_content_blocks(
                    response.get("content_blocks", [])
                )
                message_service.add_message(
                    chat_id=chat_id,
                    role="assistant",
                    content=serialized_content
                )

                # Execute each tool
                for tool_block in tool_use_blocks:
                    tool_id = tool_block.get("id")
                    tool_name = tool_block.get("name")
                    tool_input = tool_block.get("input", {})

                    print(f"Executing tool: {tool_name}")

                    result = self._execute_tool(chat_id, tool_name, tool_input)

                    message_service.add_tool_result_message(
                        chat_id=chat_id,
                        tool_use_id=tool_id,
                        result=result
                    )

                # Call Claude again
                api_messages = message_service.build_api_messages(chat_id)
                response = claude_service.send_message(
                    messages=api_messages,
                    system_prompt=system_prompt,
                    tools=tools,
                )

            # Step 5: Get final text and store
            final_response_text = extract_text(response)
            if final_response_text.strip():
                accumulated_text_parts.append(final_response_text)

            final_text = "\n\n".join(accumulated_text_parts) if accumulated_text_parts else ""

            assistant_msg = message_service.add_assistant_message(
                chat_id=chat_id,
                content=final_text if final_text.strip() else "I've processed your request.",
                model=response.get("model"),
                tokens=response.get("usage")
            )

        except Exception as api_error:
            print(f"Error in main chat: {api_error}")
            assistant_msg = message_service.add_assistant_message(
                chat_id=chat_id,
                content=f"Sorry, I encountered an error: {str(api_error)}",
                error=True
            )

        # Sync chat index
        chat_service.sync_to_index(chat_id)

        return user_msg, assistant_msg

    def _execute_tool(
        self,
        chat_id: str,
        tool_name: str,
        tool_input: Dict[str, Any]
    ) -> str:
        """
        Execute a tool and return result string.

        Args:
            chat_id: The chat UUID
            tool_name: Name of the tool
            tool_input: Tool input parameters

        Returns:
            Tool execution result as string
        """
        if tool_name == "generate_website":
            return self._handle_generate_website(chat_id, tool_input)
        else:
            return f"Unknown tool: {tool_name}"

    def _handle_generate_website(
        self,
        chat_id: str,
        tool_input: Dict[str, Any]
    ) -> str:
        """
        Handle the generate_website tool call.

        Triggers the website agent to generate the website.

        Args:
            chat_id: The chat UUID
            tool_input: Contains 'direction' and optional 'resources'

        Returns:
            Result message
        """
        # Import here to avoid circular imports
        from app.services.website_agent_service import website_agent_service

        direction = tool_input.get("direction", "")

        # Get resources - either from tool input or fetch from brand service
        resources = tool_input.get("resources", [])
        if not resources:
            # Fallback: get resources from brand service if not provided in tool call
            resources = brand_service.get_resources_for_agent(chat_id)

        print(f"Triggering website agent for chat {chat_id}")
        print(f"Direction: {direction[:100]}...")
        print(f"Resources: {len(resources)} available")

        try:
            result = website_agent_service.generate_website(
                chat_id=chat_id,
                direction=direction,
                resources=resources,
                progress_callback=getattr(self, '_progress_callback', None)
            )

            if result.get("success"):
                website_id = result.get("website_id")

                # Update chat with website_id
                chat_service.update_chat(chat_id, {"website_id": website_id})

                return (
                    f"Website generated successfully!\n"
                    f"Website ID: {website_id}\n"
                    f"Pages created: {', '.join(result.get('pages_created', []))}\n"
                    f"Features: {', '.join(result.get('features_implemented', []))}"
                )
            else:
                return f"Website generation failed: {result.get('error', 'Unknown error')}"

        except Exception as e:
            print(f"Error in website generation: {e}")
            return f"Error generating website: {str(e)}"


# Singleton instance
main_chat_service = MainChatService()
