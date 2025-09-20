"""Synthesizer stage - finds cross-cutting themes across summaries."""

from pathlib import Path

from rich.console import Console
from rich.progress import Progress
from rich.progress import SpinnerColumn
from rich.progress import TextColumn

from amplifier.ccsdk_toolkit.defensive import write_json_with_retry

from ..models import CrossCuttingTheme
from ..models import FileSummary
from ..models import SynthesisState
from ..utils import query_claude_with_timeout


class SynthesizerStage:
    """Synthesizes themes across document summaries."""

    def __init__(self, state_file: Path, console: Console | None = None):
        """Initialize the synthesizer stage.

        Args:
            state_file: Path to save state
            console: Rich console for output
        """
        self.state_file = state_file
        self.console = console or Console()

    async def synthesize_themes(self, summaries: list[FileSummary], state: SynthesisState) -> list[CrossCuttingTheme]:
        """Find cross-cutting themes from summaries.

        Args:
            summaries: List of file summaries
            state: Current synthesis state

        Returns:
            List of cross-cutting themes
        """
        # Skip if already processed
        if state.themes:
            self.console.print("[yellow]Themes already synthesized, skipping...[/yellow]")
            return state.themes

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=self.console
        ) as progress:
            task = progress.add_task("Synthesizing themes...", total=1)

            try:
                themes = await self._synthesize(summaries)

                # Save themes to state
                state.themes = themes
                state.current_stage = "synthesizer"
                self._save_state(state)

                progress.update(task, advance=1, description=f"Found {len(themes)} themes")

                return themes

            except Exception as e:
                self.console.print(f"[red]Error synthesizing themes: {e}[/red]")
                return []

    async def _synthesize(self, summaries: list[FileSummary]) -> list[CrossCuttingTheme]:
        """Perform theme synthesis using Claude.

        Args:
            summaries: List of file summaries

        Returns:
            List of themes
        """
        # Prepare summary data for Claude
        summary_data = []
        for summary in summaries:
            summary_data.append(
                {
                    "file": str(summary.file_path.name),
                    "key_points": summary.key_points,
                    "main_ideas": summary.main_ideas,
                }
            )

        system_prompt = """You are an expert at finding patterns and themes across multiple documents.
Your task is to identify cross-cutting themes that appear across different documents."""

        prompt = f"""Analyze these document summaries and identify cross-cutting themes:

Summaries:
```json
{str(summary_data)[:10000]}  # Limit size
```

Identify 3-7 major themes that appear across multiple documents. For each theme provide:

1. A clear theme name
2. A description of what this theme represents
3. Supporting points from the documents
4. Which documents support this theme

Return a JSON array of themes:
[
  {{
    "theme": "Theme Name",
    "description": "What this theme represents",
    "supporting_points": ["point 1", "point 2", ...],
    "source_files": ["file1.md", "file2.md", ...],
    "confidence": 0.8  // 0.0 to 1.0 based on evidence strength
  }}
]

Focus on themes that:
- Appear in multiple documents
- Represent important concepts or patterns
- Could guide decision-making or architecture
- Show evolution of thinking over time"""

        response = await query_claude_with_timeout(prompt=prompt, system_prompt=system_prompt, parse_json=True)

        themes = []
        # Ensure response is a list
        theme_list = response if isinstance(response, list) else []
        for theme_data in theme_list:
            if not isinstance(theme_data, dict):
                continue
            # Map file names back to paths
            source_paths = []
            for file_name in theme_data.get("source_files", []):
                for summary in summaries:
                    if summary.file_path.name == file_name:
                        source_paths.append(summary.file_path)
                        break

            themes.append(
                CrossCuttingTheme(
                    theme=theme_data.get("theme", ""),
                    description=theme_data.get("description", ""),
                    supporting_points=theme_data.get("supporting_points", []),
                    source_files=source_paths,
                    confidence=theme_data.get("confidence", 0.5),
                )
            )

        return themes

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
