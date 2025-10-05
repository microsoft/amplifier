#!/usr/bin/env python3
"""
Setup script to create built-in demo modes for Amplifier.
Run this after installing amplifier to get started quickly.
"""

import json
import sys
from pathlib import Path

# Built-in mode configurations
BUILT_IN_MODES = {
    "default": {
        "name": "default",
        "description": "Default mode with no modules loaded - add modules as needed",
        "modules": []
    },
    "development": {
        "name": "development",
        "description": "Development mode with Claude, UltraThink, Philosophy, and Agent Registry",
        "modules": [
            "amplifier_mod_llm_claude",
            "amplifier_mod_tool_ultra_think",
            "amplifier_mod_philosophy",
            "amplifier_mod_agent_registry"
        ]
    },
    "research": {
        "name": "research",
        "description": "Research mode with OpenAI, UltraThink, and Blog Generator",
        "modules": [
            "amplifier_mod_llm_openai",
            "amplifier_mod_tool_ultra_think",
            "amplifier_mod_tool_blog_generator"
        ]
    },
    "creative": {
        "name": "creative",
        "description": "Creative writing mode with Claude, Blog Generator, and Philosophy",
        "modules": [
            "amplifier_mod_llm_claude",
            "amplifier_mod_tool_blog_generator",
            "amplifier_mod_philosophy"
        ]
    },
    "demo": {
        "name": "demo",
        "description": "Demo mode with OpenAI and all tools to showcase capabilities",
        "modules": [
            "amplifier_mod_llm_openai",
            "amplifier_mod_tool_ultra_think",
            "amplifier_mod_tool_blog_generator",
            "amplifier_mod_philosophy",
            "amplifier_mod_agent_registry"
        ]
    }
}


def setup_demo_modes():
    """Create built-in demo modes in the config directory."""
    # Get the modes directory
    modes_dir = Path.home() / ".amplifier" / "modes"

    # Create directory if it doesn't exist
    modes_dir.mkdir(parents=True, exist_ok=True)

    print("🚀 Setting up Amplifier demo modes...")
    print(f"📁 Modes directory: {modes_dir}")
    print()

    # Create each mode
    created = []
    updated = []

    for mode_name, manifest in BUILT_IN_MODES.items():
        mode_file = modes_dir / f"{mode_name}.json"

        if mode_file.exists():
            updated.append(mode_name)
        else:
            created.append(mode_name)

        # Write the manifest
        with open(mode_file, 'w') as f:
            json.dump(manifest, f, indent=2)

    # Report results
    if created:
        print(f"✅ Created {len(created)} new modes: {', '.join(created)}")

    if updated:
        print(f"🔄 Updated {len(updated)} existing modes: {', '.join(updated)}")

    print()
    print("📚 Available modes:")
    for mode_name, manifest in BUILT_IN_MODES.items():
        print(f"  • {mode_name}: {manifest['description']}")

    print()
    print("🎯 Quick start examples:")
    print()
    print("  # List all available modes")
    print("  amplifier list-modes")
    print()
    print("  # Run in demo mode (requires OpenAI API key)")
    print("  export OPENAI_API_KEY='your-key-here'")
    print("  amplifier run demo")
    print()
    print("  # Run in interactive mode with development configuration")
    print("  amplifier interactive --mode development")
    print()
    print("  # Create your own custom mode")
    print("  amplifier init --name mymode --modules amplifier_mod_llm_openai,amplifier_mod_tool_ultra_think")
    print()
    print("💡 Tip: Set your API keys as environment variables:")
    print("  export OPENAI_API_KEY='your-openai-key'")
    print("  export ANTHROPIC_API_KEY='your-claude-key'")
    print()


if __name__ == "__main__":
    try:
        setup_demo_modes()
        print("✨ Demo setup complete! Try 'amplifier list-modes' to see available modes.")
    except Exception as e:
        print(f"❌ Error setting up demo modes: {e}", file=sys.stderr)
        sys.exit(1)