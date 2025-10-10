"""Core chunking logic for repository content."""

import logging
import re

from .models import Chunk
from .models import ChunkingResult
from .tokenizer import TokenCounter

logger = logging.getLogger(__name__)


class ChunkManager:
    """Manages the chunking of repository XML content.

    Splits large repository XML into manageable chunks while preserving
    file boundaries where possible and maintaining overlap for context.
    """

    def __init__(self, target_chunk_size: int = 10000, overlap_size: int = 1000, encoding: str = "cl100k_base"):
        """Initialize the ChunkManager.

        Args:
            target_chunk_size: Target size for each chunk in tokens (default: 10000)
            overlap_size: Number of tokens to overlap between chunks (default: 1000)
            encoding: Tiktoken encoding to use (default: "cl100k_base")
        """
        self.target_chunk_size = target_chunk_size
        self.overlap_size = overlap_size
        self.token_counter = TokenCounter(encoding)

        # Validate parameters
        if overlap_size >= target_chunk_size:
            logger.warning(
                f"Overlap size ({overlap_size}) >= chunk size ({target_chunk_size}). "
                f"Setting overlap to {target_chunk_size // 10}"
            )
            self.overlap_size = target_chunk_size // 10

    def create_chunks(self, content: str) -> ChunkingResult:
        """Create chunks from repository XML content.

        Attempts to break at XML file boundaries where possible while
        maintaining the target chunk size and overlap.

        Args:
            content: The repository XML content to chunk

        Returns:
            ChunkingResult containing all chunks and statistics
        """
        if not content:
            return ChunkingResult(
                chunks=[],
                total_tokens=0,
                total_chunks=0,
                average_chunk_size=0,
                max_chunk_size=0,
                min_chunk_size=0,
                total_files=0,
                target_chunk_size=self.target_chunk_size,
                overlap_size=self.overlap_size,
            )

        # Extract file boundaries
        file_sections = self._extract_file_sections(content)

        # If content is small enough, return as single chunk
        total_tokens = self.token_counter.count_tokens(content)
        if total_tokens <= self.target_chunk_size:
            chunk = Chunk(
                index=0,
                content=content,
                token_count=total_tokens,
                start_position=0,
                end_position=len(content),
                files_included=list(file_sections.keys()),
                is_complete_file=True,
            )

            return ChunkingResult(
                chunks=[chunk],
                total_tokens=total_tokens,
                total_chunks=1,
                average_chunk_size=float(total_tokens),
                max_chunk_size=total_tokens,
                min_chunk_size=total_tokens,
                total_files=len(file_sections),
                target_chunk_size=self.target_chunk_size,
                overlap_size=self.overlap_size,
            )

        # Create chunks respecting file boundaries where possible
        chunks = self._create_chunks_with_boundaries(content, file_sections)

        # Calculate statistics
        if chunks:
            token_counts = [c.token_count for c in chunks]
            total_tokens_with_overlap = sum(token_counts)

            # Calculate unique tokens (excluding overlaps)
            unique_tokens = chunks[0].token_count
            for chunk in chunks[1:]:
                unique_tokens += chunk.token_count - chunk.overlap_tokens

            result = ChunkingResult(
                chunks=chunks,
                total_tokens=unique_tokens,
                total_chunks=len(chunks),
                average_chunk_size=sum(token_counts) / len(chunks),
                max_chunk_size=max(token_counts),
                min_chunk_size=min(token_counts),
                total_files=len(file_sections),
                target_chunk_size=self.target_chunk_size,
                overlap_size=self.overlap_size,
                metadata={"total_tokens_with_overlap": total_tokens_with_overlap},
            )
        else:
            result = ChunkingResult(
                chunks=[],
                total_tokens=0,
                total_chunks=0,
                average_chunk_size=0,
                max_chunk_size=0,
                min_chunk_size=0,
                total_files=0,
                target_chunk_size=self.target_chunk_size,
                overlap_size=self.overlap_size,
            )

        logger.info(f"Created {result.total_chunks} chunks from {total_tokens} tokens with {result.total_files} files")

        return result

    def _extract_file_sections(self, content: str) -> dict[str, tuple[int, int]]:
        """Extract file sections from repository XML.

        Args:
            content: Repository XML content

        Returns:
            Dictionary mapping file paths to (start_pos, end_pos) tuples
        """
        file_sections = {}

        # Pattern to match file tags with path attribute
        file_pattern = re.compile(r'<file\s+path="([^"]+)"[^>]*>(.*?)</file>', re.DOTALL)

        for match in file_pattern.finditer(content):
            file_path = match.group(1)
            start_pos = match.start()
            end_pos = match.end()
            file_sections[file_path] = (start_pos, end_pos)

        return file_sections

    def _create_chunks_with_boundaries(self, content: str, file_sections: dict[str, tuple[int, int]]) -> list[Chunk]:
        """Create chunks while respecting file boundaries where possible.

        Args:
            content: The full repository XML content
            file_sections: Dictionary of file paths to position tuples

        Returns:
            List of Chunk objects
        """
        chunks = []
        current_pos = 0
        chunk_index = 0

        # Sort files by position for sequential processing
        sorted_files = sorted(file_sections.items(), key=lambda x: x[1][0])

        while current_pos < len(content):
            # Determine chunk end position
            chunk_start = current_pos

            # Find ideal chunk end based on token count
            ideal_end = self._find_chunk_end_by_tokens(content, chunk_start, self.target_chunk_size)

            # Try to adjust to file boundary if close
            chunk_end = self._adjust_to_file_boundary(ideal_end, sorted_files, content, chunk_start)

            # Extract chunk content
            chunk_content = content[chunk_start:chunk_end]

            # Add overlap from previous chunk if not the first chunk
            overlap_tokens = 0
            if chunks and self.overlap_size > 0:
                overlap_content = self._get_overlap_content(content, chunks[-1], self.overlap_size)
                if overlap_content:
                    chunk_content = overlap_content + chunk_content
                    overlap_tokens = self.token_counter.count_tokens(overlap_content)

            # Determine which files are in this chunk
            files_in_chunk = self._find_files_in_range(sorted_files, chunk_start, chunk_end)

            # Check if chunk contains only complete files
            is_complete = self._check_complete_files(chunk_content, files_in_chunk)

            # Create chunk
            chunk = Chunk(
                index=chunk_index,
                content=chunk_content,
                token_count=self.token_counter.count_tokens(chunk_content),
                start_position=chunk_start,
                end_position=chunk_end,
                overlap_tokens=overlap_tokens,
                files_included=files_in_chunk,
                is_complete_file=is_complete,
                previous_chunk_index=chunk_index - 1 if chunk_index > 0 else None,
                next_chunk_index=None,  # Will be set later
            )

            # Update previous chunk's next_chunk_index
            if chunks:
                chunks[-1].next_chunk_index = chunk_index

            chunks.append(chunk)

            # Move to next chunk position
            current_pos = chunk_end
            chunk_index += 1

            # Safety check to prevent infinite loops
            if chunk_index > 10000:
                logger.error("Chunk creation exceeded maximum iterations")
                break

        return chunks

    def _find_chunk_end_by_tokens(self, content: str, start_pos: int, target_tokens: int) -> int:
        """Find the end position for a chunk with target token count.

        Args:
            content: Full content string
            start_pos: Starting position in content
            target_tokens: Target number of tokens

        Returns:
            End position for the chunk
        """
        # Start with a rough estimate (assuming ~4 chars per token)
        estimated_chars = target_tokens * 4
        test_end = min(start_pos + estimated_chars, len(content))

        # Binary search to find the right position
        left = start_pos
        right = len(content)
        best_end = test_end

        while left < right:
            mid = (left + right) // 2
            test_content = content[start_pos:mid]
            token_count = self.token_counter.count_tokens(test_content)

            if token_count <= target_tokens:
                best_end = mid
                left = mid + 1
            else:
                right = mid

            # Close enough
            if abs(token_count - target_tokens) < 50:
                best_end = mid
                break

        return min(best_end, len(content))

    def _adjust_to_file_boundary(
        self, ideal_end: int, sorted_files: list[tuple[str, tuple[int, int]]], content: str, chunk_start: int
    ) -> int:
        """Adjust chunk end to align with file boundaries if possible.

        Args:
            ideal_end: The ideal end position based on token count
            sorted_files: List of (file_path, (start, end)) tuples sorted by position
            content: Full content string
            chunk_start: Start position of the current chunk

        Returns:
            Adjusted end position
        """
        # Look for </file> tags near the ideal end
        search_window = 500  # Characters to search before/after ideal position
        search_start = max(ideal_end - search_window, chunk_start + 100)
        search_end = min(ideal_end + search_window, len(content))

        search_text = content[search_start:search_end]

        # Find all </file> tags in the search window
        file_ends = []
        for match in re.finditer(r"</file>", search_text):
            actual_pos = search_start + match.end()
            file_ends.append(actual_pos)

        # Choose the closest file boundary
        if file_ends:
            # Find the boundary closest to ideal_end
            closest_boundary = min(file_ends, key=lambda x: abs(x - ideal_end))

            # Only use it if it's not too far from ideal
            if abs(closest_boundary - ideal_end) < search_window:
                return closest_boundary

        return ideal_end

    def _get_overlap_content(self, content: str, previous_chunk: Chunk, overlap_tokens: int) -> str | None:
        """Get overlap content from the end of the previous chunk.

        Args:
            content: Full content string
            previous_chunk: The previous chunk
            overlap_tokens: Number of tokens to overlap

        Returns:
            Overlap content string or None
        """
        if not previous_chunk or overlap_tokens <= 0:
            return None

        # Get the end portion of the previous chunk
        prev_content = previous_chunk.content

        # Use token counter to get the last N tokens
        tokens = self.token_counter.encode(prev_content)
        if len(tokens) <= overlap_tokens:
            return prev_content

        overlap_token_ids = tokens[-overlap_tokens:]
        return self.token_counter.decode(overlap_token_ids)

    def _find_files_in_range(
        self, sorted_files: list[tuple[str, tuple[int, int]]], start_pos: int, end_pos: int
    ) -> list[str]:
        """Find which files are included in the given position range.

        Args:
            sorted_files: List of (file_path, (start, end)) tuples
            start_pos: Start position of range
            end_pos: End position of range

        Returns:
            List of file paths in the range
        """
        files_in_range = []

        for file_path, (file_start, file_end) in sorted_files:
            # Check if file overlaps with the chunk range
            if file_start < end_pos and file_end > start_pos:
                files_in_range.append(file_path)

        return files_in_range

    def _check_complete_files(self, chunk_content: str, files_in_chunk: list[str]) -> bool:
        """Check if chunk contains only complete files.

        Args:
            chunk_content: The chunk content
            files_in_chunk: List of file paths in the chunk

        Returns:
            True if all files in chunk are complete, False otherwise
        """
        if not files_in_chunk:
            return True

        # Count opening and closing file tags for each file
        for file_path in files_in_chunk:
            # Look for opening tag with this path
            open_pattern = f'<file\\s+path="{re.escape(file_path)}"[^>]*>'
            close_pattern = r"</file>"

            open_matches = len(re.findall(open_pattern, chunk_content))
            close_matches = len(re.findall(close_pattern, chunk_content))

            # If counts don't match, files are not complete
            if open_matches != close_matches:
                return False

        return True
