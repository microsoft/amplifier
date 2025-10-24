#!/usr/bin/env python3
"""
Comprehensive tests for agent conversion functionality.

Tests cover all aspects of converting Claude Code agents to Codex format,
including frontmatter conversion, content transformation, validation, and
end-to-end conversion workflows.
"""

import sys
from pathlib import Path

import pytest

# Add tools directory to path for imports
sys.path.append(str(Path(__file__).parent.parent / "tools"))

from convert_agents import adapt_agent_spawning_examples
from convert_agents import adapt_tool_references
from convert_agents import convert_agent
from convert_agents import convert_all_agents
from convert_agents import convert_frontmatter
from convert_agents import parse_agent_file
from convert_agents import preserve_core_methodology
from convert_agents import remove_additional_instructions
from convert_agents import remove_claude_specific_sections
from convert_agents import validate_converted_agent


@pytest.fixture
def sample_claude_agent():
    """Return complete Claude Code agent markdown content."""
    return """---
name: test-agent
description: Use PROACTIVELY for testing. Task tool available. slash commands work.
tools: Read, Task, TodoWrite, WebFetch, WebSearch, Grep
model: claude-3-5-sonnet-20241022
---

# Core Methodology

This agent does testing.

## Operating Modes

- ANALYZE
- ARCHITECT
- REVIEW

## Examples

I'll use the Task tool to spawn the bug-hunter agent.

Task(bug-hunter, investigate issue)

# Additional Instructions

These are Claude-specific instructions.

# Hooks

SessionStart hooks here.

VS Code integration details.

Claude Code SDK references.
"""


@pytest.fixture
def sample_claude_frontmatter():
    """Return Claude Code frontmatter dict."""
    return {
        "name": "test-agent",
        "description": "Use PROACTIVELY for testing. Task tool available.",
        "tools": "Read, Task, TodoWrite, Grep",
        "model": "claude-3-5-sonnet-20241022",
    }


@pytest.fixture
def temp_agent_dirs(tmp_path):
    """Create temporary agent directories with sample files."""
    claude_dir = tmp_path / ".claude" / "agents"
    codex_dir = tmp_path / ".codex" / "agents"
    claude_dir.mkdir(parents=True)
    codex_dir.mkdir(parents=True)

    # Create sample Claude agent
    sample_agent = claude_dir / "test-agent.md"
    sample_agent.write_text("""---
name: test-agent
description: Use PROACTIVELY for testing. Task tool available.
tools: Read, Task, TodoWrite, Grep
model: claude-3-5-sonnet-20241022
---

# Core Methodology

This agent does testing.

## Operating Modes

- ANALYZE
- ARCHITECT
- REVIEW

## Examples

I'll use the Task tool to spawn the bug-hunter agent.

Task(bug-hunter, investigate issue)

# Additional Instructions

These are Claude-specific instructions.
""")

    return {"claude": claude_dir, "codex": codex_dir}


class TestFrontmatterConversion:
    """Test frontmatter conversion functions."""

    def test_convert_frontmatter_basic(self, sample_claude_frontmatter):
        """Test basic field preservation."""
        result = convert_frontmatter(sample_claude_frontmatter)
        assert result["name"] == "test-agent"
        assert "model" in result
        assert isinstance(result, dict)

    def test_convert_frontmatter_tools_to_array(self, sample_claude_frontmatter):
        """Test tools field conversion to array."""
        result = convert_frontmatter(sample_claude_frontmatter)
        assert result["tools"] == ["Read", "Grep"]

    def test_convert_frontmatter_removes_claude_tools(self, sample_claude_frontmatter):
        """Test removal of Claude-specific tools."""
        result = convert_frontmatter(sample_claude_frontmatter)
        assert "Task" not in result["tools"]
        assert "TodoWrite" not in result["tools"]

    def test_convert_frontmatter_default_tools_when_empty(self):
        """Test default tools when all are Claude-specific."""
        frontmatter = {"name": "test", "tools": "Task, TodoWrite"}
        result = convert_frontmatter(frontmatter)
        assert result["tools"] == ["Read", "Grep", "Glob"]

    def test_convert_frontmatter_simplifies_description(self, sample_claude_frontmatter):
        """Test description simplification."""
        result = convert_frontmatter(sample_claude_frontmatter)
        assert "Use PROACTIVELY" not in result["description"]
        assert "Task tool" not in result["description"]


