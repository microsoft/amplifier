"""Summarizer stage - creates summaries of each file using AI."""

from pathlib import Path

from rich.console import Console
from rich.progress import BarColumn
from rich.progress import Progress
from rich.progress import SpinnerColumn
from rich.progress import TaskProgressColumn
from rich.progress import TextColumn

from amplifier.ccsdk_toolkit.defensive import write_json_with_retry

from ..models import FileSummary
from ..models import SourceFile
from ..models import SynthesisState
from ..utils import query_claude_with_timeout


class SummarizerStage:
    """Summarizes markdown files using Claude."""

    def __init__(self, state_file: Path, console: Console | None = None):
        """Initialize the summarizer stage.

        Args:
            state_file: Path to save state
            console: Rich console for output
        """
        self.state_file = state_file
        self.console = console or Console()

    async def summarize_files(self, files: list[SourceFile], state: SynthesisState) -> list[FileSummary]:
        """Summarize a list of files.

        Args:
            files: List of source files to summarize
            state: Current synthesis state

        Returns:
            List of file summaries
        """
        summaries = []

        # Check which files are already processed
        processed_paths = {s.file_path for s in state.summaries}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console,
        ) as progress:
            task = progress.add_task(f"Summarizing {len(files)} files...", total=len(files))

            for file in files:
                # Skip if already processed
                if file.path in processed_paths:
                    progress.update(task, advance=1)
                    continue

                try:
                    summary = await self._summarize_single(file)
                    summaries.append(summary)

                    # Add to state and save immediately
                    state.summaries.append(summary)
                    state.processed_files += 1
                    state.current_stage = "summarizer"
                    self._save_state(state)

                    progress.update(task, advance=1, description=f"Summarized {file.path.name}")

                except Exception as e:
                    self.console.print(f"[red]Error summarizing {file.path}: {e}[/red]")
                    progress.update(task, advance=1)
                    continue

        return summaries

    async def _summarize_single(self, file: SourceFile) -> FileSummary:
        """Summarize a single file.

        Args:
            file: Source file to summarize

        Returns:
            FileSummary object
        """
        system_prompt = """You are an expert at analyzing documentation and extracting key insights.
Your task is to create structured summaries that capture the essence of documents."""

        prompt = f"""Analyze this document and provide a JSON summary:

Document: {file.path.name}
Content:
```
{file.content[:8000]}  # Limit content size
```

Provide a JSON response with the following structure:
{{
    "key_points": ["point 1", "point 2", ...],  // 3-5 key points
    "main_ideas": ["idea 1", "idea 2", ...],     // 2-3 main ideas
    "important_quotes": ["quote 1", "quote 2", ...]  // 2-3 important quotes
}}

Focus on:
- Core concepts and principles
- Actionable insights
- Cross-cutting themes
- Important patterns or methodologies"""

        response = await query_claude_with_timeout(prompt=prompt, system_prompt=system_prompt, parse_json=True)

        # Handle both dict and list responses
        if isinstance(response, dict):
            key_points = response.get("key_points", [])
            main_ideas = response.get("main_ideas", [])
            important_quotes = response.get("important_quotes", [])
        else:
            # Fallback for empty or malformed responses
            key_points = []
            main_ideas = []
            important_quotes = []

        return FileSummary(
            file_path=file.path,
            key_points=key_points,
            main_ideas=main_ideas,
            important_quotes=important_quotes,
            metadata=file.metadata,
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
