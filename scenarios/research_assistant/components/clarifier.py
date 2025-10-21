"""Question clarification component for refining research questions."""

import logging
from typing import Any

from anthropic import Anthropic

from ..cli import get_user_input
from ..cli import print_info
from ..cli import print_progress
from ..models import ResearchContext
from ..models import ResearchDepth
from ..models import ResearchType

logger = logging.getLogger(__name__)


class QuestionClarifier:
    """Refines research questions through interactive dialogue."""

    def __init__(self: "QuestionClarifier", api_key: str) -> None:
        """Initialize question clarifier.

        Args:
            api_key: Anthropic API key
        """
        self.client = Anthropic(api_key=api_key)

    async def clarify_question(self: "QuestionClarifier", question: str) -> ResearchContext:
        """Interactive loop to refine question into full context.

        Args:
            question: Initial research question

        Returns:
            Complete ResearchContext
        """
        print_progress("Analyzing your research question...")

        clarifying_questions = self._generate_clarifying_questions(question)

        print_info("Let me ask a few questions to better understand your research needs:")
        print()

        answers: dict[str, str] = {}
        for i, q in enumerate(clarifying_questions, 1):
            print(f"[bold]{i}. {q}[/bold]")
            answer = get_user_input("Your answer")
            answers[q] = answer
            print()

        print_progress("Building research context from your responses...")

        context = self._build_context(question, clarifying_questions, answers)

        return context

    def _generate_clarifying_questions(self: "QuestionClarifier", question: str) -> list[str]:
        """Generate 3-5 clarifying questions using Claude.

        Args:
            question: Initial research question

        Returns:
            List of clarifying questions
        """
        prompt = f"""You are helping clarify a research question. Given the question below, generate 3-5 clarifying questions to better understand:

1. Research type (pricing, product comparison, market analysis, positioning, brand strategy, technical, competitive, or general)
2. Persona/lens (e.g., product manager, brand strategist, developer, etc.)
3. Research depth (quick overview with 5-10 sources, moderate research with 15-25 sources, or deep comprehensive analysis with 30+ sources)
4. Any constraints or focus areas

Research Question: {question}

Generate 3-5 clear, specific questions that will help clarify these aspects. Return ONLY the questions, one per line, without numbering."""

        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022", max_tokens=1024, messages=[{"role": "user", "content": prompt}]
        )

        questions_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                questions_text = block.text  # type: ignore[attr-defined]
                break
        if not questions_text:
            questions_text = str(response.content[0])

        questions = [q.strip() for q in questions_text.strip().split("\n") if q.strip()]

        return questions[:5]

    def _build_context(
        self: "QuestionClarifier", question: str, questions: list[str], answers: dict[str, str]
    ) -> ResearchContext:
        """Build ResearchContext from Q&A.

        Args:
            question: Original question
            questions: Clarifying questions asked
            answers: User's answers

        Returns:
            Populated ResearchContext
        """
        qa_text = "\n".join([f"Q: {q}\nA: {answers[q]}" for q in questions])

        prompt = f"""Based on the original research question and the clarifying Q&A below, extract structured information:

Original Question: {question}

Clarifying Q&A:
{qa_text}

Provide the following information in this exact format:

RESEARCH_TYPE: <one of: pricing, product_comparison, market_analysis, positioning, brand_strategy, technical, competitive, general>
PERSONA: <brief description of researcher persona, or "none" if not specified>
DEPTH: <one of: quick, moderate, deep>
CONSTRAINTS: <comma-separated list of constraints/focus areas, or "none" if not specified>

Be concise and direct."""

        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022", max_tokens=512, messages=[{"role": "user", "content": prompt}]
        )

        result_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                result_text = block.text  # type: ignore[attr-defined]
                break
        if not result_text:
            result_text = str(response.content[0])

        parsed = self._parse_context_response(result_text)

        return ResearchContext(
            question=question,
            research_type=ResearchType(parsed["research_type"]),
            persona=parsed["persona"] if parsed["persona"] != "none" else None,
            depth=ResearchDepth(parsed["depth"]),
            constraints=parsed["constraints"] if parsed["constraints"] else [],
        )

    def _parse_context_response(self: "QuestionClarifier", text: str) -> dict[str, Any]:
        """Parse Claude's structured response.

        Args:
            text: Response text

        Returns:
            Parsed values
        """
        lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
        parsed: dict[str, Any] = {}

        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower()
                value = value.strip()

                if key == "research_type":
                    parsed["research_type"] = value
                elif key == "persona":
                    parsed["persona"] = value
                elif key == "depth":
                    parsed["depth"] = value
                elif key == "constraints":
                    if value.lower() != "none":
                        parsed["constraints"] = [c.strip() for c in value.split(",")]
                    else:
                        parsed["constraints"] = []

        return parsed
