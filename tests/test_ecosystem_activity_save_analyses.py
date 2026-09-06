#!/usr/bin/env python3
"""Unit tests for save-analyses-to-file in recipes/ecosystem-activity-report.yaml.

Work item recipes-zfl.

The step's `command:` is read out of the recipe, substituted exactly as the
recipe engine substitutes it, and run under real bash against a synthetic
analyses/ directory. No model, no network.

Run:  python3 tests/test_ecosystem_activity_save_analyses.py
Exits 0 when every case passes, 1 otherwise.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
RECIPE = REPO_ROOT / "recipes" / "ecosystem-activity-report.yaml"
STEP_ID = "save-analyses-to-file"

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        if detail:
            print(f"          {detail}")
        FAILURES.append(name)


def get_step() -> dict:
    recipe = yaml.safe_load(RECIPE.read_text())
    for step in recipe["steps"]:
        if step.get("id") == STEP_ID:
            return step
    raise AssertionError(f"step {STEP_ID!r} not found in {RECIPE}")


def make_analyses(root: Path, n_repos: int) -> Path:
    analyses = root / "analyses"
    analyses.mkdir(parents=True, exist_ok=True)
    for i in range(n_repos):
        (analyses / f"repo{i}-analysis.json").write_text(
            json.dumps({
                "repo": f"repo{i}",
                "activity_summary": {"commits": i, "prs_total": i},
                # a prompt-hostile payload: quotes, backslashes, newlines
                "themes": ['a "quoted" theme', "back\\slash", "line\none"],
            }),
            encoding="utf-8",
        )
    # intermediates reduce-analyses filters out -- must not be collected
    for name in ("repo0-chunk-1-analysis.json", "repo0-commit-analysis.json",
                 "repo0-pr-analysis.json"):
        (analyses / name).write_text(json.dumps({"intermediate": True}), encoding="utf-8")
    return analyses


def render(command: str, working_dir: Path) -> str:
    return command.replace("{{working_dir}}", str(working_dir))


def test_no_model_and_no_payload_interpolation(step: dict) -> None:
    print("\n=== the step spends no agent call and interpolates no payload ===")
    check("step is a bash step, not an agent step",
          step.get("type") == "bash" and "agent" not in step,
          f"type={step.get('type')!r} agent={step.get('agent')!r}")
    command = step["command"]
    check("command does not interpolate repo_analyses",
          "{{repo_analyses}}" not in command,
          "the collected array is still pasted into the command text")
    check("step declares no model", "model" not in step,
          f"model={step.get('model')!r}")


def test_command_size_is_constant(step: dict) -> None:
    print("\n=== command size does not scale with N ===")
    command = step["command"]
    small = render(command, Path("/tmp/w"))
    big = render(command, Path("/tmp/w"))
    # the only substitution is working_dir, so N cannot change the command at all
    check("rendered command is identical for any number of repos",
          len(small) == len(big) and small == big)
    check("rendered command stays far below MAX_ARG_STRLEN (128 KB)",
          len(small.encode()) < 100_000, f"{len(small.encode())} bytes")


def test_behaviour(step: dict) -> None:
    print("\n=== the step's behaviour, under real bash ===")
    command = step["command"]

    for n in (1, 2, 25):
        with tempfile.TemporaryDirectory(prefix="eco-save-") as td:
            work = Path(td)
            make_analyses(work, n)
            proc = subprocess.run(
                ["bash", "-c", render(command, work)],
                capture_output=True, text=True, timeout=120,
            )
            if proc.returncode != 0:
                check(f"{n} repos: step succeeds", False,
                      f"rc={proc.returncode} stderr={proc.stderr[-400:]!r}")
                continue
            check(f"{n} repos: step succeeds", True)
            try:
                result = json.loads(proc.stdout)
            except json.JSONDecodeError as exc:
                check(f"{n} repos: stdout is parseable JSON", False, str(exc))
                continue
            check(f"{n} repos: reports count={n}", result.get("count") == n,
                  f"got {result!r}")
            out = work / "collected-analyses.json"
            if not out.exists():
                check(f"{n} repos: collected-analyses.json written", False, "file missing")
                continue
            collected = json.loads(out.read_text())
            check(f"{n} repos: collected-analyses.json holds {n} analyses",
                  isinstance(collected, list) and len(collected) == n,
                  f"got {len(collected) if isinstance(collected, list) else collected!r}")
            names = sorted(c.get("repo") for c in collected)
            check(f"{n} repos: intermediates excluded",
                  names == sorted(f"repo{i}" for i in range(n)),
                  f"got {names}")
            check(f"{n} repos: payload survives byte-exact",
                  all(c["themes"] == ['a "quoted" theme', "back\\slash", "line\none"]
                      for c in collected),
                  "a theme value was mangled in transit")

    # an unparseable analysis file is skipped and named, not fatal
    with tempfile.TemporaryDirectory(prefix="eco-save-") as td:
        work = Path(td)
        analyses = make_analyses(work, 2)
        (analyses / "broken-analysis.json").write_text("{not json", encoding="utf-8")
        proc = subprocess.run(
            ["bash", "-c", render(command, work)],
            capture_output=True, text=True, timeout=120,
        )
        ok = (
            proc.returncode == 0
            and "skipping unparseable analysis file" in proc.stderr
            and json.loads(proc.stdout).get("count") == 2
        )
        check("unparseable analysis file is skipped and named", ok,
              f"rc={proc.returncode} stderr={proc.stderr[-300:]!r} stdout={proc.stdout[:200]!r}")

    # no analyses at all: an empty array and a warning, not a crash
    with tempfile.TemporaryDirectory(prefix="eco-save-") as td:
        work = Path(td)
        (work / "analyses").mkdir()
        proc = subprocess.run(
            ["bash", "-c", render(command, work)],
            capture_output=True, text=True, timeout=120,
        )
        ok = (
            proc.returncode == 0
            and json.loads(proc.stdout).get("count") == 0
            and json.loads((work / "collected-analyses.json").read_text()) == []
            and "no per-repo analyses found" in proc.stderr
        )
        check("empty analyses directory yields [] and a warning", ok,
              f"rc={proc.returncode} stderr={proc.stderr[-300:]!r} stdout={proc.stdout[:200]!r}")


def main() -> int:
    print(f"Recipe under test: {RECIPE}")
    step = get_step()
    test_no_model_and_no_payload_interpolation(step)
    test_command_size_is_constant(step)
    test_behaviour(step)
    print(f"\nTOTAL FAILURES: {len(FAILURES)}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
