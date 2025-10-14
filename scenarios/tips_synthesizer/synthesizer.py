"""Core synthesizer implementation for tips synthesis pipeline."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionManager
from amplifier.ccsdk_toolkit import SessionOptions
from amplifier.ccsdk_toolkit import ToolkitLogger
from amplifier.ccsdk_toolkit.defensive import isolate_prompt
from amplifier.ccsdk_toolkit.defensive import parse_llm_json
from amplifier.ccsdk_toolkit.defensive import retry_with_feedback
from amplifier.ccsdk_toolkit.defensive import write_json_with_retry

from .user_feedback import get_user_feedback_async

# System prompts for different roles
EXTRACTOR_PROMPT = """You are a tips extraction specialist. Extract individual tips/tricks from markdown content.

For each tip found:
1. Identify its core concept
2. Provide a concise title
3. Extract the full tip content
4. Note any context or prerequisites

Return as JSON array with this structure:
[
    {
        "title": "Clear, actionable title",
        "content": "Full tip content with examples",
        "context": "Any prerequisites or context",
        "category": "Category like 'productivity', 'debugging', 'workflow', etc."
    }
]"""

SYNTHESIZER_PROMPT = """You are a documentation synthesis expert. Create a cohesive guide from individual tips.

Requirements:
1. Organize tips into logical sections by category/theme
2. Create smooth transitions between topics
3. Eliminate redundancy while preserving nuance
4. Maintain grounding in source material
5. Write for clarity and usability
6. Use markdown formatting with proper headers

Structure the document with:
- Clear introduction
- Organized sections with ## headers
- Tips as subsections with ### headers
- Conclusion summarizing key takeaways"""

REVIEWER_PROMPT = """You are a quality reviewer for synthesized documentation.

Evaluate the document and provide structured feedback:
1. Completeness: Are all tips represented?
2. Grounding: Does content stay true to sources?
3. Coherence: Is the flow logical?
4. Redundancy: Is there unnecessary repetition?
5. Clarity: Is the writing clear and actionable?

Respond with JSON:
{
    "passes_review": true/false,
    "score": 0-100,
    "strengths": ["list of strengths"],
    "issues": ["list of specific issues to fix"],
    "suggestions": ["actionable improvement suggestions"]
}"""

WRITER_REFINEMENT_PROMPT = """You are a documentation writer. Refine the document based on reviewer feedback.

Reviewer feedback:
{feedback}

Current document:
{document}

