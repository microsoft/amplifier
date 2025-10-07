"""Index generation - creates index.md for all saved pages."""

import logging
from datetime import datetime
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


def generate_index(sites_dir: Path) -> str:
    """Generate markdown index of all saved pages.

    Args:
        sites_dir: Directory containing domain subdirectories

    Returns:
        Markdown content for index file
    """
    if not sites_dir.exists():
        logger.warning(f"Sites directory {sites_dir} does not exist")
        return "# Web to Markdown Index\n\nNo sites found.\n"

    # Collect all markdown files by domain
    domains = {}

    for domain_dir in sites_dir.iterdir():
        if not domain_dir.is_dir():
            continue

        domain_name = domain_dir.name
        md_files = list(domain_dir.glob("*.md"))

        if md_files:
            domains[domain_name] = []

            for md_file in sorted(md_files):
                # Try to extract metadata from frontmatter
                metadata = extract_frontmatter(md_file)

                domains[domain_name].append(
                    {
                        "file": md_file.name,
                        "path": md_file.relative_to(sites_dir),
                        "title": metadata.get("title", md_file.stem),
                        "url": metadata.get("url", ""),
                        "retrieved_at": metadata.get("retrieved_at", ""),
                    }
                )

    # Generate markdown index
    lines = [
        "# Web to Markdown Index",
        "",
        f"Generated: {datetime.now().isoformat()}",
        f"Total domains: {len(domains)}",
        "",
    ]

    if not domains:
        lines.append("No pages saved yet.")
    else:
        for domain in sorted(domains.keys()):
            lines.append(f"## {domain}")
            lines.append("")

            pages = domains[domain]
            lines.append(f"_{len(pages)} page(s)_")
            lines.append("")

            for page in pages:
                # Create relative link
                link_path = page["path"].as_posix()
                title = page["title"]

                # Add metadata if available
                if page["url"]:
                    lines.append(f"- [{title}]({link_path}) - [Original]({page['url']})")
                else:
                    lines.append(f"- [{title}]({link_path})")

                if page["retrieved_at"]:
                    lines.append(f"  - Retrieved: {page['retrieved_at']}")

            lines.append("")

    # Add statistics
    total_pages = sum(len(pages) for pages in domains.values())
    lines.extend(
        [
            "---",
            "",
            "**Statistics:**",
            f"- Total domains: {len(domains)}",
            f"- Total pages: {total_pages}",
            "",
        ]
    )

    content = "\n".join(lines)
    logger.info(f"Generated index with {len(domains)} domains and {total_pages} pages")

    return content


def extract_frontmatter(md_file: Path) -> dict:
    """Extract YAML frontmatter from markdown file.

    Args:
        md_file: Path to markdown file

    Returns:
        Dictionary of frontmatter data
    """
    try:
        with open(md_file, encoding="utf-8") as f:
            content = f.read()

        # Check if file starts with frontmatter
        if not content.startswith("---"):
            return {}

        # Find end of frontmatter
        lines = content.split("\n")
        end_index = -1

        for i, line in enumerate(lines[1:], 1):
            if line.strip() == "---":
                end_index = i
                break

        if end_index == -1:
            return {}

        # Parse YAML
        frontmatter_text = "\n".join(lines[1:end_index])
        return yaml.safe_load(frontmatter_text) or {}

    except Exception as e:
        logger.debug(f"Could not extract frontmatter from {md_file}: {e}")
        return {}
