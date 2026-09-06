#!/usr/bin/env python3
"""Unit tests for the JSON payload channel of recipes/outline-generation-from-doc.yaml.

Work item recipes-cv1.

The code under test is NOT duplicated here. Both halves are read out of the
recipe itself, so a test can never drift from the recipe that actually runs:

  * `assemble-outline-structure`'s python region between the
    `# === BEGIN json-payload-loader ===` / `# === END json-payload-loader ===`
    markers is extracted and exec'd (tolerant-repair + schema-validation tests);
  * the step's whole `command:` is substituted and run under bash
    (delivery-channel tests) -- exactly what the recipe engine does, minus the
    model.

Run:  python3 tests/test_outline_json_payload.py
Exits 0 when every shape passes, 1 otherwise.
"""

from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap
from contextlib import redirect_stderr
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
RECIPE = REPO_ROOT / "recipes" / "outline-generation-from-doc.yaml"
STEP_ID = "assemble-outline-structure"
BEGIN = "# === BEGIN json-payload-loader ==="
END = "# === END json-payload-loader ==="


# ---------------------------------------------------------------------------
# Extraction: pull the real code out of the real recipe
# ---------------------------------------------------------------------------
def step_command() -> str:
    recipe = yaml.safe_load(RECIPE.read_text())
    for step in recipe["steps"]:
        if step.get("id") == STEP_ID:
            return step["command"]
    raise AssertionError(f"step {STEP_ID!r} not found in {RECIPE}")


def load_loader_namespace() -> dict:
    command = step_command()
    start = command.index(BEGIN)
    end = command.index(END)
    source = textwrap.dedent(command[start:end])
    # The step imports json/re/sys above the marked region; supply the same
    # three names rather than dragging unrelated recipe lines into the exec.
    namespace: dict = {
        "__name__": "json_payload_loader", "json": json, "re": re, "sys": sys,
    }
    exec(compile(source, f"{RECIPE}::{STEP_ID}", "exec"), namespace)
    return namespace


# ---------------------------------------------------------------------------
# Payload shapes
# ---------------------------------------------------------------------------
# The seven shapes the v1.9.0 fix was verified against (see
# dtu-artifacts/sweep/fix-mxe/cleaner-unit-test.txt) plus the two shapes the
# work item reports as still failing.
PROMPT_SHAPES = [
    # (name, the exact prompt string the model intended to convey)
    ("backslash+newline (recipes-cv1 defect 1)", "execute \\\n  recipe_path=x"),
    ("windows path", r"C:\Users\me"),
    ("valid escapes preserved", 'a\nb "q" \tt'),
    ("unicode escape preserved", "caf\u00e9"),
    ("trailing valid backslash", "ends \\"),
    ("literal newline in string", "a\nb"),
    ("literal tab in string", "a\tb"),
    # recipes-cv1 defect 1, as it actually appeared live: a shell
    # line-continuation quoted verbatim out of a source document.
    (
        "recipes-cv1 defect 1 (live shape)",
        "Run it with:\n  amplifier tool invoke recipes \\\n"
        "    recipe_path=seed-reconcile.yaml",
    ),
    # recipes-cv1 defect 2, as it actually appeared live: a section prompt
    # quoting an embedded JSON snippet, whose inner quotes the v1.9.0 lookahead
    # heuristic was structurally unable to handle.
    (
        "recipes-cv1 defect 2 (embedded JSON snippet)",
        "Run it with:\n  amplifier tool invoke recipes \\\n"
        "    recipe_path=seed-reconcile.yaml \\\n"
        "    context='{\"tracker_project\": \"converge\", "
        '"target_repo": "./target-repo"}\'',
    ),
]

META_OBJ = {
    "name": "test-outline",
    "document_type": "vision",
    "model": "claude-sonnet-4",
}


def flat_payload(prompt: str) -> dict:
    return {
        "document_title": "# Test Document",
        "sections": [
            {
                "section_id": "section-0",
                "heading": "# Test Document",
                "level": 1,
                "parent_index": None,
                "prompt": prompt,
                "sources": [],
            },
            {
                "section_id": "section-1",
                "heading": "## Second",
                "level": 2,
                "parent_index": 0,
                "prompt": "plain prompt",
                "sources": ["a.md"],
            },
        ],
    }


# ---------------------------------------------------------------------------
# Result plumbing
# ---------------------------------------------------------------------------
FAILURES: list[str] = []


