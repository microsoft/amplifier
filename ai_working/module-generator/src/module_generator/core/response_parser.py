"""Response parsing and classification for multi-turn interactions.

This module handles parsing and classifying responses from the Claude SDK
to determine the appropriate action (code generation, clarification, etc.).
"""

import re
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any
from typing import Literal


@dataclass
class ParsedCode:
    """Parsed code block from a response."""

    filepath: Path
    content: str
    language: str = "python"
    operation: Literal["create", "modify", "delete"] = "create"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedQuestion:
    """Parsed question or clarification request from a response."""

    question: str
    context: str = ""
    options: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedResponse:
    """Complete parsed response with all components."""

    response_type: Literal["code", "question", "mixed", "progress", "error"]
    raw_content: str
    code_blocks: list[ParsedCode] = field(default_factory=list)
    questions: list[ParsedQuestion] = field(default_factory=list)
    commentary: str = ""
    requires_clarification: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class ResponseParser:
    """Parses and classifies responses from Claude SDK."""

    # Patterns for detecting different response components
    CODE_BLOCK_PATTERN = re.compile(
        r"```(?P<language>\w+)?\n"
        r"(?:# (?P<filepath>[\w/.\-_]+))?\n?"
        r"(?P<content>.*?)\n```",
        re.DOTALL | re.MULTILINE,
    )

    FILE_MARKER_PATTERN = re.compile(
        r"(?:File|Creating|Modifying|Updating):\s*`?(?P<filepath>[\w/.\-_]+)`?", re.IGNORECASE
    )

    QUESTION_PATTERNS = [
        re.compile(r"(?:^|\n)\s*\??\s*(?P<question>[^.!]*\?)", re.MULTILINE),
        re.compile(
            r"(?:I need to know|Can you clarify|What (?:is|are)|How (?:should|would)|Which)\s+(?P<question>[^.?]*)[.?]",
            re.IGNORECASE,
        ),
        re.compile(r"(?:Please (?:specify|clarify|provide|confirm))\s+(?P<question>[^.?]*)[.?]", re.IGNORECASE),
    ]

    OPTION_PATTERN = re.compile(r"(?:^\s*[-*•]\s*|\d+[.)]\s*)(?P<option>.+)$", re.MULTILINE)

    def parse(self, response: str) -> ParsedResponse:
        """Parse a response from Claude SDK.

        Args:
            response: Raw response text

        Returns:
            Parsed response with classified components
        """
        # Extract code blocks
        code_blocks = self._extract_code_blocks(response)

        # Extract questions
        questions = self._extract_questions(response)

        # Extract commentary (non-code, non-question text)
        commentary = self._extract_commentary(response, code_blocks, questions)

        # Classify response type
        response_type = self._classify_response(code_blocks, questions, commentary)

        # Determine if clarification is needed
        requires_clarification = len(questions) > 0 and len(code_blocks) == 0

        return ParsedResponse(
            response_type=response_type,
            raw_content=response,
            code_blocks=code_blocks,
            questions=questions,
            commentary=commentary,
            requires_clarification=requires_clarification,
            metadata={"word_count": len(response.split()), "line_count": len(response.splitlines())},
        )

    def _extract_code_blocks(self, response: str) -> list[ParsedCode]:
        """Extract code blocks from response.

        Args:
            response: Raw response text

        Returns:
            List of parsed code blocks
        """
        code_blocks = []
        current_file = None

        # Check for file markers before code blocks
        for match in self.FILE_MARKER_PATTERN.finditer(response):
            current_file = Path(match.group("filepath"))

        # Extract code blocks
        for match in self.CODE_BLOCK_PATTERN.finditer(response):
            language = match.group("language") or "python"
            filepath = match.group("filepath")
            content = match.group("content").strip()

            if filepath:
                current_file = Path(filepath)
            elif not current_file:
                # Try to infer filename from content or use default
                current_file = self._infer_filepath(content, language)

            if current_file and content:
                code_blocks.append(
                    ParsedCode(
                        filepath=current_file,
                        content=content,
                        language=language,
                        operation=self._determine_operation(response, current_file),
                    )
                )
                current_file = None

        return code_blocks

    def _extract_questions(self, response: str) -> list[ParsedQuestion]:
        """Extract questions and clarification requests from response.

        Args:
            response: Raw response text

        Returns:
            List of parsed questions
        """
        questions = []
        seen_questions = set()

        # Remove code blocks to avoid false positives
        clean_response = self.CODE_BLOCK_PATTERN.sub("", response)

        for pattern in self.QUESTION_PATTERNS:
            for match in pattern.finditer(clean_response):
                question_text = match.group("question").strip()

                # Skip if already seen or too short
                if question_text in seen_questions or len(question_text) < 10:
                    continue

                seen_questions.add(question_text)

                # Extract context around the question
                start = max(0, match.start() - 100)
                end = min(len(clean_response), match.end() + 100)
                context = clean_response[start:end].strip()

                # Extract any options following the question
                options = self._extract_options(clean_response[match.end() : match.end() + 500])

                questions.append(ParsedQuestion(question=question_text, context=context, options=options))

        return questions

    def _extract_options(self, text: str) -> list[str]:
        """Extract option list following a question.

        Args:
            text: Text following a question

        Returns:
            List of options
        """
        options = []
        for match in self.OPTION_PATTERN.finditer(text):
            option = match.group("option").strip()
            if option and len(option) < 200:  # Reasonable option length
                options.append(option)
            if len(options) >= 10:  # Max 10 options
                break
        return options

    def _extract_commentary(self, response: str, code_blocks: list[ParsedCode], questions: list[ParsedQuestion]) -> str:
        """Extract commentary text (non-code, non-question).

        Args:
            response: Raw response text
            code_blocks: Extracted code blocks
            questions: Extracted questions

        Returns:
            Commentary text
        """
        commentary = response

        # Remove code blocks
        commentary = self.CODE_BLOCK_PATTERN.sub("", commentary)

        # Remove questions
        for question in questions:
            commentary = commentary.replace(question.question, "")

        # Clean up
        commentary = re.sub(r"\n{3,}", "\n\n", commentary)
        commentary = commentary.strip()

        return commentary

    def _classify_response(
        self, code_blocks: list[ParsedCode], questions: list[ParsedQuestion], commentary: str
    ) -> Literal["code", "question", "mixed", "progress", "error"]:
        """Classify the response type.

        Args:
            code_blocks: Extracted code blocks
            questions: Extracted questions
            commentary: Extracted commentary

        Returns:
            Response type classification
        """
        has_code = len(code_blocks) > 0
        has_questions = len(questions) > 0
        has_commentary = len(commentary) > 50  # Significant commentary

        if has_code and has_questions:
            return "mixed"
        if has_code:
            return "code"
        if has_questions:
            return "question"
        if has_commentary:
            return "progress"
        return "error"

    def _infer_filepath(self, content: str, language: str) -> Path:
        """Infer filepath from code content or language.

        Args:
            content: Code content
            language: Code language

        Returns:
            Inferred filepath
        """
        # Check for module/class definitions
        if language == "python":
            # Check for module docstring or class definition
            if match := re.search(r"(?:class|def)\s+(\w+)", content):
                name = match.group(1).lower()
                return Path(f"{name}.py")
            if "import" in content[:100]:
                return Path("__init__.py")

        # Default based on language
        extensions = {
            "python": ".py",
            "javascript": ".js",
            "typescript": ".ts",
            "yaml": ".yml",
            "json": ".json",
            "markdown": ".md",
            "shell": ".sh",
            "bash": ".sh",
        }

        ext = extensions.get(language, ".txt")
        return Path(f"generated{ext}")

    def _determine_operation(self, response: str, filepath: Path) -> Literal["create", "modify", "delete"]:
        """Determine the operation type for a code block.

        Args:
            response: Full response text
            filepath: File path

        Returns:
            Operation type
        """
        # Check for explicit operation keywords
        if any(word in response.lower() for word in ["creating", "create new", "generating"]):
            return "create"
        if any(word in response.lower() for word in ["modifying", "updating", "changing", "edit"]):
            return "modify"
        if any(word in response.lower() for word in ["deleting", "removing"]):
            return "delete"

        # Default to create for new files
        return "create"

    def extract_final_answer(self, response: str) -> str | None:
        """Extract a final answer from a clarification response.

        Args:
            response: Response containing an answer

        Returns:
            Extracted answer or None
        """
        # Look for explicit answer patterns
        patterns = [
            re.compile(r"(?:Answer|Response|Decision):\s*(.+?)(?:\n|$)", re.IGNORECASE),
            re.compile(r"(?:I (?:choose|select|prefer)|Let\'s go with):\s*(.+?)(?:\n|$)", re.IGNORECASE),
            re.compile(r"(?:^|\n)[-*]\s*\[x\]\s*(.+?)(?:\n|$)", re.MULTILINE),  # Checked option
        ]

        for pattern in patterns:
            if match := pattern.search(response):
                return match.group(1).strip()

        # If response is short and direct, might be the answer itself
        if len(response) < 200 and not any(c in response for c in "?"):
            return response.strip()

        return None
