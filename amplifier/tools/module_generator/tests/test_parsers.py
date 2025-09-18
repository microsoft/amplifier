from pathlib import Path

from amplifier.tools.module_generator.parsers import derive_module_name_from_path
from amplifier.tools.module_generator.parsers import parse_contract
from amplifier.tools.module_generator.parsers import parse_impl_spec


def test_slug_from_filename(tmp_path: Path):
    p = tmp_path / "MY_FEATURE.contract.md"
    p.write_text("# Module Contract: My_Feature\n\n## Purpose\nDo X\n", encoding="utf-8")
    name = derive_module_name_from_path(p)
    assert name == "my_feature"


def test_parse_contract_and_spec(tmp_path: Path):
    c = tmp_path / "module.contract.md"
    s = tmp_path / "module.impl_spec.md"
    c.write_text("# Module Contract: IdeaSynthesizer\n\n## Purpose\nHello\n", encoding="utf-8")
    s.write_text("# Implementation Requirements: IdeaSynthesizer\n\n## Design Overview\nWorld\n", encoding="utf-8")
    contract = parse_contract(c)
    spec = parse_impl_spec(s, expected_name=contract.name)
    # allow either styles for slug depending on header parse
    assert contract.name in {"ideasynthesizer", "idea_synthesizer"}
    assert "Hello" in (contract.purpose or "")
    assert "World" in (spec.overview or "")
