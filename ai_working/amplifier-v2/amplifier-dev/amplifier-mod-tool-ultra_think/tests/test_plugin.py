"""
Tests for the UltraThink Plugin

Tests plugin registration and lifecycle management.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from amplifier_mod_tool_ultra_think.plugin import Plugin
from amplifier_mod_tool_ultra_think.ultra_think import UltraThinkTool


@pytest.fixture
def mock_kernel():
    """Create a mock Amplifier kernel."""
    kernel = Mock()
    kernel.add_tool = AsyncMock()
    kernel.remove_tool = AsyncMock()
    kernel.tools = {}
    kernel.model_providers = {"openai": Mock()}
    kernel.logger = Mock()
    return kernel


@pytest.mark.asyncio
async def test_plugin_attributes():
    """Test plugin has correct attributes."""
    plugin = Plugin()

    assert plugin.name == "ultra_think_tool"
    assert plugin.version == "0.1.0"
    assert "reasoning workflow" in plugin.description.lower()


@pytest.mark.asyncio
async def test_plugin_register(mock_kernel):
    """Test plugin registration adds tool to kernel."""
    plugin = Plugin()

    # Register the plugin
    await plugin.register(mock_kernel)

    # Verify add_tool was called
    mock_kernel.add_tool.assert_called_once()

    # Verify the tool passed is an UltraThinkTool
    call_args = mock_kernel.add_tool.call_args
    tool = call_args[0][0]
    assert isinstance(tool, UltraThinkTool)
    assert tool.name == "ultra_think"

    # Verify logging
    mock_kernel.logger.info.assert_called_with(
        "UltraThink tool registered successfully as 'ultra_think'"
    )


@pytest.mark.asyncio
async def test_plugin_unregister(mock_kernel):
    """Test plugin unregistration removes tool from kernel."""
    plugin = Plugin()

    # Simulate tool being in registry
    mock_kernel.tools = {"ultra_think": Mock()}

    # Unregister the plugin
    await plugin.unregister(mock_kernel)

    # Verify remove_tool was called
    mock_kernel.remove_tool.assert_called_once_with("ultra_think")

    # Verify logging
    mock_kernel.logger.info.assert_called_with(
        "UltraThink tool unregistered successfully"
    )


@pytest.mark.asyncio
async def test_plugin_unregister_not_registered(mock_kernel):
    """Test unregistering when tool is not registered."""
    plugin = Plugin()

    # Tool not in registry
    mock_kernel.tools = {}

    # Unregister should not fail
    await plugin.unregister(mock_kernel)

    # remove_tool should not be called
    mock_kernel.remove_tool.assert_not_called()


@pytest.mark.asyncio
async def test_plugin_health_check_success():
    """Test health check returns True when healthy."""
    plugin = Plugin()

    # Health check should pass
    is_healthy = await plugin.health_check()
    assert is_healthy is True


@pytest.mark.asyncio
async def test_plugin_health_check_import_available():
    """Test health check verifies import availability."""
    plugin = Plugin()

    # Mock the import to simulate it working
    import sys
    import amplifier_mod_tool_ultra_think.ultra_think

    # Temporarily ensure module is in sys.modules
    original_module = sys.modules.get("amplifier_mod_tool_ultra_think.ultra_think")

    try:
        # Health check should pass
        is_healthy = await plugin.health_check()
        assert is_healthy is True
    finally:
        # Restore original state
        if original_module:
            sys.modules["amplifier_mod_tool_ultra_think.ultra_think"] = original_module


@pytest.mark.asyncio
async def test_plugin_lifecycle(mock_kernel):
    """Test complete plugin lifecycle: register -> use -> unregister."""
    plugin = Plugin()

    # Register
    await plugin.register(mock_kernel)
    assert mock_kernel.add_tool.called

    # Simulate tool in registry
    mock_kernel.tools = {"ultra_think": Mock()}

    # Health check
    is_healthy = await plugin.health_check()
    assert is_healthy is True

    # Unregister
    await plugin.unregister(mock_kernel)
    assert mock_kernel.remove_tool.called