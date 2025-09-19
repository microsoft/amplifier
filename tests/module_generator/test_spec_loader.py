from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from amplifier.module_generator.spec_loader import load_spec_bundle


def _workspace_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _make_workspace() -> Path:
    root = _workspace_root() / "tmp" / "module_generator_tests" / str(uuid4())
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_load_spec_bundle_parses_contract_heading() -> None:
    workspace = _make_workspace()
    contract = workspace / "idea_synth.contract.md"
    spec = workspace / "idea_synth.impl_spec.md"

    contract.write_text("# Module Contract: Idea Synthesizer\n\nBody", encoding="utf-8")
    spec.write_text("# Implementation Spec\n\nDetails", encoding="utf-8")

    bundle = load_spec_bundle(contract, spec)

    assert bundle.module_name == "Idea Synthesizer"
    assert bundle.module_slug == "idea_synthesizer"
    assert bundle.contract_text.startswith("# Module Contract")
    assert bundle.spec_text.startswith("# Implementation Spec")
    assert bundle.output_module_path.as_posix().endswith("amplifier/idea_synthesizer")
