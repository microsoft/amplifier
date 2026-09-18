#!/usr/bin/env python3
"""Focused checks for public behavior-first and Anchors guidance.

Run: python3 tests/test_bundle_guidance.py
"""

from __future__ import annotations

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


def test_readme() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    assert BEHAVIOR_URI in readme
    assert "--app" in readme
    assert "anchors is the default" in readme
    assert "foundation is the default" not in readme
    assert "`foundation` bundle** remains a selectable complete root" in readme


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


def main() -> int:
    tests = (
        test_readme,
        test_module_development_example,
        test_expert_recommends_behavior_before_a_complete_new_host,
    )
    for test in tests:
        test()
        print(f"PASS: {test.__name__}")
    return 0


if __name__ == "__main__":
    sys.exit(main())