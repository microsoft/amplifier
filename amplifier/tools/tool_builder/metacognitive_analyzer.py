"""Metacognitive analyzer for determining input types from user requirements.

This module analyzes user descriptions to determine whether they need directory-based,
file-based, or text-based input, and extracts patterns for batch processing.
"""

import re


class MetacognitiveAnalyzer:
    """Analyzes user requirements to determine input type needs."""

    def __init__(self):
        # Keywords indicating directory operations
        self.directory_indicators = {
            "directory",
            "dir",
            "folder",
            "path",
            "files",
            "all",
            "batch",
            "multiple",
            "collection",
            "set of",
            "every",
            "scan",
            "traverse",
            "recursive",
            "tree",
        }

        # Keywords indicating single file operations
        self.file_indicators = {
            "file",
            "document",
            "single",
            "one",
            "specific",
            "individual",
            "this",
            "that",
            "particular",
        }

        # Common file extensions for pattern matching
        self.common_extensions = {
            "md",
            "txt",
            "py",
            "js",
            "ts",
            "json",
            "yaml",
            "yml",
            "csv",
            "xml",
            "html",
            "css",
            "cpp",
            "c",
            "h",
            "java",
            "go",
            "rs",
            "sh",
            "sql",
            "log",
            "conf",
            "config",
        }

    def analyze_input_type(self, description: str) -> dict:
        """Analyze a description to determine the primary input type.

        Args:
            description: User's description of what they want to build

        Returns:
            Dictionary with analysis results:
                - primary_type: "directory", "file", or "text"
                - is_batch: Whether batch processing is needed
                - file_pattern: Extracted file pattern like "*.md"
                - count_limit: Extracted count limit if specified
                - confidence: Confidence score (0.0 to 1.0)
        """
        # Normalize description for analysis
        desc_lower = description.lower()

        # Extract patterns and limits
        file_pattern = self._extract_file_pattern(desc_lower)
        count_limit = self._extract_count_limit(desc_lower)

        # Count indicators
        dir_score = sum(1 for word in self.directory_indicators if word in desc_lower)
        file_score = sum(1 for word in self.file_indicators if word in desc_lower)

        # Determine if batch processing is needed
        is_batch = self._detect_batch_processing(desc_lower, file_pattern, count_limit)

        # Determine primary type based on evidence
        if dir_score > file_score or is_batch:
            primary_type = "directory"
            confidence = min(1.0, (dir_score + (2 if is_batch else 0)) / 5.0)
        elif file_score > dir_score:
            primary_type = "file"
            confidence = min(1.0, file_score / 3.0)
        else:
            # Default to text input if no clear indicators
            primary_type = "text"
            confidence = 0.5

        # Adjust confidence based on pattern presence
        if file_pattern:
            confidence = min(1.0, confidence + 0.2)
            if primary_type == "text":
                primary_type = "directory"  # Pattern implies directory scan

        return {
            "primary_type": primary_type,
            "is_batch": is_batch,
            "file_pattern": file_pattern,
            "count_limit": count_limit,
            "confidence": round(confidence, 2),
        }

    def _extract_file_pattern(self, text: str) -> str | None:
        """Extract file pattern from text.

        Args:
            text: Normalized text to analyze

        Returns:
            File pattern like "*.md" or None
        """
        # Look for explicit glob patterns
        glob_match = re.search(r"\*\.(\w+)", text)
        if glob_match:
            return f"*.{glob_match.group(1)}"

        # Look for file extension mentions
        for ext in self.common_extensions:
            # Check for various phrasings
            patterns = [
                rf"\.{ext}\b",  # .ext
                rf"{ext} files?\b",  # "md files"
                rf"files? with \.{ext}",  # "files with .md"
                rf"all \.{ext}",  # "all .py"
            ]
            for pattern in patterns:
                if re.search(pattern, text):
                    return f"*.{ext}"

        # Look for generic file type mentions
        type_patterns = {
            r"markdown files?": "*.md",
            r"python files?": "*.py",
            r"javascript files?": "*.js",
            r"typescript files?": "*.ts",
            r"text files?": "*.txt",
            r"config(?:uration)? files?": "*.conf",
            r"json files?": "*.json",
            r"yaml files?": "*.yaml",
        }

        for pattern, file_pattern in type_patterns.items():
            if re.search(pattern, text):
                return file_pattern

        return None

    def _extract_count_limit(self, text: str) -> int | None:
        """Extract count limit from text.

        Args:
            text: Normalized text to analyze

        Returns:
            Integer count limit or None
        """
        # Look for "first N files" or "N files" patterns
        patterns = [
            r"first (\d+) files?",
            r"(\d+) files? only",
            r"up to (\d+) files?",
            r"maximum (?:of )?(\d+)",
            r"limit(?:ed)? (?:to )?(\d+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))

        # Look for written numbers
        written_numbers = {
            "one": 1,
            "two": 2,
            "three": 3,
            "four": 4,
            "five": 5,
            "six": 6,
            "seven": 7,
            "eight": 8,
            "nine": 9,
            "ten": 10,
        }

        for word, value in written_numbers.items():
            if re.search(rf"first {word}\b", text):
                return value

        # Look for "first X" as a placeholder (default to 5)
        if re.search(r"first x\b", text):
            return 5  # Default value when X is used as placeholder

        return None

    def _detect_batch_processing(self, text: str, file_pattern: str | None, count_limit: int | None) -> bool:
        """Detect if batch processing is needed.

        Args:
            text: Normalized text
            file_pattern: Extracted file pattern
            count_limit: Extracted count limit

        Returns:
            True if batch processing is needed
        """
        # Pattern or count limit suggests batch
        if file_pattern or count_limit:
            return True

        # Look for batch processing keywords
        batch_keywords = [
            "for each",
            "foreach",
            "every",
            "all",
            "batch",
            "multiple",
            "collection",
            "series",
            "group",
            "process all",
            "scan",
            "iterate",
            "loop through",
        ]

        for keyword in batch_keywords:
            if keyword in text:
                return True

        # Check for plural forms suggesting multiple items
        return bool(re.search(r"\bfiles\b", text) and "file" not in self.file_indicators)
