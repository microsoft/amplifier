"""Utilities for loading module contract and implementation spec artifacts."""

from __future__ import annotations

import re
from pathlib import Path

from .models import ModuleSpecBundle


class SpecLoaderError(Exception):
    """Raised when contract/spec artifacts cannot be loaded or validated."""


def load_spec_bundle(contract_path: Path, spec_path: Path) -> ModuleSpecBundle:
    """Load contract and spec markdown files into a validated bundle."""

    if not contract_path.exists():
        raise SpecLoaderError(f"Contract file not found: {contract_path}")
    if not spec_path.exists():
        raise SpecLoaderError(f"Implementation spec file not found: {spec_path}")

    contract_text = contract_path.read_text(encoding="utf-8").strip()
    spec_text = spec_path.read_text(encoding="utf-8").strip()

    if not contract_text:
        raise SpecLoaderError("Contract file is empty; cannot proceed")
    if not spec_text:
        raise SpecLoaderError("Implementation spec file is empty; cannot proceed")

    module_name = _extract_module_name(contract_text)
    module_slug = _slugify(module_name)

    return ModuleSpecBundle(
        module_name=module_name,
        module_slug=module_slug,
        contract_path=contract_path,
        spec_path=spec_path,
        contract_text=contract_text,
        spec_text=spec_text,
    )


def _extract_module_name(contract_text: str) -> str:
    """Parse the first Markdown heading to derive the module name."""

    for line in contract_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            heading = stripped.lstrip("#").strip()
            if not heading:
                continue
            if ":" in heading:
                return heading.split(":", 1)[1].strip() or heading
            if heading.lower().startswith("module contract"):
                return heading
            return heading
    raise SpecLoaderError("Unable to determine module name from contract heading")


def _slugify(value: str) -> str:
    """Create a filesystem-safe snake_case slug."""

    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value)
    value = value.strip("_")
    if not value:
        raise SpecLoaderError("Derived module slug is empty")
    return value
