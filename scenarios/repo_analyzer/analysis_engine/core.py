"""
Analysis engine for comparative repository analysis.

Performs deep analysis between source and target repositories.
"""

from typing import Any

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionOptions
from amplifier.ccsdk_toolkit.defensive import parse_llm_json
from amplifier.ccsdk_toolkit.defensive import retry_with_feedback
from amplifier.ccsdk_toolkit.sessions import SessionManager
from amplifier.utils.logger import get_logger
from scenarios.repo_analyzer.chunking import ChunkingResult
from scenarios.repo_analyzer.chunking import ChunkManager

logger = get_logger(__name__)


class AnalysisEngine:
    """Engine for deep comparative repository analysis."""

    def __init__(self) -> None:
        """Initialize the analysis engine."""
        self.session_manager = SessionManager()
        self.chunk_manager = ChunkManager()

    async def analyze_repositories(
        self, source_content: str, target_content: str, analysis_request: str, focus_areas: list[str] | None = None
    ) -> dict[str, Any]:
        """Perform deep comparative analysis between repositories.

        Args:
            source_content: Content from source repository (repomix output)
            target_content: Content from target repository (repomix output)
            analysis_request: User's specific analysis request
            focus_areas: Optional specific areas to focus on

        Returns:
            Analysis results with patterns, gaps, and opportunities
        """
        logger.info("Starting repository comparative analysis...")

        # Check if content is too large and needs chunking
        total_content_size = len(source_content) + len(target_content)
        if total_content_size > 50000:
            logger.info(f"Content too large ({total_content_size:,} chars), switching to chunked processing...")

            # Chunk the content
            self.chunk_manager.target_chunk_size = 15000
            source_chunks = self.chunk_manager.create_chunks(source_content)
            target_chunks = self.chunk_manager.create_chunks(target_content)

            # Use chunked analysis
            return await self.analyze_repository_chunked(
                source_chunks=source_chunks,
                target_chunks=target_chunks,
                analysis_request=analysis_request,
                focus_areas=focus_areas,
            )

        logger.info("Content size within limits, using standard analysis...")

        # Build focused prompt
        focus_context = ""
        if focus_areas:
            focus_context = "\n\nFOCUS AREAS:\n" + "\n".join(f"- {area}" for area in focus_areas)

        prompt = f"""Perform a deep comparative analysis between two repositories.

USER REQUEST:
{analysis_request}
{focus_context}

SOURCE REPOSITORY (Reference/Example):
{source_content[:50000]}  # Limit for context window

TARGET REPOSITORY (To be improved):
{target_content[:50000]}  # Limit for context window

Analyze and identify:

1. ARCHITECTURAL PATTERNS:
   - Key patterns and structures in source repo
   - What patterns are missing in target repo
   - How patterns could be adapted

2. CODE ORGANIZATION:
   - Module structure differences
   - Abstraction levels
   - Separation of concerns

3. IMPLEMENTATION GAPS:
   - Features present in source but not target
   - Quality differences (error handling, testing, etc.)
   - Technical debt in target

4. ADAPTATION OPPORTUNITIES:
   - Top 5-10 specific improvements for target
   - Each with concrete implementation guidance
   - Prioritized by impact

5. PHILOSOPHY ALIGNMENT:
   - How source embodies certain principles
   - Where target diverges from those principles
   - Specific changes to align philosophies

Return JSON with structure:
{{
    "patterns_identified": [
        {{"pattern": "...", "description": "...", "source_examples": [...], "target_status": "..."}}
    ],
    "gaps": [
        {{"category": "...", "description": "...", "impact": "high/medium/low", "location": "..."}}
    ],
    "opportunities": [
        {{
            "title": "...",
            "description": "...",
            "implementation_steps": [...],
            "expected_impact": "...",
            "priority": 1-10,
            "code_example": "..."
        }}
    ],
    "philosophy_analysis": {{
        "source_principles": [...],
        "target_alignment": {{"principle": "...", "status": "aligned/misaligned", "details": "..."}},
        "recommendations": [...]
    }},
    "summary": {{
        "key_findings": [...],
        "overall_assessment": "...",
        "quick_wins": [...],
        "long_term_improvements": [...]
    }}
}}"""

        options = SessionOptions(
            system_prompt="You are an expert software architect analyzing repositories for improvement opportunities.",
            retry_attempts=2,
        )

        try:
            async with ClaudeSession(options) as session:
                # Use retry_with_feedback for robust JSON extraction
                async def query_with_parsing(enhanced_prompt: str):
                    response = await session.query(enhanced_prompt)
                    if response and response.content:
                        parsed = parse_llm_json(response.content)
                        if parsed:
                            return parsed
                    return None

                parsed = await retry_with_feedback(
                    func=query_with_parsing, prompt=prompt, max_retries=3, provide_feedback=True
                )

                if parsed is None:
                    logger.error("Could not get analysis after retries")
                    return self._default_analysis()

                # Log key findings
                self._log_analysis_results(parsed)

                return parsed

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return self._default_analysis()

    def _log_analysis_results(self, analysis: dict[str, Any]) -> None:
        """Log key analysis findings for visibility."""
        logger.info("=" * 60)
        logger.info("REPOSITORY ANALYSIS COMPLETE")

        if "summary" in analysis:
            summary = analysis["summary"]
            if "key_findings" in summary:
                logger.info(f"\n📊 Key Findings ({len(summary['key_findings'])}):")
                for finding in summary["key_findings"][:3]:
                    logger.info(f"  • {finding}")

        if "opportunities" in analysis:
            opportunities = analysis["opportunities"]
            logger.info(f"\n🎯 Opportunities Identified: {len(opportunities)}")
            for i, opp in enumerate(opportunities[:3], 1):
                logger.info(f"  {i}. {opp.get('title', 'Unnamed')}")
                logger.info(f"     Priority: {opp.get('priority', 'N/A')}/10")

        if "gaps" in analysis:
            gaps = analysis["gaps"]
            high_priority = [g for g in gaps if g.get("impact") == "high"]
            logger.info(f"\n⚠️ Gaps Found: {len(gaps)} ({len(high_priority)} high priority)")

        logger.info("=" * 60)

    def _default_analysis(self) -> dict[str, Any]:
        """Return minimal analysis structure on failure."""
        return {
            "patterns_identified": [],
            "gaps": [],
            "opportunities": [],
            "philosophy_analysis": {"source_principles": [], "target_alignment": {}, "recommendations": []},
            "summary": {
                "key_findings": ["Analysis could not be completed"],
                "overall_assessment": "Failed to analyze",
                "quick_wins": [],
                "long_term_improvements": [],
            },
        }

    async def analyze_repository_chunked(
        self,
        source_chunks: ChunkingResult,
        target_chunks: ChunkingResult,
        analysis_request: str,
        focus_areas: list[str] | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Perform chunked analysis for large repositories.

        Args:
            source_chunks: Chunked source repository content
            target_chunks: Chunked target repository content
            analysis_request: User's specific analysis request
            focus_areas: Optional specific areas to focus on
            session_id: Optional session ID for resuming interrupted analysis

        Returns:
            Complete analysis results merged from all chunks
        """
        # Create or load session
        if session_id:
            session = self.session_manager.load_session(session_id)
            if not session:
                logger.warning(f"Session {session_id} not found, creating new one")
                session = self.session_manager.create_session(session_id)
        else:
            session = self.session_manager.create_session("repo_analysis")

        # Initialize session data if needed
        if "chunk_results" not in session.context:
            session.context = {
                "total_source_chunks": len(source_chunks.chunks),
                "total_target_chunks": len(target_chunks.chunks),
                "processed_chunks": [],
                "chunk_results": {},
                "status": "analyzing",
                "request": analysis_request,
                "focus_areas": focus_areas or [],
            }
            self.session_manager.save_session(session)

        logger.info(
            f"Starting chunked analysis: {len(source_chunks.chunks)} source chunks, {len(target_chunks.chunks)} target chunks"
        )

        # Process chunks with context preservation
        previous_context = ""
        chunk_analyses = []

        # For simplicity, we'll process source and target chunks in pairs
        # In practice, you might want more sophisticated pairing
        max_chunks = max(len(source_chunks.chunks), len(target_chunks.chunks))

        for i in range(max_chunks):
            chunk_key = f"chunk_{i}"

            # Skip if already processed
            if chunk_key in session.context["processed_chunks"]:
                logger.info(f"Skipping already processed chunk {i + 1}/{max_chunks}")
                if chunk_key in session.context["chunk_results"]:
                    chunk_analyses.append(session.context["chunk_results"][chunk_key])
                    # Extract context for next chunk
                    previous_context = self._extract_chunk_context(session.context["chunk_results"][chunk_key])
                continue

            logger.info(f"Processing chunk {i + 1}/{max_chunks}")

            # Get current chunks (use empty if one side has fewer chunks)
            source_chunk = source_chunks.chunks[i] if i < len(source_chunks.chunks) else None
            target_chunk = target_chunks.chunks[i] if i < len(target_chunks.chunks) else None

            if not source_chunk and not target_chunk:
                break

            # Analyze this chunk pair
            chunk_result = await self._analyze_chunk_pair(
                source_chunk=source_chunk,
                target_chunk=target_chunk,
                analysis_request=analysis_request,
                focus_areas=focus_areas,
                previous_context=previous_context,
                chunk_position=f"{i + 1}/{max_chunks}",
            )

            # Save progress immediately
            chunk_analyses.append(chunk_result)
            session.context["chunk_results"][chunk_key] = chunk_result
            session.context["processed_chunks"].append(chunk_key)
            self.session_manager.save_session(session)

            # Extract context for next chunk
            previous_context = self._extract_chunk_context(chunk_result)

            logger.info(f"Chunk {i + 1}/{max_chunks} analyzed and saved")

        # Merge all chunk results
        logger.info("Merging results from all chunks...")
        merged_result = self._merge_chunk_results(chunk_analyses)

        # Mark session as complete
        session.context["status"] = "complete"
        session.context["final_result"] = merged_result
        self.session_manager.save_session(session)

        logger.info("Chunked analysis complete")
        return merged_result

    async def _analyze_chunk_pair(
        self,
        source_chunk: Any | None,
        target_chunk: Any | None,
        analysis_request: str,
        focus_areas: list[str] | None,
        previous_context: str,
        chunk_position: str,
    ) -> dict[str, Any]:
        """Analyze a single pair of chunks."""
        # Build focused prompt with context
        focus_context = ""
        if focus_areas:
            focus_context = "\n\nFOCUS AREAS:\n" + "\n".join(f"- {area}" for area in focus_areas)

        # Include previous context if available
        context_section = ""
        if previous_context:
            context_section = f"""
CONTEXT FROM PREVIOUS CHUNKS:
{previous_context}

Build upon this context and add new findings.
"""

        source_content = source_chunk.content if source_chunk else "No source content for this chunk"
        target_content = target_chunk.content if target_chunk else "No target content for this chunk"

        prompt = f"""Perform comparative analysis on chunk {chunk_position} of repositories.

USER REQUEST:
{analysis_request}
{focus_context}
{context_section}

SOURCE REPOSITORY CHUNK (Reference/Example):
{source_content}

TARGET REPOSITORY CHUNK (To be improved):
{target_content}

Analyze this chunk and identify patterns, gaps, and opportunities.
Focus on what's present in THIS CHUNK while considering the previous context.

Return JSON with the same structure as before, but focused on this chunk's content.
Include a "chunk_summary" field with key points from this chunk.

{{
    "chunk_summary": "Brief summary of this chunk's key findings",
    "patterns_identified": [...],
    "gaps": [...],
    "opportunities": [...],
    "philosophy_analysis": {{...}},
    "summary": {{...}}
}}"""

        options = SessionOptions(
            system_prompt="You are an expert software architect analyzing repository chunks. Focus on the current chunk while maintaining context.",
            retry_attempts=2,
        )

        try:
            async with ClaudeSession(options) as session:

                async def query_with_parsing(enhanced_prompt: str) -> dict[str, Any] | None:
                    response = await session.query(enhanced_prompt)
                    if response and response.content:
                        parsed = parse_llm_json(response.content)
                        if parsed and isinstance(parsed, dict):
                            return parsed
                    return None

                parsed = await retry_with_feedback(
                    func=query_with_parsing, prompt=prompt, max_retries=2, provide_feedback=True
                )

                if parsed is None:
                    logger.warning(f"Could not analyze chunk {chunk_position}")
                    return self._default_chunk_analysis()

                return parsed

        except Exception as e:
            logger.error(f"Chunk analysis failed for {chunk_position}: {e}")
            return self._default_chunk_analysis()

    def _extract_chunk_context(self, chunk_result: dict[str, Any]) -> str:
        """Extract key context from chunk result for next chunk."""
        context_parts = []

        # Add chunk summary if available
        if "chunk_summary" in chunk_result:
            context_parts.append(f"Previous chunk summary: {chunk_result['chunk_summary']}")

        # Add top patterns
        if "patterns_identified" in chunk_result and chunk_result["patterns_identified"]:
            patterns = [p.get("pattern", "") for p in chunk_result["patterns_identified"][:3]]
            if patterns:
                context_parts.append(f"Key patterns found: {', '.join(patterns)}")

        # Add high priority gaps
        if "gaps" in chunk_result and chunk_result["gaps"]:
            high_gaps = [g for g in chunk_result["gaps"] if g.get("impact") == "high"]
            if high_gaps:
                gap_descriptions = [g.get("description", "")[:100] for g in high_gaps[:2]]
                context_parts.append(f"High priority gaps: {'; '.join(gap_descriptions)}")

        # Keep context reasonable size
        context = "\n".join(context_parts)
        if len(context) > 2000:
            context = context[:2000] + "..."

        return context

    def _merge_chunk_results(self, chunk_analyses: list[dict[str, Any]]) -> dict[str, Any]:
        """Merge results from all chunks into final analysis."""
        merged = {
            "patterns_identified": [],
            "gaps": [],
            "opportunities": [],
            "philosophy_analysis": {
                "source_principles": [],
                "target_alignment": {},
                "recommendations": [],
            },
            "summary": {
                "key_findings": [],
                "overall_assessment": "",
                "quick_wins": [],
                "long_term_improvements": [],
            },
            "chunk_summaries": [],
        }

        # Collect all unique items from chunks
        seen_patterns = set()
        seen_gaps = set()
        seen_opportunities = set()

        for chunk in chunk_analyses:
            # Add chunk summary
            if "chunk_summary" in chunk:
                merged["chunk_summaries"].append(chunk["chunk_summary"])

            # Merge patterns (deduplicate by pattern name)
            for pattern in chunk.get("patterns_identified", []):
                pattern_key = pattern.get("pattern", "")
                if pattern_key and pattern_key not in seen_patterns:
                    seen_patterns.add(pattern_key)
                    merged["patterns_identified"].append(pattern)

            # Merge gaps (deduplicate by description)
            for gap in chunk.get("gaps", []):
                gap_key = gap.get("description", "")
                if gap_key and gap_key not in seen_gaps:
                    seen_gaps.add(gap_key)
                    merged["gaps"].append(gap)

            # Merge opportunities (deduplicate by title)
            for opp in chunk.get("opportunities", []):
                opp_key = opp.get("title", "")
                if opp_key and opp_key not in seen_opportunities:
                    seen_opportunities.add(opp_key)
                    merged["opportunities"].append(opp)

            # Merge philosophy analysis
            if "philosophy_analysis" in chunk:
                phil = chunk["philosophy_analysis"]
                if "source_principles" in phil:
                    for principle in phil["source_principles"]:
                        if principle not in merged["philosophy_analysis"]["source_principles"]:
                            merged["philosophy_analysis"]["source_principles"].append(principle)
                if "recommendations" in phil:
                    for rec in phil["recommendations"]:
                        if rec not in merged["philosophy_analysis"]["recommendations"]:
                            merged["philosophy_analysis"]["recommendations"].append(rec)

            # Merge summary findings
            if "summary" in chunk:
                summary = chunk["summary"]
                for finding in summary.get("key_findings", []):
                    if finding not in merged["summary"]["key_findings"]:
                        merged["summary"]["key_findings"].append(finding)
                for win in summary.get("quick_wins", []):
                    if win not in merged["summary"]["quick_wins"]:
                        merged["summary"]["quick_wins"].append(win)
                for improvement in summary.get("long_term_improvements", []):
                    if improvement not in merged["summary"]["long_term_improvements"]:
                        merged["summary"]["long_term_improvements"].append(improvement)

        # Sort opportunities by priority
        merged["opportunities"].sort(key=lambda x: x.get("priority", 10), reverse=False)

        # Create overall assessment
        if merged["chunk_summaries"]:
            merged["summary"]["overall_assessment"] = f"Analysis of {len(chunk_analyses)} chunks completed. " + (
                merged["chunk_summaries"][0] if merged["chunk_summaries"] else "See detailed findings below."
            )

        return merged

    def _default_chunk_analysis(self) -> dict[str, Any]:
        """Return minimal chunk analysis structure on failure."""
        return {
            "chunk_summary": "Chunk analysis failed",
            "patterns_identified": [],
            "gaps": [],
            "opportunities": [],
            "philosophy_analysis": {"source_principles": [], "target_alignment": {}, "recommendations": []},
            "summary": {
                "key_findings": [],
                "overall_assessment": "",
                "quick_wins": [],
                "long_term_improvements": [],
            },
        }
