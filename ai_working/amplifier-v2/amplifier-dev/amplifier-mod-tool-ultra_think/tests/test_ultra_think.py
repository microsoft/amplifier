"""
Tests for the UltraThink Tool Module

Tests the multi-step reasoning workflow functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from amplifier_mod_tool_ultra_think.ultra_think import UltraThinkTool


@pytest.fixture
def mock_kernel():
    """Create a mock kernel with model providers."""
    kernel = Mock()

    # Create a mock model provider
    mock_model = Mock()
    mock_model.generate = AsyncMock()

    # Set up model providers
    kernel.model_providers = {"openai": mock_model}
    kernel.tools = {}
    kernel.logger = Mock()

    return kernel


@pytest.fixture
def mock_model_responses():
    """Predefined model responses for testing."""
    return [
        "From a philosophical perspective, this represents a fundamental shift in human cognition.",
        "Practically speaking, implementation requires careful consideration of resources.",
        "Critical analysis reveals potential risks that must be addressed.",
        "Creative solutions involve thinking beyond traditional boundaries.",
        "Systems thinking shows interconnected impacts across multiple domains."
    ]


@pytest.mark.asyncio
async def test_ultra_think_initialization(mock_kernel):
    """Test that UltraThinkTool initializes correctly."""
    tool = UltraThinkTool(mock_kernel)

    assert tool.name == "ultra_think"
    assert tool.kernel == mock_kernel
    assert tool.description == "Perform deep multi-perspective analysis on any topic"


@pytest.mark.asyncio
async def test_ultra_think_run_default_perspectives(mock_kernel, mock_model_responses):
    """Test running ultra-think with default perspectives."""
    tool = UltraThinkTool(mock_kernel)

    # Set up mock responses
    mock_model = mock_kernel.model_providers["openai"]

    # First 5 calls return perspective responses, last call returns synthesis
    responses = mock_model_responses + ["This is a synthesized analysis of all perspectives."]
    mock_model.generate.side_effect = responses

    # Run the tool
    result = await tool.run("test topic")

    # Verify the result contains the synthesis
    assert "Ultra-Think Analysis: test topic" in result
    assert "synthesized analysis" in result

    # Verify correct number of model calls (5 perspectives + 1 synthesis)
    assert mock_model.generate.call_count == 6


@pytest.mark.asyncio
async def test_ultra_think_run_custom_perspectives(mock_kernel):
    """Test running ultra-think with custom perspectives."""
    tool = UltraThinkTool(mock_kernel)

    # Set up mock responses
    mock_model = mock_kernel.model_providers["openai"]
    custom_perspectives = ["Technical feasibility", "User experience"]

    # Mock responses for custom perspectives + synthesis
    mock_model.generate.side_effect = [
        "Technical analysis result",
        "UX analysis result",
        "Synthesized custom perspectives"
    ]

    # Run with custom perspectives
    result = await tool.run("test topic", perspectives=custom_perspectives)

    # Verify the result
    assert "Ultra-Think Analysis: test topic" in result
    assert "Synthesized custom perspectives" in result

    # Verify correct number of calls
    assert mock_model.generate.call_count == 3  # 2 perspectives + 1 synthesis


@pytest.mark.asyncio
async def test_ultra_think_execute_method(mock_kernel):
    """Test the execute method interface."""
    tool = UltraThinkTool(mock_kernel)

    # Set up mock
    mock_model = mock_kernel.model_providers["openai"]
    mock_model.generate.side_effect = [
        "Perspective 1",
        "Perspective 2",
        "Perspective 3",
        "Perspective 4",
        "Perspective 5",
        "Final synthesis"
    ]

    # Execute via the interface method
    result = await tool.execute(topic="AI ethics")

    # Check result structure
    assert result["success"] is True
    assert result["topic"] == "AI ethics"
    assert result["perspectives_used"] == 5
    assert "Ultra-Think Analysis" in result["result"]


@pytest.mark.asyncio
async def test_ultra_think_execute_missing_topic(mock_kernel):
    """Test execute method with missing topic."""
    tool = UltraThinkTool(mock_kernel)

    # Execute without topic
    result = await tool.execute()

    # Should return error
    assert result["success"] is False
    assert "Topic is required" in result["error"]


@pytest.mark.asyncio
async def test_ultra_think_parallel_execution(mock_kernel):
    """Test that perspectives are executed in parallel."""
    tool = UltraThinkTool(mock_kernel)

    # Create a mock that tracks timing
    call_times = []

    async def mock_generate(prompt):
        call_times.append(asyncio.get_event_loop().time())
        await asyncio.sleep(0.1)  # Simulate API delay
        return f"Response for: {prompt[:20]}"

    mock_model = mock_kernel.model_providers["openai"]
    mock_model.generate = mock_generate

    # Run the tool
    start_time = asyncio.get_event_loop().time()
    await tool.run("test parallel execution")

    # If executed in parallel, should take ~0.1s for perspectives + 0.1s for synthesis
    # If sequential, would take 0.6s+
    # Check that the first 5 calls happened close together (parallel)
    perspective_times = call_times[:5]
    time_spread = max(perspective_times) - min(perspective_times)

    # Time spread should be minimal if parallel (< 0.05s)
    assert time_spread < 0.05, f"Perspectives not executed in parallel (spread: {time_spread}s)"


@pytest.mark.asyncio
async def test_ultra_think_error_handling(mock_kernel):
    """Test error handling when some perspectives fail."""
    tool = UltraThinkTool(mock_kernel)

    # Set up mock with some failures
    mock_model = mock_kernel.model_providers["openai"]
    mock_model.generate.side_effect = [
        "Success 1",
        Exception("API Error"),
        "Success 2",
        Exception("Rate limit"),
        "Success 3",
        "Synthesis of successful perspectives"
    ]

    # Run should continue despite failures
    result = await tool.run("test with errors")

    # Should get a result with successful perspectives
    assert "Ultra-Think Analysis" in result
    assert "Synthesis of successful perspectives" in result


@pytest.mark.asyncio
async def test_ultra_think_all_perspectives_fail(mock_kernel):
    """Test handling when all perspectives fail."""
    tool = UltraThinkTool(mock_kernel)

    # Set up mock with all failures
    mock_model = mock_kernel.model_providers["openai"]
    mock_model.generate.side_effect = [
        Exception("Error 1"),
        Exception("Error 2"),
        Exception("Error 3"),
        Exception("Error 4"),
        Exception("Error 5")
    ]

    # Run should return error message
    result = await tool.run("test all failures")

    assert "Unable to generate any perspectives" in result


@pytest.mark.asyncio
async def test_ultra_think_synthesis_failure(mock_kernel, mock_model_responses):
    """Test fallback when synthesis fails but perspectives succeed."""
    tool = UltraThinkTool(mock_kernel)

    # Set up mock - perspectives succeed, synthesis fails
    mock_model = mock_kernel.model_providers["openai"]
    responses = mock_model_responses + [Exception("Synthesis failed")]

    async def mock_generate(prompt):
        response = responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    mock_model.generate = mock_generate

    # Run the tool
    result = await tool.run("test synthesis failure")

    # Should fallback to raw perspectives
    assert "Ultra-Think Analysis" in result
    assert "PERSPECTIVE" in result  # Raw perspectives included
    assert "philosophical perspective" in result