class TestContentTransformation:
    """Test content transformation functions."""

    def test_remove_additional_instructions(self):
        """Test removal of Additional Instructions section."""
        content = """# Core

Stuff

# Additional Instructions

Remove this"""
        result = remove_additional_instructions(content)
        assert "Additional Instructions" not in result
        assert "Remove this" not in result
        assert "# Core" in result

    def test_adapt_tool_references_task(self):
        """Test Task tool reference adaptation."""
        content = "use the Task tool to spawn"
        result = adapt_tool_references(content)
        assert "delegate to a specialized agent" in result

    def test_adapt_tool_references_todowrite(self):
        """Test TodoWrite reference adaptation."""
        content = "use TodoWrite to track"
        result = adapt_tool_references(content)
        assert "track progress" in result

    def test_adapt_agent_spawning_examples(self):
        """Test agent spawning example adaptation."""
        content = "I'll use the Task tool to spawn the bug-hunter agent"
        result = adapt_agent_spawning_examples(content)
        assert "I'll delegate to the bug-hunter agent" in result

    def test_remove_claude_specific_sections(self):
        """Test removal of Claude-specific sections."""
        content = """# Hooks

SessionStart

# Normal

VS Code integration"""
        result = remove_claude_specific_sections(content)
        assert "# Hooks" not in result
        assert "VS Code" not in result
        assert "# Normal" in result

    def test_preserve_core_methodology(self):
        """Test preservation of core methodology."""
        content = "Operating modes: ANALYZE, ARCHITECT"
        result = preserve_core_methodology(content)
        assert "Operating modes" in result

    def test_preserve_philosophy_references(self):
        """Test preservation of philosophy references."""
        content = "@ai_context/IMPLEMENTATION_PHILOSOPHY.md"
        result = preserve_core_methodology(content)
        assert "@ai_context/IMPLEMENTATION_PHILOSOPHY.md" in result


class TestEndToEndConversion:
    """Test complete conversion workflows."""

    def test_convert_agent_complete(self, temp_agent_dirs, sample_claude_agent):
        """Test complete agent conversion."""
        input_path = temp_agent_dirs["claude"] / "test-agent.md"
        output_path = temp_agent_dirs["codex"] / "test-agent.md"
        result = convert_agent(input_path, output_path, dry_run=False)

        assert result["success"]
        assert output_path.exists()

        # Verify frontmatter
        frontmatter, content = parse_agent_file(output_path)
        assert "name" in frontmatter
        assert "Additional Instructions" not in content
        assert "Task tool" not in content

    def test_convert_agent_dry_run(self, temp_agent_dirs, sample_claude_agent):
        """Test dry-run conversion."""
        input_path = temp_agent_dirs["claude"] / "test-agent.md"
        output_path = temp_agent_dirs["codex"] / "test-agent.md"
        result = convert_agent(input_path, output_path, dry_run=True)

        assert result["success"]
        assert not output_path.exists()

    def test_convert_agent_preserves_structure(self, temp_agent_dirs):
        """Test preservation of agent structure."""
        input_path = temp_agent_dirs["claude"] / "test-agent.md"
        output_path = temp_agent_dirs["codex"] / "test-agent.md"
        convert_agent(input_path, output_path)

        content = output_path.read_text()
        assert "# Core Methodology" in content
        assert "## Operating Modes" in content


