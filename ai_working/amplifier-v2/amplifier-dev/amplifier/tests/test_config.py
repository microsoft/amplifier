"""
Tests for configuration management.
"""

import json
import tempfile
from pathlib import Path

import pytest
import yaml

from amplifier.config import (
    ConfigurationError,
    get_builtin_modes,
    get_default_config,
    list_available_modes,
    load_json,
    load_mode_manifest,
    load_yaml,
    parse_module_list,
    save_mode_manifest,
)


def test_get_builtin_modes():
    """Test that built-in modes are available."""
    modes = get_builtin_modes()
    assert "default" in modes
    assert "development" in modes
    assert "writing" in modes
    assert modes["default"]["name"] == "default"
    assert isinstance(modes["development"]["modules"], list)


def test_get_default_config():
    """Test default configuration."""
    config = get_default_config()
    assert "log_level" in config
    assert "config_dir" in config
    assert config["log_level"] == "INFO"


def test_parse_module_list_valid():
    """Test parsing valid module names."""
    modules = ["amplifier_mod_llm_openai", "amplifier.tools.test"]
    result = parse_module_list(modules)
    assert result == modules


def test_parse_module_list_invalid():
    """Test that invalid module names raise errors."""
    with pytest.raises(ConfigurationError):
        parse_module_list(["invalid-module-name"])

    with pytest.raises(ConfigurationError):
        parse_module_list(["123invalid"])

    with pytest.raises(ConfigurationError):
        parse_module_list([""])


def test_load_yaml():
    """Test YAML loading."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump({"test": "value", "number": 42}, f)
        temp_path = Path(f.name)

    try:
        data = load_yaml(temp_path)
        assert data["test"] == "value"
        assert data["number"] == 42
    finally:
        temp_path.unlink()


def test_load_json():
    """Test JSON loading."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"test": "value", "number": 42}, f)
        temp_path = Path(f.name)

    try:
        data = load_json(temp_path)
        assert data["test"] == "value"
        assert data["number"] == 42
    finally:
        temp_path.unlink()


def test_load_yaml_invalid():
    """Test that invalid YAML raises ConfigurationError."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("invalid: yaml: content: [[[")
        temp_path = Path(f.name)

    try:
        with pytest.raises(ConfigurationError):
            load_yaml(temp_path)
    finally:
        temp_path.unlink()


def test_save_and_load_mode_manifest():
    """Test saving and loading a mode manifest."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir)
        manifest = {
            "name": "test_mode",
            "description": "Test mode",
            "modules": ["test_module_1", "test_module_2"]
        }

        # Save the manifest
        save_mode_manifest("test_mode", manifest, config_dir)

        # Load it back
        loaded = load_mode_manifest("test_mode", config_dir)
        assert loaded["name"] == "test_mode"
        assert loaded["description"] == "Test mode"
        assert loaded["modules"] == ["test_module_1", "test_module_2"]


def test_list_available_modes():
    """Test listing available modes."""
    # Should at least include built-in modes
    modes = list_available_modes()
    assert "default" in modes
    assert "development" in modes
    assert "writing" in modes

    # Test with custom directory
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir)

        # Add a custom mode
        custom_manifest = {"name": "custom", "modules": []}
        save_mode_manifest("custom", custom_manifest, config_dir)

        # List should include the custom mode
        modes = list_available_modes(config_dir)
        assert "custom" in modes