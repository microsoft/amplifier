#!/usr/bin/env python3
"""Unit tests for the repo-validity gate of recipes/repo-audit.yaml.

Work item recipes-c93.

The step's `command:` is read out of the recipe, substituted exactly as the
recipe engine substitutes it (a dict renders via json.dumps; a bool renders as
lowercase true/false), and run under real bash. No model, no network.

Run:  python3 tests/test_repo_audit_validity_gate.py
Exits 0 when every case passes, 1 otherwise.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
RECIPE = REPO_ROOT / "recipes" / "repo-audit.yaml"
GATE_STEP = "enforce-repo-valid"

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        if detail:
            print(f"          {detail}")
        FAILURES.append(name)


def load_recipe() -> dict:
    return yaml.safe_load(RECIPE.read_text())


def gate_command(recipe: dict) -> str:
    for step in recipe["steps"]:
        if step.get("id") == GATE_STEP:
            return step["command"]
    raise AssertionError(f"step {GATE_STEP!r} not found in {RECIPE}")


def run_gate(command: str, validation: dict) -> subprocess.CompletedProcess:
    script = command
    script = script.replace("{{repo_validation}}", json.dumps(validation))
    script = script.replace("{{repo_owner}}", "microsoft")
    script = script.replace("{{repo_name}}", "does-not-exist")
    return subprocess.run(
        ["bash", "-c", script], capture_output=True, text=True, timeout=60,
    )


def test_placement(recipe: dict) -> None:
    print("\n=== the gate runs before anything else can spend money ===")
    ids = [s.get("id") for s in recipe["steps"]]
    try:
        gate_at = ids.index(GATE_STEP)
    except ValueError:
        check("gate step exists", False, f"{GATE_STEP} missing")
        return
    check("gate step exists", True)
    check("gate sits immediately after validate-repo",
          ids[gate_at - 1] == "validate-repo",
          f"predecessor is {ids[gate_at - 1]!r}")

    first_agent = next(
        (i for i, s in enumerate(recipe["steps"]) if s.get("agent")), len(recipe["steps"])
    )
    check("no agent step precedes the gate", gate_at < first_agent,
          f"gate at {gate_at}, first agent step at {first_agent}")

    writes_before = [
        (i, s.get("id")) for i, s in enumerate(recipe["steps"])
        if i < gate_at and "audit-report.md" in str(s.get("command", ""))
    ]
    check("no audit-report.md write precedes the gate", not writes_before,
          f"gate at {gate_at}, earlier report writes: {writes_before}")

    gate = recipe["steps"][gate_at]
    check("gate fails the recipe on error", gate.get("on_error") == "fail",
          f"on_error={gate.get('on_error')!r}")


def test_behaviour(recipe: dict) -> None:
    print("\n=== the gate's two branches, under real bash ===")
    command = gate_command(recipe)

    cases_stop = [
        ("non-existent repo",
         {"valid": False, "error": "Repository not found or not accessible"}),
        ("archived repo",
         {"valid": False, "error": "Repository is archived"}),
        ("valid=false with no reason", {"valid": False}),
        ("valid key absent entirely", {"name": "whatever"}),
    ]
    for name, validation in cases_stop:
        proc = run_gate(command, validation)
        reason = validation.get("error", "")
        ok = (
            proc.returncode != 0
            and "refusing to audit" in proc.stderr
            and "microsoft/does-not-exist" in proc.stderr
            and (not reason or reason in proc.stderr)
            and "no audit-report.md is written" in proc.stderr
        )
        check(f"stops: {name}", ok,
              f"rc={proc.returncode} stderr={proc.stderr[:300]!r}")

    cases_pass = [
        ("live repo",
         {"valid": True, "name": "amplifier-bundle-notify",
          "description": "notify bundle", "issues_enabled": True,
          "last_push": "2026-09-01T00:00:00Z"}),
        ("description containing an apostrophe and quotes",
         {"valid": True, "name": "x",
          "description": "it's a \"quoted\" description, with $VARS and `backticks`",
          "issues_enabled": False, "last_push": None}),
    ]
    for name, validation in cases_pass:
        proc = run_gate(command, validation)
        ok = proc.returncode == 0 and "auditing" in proc.stdout
        check(f"continues: {name}", ok,
              f"rc={proc.returncode} stdout={proc.stdout[:200]!r} stderr={proc.stderr[:200]!r}")


def main() -> int:
    print(f"Recipe under test: {RECIPE}")
    recipe = load_recipe()
    test_placement(recipe)
    test_behaviour(recipe)
    print(f"\nTOTAL FAILURES: {len(FAILURES)}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