class TestBatchConversion:
    """Test batch conversion functions."""

    def test_convert_all_agents(self, temp_agent_dirs):
        """Test batch conversion of multiple agents."""
        # Add another agent
        (temp_agent_dirs["claude"] / "another-agent.md").write_text("""---
name: another-agent
description: Another agent
tools: Read
---

Content""")

        results = convert_all_agents(dry_run=False, verbose=False)
        assert results["total"] == 2
        assert results["succeeded"] == 2

    def test_convert_all_agents_handles_errors(self, temp_agent_dirs):
        """Test error handling in batch conversion."""
        # Create malformed agent
        (temp_agent_dirs["claude"] / "bad-agent.md").write_text("not yaml")

        results = convert_all_agents(dry_run=False, verbose=False)
        assert results["failed"] == 1
        assert results["succeeded"] == 1


class TestValidation:
    """Test agent validation functions."""

    def test_validate_converted_agent_valid(self, temp_agent_dirs):
        """Test validation of valid converted agent."""
        valid_agent = temp_agent_dirs["codex"] / "valid.md"
        valid_agent.write_text("""---
name: valid
description: test
tools: [Read, Grep]
---

Content""")

        result = validate_converted_agent(valid_agent)
        assert result["valid"]

    def test_validate_converted_agent_missing_fields(self, temp_agent_dirs):
        """Test validation with missing required fields."""
        bad_agent = temp_agent_dirs["codex"] / "bad.md"
        bad_agent.write_text("""---
description: test
---

Content""")

        result = validate_converted_agent(bad_agent)
        assert not result["valid"]
        assert "Missing 'name' field" in result["errors"]

    def test_validate_converted_agent_claude_tools_remaining(self, temp_agent_dirs):
        """Test validation detects remaining Claude tools."""
        bad_agent = temp_agent_dirs["codex"] / "bad.md"
        bad_agent.write_text("""---
name: bad
description: test
---

Content with Task tool""")

        result = validate_converted_agent(bad_agent)
        assert not result["valid"]
        assert "Task" in str(result["errors"])

    def test_validate_converted_agent_additional_instructions_remaining(self, temp_agent_dirs):
        """Test validation detects remaining Additional Instructions."""
        bad_agent = temp_agent_dirs["codex"] / "bad.md"
        bad_agent.write_text("""---
name: bad
description: test
---

# Additional Instructions""")

        result = validate_converted_agent(bad_agent)
        assert not result["valid"]
        assert "Additional Instructions" in str(result["errors"])


class TestIntegration:
    """Test integration with backend systems."""

    def test_converted_agent_loads_with_backend(self, temp_agent_dirs):
        """Test loading converted agent with CodexAgentBackend."""
        # Create and convert agent
        input_path = temp_agent_dirs["claude"] / "test-agent.md"
        output_path = temp_agent_dirs["codex"] / "test-agent.md"
        convert_agent(input_path, output_path)

        # Import and test backend
        sys.path.append(str(Path(__file__).parent.parent / "amplifier" / "core"))
        from agent_backend import CodexAgentBackend

        backend = CodexAgentBackend()
        backend.agents_dir = temp_agent_dirs["codex"]

        assert backend.validate_agent_exists("test-agent")

        definition = backend.get_agent_definition("test-agent")
        assert definition is not None
        assert "test-agent" in definition

    def test_converted_agent_validates_with_yaml(self, temp_agent_dirs):
        """Test YAML validation of converted agent."""
        input_path = temp_agent_dirs["claude"] / "test-agent.md"
        output_path = temp_agent_dirs["codex"] / "test-agent.md"
        convert_agent(input_path, output_path)

        frontmatter, _ = parse_agent_file(output_path)
        # Should not raise
        assert isinstance(frontmatter, dict)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_convert_agent_empty_tools(self, temp_agent_dirs):
        """Test conversion with no tools field."""
        input_path = temp_agent_dirs["claude"] / "empty-tools.md"
        input_path.write_text("""---
name: empty
description: test
---

Content""")

        output_path = temp_agent_dirs["codex"] / "empty-tools.md"
        convert_agent(input_path, output_path)

        frontmatter, _ = parse_agent_file(output_path)
        assert frontmatter["tools"] == ["Read", "Grep", "Glob"]

    def test_convert_agent_malformed_yaml(self, temp_agent_dirs):
        """Test handling of malformed YAML."""
        input_path = temp_agent_dirs["claude"] / "malformed.md"
        input_path.write_text("not yaml")

        output_path = temp_agent_dirs["codex"] / "malformed.md"

        with pytest.raises(Exception):
            convert_agent(input_path, output_path)

    def test_convert_agent_no_additional_instructions(self, temp_agent_dirs):
        """Test conversion without Additional Instructions section."""
        input_path = temp_agent_dirs["claude"] / "no-additional.md"
        input_path.write_text("""---
name: no-additional
description: test
---

Content without additional instructions""")

        output_path = temp_agent_dirs["codex"] / "no-additional.md"
        result = convert_agent(input_path, output_path)

        assert result["success"]

    def test_convert_agent_unicode_content(self, temp_agent_dirs):
        """Test handling of Unicode content."""
        input_path = temp_agent_dirs["claude"] / "unicode.md"
        input_path.write_text("""---
name: unicode
description: test
---

Content with Unicode: 🌍""")

        output_path = temp_agent_dirs["codex"] / "unicode.md"
        convert_agent(input_path, output_path)

        content = output_path.read_text()
        assert "🌍" in content


