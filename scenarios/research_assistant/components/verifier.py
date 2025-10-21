"""Fact verification component."""

import logging

from anthropic import Anthropic

from ..cli import print_progress
from ..models import DeepResearchFindings
from ..models import PreliminaryFindings

logger = logging.getLogger(__name__)


class FactVerifier:
    """Verifies research notes against source content."""

    def __init__(self: "FactVerifier", api_key: str) -> None:
        """Initialize fact verifier.

        Args:
            api_key: Anthropic API key
        """
        self.client = Anthropic(api_key=api_key)

    async def verify_findings(self: "FactVerifier", findings: PreliminaryFindings | DeepResearchFindings) -> None:
        """Verify all notes against their sources (modifies in-place).

        Args:
            findings: Findings to verify
        """
        print_progress(f"Verifying {len(findings.notes)} research notes...")

        source_map = {source.url: source for source in findings.sources}

        verified_count = 0
        failed_count = 0

        for note in findings.notes:
            source = source_map.get(note.source_url)

            if not source:
                logger.warning(f"Source not found for note: {note.source_url}")
                note.verified = False
                note.verification_notes = "Source not available"
                failed_count += 1
                continue

            is_verified, verification_notes = self._verify_note(note.content, source.content)

            note.verified = is_verified
            note.verification_notes = verification_notes

            if is_verified:
                verified_count += 1
            else:
                failed_count += 1

        print_progress(f"Verification complete: {verified_count} verified, {failed_count} failed")

        if failed_count > 0:
            logger.warning(f"{failed_count} notes could not be verified against their sources")

    def _verify_note(self: "FactVerifier", note_content: str, source_content: str) -> tuple[bool, str]:
        """Verify a single note against source content.

        Args:
            note_content: Research note content
            source_content: Source content

        Returns:
            Tuple of (verified, verification_notes)
        """
        source_sample = source_content[:3000]

        prompt = f"""Verify if this research note is supported by the source content:

Research Note:
{note_content}

Source Content:
{source_sample}

Determine if the note is:
1. Directly supported by the source (facts, quotes, data match)
2. Reasonably inferred from the source
3. Not supported or contradicted by the source

Respond in this format:
VERIFIED: <yes/no>
NOTES: <brief explanation>"""

        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022", max_tokens=256, messages=[{"role": "user", "content": prompt}]
        )

        verification_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                verification_text = block.text  # type: ignore[attr-defined]
                break
        if not verification_text:
            verification_text = str(response.content[0])

        verified = False
        notes = "Unable to verify"

        for line in verification_text.strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().upper()
                value = value.strip()

                if key == "VERIFIED":
                    verified = value.lower() in ["yes", "true"]
                elif key == "NOTES":
                    notes = value

        return verified, notes
