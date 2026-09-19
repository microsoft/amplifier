#!/usr/bin/env python3
"""Focused checks for public behavior-first and Anchors guidance.

Run: python3 tests/test_bundle_guidance.py
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
ANCHORS_URI = (
    "git+https://github.com/microsoft/amplifier-foundation@main"
    "#subdirectory=bundles/anchors/bundle.md"
)
BEHAVIOR_URI = (
    "git+https://github.com/microsoft/amplifier-bundle-recipes@main"
    "#subdirectory=behaviors/recipes.yaml"
)


def read_meta_description(agent: str) -> str:
    """Read the quoted meta.description from this standalone agent frontmatter."""
    _, frontmatter, _ = agent.split("---", 2)
    in_meta = False
    for line in frontmatter.splitlines():
        if line == "meta:":
            in_meta = True
            continue
        if in_meta and line.startswith("  description: "):
            return ast.literal_eval(line.removeprefix("  description: "))
    raise AssertionError("quoted meta.description is required in frontmatter")


def test_readme() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    capability_start = readme.index(
        "### Step 4: Add a capability behavior (optional)"
    )
    capability_end = readme.index(
        "\n**First time? Quick setup wizard:**", capability_start
    )
    quickstart_capability = readme[capability_start:capability_end]

    assert BEHAVIOR_URI in readme
    assert "--app" in readme
    assert "anchors is the default" in readme
    assert "foundation is the default" not in readme
    assert "`foundation` bundle** remains a selectable complete root" in readme
    assert "`recipes:recipe-author`" in quickstart_capability
    assert "`design-intelligence:component-designer`" not in quickstart_capability


def test_module_development_example() -> None:
    guide = (REPO_ROOT / "docs" / "MODULE_DEVELOPMENT.md").read_text(encoding="utf-8")

    assert ANCHORS_URI in guide
    assert "@anchors:context/system.md" in guide
    assert "bundle: foundation" not in guide


def test_expert_recommends_behavior_before_a_complete_new_host() -> None:
    expert = (REPO_ROOT / "agents" / "amplifier-expert.md").read_text(encoding="utf-8")

    assert "Reusable capability: author a behavior" in expert
    assert "Complete new host: compose Anchors" in expert
    assert "Start with foundation bundle + composition" not in expert
    assert "Duplicating a complete root instead of composing a reusable behavior" in expert


def test_expert_description_preserves_routing_without_examples() -> None:
    expert = (REPO_ROOT / "agents" / "amplifier-expert.md").read_text(encoding="utf-8")
    description = read_meta_description(expert)

    assert len(description) <= 600
    assert "<example>" not in description
    assert "<commentary>" not in description
    assert "capability discovery" in description
    assert "implementation planning" in description
    assert "validation" in description
    assert "USE WHEN:" in description
    assert "DO NOT USE WHEN:" in description
    assert "core:core-expert" in description
    assert "foundation:foundation-expert" in description


def test_expert_behavior_uses_thin_awareness_context() -> None:
    behavior = (REPO_ROOT / "behaviors" / "amplifier-expert.yaml").read_text(
        encoding="utf-8"
    )
    awareness = (REPO_ROOT / "context" / "amplifier-awareness.md").read_text(
        encoding="utf-8"
    )
    expert = (REPO_ROOT / "agents" / "amplifier-expert.md").read_text(encoding="utf-8")

    assert "amplifier:amplifier-expert" in behavior
    assert "amplifier:context/amplifier-awareness.md" in behavior
    assert "amplifier:context/ecosystem-overview.md" not in behavior
    assert len(awareness) < 500
    assert "amplifier:amplifier-expert" in awareness
    assert "behavior composition" in awareness
    assert "Anchors" in awareness
    assert "@amplifier:context/ecosystem-overview.md" in expert


def main() -> int:
    tests = (
        test_readme,
        test_module_development_example,
        test_expert_recommends_behavior_before_a_complete_new_host,
        test_expert_description_preserves_routing_without_examples,
        test_expert_behavior_uses_thin_awareness_context,
    )
    for test in tests:
        test()
        print(f"PASS: {test.__name__}")
    return 0


if __name__ == "__main__":
    sys.exit(main())