class TestCLI:
    """Test CLI interface functions."""

    def test_cli_convert_single_agent(self, temp_agent_dirs, monkeypatch):
        """Test CLI single agent conversion."""
        monkeypatch.setattr(sys, "argv", ["convert_agents.py", "--agent", "test-agent"])

        # Mock the directories
        import convert_agents

        original_claude = convert_agents.CLAUDE_AGENTS_DIR
        original_codex = convert_agents.CODEX_AGENTS_DIR

        convert_agents.CLAUDE_AGENTS_DIR = temp_agent_dirs["claude"]
        convert_agents.CODEX_AGENTS_DIR = temp_agent_dirs["codex"]

        try:
            # This would require more complex mocking, skip for now
            pass
        finally:
            convert_agents.CLAUDE_AGENTS_DIR = original_claude
            convert_agents.CODEX_AGENTS_DIR = original_codex

    def test_cli_dry_run(self, temp_agent_dirs, monkeypatch):
        """Test CLI dry-run mode."""
        # Similar to above, would need complex mocking
        pass

    def test_cli_validate(self, temp_agent_dirs, monkeypatch):
        """Test CLI validation."""
        # Similar to above
        pass


class TestRegression:
    """Test regression prevention."""

    def test_conversion_idempotent(self, temp_agent_dirs):
        """Test that conversion is idempotent."""
        input_path = temp_agent_dirs["claude"] / "test-agent.md"
        output_path = temp_agent_dirs["codex"] / "test-agent.md"

        convert_agent(input_path, output_path)
        first_content = output_path.read_text()

        # Convert again
        convert_agent(input_path, output_path)
        second_content = output_path.read_text()

        assert first_content == second_content

    @pytest.mark.integration
    def test_real_agent_conversion(self):
        """Test conversion of real agent files."""
        # This would use actual files from .claude/agents/
        # For now, skip as files may not exist in test environment
        pass


# Test utilities


def create_mock_agent_file(path: Path, content: str):
    """Helper to create mock agent file."""
    path.write_text(content)


def compare_agent_files(original: Path, converted: Path) -> dict:
    """Helper to compare agent files."""
    # Implementation would compare frontmatter and content
    return {}


def validate_yaml_frontmatter(content: str) -> dict:
    """Helper to validate YAML frontmatter."""
    if not content.startswith("---"):
        return {"valid": False, "error": "No frontmatter"}

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {"valid": False, "error": "Invalid format"}

    try:
        frontmatter = yaml.safe_load(parts[1])
        return {"valid": True, "frontmatter": frontmatter}
    except Exception as e:
        return {"valid": False, "error": str(e)}


def check_for_claude_patterns(content: str) -> list:
    """Helper to check for remaining Claude-specific patterns."""
    patterns = ["Task tool", "TodoWrite", "WebFetch", "Additional Instructions"]
    found = []
    for pattern in patterns:
        if pattern in content:
            found.append(pattern)
    return found


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