def check(group: str, name: str, ok: bool, detail: str = "") -> None:
    status = "PASS" if ok else "FAIL"
    line = f"  {status}  {name}"
    if detail and not ok:
        line += f"\n          {detail}"
    print(line)
    if not ok:
        FAILURES.append(f"{group} :: {name}")


def write_payloads(tmp: Path, meta: dict, flat_text: str) -> tuple[Path, Path]:
    meta_path = tmp / "_outline_meta.raw.json"
    flat_path = tmp / "_flat_sections.raw.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    flat_path.write_text(flat_text, encoding="utf-8")
    return meta_path, flat_path


# ---------------------------------------------------------------------------
# Test 1: every shape survives the loader when delivered byte-exact
# ---------------------------------------------------------------------------
def test_wellformed_shapes(ns: dict, tmp: Path) -> None:
    print("\n=== loader: well-formed model JSON, delivered byte-exact ===")
    for name, prompt in PROMPT_SHAPES:
        text = json.dumps(flat_payload(prompt), indent=2)
        _, flat_path = write_payloads(tmp, META_OBJ, text)
        try:
            obj = ns["load_json_payload"](
                str(flat_path), "flat_sections",
                ns["validate_flat_sections"], ns["FLAT_KEYS"],
            )
            got = obj["sections"][0]["prompt"]
            check("wellformed", name, got == prompt,
                  f"expected {prompt!r}\n          got      {got!r}")
        except SystemExit:
            check("wellformed", name, False, "loader exited instead of parsing")


# ---------------------------------------------------------------------------
# Test 2: the two failing shapes, delivered MALFORMED, are repaired
# ---------------------------------------------------------------------------
def _corrupt_like_a_python_literal(text: str) -> str:
    """Reproduce exactly what the pre-v1.10.0 channel did to a payload.

    `flat_json = '''<payload>'''` is a NON-raw python literal, so python's own
    escape processing ate the JSON escaping before json.loads ever saw it.
    """
    namespace: dict = {}
    exec(compile("v = '''" + text + "'''\n", "<pre-v1.10.0-channel>", "exec"), namespace)
    return namespace["v"]


def test_malformed_shapes(ns: dict, tmp: Path) -> None:
    print("\n=== loader: malformed model JSON (the two recipes-cv1 shapes) ===")
    for name, prompt in PROMPT_SHAPES[-2:]:
        text = json.dumps(flat_payload(prompt), indent=2)
        corrupted = _corrupt_like_a_python_literal(text)

        # Guard: the corruption must actually break strict parsing, otherwise
        # this test proves nothing.
        try:
            json.loads(corrupted)
            check("malformed", f"{name}: corruption is real", False,
                  "corrupted payload still parses strictly")
            continue
        except json.JSONDecodeError:
            check("malformed", f"{name}: corruption is real", True)

        _, flat_path = write_payloads(tmp, META_OBJ, corrupted)
        try:
            obj = ns["load_json_payload"](
                str(flat_path), "flat_sections",
                ns["validate_flat_sections"], ns["FLAT_KEYS"],
            )
        except SystemExit:
            check("malformed", f"{name}: tolerant repair recovers it", False,
                  "loader exited instead of repairing")
            continue
        sections = obj.get("sections", [])
        ok = len(sections) == 2 and sections[1].get("prompt") == "plain prompt"
        if ok and "tracker_project" in prompt:
            # the embedded snippet must survive inside the prompt, not be
            # re-read as outline structure
            ok = "tracker_project" in sections[0].get("prompt", "")
        check("malformed", f"{name}: tolerant repair recovers it", ok,
              f"got sections={json.dumps(sections)[:300]}")


