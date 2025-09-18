"""Import mapping system for common Python packages.

This module provides intelligent import mappings to ensure generated code uses
the correct import statements for common packages, avoiding import errors.
"""

from __future__ import annotations

import subprocess
from typing import NamedTuple


class ImportMapping(NamedTuple):
    """Defines the correct import pattern for a package."""

    package_name: str  # Name used in pip/pyproject.toml
    import_pattern: str  # Correct import statement
    common_mistakes: list[str]  # Common incorrect patterns to watch for
    notes: str  # Additional context


# Master mapping of package names to their correct import patterns
PACKAGE_IMPORT_MAPPINGS: dict[str, ImportMapping] = {
    "python-slugify": ImportMapping(
        package_name="python-slugify",
        import_pattern="from slugify import slugify",
        common_mistakes=["from slugify import Slugify", "import slugify.slugify", "from python_slugify import slugify"],
        notes="The package 'python-slugify' exports function 'slugify' directly",
    ),
    "slugify-python": ImportMapping(
        package_name="slugify-python",
        import_pattern="from slugify import Slugify; slugify = Slugify()",
        common_mistakes=["from slugify import slugify", "import slugify.slugify", "from slugify_python import slugify"],
        notes="The package 'slugify-python' exports class 'Slugify' (not function). You must instantiate it.",
    ),
    "pillow": ImportMapping(
        package_name="pillow",
        import_pattern="from PIL import Image",
        common_mistakes=["import pillow", "from pillow import Image", "import PIL"],
        notes="Pillow installs as 'PIL' module, not 'pillow'",
    ),
    "beautifulsoup4": ImportMapping(
        package_name="beautifulsoup4",
        import_pattern="from bs4 import BeautifulSoup",
        common_mistakes=["from beautifulsoup4 import BeautifulSoup", "import beautifulsoup4"],
        notes="BeautifulSoup4 installs as 'bs4' module",
    ),
    "msgpack-python": ImportMapping(
        package_name="msgpack",
        import_pattern="import msgpack",
        common_mistakes=["import msgpack_python", "from msgpack_python import packb"],
        notes="Package name is 'msgpack', not 'msgpack-python'",
    ),
    "pymongo": ImportMapping(
        package_name="pymongo",
        import_pattern="from pymongo import MongoClient",
        common_mistakes=["import mongo", "from mongo import Client"],
        notes="MongoDB client is 'pymongo.MongoClient'",
    ),
    "python-dateutil": ImportMapping(
        package_name="python-dateutil",
        import_pattern="from dateutil import parser",
        common_mistakes=["from python_dateutil import parser", "import dateutil.parser as parser"],
        notes="Package installs as 'dateutil', not 'python-dateutil'",
    ),
    "opencv-python": ImportMapping(
        package_name="opencv-python",
        import_pattern="import cv2",
        common_mistakes=["import opencv", "from opencv import cv2", "import opencv_python"],
        notes="OpenCV Python bindings install as 'cv2' module",
    ),
    "scikit-learn": ImportMapping(
        package_name="scikit-learn",
        import_pattern="from sklearn import ...",
        common_mistakes=["import scikit_learn", "from scikit.learn import ...", "import scikitlearn"],
        notes="Scikit-learn installs as 'sklearn' module",
    ),
    "pyqt5": ImportMapping(
        package_name="PyQt5",
        import_pattern="from PyQt5 import QtWidgets",
        common_mistakes=["import pyqt5", "from pyqt5 import QtWidgets", "import PyQT5"],
        notes="Case-sensitive: 'PyQt5' not 'pyqt5'",
    ),
    "pytorch": ImportMapping(
        package_name="torch",
        import_pattern="import torch",
        common_mistakes=["import pytorch", "from pytorch import tensor"],
        notes="PyTorch installs as 'torch' module",
    ),
    "attrs": ImportMapping(
        package_name="attrs",
        import_pattern="import attr",
        common_mistakes=["import attrs", "from attrs import define"],
        notes="attrs package imports as 'attr' (singular)",
    ),
    "py-yaml": ImportMapping(
        package_name="PyYAML",
        import_pattern="import yaml",
        common_mistakes=["import pyyaml", "from PyYAML import load", "import py_yaml"],
        notes="PyYAML installs as 'yaml' module",
    ),
}


