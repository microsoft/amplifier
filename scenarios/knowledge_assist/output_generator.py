"""Output generator for knowledge-assist."""

import logging
from datetime import datetime
from pathlib import Path

from .citation_system import CitationContext
from .citation_system import filter_referenced_citations
from .citation_system import format_references
from .knowledge_retriever import RetrievedKnowledge
from .synthesis_engine import SynthesisResult

logger = logging.getLogger(__name__)


class OutputGenerator:
    """Generates markdown output with citations."""

    def generate(
        self,
        topic: str,
        question: str | None,
        synthesis_result: SynthesisResult,
        knowledge: RetrievedKnowledge,
        output_path: Path,
        citation_context: CitationContext | None = None,
    ) -> None:
        """Generate and save markdown output.

        Args:
            topic: Research topic
            question: Optional question
            synthesis_result: Synthesis result
            knowledge: Retrieved knowledge for citations
            output_path: Path to save output
            citation_context: Optional citation context for references
        """
        # Start with synthesis content
        content = synthesis_result.content

        # Add metadata header
        header = self._create_header(topic, question, synthesis_result)
        content = header + "\n\n" + content

        # Add references section using citation context if available
        if citation_context and citation_context.numbered_sources:
            # Filter to only actually cited sources
            # Use full content (including header) to find all citations
            filtered_context = filter_referenced_citations(content, citation_context)
            references = format_references(filtered_context)

            # Add web search note if applicable
            if synthesis_result.web_citations:
                if not references:
                    references = "## References\n\n"
                # Check if this is the placeholder web search note
                for citation in synthesis_result.web_citations:
                    if citation.get("title") == "Web Search" and not citation.get("url"):
                        references += "\n\n**Note:** Web search was used to inform general context of this analysis, specific citations are not available.\n"
                        break

            if references:
                content += "\n\n---\n\n" + references
        else:
            # Fallback to old citation format if no citation context
            citations = self._create_citations(knowledge, synthesis_result.web_citations)
            if citations:
                content += "\n\n---\n\n## Citations\n\n" + citations

        # Save to file
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                f.write(content)
            logger.info(f"Output saved to: {output_path}")
        except Exception as e:
            logger.error(f"Error saving output: {e}")
            raise

    def _create_header(self, topic: str, question: str | None, synthesis_result: SynthesisResult) -> str:
        """Create metadata header.

        Args:
            topic: Research topic
            question: Optional question
            synthesis_result: Synthesis result

        Returns:
            Header markdown
        """
        header = "---\n"
        header += f"topic: {topic}\n"
        if question:
            header += f"question: {question}\n"
        header += f"generated: {datetime.now().isoformat()}\n"
        header += f"model: {synthesis_result.model_used}\n"
        if synthesis_result.tokens_used:
            header += f"tokens: {synthesis_result.tokens_used}\n"
        header += "---"
        return header

    def _create_citations(self, knowledge: RetrievedKnowledge, web_citations: list[dict]) -> str:
        """Create citations section.

        Args:
            knowledge: Retrieved knowledge with sources
            web_citations: Web search citations

        Returns:
            Citations markdown
        """
        citations = []

        # Add knowledge sources (first reference only per spec)
        seen_sources = set()
        for source in knowledge.sources:
            if source not in seen_sources:
                citations.append(f"- Knowledge base: {source}")
                seen_sources.add(source)

        # Add web citations
        for citation in web_citations:
            if citation.get("url"):
                title = citation.get("title", "Untitled")
                url = citation["url"]
                citations.append(f"- [{title}]({url})")

        return "\n".join(citations) if citations else ""
