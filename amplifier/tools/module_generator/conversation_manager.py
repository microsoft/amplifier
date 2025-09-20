"""
Metacognitive conversation manager for Claude SDK interactions.

Manages multi-turn conversations with progress tracking and intelligent evaluation.
"""

import json
import logging
import re
import time
from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class Phase(Enum):
    """Conversation phases for module generation."""

    UNDERSTANDING = "understanding"
    PLANNING = "planning"
    IMPLEMENTING = "implementing"
    REVIEWING = "reviewing"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class ConversationState:
    """Tracks the state of a multi-turn conversation."""

    phase: Phase = Phase.UNDERSTANDING
    completed_chunks: list[str] = field(default_factory=list)
    current_context: str = ""
    remaining_tasks: list[str] = field(default_factory=list)
    files_created: list[str] = field(default_factory=list)
    errors_encountered: list[str] = field(default_factory=list)
    iteration_count: int = 0
    max_iterations: int = 10

    def to_dict(self) -> dict:
        """Convert to dictionary for logging."""
        return {
            "phase": self.phase.value,
            "completed_chunks": len(self.completed_chunks),
            "remaining_tasks": len(self.remaining_tasks),
            "files_created": self.files_created,
            "iteration_count": self.iteration_count,
            "errors": self.errors_encountered,
        }


@dataclass
class NextAction:
    """Represents the next action to take in the conversation."""

    type: str  # "continue", "clarify", "complete", "retry", "fail"
    reason: str = ""
    focus: str = ""
    approach: str = ""


@dataclass
class Signals:
    """Signals extracted from SDK responses for metacognitive evaluation."""

    has_code: bool = False
    has_file_creation: bool = False
    mentions_uncertainty: bool = False
    has_error: bool = False
    has_todo: bool = False
    is_complete: bool = False
    files_mentioned: list[str] = field(default_factory=list)


class ProgressTracker:
    """Tracks and reports generation progress."""

    def __init__(self):
        self.total_chunks = 0
        self.completed_chunks = 0
        self.start_time = time.time()
        self.chunk_times: list[float] = []
        self.last_log_time = time.time()

    def set_total_chunks(self, total: int):
        """Set the total number of chunks to process."""
        self.total_chunks = total
        logger.info(f"Starting generation with {total} chunks to process")

    def update(self, chunk_name: str = "", chunk_complete: bool = False):
        """Update progress with optional chunk completion."""
        if chunk_complete:
            self.completed_chunks += 1
            self.chunk_times.append(time.time())
            logger.info(f"✓ Completed chunk {self.completed_chunks}/{self.total_chunks}: {chunk_name}")

    def get_status(self) -> dict:
        """Get current progress status."""
        elapsed = time.time() - self.start_time
        progress_pct = (self.completed_chunks / max(self.total_chunks, 1)) * 100

        avg_time = 0
        if self.chunk_times:
            deltas = [
                self.chunk_times[i] - (self.chunk_times[i - 1] if i > 0 else self.start_time)
                for i in range(len(self.chunk_times))
            ]
            avg_time = sum(deltas) / len(deltas)

        remaining = (self.total_chunks - self.completed_chunks) * avg_time if avg_time > 0 else 0

        return {
            "progress": f"{self.completed_chunks}/{self.total_chunks} chunks",
            "percentage": progress_pct,
            "elapsed_seconds": elapsed,
            "estimated_remaining": remaining,
            "average_chunk_time": avg_time,
        }

    def should_log(self, force: bool = False) -> bool:
        """Check if we should log progress (every 10 seconds or forced)."""
        if force or time.time() - self.last_log_time > 10:
            self.last_log_time = time.time()
            return True
        return False

    def log_progress(self, force: bool = False):
        """Log current progress for visibility."""
        if self.should_log(force):
            status = self.get_status()
            logger.info(
                f"📊 Progress: {status['progress']} ({status['percentage']:.0f}%) | "
                f"Elapsed: {status['elapsed_seconds']:.0f}s | "
                f"ETA: {status['estimated_remaining']:.0f}s"
            )


