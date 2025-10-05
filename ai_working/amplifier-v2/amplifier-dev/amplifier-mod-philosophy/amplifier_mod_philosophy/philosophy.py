"""Philosophy injection module for Amplifier.

This module loads philosophy documents from a directory and injects them
as guidance into AI prompts automatically.
"""

from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class PhilosophyModule:
    """Manages philosophy documents and injects them into prompts.

    This module loads markdown philosophy documents from a directory
    and provides methods to inject them as context into AI prompts.
    """

    def __init__(self, docs_dir: Optional[Path] = None):
        """Initialize the philosophy module.

        Args:
            docs_dir: Directory containing philosophy markdown files.
                     Defaults to module's docs/ directory.
        """
        if docs_dir is None:
            # Default to the docs directory in the module
            module_dir = Path(__file__).parent.parent
            docs_dir = module_dir / "docs"

        self.docs_dir = Path(docs_dir)
        self.documents: Dict[str, str] = {}
        self.load_documents()

    def load_documents(self) -> None:
        """Load all markdown philosophy documents from the docs directory."""
        if not self.docs_dir.exists():
            logger.warning(f"Philosophy docs directory not found: {self.docs_dir}")
            return

        # Load all .md files from the docs directory
        for doc_path in self.docs_dir.glob("*.md"):
            try:
                with open(doc_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Use filename without extension as key
                    doc_name = doc_path.stem
                    self.documents[doc_name] = content
                    logger.info(f"Loaded philosophy document: {doc_name}")
            except Exception as e:
                logger.error(f"Failed to load philosophy document {doc_path}: {e}")

    def inject_guidance(self, prompt: str) -> str:
        """Inject philosophy guidance into a prompt.

        Prepends loaded philosophy documents to the given prompt
        as system context to guide AI behavior.

        Args:
            prompt: The original prompt to enhance

        Returns:
            The prompt with philosophy guidance prepended
        """
        if not self.documents:
            # No philosophy documents loaded, return original prompt
            return prompt

        # Build the philosophy context section
        philosophy_context = self._build_philosophy_context()

        # Prepend philosophy context to the prompt
        enhanced_prompt = f"{philosophy_context}\n\n{prompt}"

        logger.debug(f"Injected {len(self.documents)} philosophy documents into prompt")

        return enhanced_prompt

    def _build_philosophy_context(self) -> str:
        """Build the philosophy context section from loaded documents.

        Returns:
            Formatted philosophy context string
        """
        sections = ["<philosophy-guidance>"]

        for doc_name, content in self.documents.items():
            # Add each document as a named section
            sections.append(f"\n## {doc_name.replace('_', ' ').title()}\n")
            sections.append(content)

        sections.append("\n</philosophy-guidance>")

        return "\n".join(sections)

    def get_documents(self) -> Dict[str, str]:
        """Get all loaded philosophy documents.

        Returns:
            Dictionary mapping document names to their content
        """
        return self.documents.copy()

    def reload(self) -> None:
        """Reload philosophy documents from disk."""
        self.documents.clear()
        self.load_documents()
        logger.info(f"Reloaded {len(self.documents)} philosophy documents")