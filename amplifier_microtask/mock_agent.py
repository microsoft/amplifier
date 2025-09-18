"""Mock agent for testing when Claude SDK is not available."""

import json
import asyncio


async def mock_execute_task(prompt: str, context: dict, timeout: int = 120) -> str:
    """Mock version of execute_task that returns reasonable responses."""

    # Simulate a small delay
    await asyncio.sleep(0.1)

    # Generate mock responses based on the prompt content
    if "requirements" in prompt.lower() or "analyze" in prompt.lower():
        return json.dumps(
            {
                "requirements": [
                    "Process markdown files in batches",
                    "Summarize documents using AI",
                    "Extract and synthesize ideas",
                    "Build comprehensive documentation for ideas",
                ],
                "priority": "high",
                "complexity": "medium",
            }
        )

    elif "design" in prompt.lower() or "architecture" in prompt.lower():
        return json.dumps(
            {
                "components": ["Document Reader", "AI Summarizer", "Idea Synthesizer", "Documentation Builder"],
                "architecture": "Pipeline pattern with incremental processing",
            }
        )

    elif "risk" in prompt.lower():
        return json.dumps(
            {
                "risks": ["AI response variability", "Large file processing timeout"],
                "mitigations": ["Add response validation", "Implement incremental saves"],
            }
        )

    elif "break_into_tasks" in prompt or "tasks" in prompt.lower():
        return json.dumps(
            {
                "tasks": [
                    "Read markdown files",
                    "Process with AI",
                    "Save summaries",
                    "Synthesize ideas",
                    "Document ideas",
                ]
            }
        )

    elif "test" in prompt.lower():
        return json.dumps(
            {
                "test_cli.py": "import pytest\n\ndef test_basic():\n    assert True",
                "test_processor.py": "import pytest\n\ndef test_processor():\n    assert True",
            }
        )

    # Default response
    return json.dumps({"status": "completed", "result": "Mock response for testing"})