class MetacognitiveEvaluator:
    """Evaluates generation progress and decides next steps."""

    def evaluate_response(self, response: str, state: ConversationState) -> NextAction:
        """Analyze SDK response and determine next action."""
        logger.debug("Evaluating response for metacognitive signals...")

        # Extract signals from response
        signals = self._extract_signals(response)

        # Log what we found
        logger.debug(
            f"Signals: code={signals.has_code}, files={signals.has_file_creation}, "
            f"error={signals.has_error}, todo={signals.has_todo}, complete={signals.is_complete}"
        )

        # Evaluate completeness
        if signals.is_complete and not signals.has_todo:
            return NextAction(type="complete", reason="All requirements met")

        # Check for errors
        if signals.has_error:
            state.errors_encountered.append("Error detected in response")
            if state.iteration_count < 3:
                return NextAction(type="retry", reason="Error detected, retrying with guidance")
            return NextAction(type="fail", reason="Too many errors encountered")

        # Check for confusion/uncertainty
        if signals.mentions_uncertainty:
            return NextAction(type="clarify", focus="Unclear requirements detected")

        # Check for progress
        if signals.has_code or signals.has_file_creation:
            if signals.files_mentioned:
                state.files_created.extend(signals.files_mentioned)
            return NextAction(type="continue", reason="Progress detected, continuing")

        # Check if stuck (no progress indicators)
        if state.iteration_count > 2 and not signals.has_code:
            return NextAction(type="clarify", focus="No code generation detected")

        return NextAction(type="continue", reason="Default continuation")

    def _extract_signals(self, response: str) -> Signals:
        """Extract metacognitive signals from response."""
        response_lower = response.lower()

        # Look for code blocks
        has_code = bool(re.search(r"```\w+", response))

        # Look for file creation patterns
        file_patterns = [
            r"creating.*?(\w+\.py)",
            r"writing.*?(\w+\.py)",
            r"file:.*?(\w+\.py)",
            r"(\w+\.py):",
        ]
        files_mentioned = []
        has_file_creation = False
        for pattern in file_patterns:
            matches = re.findall(pattern, response_lower)
            if matches:
                files_mentioned.extend(matches)
                has_file_creation = True

        # Check for uncertainty
        uncertainty_phrases = ["not sure", "unclear", "ambiguous", "could you clarify", "missing"]
        mentions_uncertainty = any(phrase in response_lower for phrase in uncertainty_phrases)

        # Check for errors
        error_phrases = ["error", "failed", "exception", "cannot", "unable to"]
        has_error = any(phrase in response_lower for phrase in error_phrases)

        # Check for TODOs
        has_todo = "todo" in response_lower or "fixme" in response_lower

        # Check for completion
        completion_phrases = ["complete", "finished", "done", "successfully created", "module ready"]
        is_complete = any(phrase in response_lower for phrase in completion_phrases)

        return Signals(
            has_code=has_code,
            has_file_creation=has_file_creation,
            mentions_uncertainty=mentions_uncertainty,
            has_error=has_error,
            has_todo=has_todo,
            is_complete=is_complete,
            files_mentioned=files_mentioned,
        )