Create an improved version that addresses all the issues while maintaining the strengths.
Return the complete refined document in markdown format."""


class TipsSynthesizer:
    """Multi-stage pipeline for synthesizing tips from markdown files."""

    def __init__(
        self,
        input_dir: Path,
        output_file: Path,
        temp_dir: Path | None = None,
        max_iterations: int = 3,
        resume: bool = False,
        interactive: bool = True,
    ):
        """Initialize the tips synthesizer.

        Args:
            input_dir: Directory containing markdown files with tips
            output_file: Output path for synthesized document
            temp_dir: Temporary directory for intermediate files
            max_iterations: Maximum review-refine iterations
            resume: Whether to resume from saved state
            interactive: Whether to enable human review checkpoints
        """
        self.logger = ToolkitLogger("tips_synthesizer")
        self.input_dir = input_dir
        self.output_file = output_file
        self.max_iterations = max_iterations
        self.interactive = interactive
        self.iteration = 0
        self.user_feedback = None

        # Set up session management
        self.session_mgr = SessionManager(session_dir=Path(".data/tips_synthesizer"))

        # Load or create session
        if resume:
            # Find most recent session
            sessions = list(self.session_mgr.session_dir.glob("*.json"))
            if sessions:
                most_recent = max(sessions, key=lambda p: p.stat().st_mtime)
                session_id = most_recent.stem
                loaded_session = self.session_mgr.load_session(session_id)
                if loaded_session:
                    self.session = loaded_session
                    self.logger.info(f"Resumed session: {session_id}")
                    # Restore iteration counter
                    self.iteration = self.session.context.get("review_iteration", 0)
                else:
                    self.session = self.session_mgr.create_session("tips_synthesis")
            else:
                self.session = self.session_mgr.create_session("tips_synthesis")
        else:
            self.session = self.session_mgr.create_session("tips_synthesis")

        # Store configuration in session
        if not resume or "config" not in self.session.context:
            self.session.context["config"] = {
                "input_dir": str(input_dir),
                "output_file": str(output_file),
                "max_iterations": max_iterations,
                "interactive": interactive,
                "started_at": datetime.now().isoformat(),
            }
            self.session_mgr.save_session(self.session)

        # Set up directories
        self.session_dir = self.session_mgr.session_dir / self.session.metadata.session_id
        self.temp_dir = temp_dir or self.session_dir / "temp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"Session directory: {self.session_dir}")
        if self.interactive:
            self.logger.info("🤝 Interactive mode enabled - will pause for human review")

    async def run(self) -> bool:
        """Orchestrate the pipeline stages based on current state.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current stage from session
            stage = self.session.context.get("stage", "extract")
            self.logger.info(f"Starting from stage: {stage}")

            # Execute pipeline stages
            if stage == "extract":
                await self._run_extraction_stage()
                stage = "notes"

            if stage == "notes":
                await self.create_individual_notes()
                self.session.context["stage"] = "synthesize"
                self.session_mgr.save_session(self.session)
                stage = "synthesize"

            if stage == "synthesize":
                approved = await self._run_synthesis_stage()
                if approved:
                    # User approved, skip review
                    self.session.context["stage"] = "complete"
                    self.session.context["completed_at"] = datetime.now().isoformat()
                    self.session_mgr.save_session(self.session)
                    await self._save_final_document()
                    return True
                self.session.context["stage"] = "review"
                self.session_mgr.save_session(self.session)
                stage = "review"

            if stage == "review":
                success = await self.review_and_refine()
                if success:
                    self.session.context["stage"] = "complete"
                    self.session.context["completed_at"] = datetime.now().isoformat()
                    self.session_mgr.save_session(self.session)
                    return True

            return self.session.context.get("stage") == "complete"

        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}")
            return False

    async def _run_extraction_stage(self) -> None:
        """Run extraction stage with defensive utilities."""
        await self.extract_tips()
        self.session.context["stage"] = "notes"
        self.session_mgr.save_session(self.session)

    async def _run_synthesis_stage(self) -> bool:
        """Run synthesis stage with human feedback checkpoint.

        Returns:
            True if user approved draft, False to continue refinement
        """
        await self.synthesize_document()

        # Human feedback checkpoint (if interactive mode)
        if self.interactive:
            draft_path = self.session_dir / f"draft_v{self.iteration + 1}.md"
            mode, feedback = await get_user_feedback_async(draft_path)

            if mode == "approve":
                self.logger.info("✅ User approved draft")
                return True
            if mode == "done" and feedback:
                self.logger.info(f"📝 User provided feedback: {len(feedback)} chars")
                # Store feedback for refinement
                self.user_feedback = feedback
                self.session.context["user_feedback"] = feedback
                self.session_mgr.save_session(self.session)
            # If skip or no feedback, continue to review stage

        return False

    async def extract_tips(self) -> None:
        """Stage 1: Extract tips from each markdown file."""
        self.logger.info("\n📖 Stage 1: Extracting tips from markdown files...")

        # Read all markdown files recursively
        files = list(self.input_dir.glob("**/*.md"))
        self.logger.info(f"Found {len(files)} markdown files")

        # Store file list in session
        self.session.context["input_files"] = [str(f.relative_to(self.input_dir)) for f in files]

        # Initialize extracted tips storage
        if "extracted_tips" not in self.session.context:
            self.session.context["extracted_tips"] = {}

        # Process each file
        for i, file_path in enumerate(files, 1):
            relative_path = str(file_path.relative_to(self.input_dir))

            # Skip if already processed
            if relative_path in self.session.context["extracted_tips"]:
                self.logger.debug(f"Skipping already processed: {relative_path}")
                continue

            self.logger.info(f"  [{i}/{len(files)}] Processing: {relative_path}")

            try:
                # Read file content
                content = file_path.read_text(encoding="utf-8")

                # Extract tips using Claude with defensive retry
                # Use isolate_prompt to prevent context contamination
                full_prompt = isolate_prompt(prompt=EXTRACTOR_PROMPT, content=content)

                async with ClaudeSession(options=SessionOptions()) as claude:
                    response = await retry_with_feedback(func=claude.query, prompt=full_prompt, max_retries=3)

                # Parse response with defensive default
                self.logger.debug(f"Raw LLM response: {response.content[:500]}")
                tips = parse_llm_json(response.content, default=[])

                # Normalize response: handle single tip as dict
                if isinstance(tips, dict):
                    # Check if it's a valid tip object (has expected fields)
                    if any(key in tips for key in ["title", "content", "category"]):
                        self.logger.debug("LLM returned single tip as dict, wrapping in list")
                        tips = [tips]  # Wrap single tip in list
                    else:
                        self.logger.warning(f"Unexpected dict structure: {tips}")
                        tips = []
                elif not isinstance(tips, list):
                    self.logger.warning(f"Expected list or dict but got {type(tips)}: {tips}")
                    tips = []

                # Store extracted tips
                self.session.context["extracted_tips"][relative_path] = tips
                self.logger.info(f"    → Extracted {len(tips)} tips")

                # Save after EVERY file
                self.session_mgr.save_session(self.session)

            except Exception as e:
                self.logger.error(f"    ✗ Failed to extract from {relative_path}: {e}")
                # Store empty list to mark as processed
                self.session.context["extracted_tips"][relative_path] = []
                self.session_mgr.save_session(self.session)

        # Summary
        total_tips = sum(len(tips) for tips in self.session.context["extracted_tips"].values())
        self.logger.info(f"\n✓ Extracted {total_tips} tips from {len(files)} files")

    async def create_individual_notes(self) -> None:
        """Stage 2: Create separate note files for each tip."""
        self.logger.info("\n📝 Stage 2: Creating individual note files...")

        extracted_tips = self.session.context.get("extracted_tips", {})
        if not extracted_tips:
            self.logger.warning("No extracted tips found!")
            return

        # Initialize note files storage
        if "note_files" not in self.session.context:
            self.session.context["note_files"] = {}

        note_index = 0
        for source_file, tips in extracted_tips.items():
            for tip in tips:
                note_id = f"tip_{note_index:04d}"

                # Skip if already created
                if note_id in self.session.context["note_files"]:
                    note_index += 1
                    continue

                # Create note content
                note_content = {
                    "id": note_id,
                    "source": source_file,
                    "title": tip.get("title", "Untitled Tip"),
                    "content": tip.get("content", ""),
                    "context": tip.get("context", ""),
                    "category": tip.get("category", "general"),
                }

                # Write note file with retry (defensive I/O)
                note_path = self.temp_dir / f"{note_id}.json"
                write_json_with_retry(note_content, note_path)

                # Store path in session
                self.session.context["note_files"][note_id] = str(note_path)
                note_index += 1

                # Save session periodically
                if note_index % 10 == 0:
                    self.session_mgr.save_session(self.session)

        # Final save
        self.session_mgr.save_session(self.session)
        self.logger.info(f"✓ Created {len(self.session.context['note_files'])} note files")

    async def synthesize_document(self) -> None:
        """Stage 3: Synthesize all tips into unified document."""
        self.logger.info("\n📚 Stage 3: Synthesizing tips into cohesive document...")

        note_files = self.session.context.get("note_files", {})
        if not note_files:
            self.logger.warning("No note files found!")
            return

        # Read all notes
        all_tips = []
        for note_id, note_path in note_files.items():
            try:
                with open(note_path, encoding="utf-8") as f:
                    note = json.load(f)
                    all_tips.append(note)
            except Exception as e:
                self.logger.warning(f"Could not read note {note_id}: {e}")

        if not all_tips:
            self.logger.error("No tips could be loaded!")
            return

        # Group tips by category
        categories: dict[str, list[Any]] = {}
        for tip in all_tips:
            category = tip.get("category", "general")
            if category not in categories:
                categories[category] = []
            categories[category].append(tip)

        # Create structured input for synthesis
        tips_summary = f"Total tips: {len(all_tips)}\nCategories: {', '.join(categories.keys())}\n\n"
        for category, tips in categories.items():
            tips_summary += f"\n## {category.title()} ({len(tips)} tips)\n"
            for tip in tips[:3]:  # Sample first 3 per category
                tips_summary += f"- {tip['title']}\n"

        # Full tips content
        tips_content = json.dumps(all_tips, indent=2)

        # Synthesize using Claude with defensive retry
        synthesis_prompt = (
            SYNTHESIZER_PROMPT
            + f"""

Here's a summary of the tips to synthesize:
{tips_summary}

Full tips content:
{tips_content}

Create a cohesive, well-organized document that incorporates all these tips."""
        )

        async with ClaudeSession(options=SessionOptions()) as claude:
            response = await retry_with_feedback(func=claude.query, prompt=synthesis_prompt, max_retries=3)

        # Store synthesized document
        self.session.context["current_draft"] = response.content
        self.session.context["draft_versions"] = [
            {
                "version": 1,
                "content": response.content,
                "timestamp": datetime.now().isoformat(),
            }
        ]

        # Save draft to file
        draft_path = self.session_dir / "draft_v1.md"
        draft_path.write_text(response.content, encoding="utf-8")

        self.session_mgr.save_session(self.session)
        self.logger.info(f"✓ Synthesized document created ({len(response.content)} chars)")

    async def review_and_refine(self) -> bool:
        """Stage 4: Iterative review loop with writer-reviewer pattern.

        Returns:
            True if document passes review, False otherwise
        """
        self.logger.info("\n🔄 Stage 4: Review and refinement loop...")

        max_iterations = self.session.context["config"]["max_iterations"]
        iteration = self.session.context.get("review_iteration", 0)

        # Initialize review history
        if "review_history" not in self.session.context:
            self.session.context["review_history"] = []

        while iteration < max_iterations:
            iteration += 1
            self.iteration = iteration
            self.logger.info(f"\n  Iteration {iteration}/{max_iterations}")

            current_draft = self.session.context.get("current_draft", "")
            if not current_draft:
                self.logger.error("No draft found for review!")
                return False

            # Reviewer role - evaluate the document
            self.logger.info("  🔍 Reviewing document quality...")
            review_prompt = REVIEWER_PROMPT + f"\n\nReview this synthesized tips document:\n\n{current_draft}"

            async with ClaudeSession(options=SessionOptions()) as reviewer:
                review_response = await retry_with_feedback(func=reviewer.query, prompt=review_prompt, max_retries=3)

            # Parse review response with defensive default
            # Add debug logging to see raw response
            self.logger.debug(f"Raw review response: {review_response.content[:500]}")

            review_result = parse_llm_json(
                review_response.content,
                default={
                    "passes_review": False,
                    "score": 0,
                    "issues": ["Could not parse review response"],
                },
            )

            # Additional validation and logging
            if not isinstance(review_result, dict):
                self.logger.warning(f"Review result not a dict: {type(review_result)}")
                review_result = {
                    "passes_review": False,
                    "score": 0,
                    "issues": ["Could not parse review response"],
                }

            # Log parsed review result for debugging
            self.logger.debug(f"Parsed review result: {review_result}")

            # Log review results
            score = review_result.get("score", 0)
            # Ensure score is numeric
            try:
                score = int(score) if score is not None else 0
            except (ValueError, TypeError):
                self.logger.warning(f"Invalid score value: {score}, defaulting to 0")
                score = 0

            self.logger.info(f"  📊 Review score: {score}/100")
            passes_review = review_result.get("passes_review", False)

            # Store review in history
            self.session.context["review_history"].append(
                {
                    "iteration": iteration,
                    "feedback": review_result,
                    "passed": passes_review,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Save state after review
            self.session.context["review_iteration"] = iteration
            self.session_mgr.save_session(self.session)

            # ALWAYS refine based on feedback, regardless of review score
            # The review score is informational only, not a gating condition
            self.logger.info(f"  📝 Refining based on review feedback (score: {score}/100)")
            await self._refine_document(review_result, iteration)

            # Human feedback checkpoint AFTER EVERY refinement (if interactive mode)
            if self.interactive:
                draft_path = self.session_dir / f"draft_v{iteration + 1}.md"
                self.logger.info(f"\n  📄 Draft refined: {draft_path.name}")

                mode, feedback = await get_user_feedback_async(draft_path)

                if mode == "approve":
                    self.logger.info("  ✅ User approved refined draft")
                    await self._save_final_document()
                    return True
                if mode == "done" and feedback:
                    self.logger.info(f"  📝 User provided additional feedback: {len(feedback)} chars")
                    # Store feedback for next iteration
                    self.user_feedback = feedback
                    self.session.context["user_feedback"] = feedback
                    self.session_mgr.save_session(self.session)
                    # Continue to next iteration
                elif mode == "skip":
                    self.logger.info("  ⏭️ User skipped review, continuing refinement")
                    # Continue to next iteration without user feedback

        # Max iterations reached
        self.logger.warning(f"\n⚠️ Maximum iterations ({max_iterations}) reached without full approval")
        self.logger.info("  ℹ️ Draft saved in session directory. Run again with --resume to continue refinement.")
        self.logger.info(f"  📂 Session directory: {self.session_dir}")
        # Don't save final document without approval
        return False

    async def _refine_document(self, review_feedback: dict[str, Any], iteration: int) -> None:
        """Refine document based on reviewer AND user feedback.

        Args:
            review_feedback: Feedback from reviewer
            iteration: Current iteration number
        """
        self.logger.info("  ✏️ Refining document based on feedback...")

        current_draft = self.session.context.get("current_draft", "")
        issues = review_feedback.get("issues", [])
        suggestions = review_feedback.get("suggestions", [])

        # Always refine if we have any feedback, even if minimal
        # This ensures we give the human a chance to review improvements

        # Combine reviewer and user feedback
        combined_feedback = {
            "issues": issues,
            "suggestions": suggestions,
            "strengths": review_feedback.get("strengths", []),
        }

        # Add user feedback if available
        if self.user_feedback or self.session.context.get("user_feedback"):
            user_fb = self.user_feedback or self.session.context.get("user_feedback")
            combined_feedback["user_feedback"] = user_fb
            self.logger.info("  📝 Including user feedback in refinement")

        # Format feedback for refinement
        feedback_json = json.dumps(combined_feedback, indent=2)

        # Refine the document with defensive retry
        refinement_prompt = WRITER_REFINEMENT_PROMPT.format(feedback=feedback_json, document=current_draft)

        async with ClaudeSession(options=SessionOptions()) as writer:
            refinement_response = await retry_with_feedback(func=writer.query, prompt=refinement_prompt, max_retries=3)

        # Update draft
        self.session.context["current_draft"] = refinement_response.content
        self.session.context["draft_versions"].append(
            {
                "version": iteration + 1,
                "content": refinement_response.content,
                "timestamp": datetime.now().isoformat(),
                "based_on_feedback": combined_feedback,
            }
        )

        # Save draft to file
        draft_path = self.session_dir / f"draft_v{iteration + 1}.md"
        draft_path.write_text(refinement_response.content, encoding="utf-8")

        # Clear user feedback after use
        self.user_feedback = None
        if "user_feedback" in self.session.context:
            del self.session.context["user_feedback"]

        # Save session after EVERY iteration
        self.session_mgr.save_session(self.session)
        self.logger.info(f"  💾 Refined draft saved (version {iteration + 1})")

    async def _save_final_document(self) -> None:
        """Save the final synthesized document."""
        current_draft = self.session.context.get("current_draft", "")
        if not current_draft:
            self.logger.error("No draft to save!")
            return

        try:
            # Write to output file
            self.output_file.parent.mkdir(parents=True, exist_ok=True)
            self.output_file.write_text(current_draft, encoding="utf-8")

            # Also save in session directory
            final_path = self.session_dir / "final_output.md"
            final_path.write_text(current_draft, encoding="utf-8")

            self.logger.info(f"✓ Final document saved to: {self.output_file}")

        except Exception as e:
            self.logger.error(f"Failed to save final document: {e}")
            raise
