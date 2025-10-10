"""
Opportunity generator module.

Creates detailed implementation proposals from analysis results.
"""

from typing import Any

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionOptions
from amplifier.ccsdk_toolkit.defensive import parse_llm_json
from amplifier.ccsdk_toolkit.defensive import retry_with_feedback
from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


class OpportunityGenerator:
    """Generate actionable implementation opportunities."""

    async def generate_opportunities(
        self, analysis_results: dict[str, Any], target_context: str, max_opportunities: int = 10
    ) -> list[dict[str, Any]]:
        """Generate detailed implementation opportunities.

        Args:
            analysis_results: Results from analysis engine
            target_context: Target repository context
            max_opportunities: Maximum number to generate

        Returns:
            List of detailed opportunity proposals
        """
        # Extract key insights from analysis
        patterns = analysis_results.get("patterns_identified", [])
        gaps = analysis_results.get("gaps", [])
        existing_opps = analysis_results.get("opportunities", [])

        # If we already have opportunities from analysis, enhance them
        if existing_opps:
            logger.info(f"Enhancing {len(existing_opps)} existing opportunities from analysis...")
            return await self._enhance_existing_opportunities(
                existing_opps, patterns, gaps, target_context, max_opportunities
            )

        # Otherwise generate new ones
        logger.info(f"Generating up to {max_opportunities} new opportunities...")

        prompt = f"""Based on this repository analysis, generate detailed implementation opportunities.

ANALYSIS FINDINGS:
Patterns Identified: {len(patterns)}
Gaps Found: {len(gaps)}

KEY PATTERNS:
{self._format_patterns(patterns[:5])}

CRITICAL GAPS:
{self._format_gaps(gaps[:5])}

TARGET REPOSITORY CONTEXT:
{target_context[:10000]}

Generate {max_opportunities} DETAILED implementation opportunities. For each:

1. Give it a clear, actionable title
2. Provide comprehensive implementation guidance
3. Include concrete code examples where possible
4. Estimate effort and impact
5. Identify dependencies and risks
6. Suggest validation criteria

Return JSON array where each opportunity has:
{{
    "id": "opp_1",
    "title": "Clear actionable title",
    "category": "architecture|feature|quality|performance|testing",
    "description": "What and why",
    "implementation": {{
        "overview": "High-level approach",
        "steps": [
            {{"step": 1, "action": "...", "details": "...", "code_hint": "..."}}
        ],
        "code_examples": [
            {{"file": "path/to/file", "change": "before/after or new code", "language": "python"}}
        ],
        "estimated_effort": "hours|days|weeks",
        "complexity": "low|medium|high"
    }},
    "impact": {{
        "benefits": ["benefit1", "benefit2"],
        "metrics": ["metric to measure success"],
        "priority": 1-10,
        "risk_level": "low|medium|high"
    }},
    "dependencies": ["what needs to be in place first"],
    "validation": {{
        "success_criteria": ["criterion1", "criterion2"],
        "test_approach": "how to validate"
    }},
    "notes": "Additional context or warnings"
}}"""

        options = SessionOptions(
            system_prompt="You are an expert software architect creating actionable implementation plans.",
            retry_attempts=2,
        )

        try:
            async with ClaudeSession(options) as session:

                async def query_with_parsing(enhanced_prompt: str):
                    response = await session.query(enhanced_prompt)
                    if response and response.content:
                        logger.debug(f"Raw response length: {len(response.content)} chars")
                        parsed = parse_llm_json(response.content, verbose=True)

                        if parsed:
                            # Validate and extract opportunities
                            opportunities = self._extract_opportunities(parsed)
                            if opportunities:
                                logger.info(f"Successfully extracted {len(opportunities)} opportunities")
                                # Validate each opportunity has minimum required fields
                                valid_opps = []
                                for i, opp in enumerate(opportunities):
                                    if self._validate_opportunity(opp):
                                        valid_opps.append(opp)
                                    else:
                                        logger.warning(f"Opportunity {i + 1} missing required fields, skipping")

                                if valid_opps:
                                    return valid_opps
                                logger.error("No valid opportunities after validation")
                                return None
                            logger.error("Failed to extract opportunities from parsed JSON")
                            return None
                    logger.warning("Failed to parse response or empty content")
                    return None

                opportunities = await retry_with_feedback(
                    func=query_with_parsing, prompt=prompt, max_retries=3, provide_feedback=True
                )

                if opportunities is None:
                    logger.error("Could not generate opportunities after retries")
                    return []

                # Sort by priority
                opportunities = sorted(
                    opportunities, key=lambda x: x.get("impact", {}).get("priority", 5), reverse=True
                )

                self._log_opportunities(opportunities)
                return opportunities[:max_opportunities]

        except Exception as e:
            logger.error(f"Opportunity generation failed: {e}")
            return []

    async def _enhance_existing_opportunities(
        self,
        existing_opps: list[dict[str, Any]],
        patterns: list[dict],
        gaps: list[dict],
        target_context: str,
        max_opportunities: int,
    ) -> list[dict[str, Any]]:
        """Enhance existing opportunities with detailed implementation plans.

        Args:
            existing_opps: Opportunities from analysis engine
            patterns: Identified patterns
            gaps: Identified gaps
            target_context: Target repository context
            max_opportunities: Maximum to return

        Returns:
            Enhanced opportunities with full details
        """
        # If opportunities already have full structure, just return them
        if existing_opps and self._opportunities_are_complete(existing_opps[0]):
            logger.info("Opportunities already have complete structure, returning as-is")
            return existing_opps[:max_opportunities]

        prompt = f"""Enhance these existing opportunities with detailed implementation plans.

EXISTING OPPORTUNITIES ({len(existing_opps)}):
{self._format_existing_opportunities(existing_opps)}

SUPPORTING CONTEXT:
Patterns Identified: {len(patterns)}
Gaps Found: {len(gaps)}

TARGET REPOSITORY CONTEXT:
{target_context[:10000]}

For each opportunity above, enhance it with:
1. Clear, actionable title (keep existing if good)
2. Comprehensive implementation guidance
3. Concrete code examples where possible
4. Effort and impact estimates
5. Dependencies and risks
6. Validation criteria

Return JSON array with the SAME opportunities but enhanced:
{{
    "id": "opp_1",
    "title": "Original or improved title",
    "category": "architecture|feature|quality|performance|testing",
    "description": "Enhanced description",
    "implementation": {{
        "overview": "High-level approach",
        "steps": [
            {{"step": 1, "action": "...", "details": "...", "code_hint": "..."}}
        ],
        "code_examples": [
            {{"file": "path/to/file", "change": "before/after or new code", "language": "python"}}
        ],
        "estimated_effort": "hours|days|weeks",
        "complexity": "low|medium|high"
    }},
    "impact": {{
        "benefits": ["benefit1", "benefit2"],
        "metrics": ["metric to measure success"],
        "priority": 1-10,
        "risk_level": "low|medium|high"
    }},
    "dependencies": ["what needs to be in place first"],
    "validation": {{
        "success_criteria": ["criterion1", "criterion2"],
        "test_approach": "how to validate"
    }},
    "notes": "Additional context or warnings"
}}"""

        options = SessionOptions(
            system_prompt="You are an expert software architect enhancing implementation plans.",
            retry_attempts=2,
        )

        try:
            async with ClaudeSession(options) as session:

                async def query_with_parsing(enhanced_prompt: str):
                    response = await session.query(enhanced_prompt)
                    if response and response.content:
                        logger.debug(f"Raw response length: {len(response.content)} chars")
                        parsed = parse_llm_json(response.content, verbose=True)

                        if parsed:
                            # Validate and extract opportunities
                            opportunities = self._extract_opportunities(parsed)
                            if opportunities:
                                logger.info(f"Successfully extracted {len(opportunities)} opportunities")
                                # Validate each opportunity has minimum required fields
                                valid_opps = []
                                for i, opp in enumerate(opportunities):
                                    if self._validate_opportunity(opp):
                                        valid_opps.append(opp)
                                    else:
                                        logger.warning(f"Opportunity {i + 1} missing required fields, skipping")

                                if valid_opps:
                                    return valid_opps
                                logger.error("No valid opportunities after validation")
                                return None
                            logger.error("Failed to extract opportunities from parsed JSON")
                            return None
                    logger.warning("Failed to parse response or empty content")
                    return None

                opportunities = await retry_with_feedback(
                    func=query_with_parsing, prompt=prompt, max_retries=3, provide_feedback=True
                )

                if opportunities is None:
                    logger.warning("Could not enhance opportunities, returning originals")
                    return existing_opps[:max_opportunities]

                # Sort by priority
                opportunities = sorted(
                    opportunities, key=lambda x: x.get("impact", {}).get("priority", 5), reverse=True
                )

                self._log_opportunities(opportunities)
                return opportunities[:max_opportunities]

        except Exception as e:
            logger.error(f"Opportunity enhancement failed: {e}")
            logger.warning("Returning original opportunities")
            return existing_opps[:max_opportunities]

    def _opportunities_are_complete(self, opp: dict[str, Any]) -> bool:
        """Check if opportunity already has full structure."""
        required_fields = ["implementation", "impact", "validation"]
        return all(field in opp for field in required_fields)

    def _extract_opportunities(self, parsed: Any) -> list[dict[str, Any]] | None:
        """Extract opportunities from parsed JSON response.

        Handles various response formats:
        - Direct list of opportunities
        - Dict with 'opportunities' key
        - Dict with 'items' or 'results' key
        """
        if not parsed:
            return None

        # If it's already a list, validate it contains opportunities
        if isinstance(parsed, list):
            if parsed and isinstance(parsed[0], dict):
                # Check if it's actually opportunities vs code examples
                first_item = parsed[0]
                if "file" in first_item and "change" in first_item and "id" not in first_item:
                    logger.error("List contains code examples, not opportunities")
                    return None
                return parsed
            return None

        # If it's a dict, look for opportunities in various keys
        if isinstance(parsed, dict):
            # Common keys where opportunities might be stored
            for key in ["opportunities", "items", "results", "data"]:
                if key in parsed and isinstance(parsed[key], list):
                    return self._extract_opportunities(parsed[key])

            # Check if this is a single opportunity mistakenly parsed
            if "file" in parsed and "change" in parsed:
                logger.error("Parsed a code example structure instead of opportunities")
                return None

            # Check if dict itself looks like a single opportunity
            if "id" in parsed or "title" in parsed:
                logger.warning("Found single opportunity instead of list, wrapping it")
                return [parsed]

        return None

    def _validate_opportunity(self, opp: dict[str, Any]) -> bool:
        """Validate opportunity has minimum required fields."""
        if not isinstance(opp, dict):
            return False

        # Must have at least a title or description
        if not (opp.get("title") or opp.get("description")):
            logger.warning(f"Opportunity missing title and description: {opp.get('id', 'unknown')}")
            return False

        # Must have an ID (generate one if missing)
        if not opp.get("id"):
            import uuid

            opp["id"] = f"opp_{uuid.uuid4().hex[:8]}"
            logger.debug(f"Generated ID for opportunity: {opp['id']}")

        return True

    def _format_existing_opportunities(self, opportunities: list[dict]) -> str:
        """Format existing opportunities for enhancement prompt."""
        if not opportunities:
            return "No opportunities to enhance"

        formatted = []
        for i, opp in enumerate(opportunities, 1):
            formatted.append(f"\n{i}. {opp.get('title', 'Untitled')}")
            formatted.append(f"   Description: {opp.get('description', 'No description')}")
            if "priority" in opp:
                formatted.append(f"   Priority: {opp.get('priority')}/10")
            if "expected_impact" in opp:
                formatted.append(f"   Expected Impact: {opp.get('expected_impact')}")
            if "implementation_steps" in opp:
                steps = opp.get("implementation_steps", [])
                formatted.append(f"   Steps: {len(steps)} defined")

        return "\n".join(formatted)

    def _format_patterns(self, patterns: list[dict]) -> str:
        """Format patterns for prompt."""
        if not patterns:
            return "No patterns identified"

        formatted = []
        for p in patterns:
            formatted.append(f"- {p.get('pattern', 'Unknown')}: {p.get('description', '')}")
        return "\n".join(formatted)

    def _format_gaps(self, gaps: list[dict]) -> str:
        """Format gaps for prompt."""
        if not gaps:
            return "No gaps identified"

        formatted = []
        for g in gaps:
            impact = g.get("impact", "unknown")
            formatted.append(f"- [{impact.upper()}] {g.get('description', '')}")
        return "\n".join(formatted)

    def _log_opportunities(self, opportunities: list[dict[str, Any]]) -> None:
        """Log generated opportunities."""
        logger.info("=" * 60)
        logger.info(f"GENERATED {len(opportunities)} OPPORTUNITIES")

        for i, opp in enumerate(opportunities[:5], 1):
            logger.info(f"\n{i}. {opp.get('title', 'Unnamed')}")
            logger.info(f"   Category: {opp.get('category', 'unknown')}")

            impact = opp.get("impact", {})
            logger.info(f"   Priority: {impact.get('priority', 'N/A')}/10")
            logger.info(f"   Effort: {opp.get('implementation', {}).get('estimated_effort', 'unknown')}")
            logger.info(f"   Risk: {impact.get('risk_level', 'unknown')}")

        if len(opportunities) > 5:
            logger.info(f"\n... and {len(opportunities) - 5} more opportunities")

        logger.info("=" * 60)
