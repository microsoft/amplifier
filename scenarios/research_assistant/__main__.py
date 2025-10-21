"""Main orchestrator for research assistant CLI."""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

from .cli import print_error
from .cli import print_info
from .cli import print_section_header
from .cli import print_success
from .components.clarifier import QuestionClarifier
from .components.researcher import WebResearcher
from .components.themes import ThemeManager
from .components.verifier import FactVerifier
from .components.writer import ReportWriter
from .models import DeepResearchFindings
from .models import ResearchPhase
from .models import ResearchSession

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class ResearchAssistant:
    """Main orchestrator for research workflow."""

    def __init__(self: "ResearchAssistant", api_key: str, workspace_dir: Path) -> None:
        """Initialize research assistant.

        Args:
            api_key: Anthropic API key
            workspace_dir: Workspace directory for session data
        """
        self.api_key = api_key
        self.workspace_dir = workspace_dir
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

        self.clarifier = QuestionClarifier(api_key)
        self.researcher = WebResearcher(api_key)
        self.theme_manager = ThemeManager(api_key)
        self.verifier = FactVerifier(api_key)
        self.writer = ReportWriter(api_key)

    async def run(self: "ResearchAssistant", question: str | None = None, resume: bool = False) -> None:
        """Run the research workflow.

        Args:
            question: Initial research question (for new session)
            resume: Whether to resume last session
        """
        if resume:
            session = self._load_or_create_session(None)
            print_info(f"Resuming session: {session.session_id}")
        elif question:
            session = self._load_or_create_session(question)
            print_info(f"Starting new session: {session.session_id}")
        else:
            print_error("Either provide a question or use --resume")
            sys.exit(1)

        try:
            while session.phase != ResearchPhase.COMPLETED:
                if session.phase == ResearchPhase.CLARIFICATION:
                    await self._phase_clarification(session, question or "")

                elif session.phase == ResearchPhase.PRELIMINARY_RESEARCH:
                    await self._phase_preliminary_research(session)

                elif session.phase == ResearchPhase.THEME_REFINEMENT:
                    await self._phase_theme_refinement(session)

                elif session.phase == ResearchPhase.DEEP_RESEARCH:
                    await self._phase_deep_research(session)

                elif session.phase == ResearchPhase.REPORT_GENERATION:
                    await self._phase_report_generation(session)

                session.save(self.workspace_dir)

            print_section_header("Research Complete!")
            print_success(f"Final report saved to: {self.workspace_dir / 'final_report.md'}")
            print()
            print(session.final_report)

        except KeyboardInterrupt:
            print_info("\nSession interrupted. Progress saved. Use --resume to continue.")
            session.save(self.workspace_dir)
            sys.exit(0)

        except Exception as e:
            print_error(f"Error during research: {e}")
            logger.exception("Research workflow error")
            session.save(self.workspace_dir)
            sys.exit(1)

    async def _phase_clarification(self: "ResearchAssistant", session: ResearchSession, question: str) -> None:
        """Execute clarification phase.

        Args:
            session: Research session
            question: Initial question
        """
        print_section_header("Phase 1: Question Clarification")

        context = await self.clarifier.clarify_question(question)
        session.context = context
        session.phase = ResearchPhase.PRELIMINARY_RESEARCH

        print_info(f"Research Type: {context.research_type.value}")
        print_info(f"Research Depth: {context.depth.value}")
        if context.persona:
            print_info(f"Persona: {context.persona}")

    async def _phase_preliminary_research(self: "ResearchAssistant", session: ResearchSession) -> None:
        """Execute preliminary research phase.

        Args:
            session: Research session
        """
        print_section_header("Phase 2: Preliminary Research")

        if not session.context:
            print_error("No research context found")
            return

        max_sources = {"quick": 10, "moderate": 20, "deep": 30}
        target_sources = max_sources.get(session.context.depth.value, 20)

        findings = await self.researcher.research(session.context, max_sources=target_sources)

        await self.verifier.verify_findings(findings)

        session.preliminary_findings = findings
        session.phase = ResearchPhase.THEME_REFINEMENT

    async def _phase_theme_refinement(self: "ResearchAssistant", session: ResearchSession) -> None:
        """Execute theme refinement phase.

        Args:
            session: Research session
        """
        print_section_header("Phase 3: Theme Refinement")

        if not session.context or not session.preliminary_findings:
            print_error("Missing required data for theme refinement")
            return

        themes = await self.theme_manager.extract_themes(session.preliminary_findings, session.context)

        refined_themes = await self.theme_manager.refine_themes_with_user(themes)

        session.themes = refined_themes
        session.phase = ResearchPhase.DEEP_RESEARCH

    async def _phase_deep_research(self: "ResearchAssistant", session: ResearchSession) -> None:
        """Execute deep research phase.

        Args:
            session: Research session
        """
        print_section_header("Phase 4: Deep Research")

        if not session.context:
            print_error("No research context found")
            return

        print_info("Conducting focused research on refined themes...")

        deep_findings = DeepResearchFindings(themes_researched=[t.title for t in session.themes])

        for theme in session.themes[:5]:
            print_info(f"Researching theme: {theme.title}")

            findings = await self.researcher.research(session.context, max_sources=5)

            deep_findings.sources.extend(findings.sources)
            deep_findings.notes.extend(findings.notes)

        await self.verifier.verify_findings(deep_findings)

        session.deep_research = deep_findings
        session.phase = ResearchPhase.REPORT_GENERATION

    async def _phase_report_generation(self: "ResearchAssistant", session: ResearchSession) -> None:
        """Execute report generation phase.

        Args:
            session: Research session
        """
        print_section_header("Phase 5: Report Generation")

        if not session.context or not session.preliminary_findings or not session.deep_research:
            print_error("Missing required data for report generation")
            return

        draft = await self.writer.generate_report(
            session.context, session.preliminary_findings, session.deep_research, session.themes
        )

        session.report_draft = draft

        final_report = await self.writer.refine_with_feedback(draft, session.context)

        session.final_report = final_report
        session.phase = ResearchPhase.COMPLETED

        report_file = self.workspace_dir / "final_report.md"
        report_file.write_text(final_report)

    def _load_or_create_session(self: "ResearchAssistant", question: str | None) -> ResearchSession:
        """Load existing session or create new one.

        Args:
            question: Research question for new session

        Returns:
            ResearchSession
        """
        session_file = self.workspace_dir / "session.json"

        if session_file.exists():
            return ResearchSession.load(self.workspace_dir)

        if question:
            session_id = f"research_{int(asyncio.get_event_loop().time())}"
            session = ResearchSession.create_new(session_id)
            return session

        print_error("No existing session found and no question provided")
        sys.exit(1)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Interactive CLI tool for web research with AI assistance")
    parser.add_argument("question", nargs="?", help="Research question to investigate")
    parser.add_argument("--resume", action="store_true", help="Resume the last session")
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.home() / ".data" / "research_assistant",
        help="Workspace directory for session data",
    )

    args = parser.parse_args()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print_error("ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)

    assistant = ResearchAssistant(api_key, args.workspace)

    asyncio.run(assistant.run(question=args.question, resume=args.resume))


if __name__ == "__main__":
    main()