def get_import_guidance(package_name: str) -> str | None:
    """Get import guidance for a package if it has known issues.

    Args:
        package_name: The package name as it appears in pip/pyproject.toml

    Returns:
        Formatted guidance string or None if no special handling needed
    """
    mapping = PACKAGE_IMPORT_MAPPINGS.get(package_name.lower())
    if not mapping:
        # Check alternative names
        for key, value in PACKAGE_IMPORT_MAPPINGS.items():
            if package_name.lower() in [key, value.package_name.lower()]:
                mapping = value
                break

    if mapping:
        return (
            f"⚠️  Import guidance for '{package_name}':\n   Correct: {mapping.import_pattern}\n   Note: {mapping.notes}"
        )
    return None


def build_import_instructions() -> str:
    """Build comprehensive import instructions for the AI.

    Returns:
        Formatted instructions about common import patterns
    """
    instructions = [
        "CRITICAL IMPORT RULES:",
        "===================",
        "Many Python packages have non-obvious import patterns. Follow these rules:",
        "",
    ]

    for mapping in PACKAGE_IMPORT_MAPPINGS.values():
        instructions.append(f"• {mapping.package_name}:")
        instructions.append(f"  CORRECT: {mapping.import_pattern}")
        instructions.append(f"  WRONG: {mapping.common_mistakes[0]}")
        instructions.append(f"  NOTE: {mapping.notes}")
        instructions.append("")

    instructions.extend(
        [
            "BEFORE USING ANY PACKAGE:",
            "1. Check if it's in the list above",
            "2. Use the EXACT import pattern specified",
            "3. Test imports with 'python -c \"<import statement>\"'",
            "4. If unsure, check the package documentation",
            "",
        ]
    )

    return "\n".join(instructions)


def get_installed_packages() -> set[str]:
    """Get a set of installed package names.

    Returns:
        Set of package names that are currently installed
    """
    try:
        # Use uv pip list to get installed packages
        result = subprocess.run(["uv", "pip", "list"], capture_output=True, text=True, check=True)
        packages = set()
        for line in result.stdout.split("\n")[2:]:  # Skip header lines
            if line.strip():
                # Extract package name (first column)
                parts = line.split()
                if parts:
                    packages.add(parts[0].lower())
        return packages
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback: try pip list
        try:
            result = subprocess.run(["pip", "list"], capture_output=True, text=True, check=True)
            packages = set()
            for line in result.stdout.split("\n")[2:]:  # Skip header lines
                if line.strip():
                    parts = line.split()
                    if parts:
                        packages.add(parts[0].lower())
            return packages
        except (subprocess.CalledProcessError, FileNotFoundError, Exception):
            return set()


def validate_imports_in_code(code: str) -> list[str]:
    """Check code for problematic imports and return warnings.

    Args:
        code: Python source code to check

    Returns:
        List of warning messages for problematic imports
    """
    warnings = []
    lines = code.split("\n")

    # Get installed packages once
    installed_packages = get_installed_packages()

    # Determine which slugify package is installed (if any)
    installed_slugify = None
    if "python-slugify" in installed_packages:
        installed_slugify = "python-slugify"
    elif "slugify-python" in installed_packages:
        installed_slugify = "slugify-python"

    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not (line.startswith("import ") or line.startswith("from ")):
            continue

        # Special handling for slugify packages since they conflict
        if "from slugify import" in line or "import slugify" in line:
            if installed_slugify == "python-slugify":
                # Check if using correct pattern for python-slugify
                if "from slugify import Slugify" in line:
                    warnings.append(
                        f"Line {line_num}: Incorrect import for python-slugify!\n"
                        f"  Found: {line}\n"
                        f"  Should be: from slugify import slugify\n"
                        f"  Reason: python-slugify exports function 'slugify' directly"
                    )
            elif installed_slugify == "slugify-python" and "from slugify import slugify" in line:
                # Using wrong pattern for slugify-python
                warnings.append(
                    f"Line {line_num}: Incorrect import for slugify-python!\n"
                    f"  Found: {line}\n"
                    f"  Should be: from slugify import Slugify; slugify = Slugify()\n"
                    f"  Reason: slugify-python exports class 'Slugify' (not function)"
                )
            continue  # Don't check other mappings for slugify imports

        # Check other packages against their specific mappings
        for mapping in PACKAGE_IMPORT_MAPPINGS.values():
            # Skip slugify packages as they're handled above
            if mapping.package_name in ["python-slugify", "slugify-python"]:
                continue

            # Only check if the package is installed
            if mapping.package_name.lower() in installed_packages:
                for mistake in mapping.common_mistakes:
                    if mistake in line:
                        warnings.append(
                            f"Line {line_num}: Incorrect import detected!\n"
                            f"  Found: {line}\n"
                            f"  Should be: {mapping.import_pattern}\n"
                            f"  Reason: {mapping.notes}"
                        )
                        break

    return warnings
