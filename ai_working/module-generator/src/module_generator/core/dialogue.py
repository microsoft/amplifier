"""Dialogue flow controller for multi-turn conversations.

This module orchestrates the multi-turn dialogue flow between
the user, Claude SDK, and clarification handlers.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .clarification import ClarificationStrategy
from .conversation import ConversationManager
from .conversation import ConversationState
from .response_parser import ParsedResponse
from .response_parser import ResponseParser


@dataclass
class DialogueResult:
    """Result of a dialogue interaction."""

    success: bool
    generated_files: list[Path] = None
    conversation_state: ConversationState = None
    error: str | None = None
    metadata: dict[str, Any] = None


class DialogueController:
    """Controls the flow of multi-turn dialogue for module generation."""

    def __init__(
        self,
        conversation_manager: ConversationManager,
        response_parser: ResponseParser,
        clarification_handler: ClarificationStrategy,
        max_turns: int = 10,
    ):
        """Initialize dialogue controller.

        Args:
            conversation_manager: Manages conversation state
            response_parser: Parses responses
            clarification_handler: Handles clarifications
            max_turns: Maximum conversation turns
        """
        self.conversation_manager = conversation_manager
        self.response_parser = response_parser
        self.clarification_handler = clarification_handler
        self.max_turns = max_turns

    async def run_dialogue(
        self,
        claude_sdk,
        initial_prompt: str,
        module_spec: dict[str, Any],
        working_directory: Path,
        target_directory: Path,
    ) -> DialogueResult:
        """Run a multi-turn dialogue for module generation.

        Args:
            claude_sdk: Claude SDK instance
            initial_prompt: Initial generation prompt
            module_spec: Module specification
            working_directory: Working directory
            target_directory: Target for generated files

        Returns:
            Dialogue result with generated files and state
        """
        # Start conversation
        conversation_state = self.conversation_manager.start_conversation(
            module_spec=module_spec, working_directory=working_directory, target_directory=target_directory
        )

        # Add initial prompt
        self.conversation_manager.add_message("user", initial_prompt)

        generated_files = []
        turn_count = 0

        try:
            # Initial query to Claude
            response = await claude_sdk.query(initial_prompt)

            while turn_count < self.max_turns:
                turn_count += 1

                # Parse response
                parsed = self.response_parser.parse(response)

                # Add assistant response to conversation
                self.conversation_manager.add_message("assistant", response)

                # Handle different response types
                context_dict = {
                    "module_spec": conversation_state.context.module_spec,
                    "working_directory": conversation_state.context.working_directory,
                    "target_directory": conversation_state.context.target_directory,
                    "config": conversation_state.context.config,
                    "state": conversation_state.context.state,
                }
                result = await self._handle_response(parsed, claude_sdk, context_dict)

                if result["complete"]:
                    # Generation complete
                    generated_files.extend(result.get("files", []))
                    break

                if result.get("needs_response"):
                    # Continue conversation
                    response = result["next_response"]

                    # Add any clarification to conversation
                    if result.get("clarification"):
                        self.conversation_manager.add_message("user", result["clarification"])
                else:
                    # No more responses needed
                    break

            # Update status
            self.conversation_manager.update_status("completed")

            return DialogueResult(
                success=True,
                generated_files=generated_files,
                conversation_state=conversation_state,
                metadata={"turn_count": turn_count},
            )

        except Exception as e:
            # Update status and return error
            self.conversation_manager.update_status("failed")

            return DialogueResult(
                success=False, conversation_state=conversation_state, error=str(e), metadata={"turn_count": turn_count}
            )

    async def _handle_response(self, parsed: ParsedResponse, claude_sdk, context: dict[str, Any]) -> dict[str, Any]:
        """Handle a parsed response.

        Args:
            parsed: Parsed response
            claude_sdk: Claude SDK instance
            context: Conversation context

        Returns:
            Handler result with next actions
        """
        if parsed.response_type == "code":
            # Code generation - save files
            files = await self._save_code_blocks(parsed, context)
            return {"complete": True, "files": files, "needs_response": False}

        if parsed.response_type == "question":
            # Need clarification
            clarification = await self._get_clarification(parsed, context)

            # Continue conversation with clarification
            next_response = await claude_sdk.send_message(clarification)

            return {
                "complete": False,
                "needs_response": True,
                "clarification": clarification,
                "next_response": next_response,
            }

        if parsed.response_type == "mixed":
            # Has both code and questions
            files = await self._save_code_blocks(parsed, context)

            if parsed.requires_clarification:
                clarification = await self._get_clarification(parsed, context)
                next_response = await claude_sdk.send_message(clarification)

                return {
                    "complete": False,
                    "files": files,
                    "needs_response": True,
                    "clarification": clarification,
                    "next_response": next_response,
                }
            return {"complete": True, "files": files, "needs_response": False}

        if parsed.response_type == "progress":
            # Progress update - continue if SDK has more
            if hasattr(claude_sdk, "has_more") and claude_sdk.has_more():
                next_response = await claude_sdk.receive_message()
                return {"complete": False, "needs_response": True, "next_response": next_response}
            return {"complete": True, "needs_response": False}

        # error
        return {"complete": True, "needs_response": False, "error": "Unexpected response type"}

    async def _save_code_blocks(self, parsed: ParsedResponse, context: dict[str, Any]) -> list[Path]:
        """Save code blocks to files.

        Args:
            parsed: Parsed response with code blocks
            context: Conversation context

        Returns:
            List of saved file paths
        """
        saved_files = []
        target_dir = context["target_directory"]

        for code_block in parsed.code_blocks:
            file_path = target_dir / code_block.filepath

            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Save based on operation
            if code_block.operation in ["create", "modify"]:
                with open(file_path, "w") as f:
                    f.write(code_block.content)
                saved_files.append(file_path)

            elif code_block.operation == "delete":
                if file_path.exists():
                    file_path.unlink()

        return saved_files

    async def _get_clarification(self, parsed: ParsedResponse, context: dict[str, Any]) -> str:
        """Get clarification for questions in response.

        Args:
            parsed: Parsed response with questions
            context: Conversation context

        Returns:
            Clarification text
        """
        clarifications = []

        for question in parsed.questions:
            answer = await self.clarification_handler.get_clarification(question, context)
            clarifications.append(f"Q: {question.question}\nA: {answer}")

        return "\n\n".join(clarifications)

    async def resume_dialogue(self, claude_sdk, checkpoint_path: Path) -> DialogueResult:
        """Resume a dialogue from a checkpoint.

        Args:
            claude_sdk: Claude SDK instance
            checkpoint_path: Path to checkpoint file

        Returns:
            Dialogue result
        """
        # Load checkpoint
        conversation_state = self.conversation_manager.load_checkpoint(checkpoint_path)

        if conversation_state.status == "completed":
            # Already complete
            return DialogueResult(
                success=True,
                conversation_state=conversation_state,
                metadata={"resumed": True, "already_complete": True},
            )

        # Get last message
        messages = self.conversation_manager.get_messages()
        if not messages:
            return DialogueResult(
                success=False, conversation_state=conversation_state, error="No messages in checkpoint"
            )

        # Resume based on last message role
        last_message = messages[-1]

        if last_message.role == "assistant":
            # Last was assistant - might need clarification
            parsed = self.response_parser.parse(last_message.content)

            if parsed.requires_clarification:
                # Get clarification and continue
                context_dict = {
                    "module_spec": conversation_state.context.module_spec,
                    "working_directory": conversation_state.context.working_directory,
                    "target_directory": conversation_state.context.target_directory,
                    "config": conversation_state.context.config,
                    "state": conversation_state.context.state,
                }
                clarification = await self._get_clarification(parsed, context_dict)

                self.conversation_manager.add_message("user", clarification)
                response = await claude_sdk.send_message(clarification)

                # Continue dialogue loop
                return await self._continue_dialogue(claude_sdk, response, conversation_state)

        elif last_message.role == "user":
            # Last was user - need assistant response
            response = await claude_sdk.send_message(last_message.content)

            # Continue dialogue loop
            return await self._continue_dialogue(claude_sdk, response, conversation_state)

        return DialogueResult(
            success=False, conversation_state=conversation_state, error="Cannot resume from system message"
        )

    async def _continue_dialogue(
        self, claude_sdk, response: str, conversation_state: ConversationState
    ) -> DialogueResult:
        """Continue an existing dialogue.

        Args:
            claude_sdk: Claude SDK instance
            response: Current response
            conversation_state: Current conversation state

        Returns:
            Dialogue result
        """
        generated_files = []
        turn_count = len([m for m in conversation_state.messages if m.role == "assistant"])

        while turn_count < self.max_turns:
            turn_count += 1

            # Parse and handle response
            parsed = self.response_parser.parse(response)
            self.conversation_manager.add_message("assistant", response)

            context_dict = {
                "module_spec": conversation_state.context.module_spec,
                "working_directory": conversation_state.context.working_directory,
                "target_directory": conversation_state.context.target_directory,
                "config": conversation_state.context.config,
                "state": conversation_state.context.state,
            }
            result = await self._handle_response(parsed, claude_sdk, context_dict)

            if result["complete"]:
                generated_files.extend(result.get("files", []))
                break

            if result.get("needs_response"):
                response = result["next_response"]
                if result.get("clarification"):
                    self.conversation_manager.add_message("user", result["clarification"])
            else:
                break

        self.conversation_manager.update_status("completed")

        return DialogueResult(
            success=True,
            generated_files=generated_files,
            conversation_state=conversation_state,
            metadata={"turn_count": turn_count, "resumed": True},
        )
