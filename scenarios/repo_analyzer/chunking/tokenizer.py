"""Token counting and manipulation utilities using tiktoken."""

import logging

import tiktoken

logger = logging.getLogger(__name__)


class TokenCounter:
    """Utility class for counting and manipulating tokens.

    Uses tiktoken for accurate token counting compatible with OpenAI models.
    Defaults to cl100k_base encoding used by GPT-4.
    """

    def __init__(self, encoding_name: str = "cl100k_base"):
        """Initialize the token counter with specified encoding.

        Args:
            encoding_name: Name of the tiktoken encoding to use.
                          Default is "cl100k_base" (GPT-4 encoding).
                          Other options: "p50k_base", "r50k_base"
        """
        try:
            self.encoding = tiktoken.get_encoding(encoding_name)
            self.encoding_name = encoding_name
            logger.info(f"Initialized TokenCounter with {encoding_name} encoding")
        except Exception as e:
            # Fallback to cl100k_base if specified encoding fails
            logger.warning(f"Failed to load {encoding_name} encoding: {e}, falling back to cl100k_base")
            self.encoding = tiktoken.get_encoding("cl100k_base")
            self.encoding_name = "cl100k_base"

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in the given text.

        Args:
            text: The text to count tokens for

        Returns:
            Number of tokens in the text
        """
        if not text:
            return 0

        try:
            tokens = self.encoding.encode(text)
            return len(tokens)
        except Exception as e:
            logger.error(f"Error counting tokens: {e}")
            # Rough estimate as fallback: ~4 chars per token
            return len(text) // 4

    def encode(self, text: str) -> list[int]:
        """Encode text into token IDs.

        Args:
            text: The text to encode

        Returns:
            List of token IDs
        """
        if not text:
            return []

        try:
            return self.encoding.encode(text)
        except Exception as e:
            logger.error(f"Error encoding text: {e}")
            return []

    def decode(self, tokens: list[int]) -> str:
        """Decode token IDs back into text.

        Args:
            tokens: List of token IDs to decode

        Returns:
            Decoded text string
        """
        if not tokens:
            return ""

        try:
            return self.encoding.decode(tokens)
        except Exception as e:
            logger.error(f"Error decoding tokens: {e}")
            return ""

    def truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """Truncate text to fit within a maximum token count.

        Args:
            text: The text to truncate
            max_tokens: Maximum number of tokens allowed

        Returns:
            Truncated text that fits within the token limit
        """
        if not text or max_tokens <= 0:
            return ""

        tokens = self.encode(text)
        if len(tokens) <= max_tokens:
            return text

        # Truncate tokens and decode back to text
        truncated_tokens = tokens[:max_tokens]
        return self.decode(truncated_tokens)

    def split_by_tokens(self, text: str, chunk_size: int, overlap: int = 0) -> list[str]:
        """Split text into chunks of approximately the specified token size.

        Args:
            text: The text to split
            chunk_size: Target size for each chunk in tokens
            overlap: Number of tokens to overlap between chunks

        Returns:
            List of text chunks
        """
        if not text or chunk_size <= 0:
            return []

        tokens = self.encode(text)
        total_tokens = len(tokens)

        if total_tokens <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < total_tokens:
            # Calculate end position for this chunk
            end = min(start + chunk_size, total_tokens)

            # Extract chunk tokens and decode to text
            chunk_tokens = tokens[start:end]
            chunk_text = self.decode(chunk_tokens)
            chunks.append(chunk_text)

            # Move start position, accounting for overlap
            if end >= total_tokens:
                break

            start = end - overlap
            if start >= end:  # Prevent infinite loop if overlap >= chunk_size
                start = end

        return chunks

    def estimate_cost(self, token_count: int, model: str = "gpt-4") -> dict:
        """Estimate API cost for the given token count.

        Args:
            token_count: Number of tokens
            model: Model name for pricing (default: "gpt-4")

        Returns:
            Dictionary with cost estimates for input and output
        """
        # Approximate pricing as of 2024 (in USD per 1K tokens)
        # These are example values and should be updated with current pricing
        pricing = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        }

        model_pricing = pricing.get(model, pricing["gpt-4"])

        return {
            "model": model,
            "token_count": token_count,
            "estimated_input_cost": (token_count / 1000) * model_pricing["input"],
            "estimated_output_cost": (token_count / 1000) * model_pricing["output"],
            "currency": "USD",
        }
