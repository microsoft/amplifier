from __future__ import annotations

import re
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ModuleContract:
    name: str
    raw: str
    purpose: str | None = None
    header: dict[str, Any] = field(default_factory=dict)
    depends_on: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ModuleImplSpec:
    name: str
    raw: str
    overview: str | None = None
    header: dict[str, Any] = field(default_factory=dict)


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


def _split_front_matter(text: str) -> tuple[dict[str, Any], str]:
    header: dict[str, Any] = {}
    body = text
    if text.startswith("---"):
        parts = text.splitlines()
        if parts and parts[0].strip() == "---":
            for idx in range(1, len(parts)):
                if parts[idx].strip() == "---":
                    fm = "\n".join(parts[1:idx])
                    body = "\n".join(parts[idx + 1 :])
                    if fm.strip():
                        header = yaml.safe_load(fm) or {}
                    break
    return header, body


def parse_contract(path: Path) -> ModuleContract:
    text = path.read_text(encoding="utf-8")
    header, body = _split_front_matter(text)
    m = _H1_RE.search(text)
    name_from_header = None
    if isinstance(header, dict) and header.get("module"):
        name_from_header = str(header["module"])
    if m:
        h1 = m.group(1).strip()
        if ":" in h1:
            _, right = h1.split(":", 1)
            name_from_header = right.strip()
        else:
            name_from_header = h1.strip()
    name = _slugify(name_from_header) if name_from_header else derive_module_name_from_path(path)
    purpose = None
    pm = _PURPOSE_RE.search(body)
    if pm:
        purpose = pm.group("body").strip()
    depends_on = []
    if isinstance(header, dict):
        raw_depends_on = header.get("depends_on") or []
        if isinstance(raw_depends_on, dict):
            depends_on = [raw_depends_on]
        elif isinstance(raw_depends_on, list):
            depends_on = raw_depends_on
    if isinstance(depends_on, dict):
        depends_on = [depends_on]
    header_dict = header if isinstance(header, dict) else {}
    return ModuleContract(name=name, raw=text, purpose=purpose, header=header_dict, depends_on=depends_on)


def parse_impl_spec(path: Path, expected_name: str | None = None) -> ModuleImplSpec:
    text = path.read_text(encoding="utf-8")
    header, body = _split_front_matter(text)
    m = _H1_RE.search(text)
    name_from_header = None
    if isinstance(header, dict) and header.get("module"):
        name_from_header = str(header["module"])
    if m:
        h1 = m.group(1).strip()
        if ":" in h1:
            _, right = h1.split(":", 1)
            name_from_header = right.strip()
        else:
            name_from_header = h1.strip()
    name = _slugify(name_from_header) if name_from_header else (expected_name or derive_module_name_from_path(path))
    ov = None
    om = _OVERVIEW_RE.search(body)
    if om:
        ov = om.group("body").strip()
    header_dict = header if isinstance(header, dict) else {}
    return ModuleImplSpec(name=name, raw=text, overview=ov, header=header_dict)
