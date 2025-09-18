from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ModuleContract:
    name: str
    raw: str
    purpose: str | None = None


@dataclass
class ModuleImplSpec:
    name: str
    raw: str
    overview: str | None = None


_H1_RE = re.compile(r"^#\s*(.+)$", re.M)
_PURPOSE_RE = re.compile(r"^##\s*Purpose\s*\n(?P<body>.+?)(?:\n##|\Z)", re.S | re.M)
_OVERVIEW_RE = re.compile(r"^##\s*(Design Overview|Overview)\s*\n(?P<body>.+?)(?:\n##|\Z)", re.S | re.M)


def _slugify(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", name.strip())
    s = re.sub(r"_+", "_", s).strip("_")
    return s.lower()


def derive_module_name_from_path(path: Path) -> str:
    base = path.stem
    base = re.sub(r"\.(contract|impl|impl_spec)$", "", base, flags=re.I)
    return _slugify(base)


def parse_contract(path: Path) -> ModuleContract:
    text = path.read_text(encoding="utf-8")
    m = _H1_RE.search(text)
    name_from_header = None
    if m:
        header = m.group(1).strip()
        if ":" in header:
            _, right = header.split(":", 1)
            name_from_header = right.strip()
        else:
            name_from_header = header.strip()
    name = _slugify(name_from_header) if name_from_header else derive_module_name_from_path(path)
    purpose = None
    pm = _PURPOSE_RE.search(text)
    if pm:
        purpose = pm.group("body").strip()
    return ModuleContract(name=name, raw=text, purpose=purpose)


def parse_impl_spec(path: Path, expected_name: str | None = None) -> ModuleImplSpec:
    text = path.read_text(encoding="utf-8")
    m = _H1_RE.search(text)
    name_from_header = None
    if m:
        header = m.group(1).strip()
        if ":" in header:
            _, right = header.split(":", 1)
            name_from_header = right.strip()
        else:
            name_from_header = header.strip()
    name = _slugify(name_from_header) if name_from_header else (expected_name or derive_module_name_from_path(path))
    ov = None
    om = _OVERVIEW_RE.search(text)
    if om:
        ov = om.group("body").strip()
    return ModuleImplSpec(name=name, raw=text, overview=ov)
