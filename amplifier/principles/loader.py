"""Loader for AI-First Principles specifications."""

import logging
import re
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Principle:
    """Represents a single AI-First principle."""

    number: int
    name: str
    category: str
    path: Path
    title: str | None = None
    description: str | None = None
    content: str | None = None
    metadata: dict | None = None
    related_principles: list[int] = None
    examples: list[dict] = None
    implementation_approaches: list[dict] = None
    common_pitfalls: list[str] = None
    tools: list[str] = None
    checklist: list[str] = None

    def __post_init__(self):
        """Initialize empty lists for list attributes if None."""
        if self.related_principles is None:
            self.related_principles = []
        if self.examples is None:
            self.examples = []
        if self.implementation_approaches is None:
            self.implementation_approaches = []
        if self.common_pitfalls is None:
            self.common_pitfalls = []
        if self.tools is None:
            self.tools = []
        if self.checklist is None:
            self.checklist = []

    def to_dict(self) -> dict:
        """Convert principle to dictionary."""
        return {
            "number": self.number,
            "name": self.name,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "related_principles": self.related_principles,
            "examples_count": len(self.examples),
            "approaches_count": len(self.implementation_approaches),
            "pitfalls_count": len(self.common_pitfalls),
            "tools_count": len(self.tools),
            "checklist_items": len(self.checklist),
        }


