"""Module generation microtask for Tool Builder.

This module generates actual code files for each architectural module,
creating working implementations that can be tested and refined.
"""

import asyncio
import json
from pathlib import Path
from typing import Any

from .exceptions import CCSDKRequiredError
from .exceptions import MicrotaskError


class ModuleGenerator:
    """Generates code modules using Claude Code SDK and templates."""

    def __init__(self):
        """Initialize the generator and verify CC SDK availability."""
        self._verify_sdk_available()

    def _verify_sdk_available(self):
        """Verify Claude Code SDK is available - fail fast if not."""
        import importlib.util

        if importlib.util.find_spec("claude_code_sdk") is None:
            raise CCSDKRequiredError()

    async def generate(
        self,
        tool_name: str,
        module_spec: dict[str, Any],
        requirements: dict[str, Any],
        output_dir: Path,
    ) -> dict[str, Any]:
        """Generate code for a single module.

        This microtask creates actual working code following our principles:
        - Complete, runnable implementations (no stubs)
        - Minimal but functional
        - Clear contracts/interfaces
        - Includes basic tests

        Args:
            tool_name: Name of the tool being built
            module_spec: Module specification from architecture
            requirements: Original requirements for context
            output_dir: Where to write generated files

        Returns:
            Generation result with file paths and status
        """
        try:
            from claude_code_sdk import ClaudeCodeOptions
            from claude_code_sdk import ClaudeSDKClient
        except ImportError:
            raise CCSDKRequiredError()

        # Try up to 3 times with error feedback
        max_attempts = 3
        last_error = ""

        for attempt in range(max_attempts):
            if attempt == 0:
                # First attempt - use normal prompt
                prompt = self._build_generation_prompt(tool_name, module_spec, requirements)
            else:
                # Retry attempt - include error feedback
                prompt = self._build_retry_prompt(tool_name, module_spec, requirements, last_error)
                print(f"Attempt {attempt + 1}/{max_attempts}: Retrying with error feedback...")

            response = ""

            try:
                # Code generation needs time to create complete implementations
                async with asyncio.timeout(300):  # 5 minutes max per module
                    async with ClaudeSDKClient(
                        options=ClaudeCodeOptions(
                            system_prompt=self._get_system_prompt(),
                            max_turns=1,
                        )
                    ) as client:
                        await client.query(prompt)

                        async for message in client.receive_response():
                            if hasattr(message, "content"):
                                content = getattr(message, "content", [])
                                if isinstance(content, list):
                                    for block in content:
                                        if hasattr(block, "text"):
                                            response += getattr(block, "text", "")

                # Try to parse and write the files
                result = await self._write_module_files(response, module_spec, output_dir)
                # Success! Return the result
                return result

            except TimeoutError:
                raise MicrotaskError(f"Module generation timed out for {module_spec.get('name', 'unknown')}")
            except MicrotaskError as e:
                # Save error for retry
                last_error = str(e)
                if attempt < max_attempts - 1:
                    # We'll retry
                    continue
                # Final attempt failed - fail loudly
                raise MicrotaskError(
                    f"Failed to generate valid module after {max_attempts} attempts.\n"
                    f"Last error: {last_error}\n"
                    f"NO FALLBACK - The tool generation has FAILED.\n"
                    f"The Claude Code SDK could not generate valid working code."
                )
            except Exception as e:
                raise MicrotaskError(f"Module generation failed: {str(e)}")

        # This should never be reached, but satisfies the linter
        raise MicrotaskError(
            f"Module generation failed after {max_attempts} attempts.\nNO FALLBACK - The tool generation has FAILED."
        )

    def _get_system_prompt(self) -> str:
        """Get the system prompt for module generation."""
        return """You are a code generator for the Amplifier Tool Builder.

Generate COMPLETE, WORKING Python code following these principles:

REQUIREMENTS:
- NO STUBS: Every function must have a working implementation
- NO TODOs: Complete the code now, not later
- NO NotImplementedError: If you can't implement it, simplify the scope
- MINIMAL BUT FUNCTIONAL: Start simple, but it must work

CODE STRUCTURE:
- Use Click for CLI interfaces
- Use async/await where beneficial (I/O operations)
- Include type hints for all functions
- Follow PEP 8 and project conventions
- Add docstrings for public functions

TESTING:
- Include at least one working test per public function
- Tests should actually validate behavior
- Use pytest for test framework

OUTPUT FORMAT:
Return JSON with file contents:
{
    "files": {
        "filename.py": "# Complete file contents\\n...",
        "test_filename.py": "# Test file contents\\n..."
    },
    "summary": "What was generated",
    "notes": "Any important implementation details"
}

CRITICAL: Return ONLY valid JSON, no conversational text before or after.
Do NOT include markdown formatting like ```json.
The ENTIRE response must be parseable JSON.

Example of CORRECT response (return exactly this format):
{
    "files": {
        "main.py": "import click\\n\\n@click.command()\\ndef process():\\n    click.echo('Processing...')\\n\\nif __name__ == '__main__':\\n    process()",
        "test_main.py": "import pytest\\nfrom click.testing import CliRunner\\nfrom main import process\\n\\ndef test_process():\\n    runner = CliRunner()\\n    result = runner.invoke(process)\\n    assert result.exit_code == 0"
    },
    "summary": "Generated main module with CLI interface",
    "notes": "Simple working implementation"
}

Remember: Return ONLY JSON. No text before or after the JSON object."""

    def _build_retry_prompt(
        self,
        tool_name: str,
        module_spec: dict[str, Any],
        requirements: dict[str, Any],
        error: str,
    ) -> str:
        """Build retry prompt with error feedback."""
        return f"""Your previous response had an error: {error}

Please try again with the following requirements:

{self._build_generation_prompt(tool_name, module_spec, requirements)}

CRITICAL: Return ONLY valid JSON. No explanations, no markdown, no text before or after the JSON object.
The response must start with {{ and end with }}"""

    def _build_generation_prompt(
        self,
        tool_name: str,
        module_spec: dict[str, Any],
        requirements: dict[str, Any],
    ) -> str:
        """Build the prompt for module generation."""
        from .exemplars import get_best_exemplar_for_requirements

        # Get best exemplar pattern for this tool's requirements
        pattern_type, exemplar_code = get_best_exemplar_for_requirements(requirements.get("core_functionality", ""))

        # Check if this tool requires AI integration
        needs_ai = self._needs_ai_integration(requirements)

        exemplar_section = ""
        if needs_ai:
            exemplar_section = f"""

EXEMPLAR PATTERN TO USE ({pattern_type}):
===== START EXEMPLAR =====
{exemplar_code}
===== END EXEMPLAR =====

IMPORTANT: Use the exemplar pattern above as a reference for implementing AI integration.
Adapt it to the specific requirements but maintain the Claude Code SDK usage pattern."""

        # Generate CLI-specific instructions based on cli_type
        cli_instructions = self._get_cli_instructions(requirements)

        return f"""Generate code for this Amplifier tool module:

Tool: {tool_name}
Module: {module_spec.get("name", "core")}

Module Specification:
- Purpose: {module_spec.get("purpose", "Core functionality")}
- Contract: {module_spec.get("contract", "Main interface")}
- Dependencies: {json.dumps(module_spec.get("dependencies", []))}
- Files to generate: {json.dumps(module_spec.get("files", ["main.py"]))}

Context from Requirements:
- Functionality: {requirements.get("core_functionality", "Process data")}
- Inputs: {json.dumps(requirements.get("inputs", []))}
- Outputs: {json.dumps(requirements.get("outputs", []))}
- CLI Type: {requirements.get("cli_type", "text_processor")}
{exemplar_section}
{cli_instructions}
IMPORTANT:
1. Generate COMPLETE, WORKING code - no stubs or placeholders
2. If AI integration is needed, USE Claude Code SDK following the exemplar pattern
3. If the full scope is too complex, simplify to something that works
4. Include at least one real test that validates the code works
5. Follow Amplifier patterns (Click CLI, async where useful)
6. Return ONLY JSON output, no conversational text

Generate the complete module implementation as valid JSON only."""

    async def _write_module_files(
        self,
        response: str,
        module_spec: dict[str, Any],
        output_dir: Path,
    ) -> dict[str, Any]:
        """Parse response and write module files."""
        # Clean response if wrapped in markdown
        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        cleaned = cleaned.strip()

        try:
            result = json.loads(cleaned)
            files_data = result.get("files", {})

            if not files_data:
                # No files in response - this is a generation failure
                raise MicrotaskError(
                    "Module generation returned no files. "
                    "The response was parsed as JSON but contained no 'files' field."
                )

            # Validate that the generated code is not just stubs
            self._validate_generated_code(files_data, module_spec)

            # Create module directory
            module_name = module_spec.get("name", "core")
            module_dir = output_dir / module_name
            module_dir.mkdir(parents=True, exist_ok=True)

            # Write each file
            written_files = []
            for filename, content in files_data.items():
                file_path = module_dir / filename
                file_path.write_text(content)
                written_files.append(str(file_path))

            return {
                "module": module_name,
                "files": written_files,
                "summary": result.get("summary", "Module generated"),
                "notes": result.get("notes", ""),
                "status": "success",
            }

        except json.JSONDecodeError as e:
            # JSON parsing failed - show what we got and fail loudly
            preview = cleaned[:500] if len(cleaned) > 500 else cleaned
            error_msg = (
                f"Failed to parse module generation response as JSON.\n"
                f"Error: {str(e)}\n"
                f"Response appears to contain conversational text instead of JSON.\n"
                f"First 500 chars of response: {preview}\n\n"
                f"This is a generation failure - the Claude Code SDK likely returned "
                f"conversational text instead of the requested JSON format."
            )
            raise MicrotaskError(error_msg)
        except Exception as e:
            # Other error - fail loudly
            raise MicrotaskError(f"Module generation failed: {str(e)}")

    def _get_cli_instructions(self, requirements: dict[str, Any]) -> str:
        """Generate CLI-specific instructions based on cli_type."""
        cli_type = requirements.get("cli_type", "text_processor")

        if cli_type == "directory_processor":
            file_pattern = requirements.get("file_pattern", "*.txt")
            file_limit = requirements.get("file_limit", 5)
            batch_processing = requirements.get("batch_processing", False)

            return f"""
CLI STRUCTURE (Directory Processor):
The main.py file should have this CLI structure:

```python
import click
from pathlib import Path

@click.command()
@click.argument('source_dir', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--output-dir', '-o', default='./output', help='Output directory for results')
@click.option('--max-files', '-m', default={file_limit}, type=int, help='Maximum number of files to process')
@click.option('--pattern', '-p', default='{file_pattern}', help='File pattern to match (glob)')
def run(source_dir: str, output_dir: str, max_files: int, pattern: str):
    '''Process files from source directory matching the pattern.'''
    source_path = Path(source_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Find matching files
    files = list(source_path.glob(pattern))[:max_files]

    # Process each file
    for file_path in files:
        # Process file logic here
        result = process_file(file_path)  # Implementation goes here
```

The tool should:
1. Accept a source directory as input
2. Find files matching the pattern (default: {file_pattern})
3. Process up to {file_limit} files (configurable via --max-files)
4. Save results to the output directory
{"5. Support batch processing of multiple files" if batch_processing else ""}
"""

        if cli_type == "file_processor":
            return """
CLI STRUCTURE (File Processor):
The main.py file should have this CLI structure:

```python
import click
from pathlib import Path

@click.command()
@click.argument('input_file', type=click.Path(exists=True, file_okay=True, dir_okay=False))
@click.option('--output', '-o', help='Output file path (optional)')
def run(input_file: str, output: str = None):
    '''Process a single input file.'''
    input_path = Path(input_file)

    # Read and process the file
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Process content logic here
    result = process_content(content)

    # Output handling
    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result)
    else:
        click.echo(result)
```

The tool should:
1. Accept a single file path as input
2. Process the file contents
3. Either save to an output file or print to stdout
"""

        # text_processor (default)
        return """
CLI STRUCTURE (Text Processor):
The main.py file should have this CLI structure:

```python
import click

@click.command()
@click.argument('text')
@click.option('--output', '-o', help='Output file path (optional)')
def run(text: str, output: str = None):
    '''Process text input directly.'''
    # Process text logic here
    result = process_text(text)

    # Output handling
    if output:
        from pathlib import Path
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result)
    else:
        click.echo(result)
```

The tool should:
1. Accept text as a command-line argument
2. Process the text
3. Either save to an output file or print to stdout
"""

    def _needs_ai_integration(self, requirements: dict[str, Any]) -> bool:
        """Determine if this tool requires AI integration."""
        functionality = requirements.get("core_functionality", "").lower()
        ai_keywords = [
            "ai",
            "claude",
            "llm",
            "language model",
            "gpt",
            "summarize",
            "synthesize",
            "analyze",
            "generate",
            "extract insights",
            "understand",
            "interpret",
            "natural language",
            "semantic",
            "expand",
        ]
        return any(keyword in functionality for keyword in ai_keywords)

    def _validate_generated_code(self, files_data: dict[str, str], module_spec: dict[str, Any]) -> None:
        """Validate that generated code is not just stubs."""
        # Check for stub patterns in main module files
        for filename, content in files_data.items():
            if "main.py" in filename or module_spec.get("name", "core") in filename:
                # Check for NotImplementedError stubs (validation check, not implementation)
                not_implemented_pattern = "raise " + "NotImplementedError"  # Split to avoid linter false positive
                if not_implemented_pattern in content:
                    raise MicrotaskError(
                        "Generated code contains NotImplementedError stubs. "
                        "The Tool Builder requires working implementations, not placeholders."
                    )

                # Check for TODO placeholders
                todo_pattern = "TO" + "DO"  # Split to avoid linter false positive
                if todo_pattern in content and "implement" in content.lower():
                    raise MicrotaskError(
                        "Generated code contains TODO placeholders. All functionality must be implemented."
                    )

                # Check for explicit stub markers
                if "pass  # stub" in content or "pass # stub" in content:
                    raise MicrotaskError(
                        "Generated code contains stub placeholders. The Tool Builder requires complete implementations."
                    )

                # Check for generic stub patterns
                if 'f"Processed: {input_data}"' in content or 'f"Processed {len(' in content:
                    raise MicrotaskError(
                        "Generated code appears to be a generic stub that just echoes input. "
                        "The Tool Builder requires actual functionality for the requested tool."
                    )
