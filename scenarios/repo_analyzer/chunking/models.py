"""Data models for the chunking module."""

from dataclasses import dataclass
from dataclasses import field


@dataclass
class Chunk:
    """Represents a single chunk of repository content.

    Each chunk contains a portion of repository XML with metadata
    about its position, size, and relationships to other chunks.
    """

    index: int
    """Zero-based index of this chunk in the sequence."""

    content: str
    """The actual XML content of this chunk."""

    token_count: int
    """Number of tokens in this chunk."""

    start_position: int
    """Character position where this chunk starts in the original content."""

    end_position: int
    """Character position where this chunk ends in the original content."""

    overlap_tokens: int = 0
    """Number of tokens overlapping with the previous chunk."""

    files_included: list[str] = field(default_factory=list)
    """List of file paths included in this chunk (fully or partially)."""

    is_complete_file: bool = False
    """True if this chunk contains complete files only (no partial files)."""

    previous_chunk_index: int | None = None
    """Index of the previous chunk (None for first chunk)."""

    next_chunk_index: int | None = None
    """Index of the next chunk (None for last chunk)."""

    metadata: dict = field(default_factory=dict)
    """Additional metadata about this chunk."""


@dataclass
class ChunkingResult:
    """Result of chunking a repository.

    Contains all chunks and statistics about the chunking operation.
    """

    chunks: list[Chunk]
    """List of all chunks created from the repository."""

    total_tokens: int
    """Total number of tokens across all chunks."""

    total_chunks: int
    """Number of chunks created."""

    average_chunk_size: float
    """Average number of tokens per chunk."""

    max_chunk_size: int
    """Size of the largest chunk in tokens."""

    min_chunk_size: int
    """Size of the smallest chunk in tokens."""

    total_files: int
    """Total number of files included across all chunks."""

    chunking_strategy: str = "token_based_with_xml_boundaries"
    """Strategy used for chunking."""

    target_chunk_size: int = 10000
    """Target size for each chunk in tokens."""

    overlap_size: int = 1000
    """Number of overlapping tokens between chunks."""

    metadata: dict = field(default_factory=dict)
    """Additional metadata about the chunking operation."""

    def get_chunk(self, index: int) -> Chunk | None:
        """Get a chunk by index.

        Args:
            index: Zero-based index of the chunk

        Returns:
            The chunk at the given index, or None if index is out of bounds
        """
        if 0 <= index < len(self.chunks):
            return self.chunks[index]
        return None

    def get_chunks_for_file(self, file_path: str) -> list[Chunk]:
        """Get all chunks that contain a specific file.

        Args:
            file_path: Path of the file to search for

        Returns:
            List of chunks that include the specified file
        """
        return [chunk for chunk in self.chunks if file_path in chunk.files_included]
