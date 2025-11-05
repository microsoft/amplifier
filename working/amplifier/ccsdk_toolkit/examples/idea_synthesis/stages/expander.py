"""Expander stage - expands themes with deeper context and synthesis."""

from pathlib import Path

from rich.console import Console
from rich.progress import Progress
from rich.progress import SpinnerColumn
from rich.progress import TextColumn

from amplifier.ccsdk_toolkit.defensive import write_json_with_retry

from ..models import CrossCuttingTheme
from ..models import ExpandedIdea
from ..models import FileSummary
from ..models import SourceFile
from ..models import SynthesisState
from ..utils import query_claude_with_timeout


class ExpanderStage:
    """Expands themes into comprehensive synthesis."""

    def __init__(self, state_file: Path, console: Console | None = None):
        """Initialize the expander stage.

        Args:
            state_file: Path to save state
            console: Rich console for output
        """
        self.state_file = state_file
        self.console = console or Console()

    async def expand_ideas(
        self,
        themes: list[CrossCuttingTheme],
        summaries: list[FileSummary],
        source_files: list[SourceFile],
        state: SynthesisState,
    ) -> list[ExpandedIdea]:
        """Expand themes into comprehensive ideas with context.

        Args:
            themes: List of cross-cutting themes
            summaries: List of file summaries
            source_files: Original source files
            state: Current synthesis state

        Returns:
            List of expanded ideas
        """
        # Skip if already processed
        if state.expanded_ideas:
            self.console.print("[yellow]Ideas already expanded, skipping...[/yellow]")
            return state.expanded_ideas

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=self.console
        ) as progress:
            task = progress.add_task(f"Expanding {len(themes)} themes...", total=len(themes))

            expanded_ideas = []

            for theme in themes:
                try:
                    expanded = await self._expand_theme(theme, summaries, source_files)
                    expanded_ideas.append(expanded)

                    # Save immediately
                    state.expanded_ideas.append(expanded)
                    state.current_stage = "expander"
                    self._save_state(state)

                    progress.update(task, advance=1, description=f"Expanded: {theme.theme[:30]}...")

                except Exception as e:
                    self.console.print(f"[red]Error expanding theme '{theme.theme}': {e}[/red]")
                    progress.update(task, advance=1)
                    continue

            return expanded_ideas

    async def _expand_theme(
        self, theme: CrossCuttingTheme, summaries: list[FileSummary], source_files: list[SourceFile]
    ) -> ExpandedIdea:
        """Expand a single theme with full context.

        Args:
            theme: Theme to expand
            summaries: All file summaries
            source_files: Original source files

        Returns:
            Expanded idea
        """
        # Gather relevant quotes from source files
        relevant_quotes = []
        for source_path in theme.source_files:
            # Find the source file
            source = next((s for s in source_files if s.path == source_path), None)
            if source:
                # Find summary for this file
                summary = next((s for s in summaries if s.file_path == source_path), None)
                if summary and summary.important_quotes:
                    for quote in summary.important_quotes[:2]:  # Limit quotes per file
                        relevant_quotes.append((source_path, quote))

        system_prompt = """You are an expert at synthesizing ideas and creating actionable insights.
Your task is to expand themes into comprehensive, actionable syntheses."""

        prompt = f"""Expand this theme into a comprehensive synthesis:

Theme: {theme.theme}
Description: {theme.description}

Supporting Points:
{chr(10).join(f"- {point}" for point in theme.supporting_points[:10])}

Source Documents: {", ".join(f.name for f in theme.source_files[:10])}

Important Quotes:
{chr(10).join(f'"{quote}" (from {path.name})' for path, quote in relevant_quotes[:10])}

Create an expanded synthesis that:
1. Provides a compelling title
2. Synthesizes the theme into actionable insights
3. Suggests concrete action items
4. Connects to the broader context

Return JSON:
{{
    "title": "Compelling title for this synthesis",
    "synthesis": "2-3 paragraph synthesis connecting all the ideas",
    "action_items": ["action 1", "action 2", "action 3"]
}}"""

        response = await query_claude_with_timeout(prompt=prompt, system_prompt=system_prompt, parse_json=True)

        # Handle both dict and list responses
        if isinstance(response, dict):
            title = response.get("title", theme.theme)
            synthesis = response.get("synthesis", "")
            action_items = response.get("action_items", [])
        else:
            # Fallback for empty or malformed responses
            title = theme.theme
            synthesis = theme.description
            action_items = []

        return ExpandedIdea(
            title=title,
            synthesis=synthesis,
            themes=[theme],
            supporting_quotes=relevant_quotes,
            action_items=action_items,
            metadata={"confidence": theme.confidence},
        )

    def _save_state(self, state: SynthesisState) -> None:
        """Save current state to disk."""
        state_dict = {
            "session_id": state.session_id,
            "total_files": state.total_files,
            "processed_files": state.processed_files,
            "current_stage": state.current_stage,
            "last_updated": state.last_updated.isoformat(),
            "metadata": state.metadata,
            "summaries": [
                {
                    "file_path": str(s.file_path),
                    "key_points": s.key_points,
                    "main_ideas": s.main_ideas,
                    "important_quotes": s.important_quotes,
                    "metadata": s.metadata,
                    "timestamp": s.timestamp.isoformat(),
                }
                for s in state.summaries
            ],
            "themes": [
                {
                    "theme": t.theme,
                    "description": t.description,
                    "supporting_points": t.supporting_points,
                    "source_files": [str(f) for f in t.source_files],
                    "confidence": t.confidence,
                    "metadata": t.metadata,
                }
                for t in state.themes
            ],
            "expanded_ideas": [
                {
                    "title": e.title,
                    "synthesis": e.synthesis,
                    "themes": [t.theme for t in e.themes],
                    "supporting_quotes": [[str(q[0]), q[1]] for q in e.supporting_quotes],
                    "action_items": e.action_items,
                    "metadata": e.metadata,
                    "timestamp": e.timestamp.isoformat(),
                }
                for e in state.expanded_ideas
            ],
        }

        write_json_with_retry(state_dict, self.state_file)