# ---------------------------------------------------------------------------
# Test 3: schema validation + fail-loud
# ---------------------------------------------------------------------------
def test_schema_and_fail_loud(ns: dict, tmp: Path) -> None:
    print("\n=== loader: strict schema validation and loud failure ===")

    cases = [
        ("empty sections array", json.dumps({"document_title": "# x", "sections": []})),
        ("sections missing entirely", json.dumps({"document_title": "# x"})),
        ("section missing heading", json.dumps(
            {"sections": [{"prompt": "p", "level": 1}]})),
        ("section level not an integer", json.dumps(
            {"sections": [{"heading": "# h", "prompt": "p", "level": "deep"}]})),
        ("irrecoverable garbage", "this is not JSON at all {[}"),
    ]
    for name, text in cases:
        _, flat_path = write_payloads(tmp, META_OBJ, text)
        buf = io.StringIO()
        exited = False
        try:
            with redirect_stderr(buf):
                ns["load_json_payload"](
                    str(flat_path), "flat_sections",
                    ns["validate_flat_sections"], ns["FLAT_KEYS"],
                )
        except SystemExit as exc:
            exited = exc.code == 1
        err = buf.getvalue()
        loud = (
            exited
            and "ERROR: flat_sections" in err
            and str(flat_path) in err
            and ("offending snippet" in err or "schema violation" in err)
        )
        check("fail-loud", name, loud,
              f"exited={exited} stderr={err[:300]!r}")

    # meta validator enforces exactly what validate-assembled-outline demands
    meta_path = tmp / "_outline_meta.raw.json"
    meta_path.write_text(json.dumps({"name": "x"}), encoding="utf-8")
    buf = io.StringIO()
    exited = False
    try:
        with redirect_stderr(buf):
            ns["load_json_payload"](
                str(meta_path), "outline_meta",
                ns["validate_outline_meta"], ns["META_KEYS"],
            )
    except SystemExit as exc:
        exited = exc.code == 1
    err = buf.getvalue()
    check("fail-loud", "outline_meta missing document_type/model",
          exited and "document_type" in err and "model" in err,
          f"exited={exited} stderr={err[:300]!r}")


# ---------------------------------------------------------------------------
# Test 4: the delivery channel itself, run through real bash
# ---------------------------------------------------------------------------
def test_delivery_channel(tmp: Path) -> None:
    print("\n=== step command: heredoc delivery is byte-exact (real bash) ===")
    command = step_command()

    if "'''{{" in command or '"""{{' in command:
        check("delivery", "no python-string-literal injection remains", False,
              "step still pastes a payload into a python string literal")
    else:
        check("delivery", "no python-string-literal injection remains", True)

    for name, prompt in PROMPT_SHAPES:
        work = tmp / "bash" / re.sub(r"[^a-z0-9]+", "-", name.lower())
        work.mkdir(parents=True, exist_ok=True)
        flat_text = json.dumps(flat_payload(prompt), indent=2)
        meta_text = json.dumps(META_OBJ, indent=2)

        script = command
        script = script.replace("{{working_dir}}", str(work))
        script = script.replace("{{target_document_path}}", "docs/OUT.md")
        script = script.replace("{{outline_meta}}", meta_text)
        script = script.replace("{{flat_sections}}", flat_text)

        proc = subprocess.run(
            ["bash", "-c", script], capture_output=True, text=True, timeout=120,
        )
        if proc.returncode != 0:
            check("delivery", name, False,
                  f"rc={proc.returncode} stderr={proc.stderr[-400:]!r}")
            continue
        try:
            outline = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            check("delivery", name, False, f"step stdout is not JSON: {exc}")
            continue
        got = outline["document"]["sections"][0]["prompt"]
        check("delivery", name, got == prompt,
              f"expected {prompt!r}\n          got      {got!r}")


def test_delivery_fails_loud(tmp: Path) -> None:
    print("\n=== step command: irrecoverable payload fails loud (real bash) ===")
    command = step_command()
    work = tmp / "bash" / "garbage"
    work.mkdir(parents=True, exist_ok=True)
    script = command
    script = script.replace("{{working_dir}}", str(work))
    script = script.replace("{{target_document_path}}", "docs/OUT.md")
    script = script.replace("{{outline_meta}}", json.dumps(META_OBJ, indent=2))
    script = script.replace("{{flat_sections}}", "not json at all {[}")
    proc = subprocess.run(
        ["bash", "-c", script], capture_output=True, text=True, timeout=120,
    )
    ok = (
        proc.returncode != 0
        and "ERROR: flat_sections" in proc.stderr
        and "offending snippet" in proc.stderr
        and str(work) in proc.stderr
    )
    check("delivery", "garbage payload -> non-zero exit naming the snippet", ok,
          f"rc={proc.returncode} stderr={proc.stderr[-400:]!r}")


def main() -> int:
    print(f"Recipe under test: {RECIPE}")
    ns = load_loader_namespace()
    with tempfile.TemporaryDirectory(prefix="outline-json-") as td:
        tmp = Path(td)
        test_wellformed_shapes(ns, tmp)
        test_malformed_shapes(ns, tmp)
        test_schema_and_fail_loud(ns, tmp)
        test_delivery_channel(tmp)
        test_delivery_fails_loud(tmp)

    print(f"\nTOTAL FAILURES: {len(FAILURES)}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