class ProgressivePromptBuilder:
    """Builds focused prompts for each conversation turn."""

    def build_understanding_prompt(self, contract: str, spec: str) -> str:
        """Phase 1: Understand requirements and create a plan."""
        return f"""I need you to understand this module requirement and create a clear implementation plan.

CONTRACT (what it must do):
{contract[:1000]}  # Truncate if too long

SPECIFICATION (implementation approach):
{spec[:1000]}  # Truncate if too long

Please provide:
1. Your understanding of the key requirements (2-3 sentences)
2. List of main Python files you'll create (e.g., __init__.py, core.py, etc.)
3. Any clarifications needed before we start

Keep your response focused and under 500 words. We'll implement in the next steps."""

    def build_initial_structure_prompt(self, plan: str, module_name: str) -> str:
        """Phase 2a: Create the basic module structure."""
        return f"""Now let's create the basic structure for the {module_name} module.

Based on our plan:
{plan}

Please create:
1. __init__.py with proper exports
2. Basic module structure in core.py or main implementation file
3. Empty test file structure

Use the Write or Edit tools to create these files in amplifier/{module_name}/

Focus on structure first - we'll add implementation details next."""

    def build_implementation_prompt(self, context: str, chunk: str) -> str:
        """Phase 2b: Implement specific functionality."""
        return f"""Continue implementing the module.

Previous work:
{context[-500:]}  # Last 500 chars for context

Now implement:
{chunk}

Use Edit tool to add this functionality to the existing files.
Write complete, working code. Include proper error handling and docstrings."""

    def build_review_prompt(self, state: ConversationState) -> str:
        """Phase 3: Review and complete the implementation."""
        files_list = "\n".join(f"- {f}" for f in state.files_created)
        return f"""Let's review and finalize the module implementation.

Files created so far:
{files_list}

Please:
1. Check that all contract requirements are met
2. Ensure all files have proper docstrings and type hints
3. Verify the module can be imported and used
4. Add any missing error handling

If anything is incomplete, please fix it now."""

    def build_clarification_prompt(self, focus: str) -> str:
        """Build a prompt to clarify confusion."""
        return f"""I need clarification on: {focus}

Please provide more specific guidance on how to proceed.
What exactly should I implement for this part?"""

    def build_retry_prompt(self, error: str) -> str:
        """Build a prompt to retry after an error."""
        return f"""The previous attempt encountered an issue: {error}

Let's try a different approach. Please:
1. Identify what went wrong
2. Suggest an alternative implementation
3. Proceed with the corrected approach"""