class PrincipleLoader:
    """Loads and parses AI-First principles from markdown files."""

    def __init__(self, principles_dir: Path = None):
        """Initialize the loader with principles directory."""
        if principles_dir is None:
            # Default to ai-first-principles in project root
            principles_dir = Path(__file__).parent.parent.parent / "ai-first-principles"
        self.principles_dir = principles_dir
        self.principles: dict[int, Principle] = {}
        self._load_all_principles()

    def _parse_principle_file(self, filepath: Path) -> Principle | None:
        """Parse a principle markdown file."""
        try:
            content = filepath.read_text(encoding="utf-8")

            # Extract principle number and name from filename
            filename = filepath.stem
            match = re.match(r"^(\d+)-(.+)$", filename)
            if not match:
                logger.warning(f"Invalid principle filename format: {filename}")
                return None

            number = int(match.group(1))
            name = match.group(2)

            # Determine category based on number
            if 1 <= number <= 6:
                category = "people"
            elif 7 <= number <= 19:
                category = "process"
            elif 20 <= number <= 37:
                category = "technology"
            elif 38 <= number <= 44:
                category = "governance"
            elif 45 <= number <= 52:
                category = "technology"  # Extended technology principles
            elif 53 <= number <= 55:
                category = "process"  # Extended process principles
            else:
                category = "unknown"

            # Extract title from H1
            title_match = re.search(r"^# (.+)$", content, re.MULTILINE)
            title = title_match.group(1) if title_match else name.replace("-", " ").title()

            # Extract plain-language definition
            def_match = re.search(r"## Plain-Language Definition\s+(.+?)(?=\n##|\Z)", content, re.DOTALL)
            description = def_match.group(1).strip() if def_match else None

            # Extract related principles
            related = []
            related_section = re.search(r"## Related Principles\s+(.+?)(?=\n##|\Z)", content, re.DOTALL)
            if related_section:
                related_nums = re.findall(r"#(\d+)", related_section.group(1))
                related = [int(n) for n in related_nums]

            # Extract implementation approaches count
            approaches = []
            approaches_section = re.search(r"## Implementation Approaches\s+(.+?)(?=\n##|\Z)", content, re.DOTALL)
            if approaches_section:
                # Count ### subsections
                approaches = re.findall(r"^### ", approaches_section.group(1), re.MULTILINE)

            # Extract examples count
            examples = []
            examples_section = re.search(r"## Good Examples vs Bad Examples\s+(.+?)(?=\n##|\Z)", content, re.DOTALL)
            if examples_section:
                # Count Good: and Bad: pairs
                good_examples = re.findall(r"^Good:", examples_section.group(1), re.MULTILINE)
                bad_examples = re.findall(r"^Bad:", examples_section.group(1), re.MULTILINE)
                examples = list(zip(good_examples, bad_examples, strict=False))

            # Extract common pitfalls
            pitfalls = []
            pitfalls_section = re.search(r"## Common Pitfalls\s+(.+?)(?=\n##|\Z)", content, re.DOTALL)
            if pitfalls_section:
                # Count numbered items
                pitfalls = re.findall(r"^\d+\. ", pitfalls_section.group(1), re.MULTILINE)

            # Extract tools
            tools = []
            tools_section = re.search(r"## Tools & Frameworks\s+(.+?)(?=\n##|\Z)", content, re.DOTALL)
            if tools_section:
                # Count bullet points
                tools = re.findall(r"^- ", tools_section.group(1), re.MULTILINE)

            # Extract checklist items
            checklist = []
            checklist_section = re.search(r"## Implementation Checklist\s+(.+?)(?=\n##|\Z)", content, re.DOTALL)
            if checklist_section:
                # Count checkbox items
                checklist = re.findall(r"^\[ \]", checklist_section.group(1), re.MULTILINE)

            principle = Principle(
                number=number,
                name=name,
                category=category,
                path=filepath,
                title=title,
                description=description,
                content=content,
                related_principles=related,
                implementation_approaches=approaches,
                examples=examples,
                common_pitfalls=pitfalls,
                tools=tools,
                checklist=checklist,
            )

            return principle

        except Exception as e:
            logger.error(f"Error parsing principle file {filepath}: {e}")
            return None

    def _load_all_principles(self):
        """Load all principles from the principles directory."""
        principles_path = self.principles_dir / "principles"
        if not principles_path.exists():
            logger.warning(f"Principles directory not found: {principles_path}")
            return

        # Find all principle markdown files
        for category_dir in principles_path.iterdir():
            if category_dir.is_dir() and category_dir.name in ["people", "process", "technology", "governance"]:
                for filepath in category_dir.glob("*.md"):
                    principle = self._parse_principle_file(filepath)
                    if principle:
                        self.principles[principle.number] = principle
                        logger.debug(f"Loaded principle #{principle.number}: {principle.name}")

        logger.info(f"Loaded {len(self.principles)} principles")

    def get_principle(self, number: int) -> Principle | None:
        """Get a principle by number."""
        return self.principles.get(number)

    def get_all_principles(self) -> list[Principle]:
        """Get all loaded principles."""
        return sorted(self.principles.values(), key=lambda p: p.number)

    def get_by_category(self, category: str) -> list[Principle]:
        """Get principles by category."""
        return sorted([p for p in self.principles.values() if p.category == category], key=lambda p: p.number)

    def get_related_principles(self, principle_number: int) -> list[Principle]:
        """Get principles related to a given principle."""
        principle = self.get_principle(principle_number)
        if not principle:
            return []

        related = []
        for num in principle.related_principles:
            related_principle = self.get_principle(num)
            if related_principle:
                related.append(related_principle)
        return related

    def search_by_keyword(self, keyword: str) -> list[Principle]:
        """Search principles by keyword in content."""
        keyword_lower = keyword.lower()
        results = []

        for principle in self.principles.values():
            if principle.content and keyword_lower in principle.content.lower():
                results.append(principle)

        return sorted(results, key=lambda p: p.number)

    def get_statistics(self) -> dict:
        """Get statistics about loaded principles."""
        stats = {
            "total": len(self.principles),
            "by_category": {},
            "complete": 0,
            "with_examples": 0,
            "with_approaches": 0,
            "with_checklist": 0,
        }

        for principle in self.principles.values():
            # Count by category
            if principle.category not in stats["by_category"]:
                stats["by_category"][principle.category] = 0
            stats["by_category"][principle.category] += 1

            # Count complete specs (basic heuristic)
            if (
                len(principle.examples) >= 5
                and len(principle.implementation_approaches) >= 6
                and len(principle.checklist) >= 8
            ):
                stats["complete"] += 1

            # Count specs with various elements
            if principle.examples:
                stats["with_examples"] += 1
            if principle.implementation_approaches:
                stats["with_approaches"] += 1
            if principle.checklist:
                stats["with_checklist"] += 1

        return stats
