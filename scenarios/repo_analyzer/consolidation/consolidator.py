"""
Core consolidation logic for cross-chunk analysis and context expansion.
"""

import logging
import time
from typing import Any

from amplifier.ccsdk_toolkit.claude import ClaudeSession
from amplifier.ccsdk_toolkit.defensive import parse_llm_json

from ..analysis_engine.session_manager import SessionManager
from ..chunking.models import Chunk
from ..chunking.models import ChunkingResult
from .models import ChunkAnalysis
from .models import ChunkReference
from .models import ConsolidatedResult

logger = logging.getLogger(__name__)


class ResultConsolidator:
    """Consolidates chunked analysis results with context expansion."""

    def __init__(self, session: ClaudeSession, session_manager: SessionManager):
        """Initialize the consolidator.

        Args:
            session: Claude session for LLM interactions
            session_manager: Session manager for tracking state
        """
        self.session = session
        self.session_manager = session_manager

    async def consolidate(
        self,
        chunking_result: ChunkingResult,
        chunk_analyses: list[dict[str, Any]],
        original_request: str,
        context_window: int = 2,
    ) -> ConsolidatedResult:
        """Consolidate chunk analyses with context expansion.

        Args:
            chunking_result: Original chunking result with chunk data
            chunk_analyses: List of initial analysis results per chunk
            original_request: The original analysis request
            context_window: Number of chunks to include before/after (default 2)

        Returns:
            Consolidated analysis result with merged insights
        """
        start_time = time.time()
        result = ConsolidatedResult()
        result.total_chunks_analyzed = len(chunk_analyses)

        # Step 1: Identify relevant chunks
        logger.info("Identifying relevant chunks for consolidation...")
        relevant_chunks = self.identify_relevant_chunks(chunk_analyses)
        result.chunk_references = relevant_chunks
        result.chunks_with_findings = len(relevant_chunks)

        # Step 2: Expand context windows for relevant chunks
        logger.info(f"Expanding context for {len(relevant_chunks)} relevant chunks...")
        expansion_groups = self.expand_context_windows(relevant_chunks, chunking_result.chunks, context_window)

        # Step 3: Re-read chunks with expanded context
        logger.info("Re-analyzing chunks with expanded context...")
        reanalyzed_chunks = await self.reread_with_context(expansion_groups, chunking_result.chunks, original_request)
        result.analyzed_chunks = reanalyzed_chunks
        result.chunks_reanalyzed = len(reanalyzed_chunks)
        result.llm_calls_made += len(reanalyzed_chunks)

        # Step 4: Merge insights from all analyses
        logger.info("Merging insights from all analyses...")
        self.merge_insights(result, chunk_analyses, reanalyzed_chunks)

        # Step 5: Identify cross-chunk patterns
        logger.info("Identifying cross-chunk patterns...")
        await self.identify_cross_chunk_patterns(result, original_request)
        result.llm_calls_made += 1

        result.processing_time = time.time() - start_time
        logger.info(f"Consolidation complete. {result.unique_findings_count} unique findings identified.")

        return result

    def identify_relevant_chunks(self, chunk_analyses: list[dict[str, Any]]) -> list[ChunkReference]:
        """Identify chunks containing opportunities, insights, or patterns.

        Args:
            chunk_analyses: List of analysis results from initial chunk processing

        Returns:
            List of chunk references for chunks with relevant findings
        """
        relevant_chunks = []

        for idx, analysis in enumerate(chunk_analyses):
            relevance_score = 0.0
            key_findings = []
            reasons = []

            # Check for opportunities
            opportunities = analysis.get("opportunities", [])
            if opportunities:
                relevance_score += min(0.4, len(opportunities) * 0.1)
                key_findings.extend([opp.get("title", "Opportunity") for opp in opportunities[:2]])
                reasons.append(f"{len(opportunities)} opportunities")

            # Check for insights
            insights = analysis.get("insights", [])
            if insights:
                relevance_score += min(0.3, len(insights) * 0.1)
                key_findings.extend([ins.get("title", "Insight") for ins in insights[:2]])
                reasons.append(f"{len(insights)} insights")

            # Check for patterns
            patterns = analysis.get("patterns", [])
            if patterns:
                relevance_score += min(0.2, len(patterns) * 0.1)
                key_findings.extend([pat.get("title", "Pattern") for pat in patterns[:1]])
                reasons.append(f"{len(patterns)} patterns")

            # Check for gaps
            gaps = analysis.get("gaps", [])
            if gaps:
                relevance_score += min(0.1, len(gaps) * 0.05)
                reasons.append(f"{len(gaps)} gaps")

            # Check for high-priority items
            high_priority_count = sum(
                1 for item in (opportunities + insights + patterns + gaps) if item.get("priority", 0) >= 8
            )
            if high_priority_count > 0:
                relevance_score += high_priority_count * 0.1
                reasons.append(f"{high_priority_count} high-priority items")

            # Add chunk if it has relevant content
            if relevance_score > 0:
                chunk_info = analysis.get("chunk_info", {})
                relevant_chunks.append(
                    ChunkReference(
                        chunk_index=idx,
                        start_line=chunk_info.get("start_line", idx * 100),
                        end_line=chunk_info.get("end_line", (idx + 1) * 100),
                        relevance_score=min(1.0, relevance_score),
                        reason=", ".join(reasons),
                        key_findings=key_findings[:5],  # Keep top 5 findings
                    )
                )

        # Sort by relevance score
        relevant_chunks.sort(key=lambda x: x.relevance_score, reverse=True)

        return relevant_chunks

    def expand_context_windows(
        self, relevant_chunks: list[ChunkReference], all_chunks: list[Chunk], context_window: int = 2
    ) -> list[tuple[int, set[int]]]:
        """Expand context windows around relevant chunks.

        Args:
            relevant_chunks: List of relevant chunk references
            all_chunks: All available chunks
            context_window: Number of chunks before/after to include

        Returns:
            List of (primary_index, context_indices_set) tuples
        """
        expansion_groups = []
        processed_primary = set()

        for chunk_ref in relevant_chunks:
            primary_idx = chunk_ref.chunk_index

            # Skip if already processed as primary
            if primary_idx in processed_primary:
                continue

            # Calculate context range
            start_idx = max(0, primary_idx - context_window)
            end_idx = min(len(all_chunks), primary_idx + context_window + 1)

            # Create set of context indices
            context_indices = set(range(start_idx, end_idx))

            # Check for overlapping groups
            merged = False
            for i, (existing_primary, existing_context) in enumerate(expansion_groups):
                if context_indices & existing_context:
                    # Merge overlapping groups
                    expansion_groups[i] = (existing_primary, existing_context | context_indices)
                    merged = True
                    break

            if not merged:
                expansion_groups.append((primary_idx, context_indices))
                processed_primary.add(primary_idx)

        return expansion_groups

    async def reread_with_context(
        self, expansion_groups: list[tuple[int, set[int]]], all_chunks: list[Chunk], original_request: str
    ) -> list[ChunkAnalysis]:
        """Re-analyze chunks with expanded context.

        Args:
            expansion_groups: Groups of chunks to analyze together
            all_chunks: All available chunks
            original_request: Original analysis request

        Returns:
            List of chunk analyses with expanded context
        """
        reanalyzed_chunks = []

        for primary_idx, context_indices in expansion_groups:
            # Sort indices for proper ordering
            sorted_indices = sorted(context_indices)

            # Combine content from all context chunks
            expanded_content_parts = []
            for idx in sorted_indices:
                if idx < len(all_chunks):
                    chunk = all_chunks[idx]
                    expanded_content_parts.append(
                        f"# --- Chunk {idx + 1} (Position {chunk.start_position}-{chunk.end_position}) ---\n{chunk.content}\n"
                    )

            expanded_content = "\n".join(expanded_content_parts)

            # Create focused prompt for re-analysis
            prompt = f"""Analyze this code with expanded context. The primary focus is on chunk {primary_idx + 1},
but you have surrounding chunks for better understanding.

Original Analysis Request: {original_request}

Code with Context:
{expanded_content}

Provide a detailed analysis focusing on:
1. Opportunities for improvement (with priority 1-10)
2. Key insights about the code structure and patterns
3. Identified patterns (both good and problematic)
4. Gaps or missing elements

Consider how the surrounding context affects your understanding of the primary chunk.

Return your analysis as JSON with this structure:
{{
    "opportunities": [
        {{
            "title": "Brief title",
            "description": "Detailed description",
            "priority": 8,
            "location": "Specific location in code",
            "suggestion": "Concrete improvement suggestion"
        }}
    ],
    "insights": [...],
    "patterns": [...],
    "gaps": [...]
}}"""

            try:
                response = await self.session.send_message(prompt)
                analysis_data = parse_llm_json(response)

                # Ensure analysis_data is a dict
                if not isinstance(analysis_data, dict):
                    analysis_data = {}

                chunk_analysis = ChunkAnalysis(
                    primary_chunk_index=primary_idx,
                    context_indices=sorted_indices,
                    expanded_content=expanded_content,
                    opportunities=analysis_data.get("opportunities", []) if analysis_data else [],
                    insights=analysis_data.get("insights", []) if analysis_data else [],
                    patterns=analysis_data.get("patterns", []) if analysis_data else [],
                    gaps=analysis_data.get("gaps", []) if analysis_data else [],
                    total_lines=sum(
                        len(all_chunks[idx].content.splitlines()) for idx in sorted_indices if idx < len(all_chunks)
                    ),
                    analysis_focus=f"Focused re-analysis with ±{len(sorted_indices) // 2} context",
                )

                reanalyzed_chunks.append(chunk_analysis)
                logger.info(f"Re-analyzed chunk {primary_idx + 1} with {len(sorted_indices)} total chunks of context")

            except Exception as e:
                logger.error(f"Error re-analyzing chunk {primary_idx + 1}: {e}")
                # Create empty analysis on error
                reanalyzed_chunks.append(
                    ChunkAnalysis(
                        primary_chunk_index=primary_idx,
                        context_indices=sorted_indices,
                        expanded_content=expanded_content,
                        total_lines=0,
                    )
                )

        return reanalyzed_chunks

    def merge_insights(
        self, result: ConsolidatedResult, initial_analyses: list[dict[str, Any]], reanalyzed_chunks: list[ChunkAnalysis]
    ):
        """Merge insights from initial and re-analyzed chunks.

        Args:
            result: Consolidated result to populate
            initial_analyses: Original chunk analyses
            reanalyzed_chunks: Re-analyzed chunks with context
        """
        # Track which chunks have been reanalyzed
        reanalyzed_indices = {chunk.primary_chunk_index for chunk in reanalyzed_chunks}

        # Process initial analyses (skip if chunk was reanalyzed)
        for idx, analysis in enumerate(initial_analyses):
            if idx in reanalyzed_indices:
                continue  # Skip - we have better analysis with context

            # Create chunk reference
            chunk_ref = ChunkReference(
                chunk_index=idx,
                start_line=analysis.get("chunk_info", {}).get("start_line", 0),
                end_line=analysis.get("chunk_info", {}).get("end_line", 0),
                relevance_score=0.5,  # Default score for non-reanalyzed
                reason="Initial analysis",
            )

            # Add findings
            for opp in analysis.get("opportunities", []):
                result.add_finding("opportunity", opp, chunk_ref)

            for insight in analysis.get("insights", []):
                result.add_finding("insight", insight, chunk_ref)

            for pattern in analysis.get("patterns", []):
                result.add_finding("pattern", pattern, chunk_ref)

            for gap in analysis.get("gaps", []):
                result.add_finding("gap", gap, chunk_ref)

        # Process reanalyzed chunks (these have priority)
        for chunk_analysis in reanalyzed_chunks:
            # Create chunk reference
            chunk_ref = ChunkReference(
                chunk_index=chunk_analysis.primary_chunk_index,
                start_line=0,  # Would need chunk info
                end_line=0,
                relevance_score=0.8,  # Higher score for reanalyzed
                reason="Re-analyzed with context",
            )

            # Add findings from reanalysis
            for opp in chunk_analysis.opportunities:
                result.add_finding("opportunity", opp, chunk_ref)

            for insight in chunk_analysis.insights:
                result.add_finding("insight", insight, chunk_ref)

            for pattern in chunk_analysis.patterns:
                result.add_finding("pattern", pattern, chunk_ref)

            for gap in chunk_analysis.gaps:
                result.add_finding("gap", gap, chunk_ref)

    async def identify_cross_chunk_patterns(self, result: ConsolidatedResult, original_request: str):
        """Identify patterns that span multiple chunks.

        Args:
            result: Consolidated result with all findings
            original_request: Original analysis request
        """
        if not result.opportunities and not result.insights and not result.patterns:
            return  # No findings to analyze

        # Create summary of all findings
        findings_summary = {
            "opportunities": [
                {"title": opp.get("title"), "priority": opp.get("priority", 5)}
                for opp in result.opportunities[:10]  # Top 10
            ],
            "insights": [{"title": ins.get("title")} for ins in result.insights[:10]],
            "patterns": [{"title": pat.get("title")} for pat in result.patterns[:10]],
            "gaps": [{"title": gap.get("title")} for gap in result.gaps[:5]],
        }

        prompt = f"""Given these findings from analyzing a codebase in chunks, identify cross-cutting patterns and system-level insights.

Original Request: {original_request}

Findings Summary:
- {len(result.opportunities)} opportunities identified
- {len(result.insights)} insights found
- {len(result.patterns)} patterns detected
- {len(result.gaps)} gaps identified

Top Findings:
{findings_summary}

Analyze these findings to identify:
1. Cross-cutting patterns that appear across multiple areas
2. System-level insights about the overall architecture
3. Common themes or recurring issues
4. Strategic recommendations based on the aggregate findings

Return as JSON:
{{
    "cross_chunk_patterns": [
        {{
            "title": "Pattern name",
            "description": "Description of the pattern",
            "evidence": ["Finding 1", "Finding 2"],
            "impact": "High/Medium/Low"
        }}
    ],
    "system_level_insights": [
        {{
            "title": "Insight title",
            "description": "System-level observation",
            "implications": "What this means for the system",
            "priority": 8
        }}
    ]
}}"""

        try:
            response = await self.session.send_message(prompt)
            cross_analysis = parse_llm_json(response)

            # Ensure cross_analysis is a dict
            if not isinstance(cross_analysis, dict):
                cross_analysis = {}

            result.cross_chunk_patterns = cross_analysis.get("cross_chunk_patterns", []) if cross_analysis else []
            result.system_level_insights = cross_analysis.get("system_level_insights", []) if cross_analysis else []

            logger.info(
                f"Identified {len(result.cross_chunk_patterns)} cross-chunk patterns "
                f"and {len(result.system_level_insights)} system-level insights"
            )

        except Exception as e:
            logger.error(f"Error identifying cross-chunk patterns: {e}")
            # Continue without cross-chunk analysis