class ConversationManager:
    """Manages multi-turn conversations with Claude SDK for module generation."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.state = ConversationState()
        self.evaluator = MetacognitiveEvaluator()
        self.progress = ProgressTracker()
        self.prompt_builder = ProgressivePromptBuilder()

    def log_state(self):
        """Log the current conversation state."""
        logger.info(f"Conversation state: {json.dumps(self.state.to_dict(), indent=2)}")

    async def generate_with_conversation(
        self,
        module_name: str,
        contract: str,
        spec: str,
        sdk_client,  # Claude SDK client instance
    ) -> bool:
        """Generate a module through guided multi-turn conversation.

        Returns True if successful, False otherwise.
        """
        logger.info(f"Starting metacognitive conversation for module: {module_name}")
        self.state.phase = Phase.UNDERSTANDING

        # Create module directory
        module_path = self.output_dir / module_name
        module_path.mkdir(parents=True, exist_ok=True)

        try:
            # Phase 1: Understanding
            logger.info("Phase 1: Understanding requirements...")
            understanding = await self._phase_understanding(contract, spec, sdk_client)
            if not understanding:
                logger.error("Failed to understand requirements")
                return False

            # Phase 2: Implementation
            logger.info("Phase 2: Creating module structure and implementation...")
            implementation = await self._phase_implementation(module_name, understanding, contract, spec, sdk_client)
            if not implementation:
                logger.error("Failed to implement module")
                return False

            # Phase 3: Review
            logger.info("Phase 3: Reviewing and finalizing...")
            finalized = await self._phase_review(sdk_client)

            logger.info(f"✅ Module generation {'successful' if finalized else 'completed with warnings'}")
            return True

        except Exception as e:
            logger.error(f"Conversation failed: {e}")
            self.state.phase = Phase.FAILED
            return False

    async def _phase_understanding(self, contract: str, spec: str, sdk_client) -> str | None:
        """Phase 1: Understand requirements and create plan."""
        self.state.phase = Phase.UNDERSTANDING
        prompt = self.prompt_builder.build_understanding_prompt(contract, spec)

        # Query SDK
        await sdk_client.query(prompt)
        response = await self._collect_response(sdk_client)

        # Evaluate response
        evaluation = self.evaluator.evaluate_response(response, self.state)

        if evaluation.type == "clarify":
            # Need clarification
            clarify_prompt = self.prompt_builder.build_clarification_prompt(evaluation.focus)
            await sdk_client.query(clarify_prompt)
            response = await self._collect_response(sdk_client)

        self.state.current_context = response
        return response

    async def _phase_implementation(self, module_name: str, plan: str, contract: str, spec: str, sdk_client) -> bool:
        """Phase 2: Implement the module in chunks."""
        self.state.phase = Phase.IMPLEMENTING

        # Break into implementation chunks
        chunks = self._create_implementation_chunks(plan)
        self.progress.set_total_chunks(len(chunks))

        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i + 1}/{len(chunks)}: {chunk['name']}")
            self.progress.log_progress(force=True)

            # Build appropriate prompt
            if i == 0:
                # Initial structure
                prompt = self.prompt_builder.build_initial_structure_prompt(plan, module_name)
            else:
                # Continue implementation
                prompt = self.prompt_builder.build_implementation_prompt(
                    self.state.current_context, chunk["description"]
                )

            # Query SDK
            await sdk_client.query(prompt)
            response = await self._collect_response(sdk_client)

            # Evaluate response
            evaluation = self.evaluator.evaluate_response(response, self.state)

            if evaluation.type == "retry":
                # Retry with guidance
                retry_prompt = self.prompt_builder.build_retry_prompt(evaluation.reason)
                await sdk_client.query(retry_prompt)
                response = await self._collect_response(sdk_client)

            # Update state
            self.state.completed_chunks.append(chunk["name"])
            self.state.current_context = response[-1000:]  # Keep last 1000 chars for context
            self.progress.update(chunk_name=chunk["name"], chunk_complete=True)

            # Check for file creation
            await self._check_created_files(module_name)

        return len(self.state.completed_chunks) > 0

    async def _phase_review(self, sdk_client) -> bool:
        """Phase 3: Review and finalize the implementation."""
        self.state.phase = Phase.REVIEWING

        prompt = self.prompt_builder.build_review_prompt(self.state)
        await sdk_client.query(prompt)
        response = await self._collect_response(sdk_client)

        # Final evaluation
        evaluation = self.evaluator.evaluate_response(response, self.state)

        if evaluation.type in ["complete", "continue"]:
            self.state.phase = Phase.COMPLETE
            return True
        logger.warning(f"Review phase ended with: {evaluation.type} - {evaluation.reason}")
        return False

    async def _collect_response(self, sdk_client, timeout: int = 60) -> str:
        """Collect response from SDK with timeout and logging."""
        logger.debug("Waiting for SDK response...")
        response = ""
        start_time = time.time()

        try:
            # Collect all response chunks
            async for message in sdk_client.receive_response():
                if hasattr(message, "content"):
                    content = getattr(message, "content", [])
                    if isinstance(content, list):
                        for block in content:
                            if hasattr(block, "text"):
                                chunk = getattr(block, "text", "")
                                response += chunk

                                # Log progress every 5 seconds
                                if time.time() - start_time > 5:
                                    logger.debug(f"Receiving response... {len(response)} chars so far")
                                    start_time = time.time()

        except TimeoutError:
            logger.warning(f"Response collection timed out after {timeout}s")

        logger.debug(f"Collected response of {len(response)} characters")
        return response

    def _create_implementation_chunks(self, plan: str) -> list[dict[str, str]]:
        """Break the implementation into manageable chunks."""
        # Simple chunking strategy - can be enhanced based on plan analysis
        chunks = [
            {"name": "Core Structure", "description": "Create module structure and main classes"},
            {"name": "Core Functions", "description": "Implement main functionality"},
            {"name": "Error Handling", "description": "Add error handling and validation"},
            {"name": "Tests", "description": "Create basic tests"},
            {"name": "Documentation", "description": "Add README and docstrings"},
        ]

        # Filter based on what's mentioned in the plan
        plan_lower = plan.lower()
        filtered_chunks = []
        for chunk in chunks:
            # Include chunk if it seems relevant to the plan
            if any(keyword in plan_lower for keyword in chunk["name"].lower().split()):
                filtered_chunks.append(chunk)

        return filtered_chunks if filtered_chunks else chunks[:3]  # At minimum, first 3 chunks

    async def _check_created_files(self, module_name: str):
        """Check what files have been created in the module directory."""
        module_path = self.output_dir / module_name
        if module_path.exists():
            files = list(module_path.glob("**/*.py"))
            for file in files:
                rel_path = file.relative_to(module_path)
                if str(rel_path) not in self.state.files_created:
                    self.state.files_created.append(str(rel_path))
                    logger.debug(f"Detected new file: {rel_path}")
