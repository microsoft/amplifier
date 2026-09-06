#!/usr/bin/env python3
"""Unit tests for set-final-validation in recipes/ecosystem-activity-report.yaml.

Work item recipes-7vl.

The step's `command:` is read out of the recipe, substituted exactly as the
recipe engine substitutes it, and run under real bash against a synthetic
working directory. No model, no network.

The case that mattered: a repo_filter or date_range that selects repos with NO
activity leaves analyses/ empty. The step used to abort under
`set -euo pipefail` before emitting anything, and its `on_error: continue` then
handed assemble-report an empty STRING for final_validation -- which failed two
steps later as "it's a str, not a dict", naming the symptom rather than this
step.

Run:  python3 tests/test_ecosystem_activity_final_validation.py
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
STEP_ID = "set-final-validation"
CONSUMER_ID = "assemble-report"

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        if detail:
            print(f"          {detail}")
        FAILURES.append(name)


def get_step(step_id: str) -> dict:
    recipe = yaml.safe_load(RECIPE.read_text())
    for step in recipe["steps"]:
        if step.get("id") == step_id:
            return step
    raise AssertionError(f"step {step_id!r} not found in {RECIPE}")


def render(command: str, working_dir: Path) -> str:
    return command.replace("{{working_dir}}", str(working_dir))


def run(command: str, working_dir: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", "-c", render(command, working_dir)],
        capture_output=True,
        text=True,
        cwd=str(working_dir),
    )


def make_working_dir(
    root: Path,
    expected: list[str] | None,
    analyzed: list[str],
    make_analyses_dir: bool = True,
) -> Path:
    """Build the on-disk state set-final-validation reads.

    expected=None means expected-repos.txt is absent entirely.
    """
    if expected is not None:
        (root / "expected-repos.txt").write_text(
            "".join(f"{r}\n" for r in sorted(expected)), encoding="utf-8"
        )
    if make_analyses_dir:
        analyses = root / "analyses"
        analyses.mkdir(parents=True, exist_ok=True)
        for repo in analyzed:
            (analyses / f"{repo}-analysis.json").write_text(
                json.dumps({"repo": repo}), encoding="utf-8"
            )
        # intermediates the count must NOT credit as analysed repos
        for name in (
            "ghost-chunk-1-analysis.json",
            "ghost-commit-analysis.json",
            "ghost-pr-analysis.json",
        ):
            (analyses / name).write_text(json.dumps({"intermediate": True}), encoding="utf-8")
    return root


def parsed_stdout(proc: subprocess.CompletedProcess):
    try:
        return json.loads(proc.stdout.strip())
    except (json.JSONDecodeError, ValueError):
        return None


def test_zero_repos_path(command: str) -> None:
    print("\n=== the zero-repos path completes and emits a JSON object ===")

    # analyses/ exists but is empty -- the exact state recipes-7vl observed
    with tempfile.TemporaryDirectory() as tmp:
        wd = make_working_dir(Path(tmp), expected=[], analyzed=[])
        proc = run(command, wd)
        obj = parsed_stdout(proc)
        check(
            "empty analyses/ + empty expected-repos.txt exits 0",
            proc.returncode == 0,
            f"rc={proc.returncode} stderr={proc.stderr.strip()[:400]}",
        )
        check(
            "emits a JSON OBJECT (not the empty string that became a str)",
            isinstance(obj, dict),
            f"stdout={proc.stdout!r}",
        )
        check(
            "reports still_missing 0 / all_complete true",
            isinstance(obj, dict)
            and obj.get("still_missing") == 0
            and obj.get("all_complete") is True,
            f"obj={obj!r}",
        )

    # analyses/ never created at all (no repo analysis ever ran)
    with tempfile.TemporaryDirectory() as tmp:
        wd = make_working_dir(Path(tmp), expected=[], analyzed=[], make_analyses_dir=False)
        proc = run(command, wd)
        obj = parsed_stdout(proc)
        check(
            "missing analyses/ directory exits 0 with an object",
            proc.returncode == 0 and isinstance(obj, dict) and obj.get("still_missing") == 0,
            f"rc={proc.returncode} stdout={proc.stdout!r} stderr={proc.stderr.strip()[:400]}",
        )


def test_missing_expected_file(command: str) -> None:
    print("\n=== a missing expected-repos.txt warns, it does not abort ===")
    with tempfile.TemporaryDirectory() as tmp:
        wd = make_working_dir(Path(tmp), expected=None, analyzed=[])
        proc = run(command, wd)
        obj = parsed_stdout(proc)
        check(
            "exits 0 with a JSON object",
            proc.returncode == 0 and isinstance(obj, dict),
            f"rc={proc.returncode} stdout={proc.stdout!r} stderr={proc.stderr.strip()[:400]}",
        )
        check(
            "says on stderr that expected-repos.txt was missing",
            "expected-repos.txt is missing" in proc.stderr,
            f"stderr={proc.stderr.strip()[:400]}",
        )


def test_happy_and_missing_repo_paths(command: str) -> None:
    print("\n=== the populated paths still count what they always counted ===")

    with tempfile.TemporaryDirectory() as tmp:
        wd = make_working_dir(Path(tmp), expected=["a", "b"], analyzed=["a", "b"])
        proc = run(command, wd)
        obj = parsed_stdout(proc)
        check(
            "all repos analysed -> all_complete true, still_missing 0",
            proc.returncode == 0
            and isinstance(obj, dict)
            and obj.get("all_complete") is True
            and obj.get("still_missing") == 0,
            f"rc={proc.returncode} obj={obj!r} stderr={proc.stderr.strip()[:400]}",
        )

    with tempfile.TemporaryDirectory() as tmp:
        wd = make_working_dir(Path(tmp), expected=["a", "b", "c"], analyzed=["a", "c"])
        proc = run(command, wd)
        obj = parsed_stdout(proc)
        check(
            "one repo missing -> all_complete false, still_missing 1",
            proc.returncode == 0
            and isinstance(obj, dict)
            and obj.get("all_complete") is False
            and obj.get("still_missing") == 1,
            f"rc={proc.returncode} obj={obj!r} stderr={proc.stderr.strip()[:400]}",
        )
        check(
            "names the missing repo",
            isinstance(obj, dict) and obj.get("repos") == ["b"],
            f"obj={obj!r}",
        )

    with tempfile.TemporaryDirectory() as tmp:
        wd = make_working_dir(Path(tmp), expected=["a"], analyzed=["a"])
        proc = run(command, wd)
        obj = parsed_stdout(proc)
        check(
            "chunk/commit/pr intermediates are not counted as analysed repos",
            proc.returncode == 0 and isinstance(obj, dict) and obj.get("still_missing") == 0,
            f"rc={proc.returncode} obj={obj!r}",
        )


def test_self_validating_shape_guard(command: str) -> None:
    print("\n=== the step validates its OWN output and fails naming ITSELF ===")

    marker = "if ! printf '%s' \"$payload\" | jq -e 'type == \"object\"'"
    check("the shape guard is present in the step", marker in command, "guard not found")
    if marker not in command:
        return

    head, _, tail = command.partition(marker)
    for label, bad_payload in (
        ("a bare string", '"just a string"'),
        ("an array", "[]"),
        ("unparseable text", "not json at all"),
    ):
        # Run the step's REAL guard code, with the payload forced to a
        # non-object right before it. Everything up to the guard is the step's
        # own text, unmodified.
        injected = f"{head}payload='{bad_payload}'\n      {marker}{tail}"
        with tempfile.TemporaryDirectory() as tmp:
            wd = make_working_dir(Path(tmp), expected=[], analyzed=[])
            proc = run(injected, wd)
            check(
                f"{label} -> non-zero exit",
                proc.returncode != 0,
                f"rc={proc.returncode} stdout={proc.stdout!r}",
            )
            check(
                f"{label} -> stderr names 'set-final-validation'",
                "set-final-validation" in proc.stderr,
                f"stderr={proc.stderr.strip()[:400]}",
            )
            check(
                f"{label} -> stderr says it is not a JSON object",
                "not a JSON object" in proc.stderr,
                f"stderr={proc.stderr.strip()[:400]}",
            )
            check(
                f"{label} -> emits nothing on stdout",
                proc.stdout.strip() == "",
                f"stdout={proc.stdout!r}",
            )


def test_step_declarations(step: dict) -> None:
    print("\n=== the step's declarations keep the failure attached to it ===")
    check("step is a bash step", step.get("type") == "bash", f"type={step.get('type')!r}")
    check("parse_json is set", step.get("parse_json") is True, f"parse_json={step.get('parse_json')!r}")
    check(
        "on_error is 'fail' -- 'continue' is what substituted an unusable value",
        step.get("on_error") == "fail",
        f"on_error={step.get('on_error')!r}",
    )


def test_consumer_zero_activity_report(consumer: dict) -> None:
    print("\n=== the consumer reports 'no activity' rather than a hollow report ===")
    command = consumer["command"]
    check(
        "assemble-report still reads final_validation.still_missing",
        "{{final_validation.still_missing}}" in command,
        "the consumer this step feeds no longer indexes into final_validation",
    )
    check(
        "writes an explicit no-activity note when zero repos had activity",
        "No activity found." in command and "repos_with_activity" in command,
        "no zero-activity branch found in assemble-report",
    )
    check(
        "key_highlights is read with a // [] default",
        "(.key_highlights // [])[]" in command,
        "an LLM object without key_highlights would abort assemble-report",
    )
    check(
        "cross_cutting_observations is read with a // [] default",
        "(.cross_cutting_observations // [])[]" in command,
        "an LLM object without cross_cutting_observations would abort assemble-report",
    )


def main() -> int:
    print(f"Testing {STEP_ID} in {RECIPE.relative_to(REPO_ROOT)}")
    step = get_step(STEP_ID)
    command = step["command"]

    test_step_declarations(step)
    test_zero_repos_path(command)
    test_missing_expected_file(command)
    test_happy_and_missing_repo_paths(command)
    test_self_validating_shape_guard(command)
    test_consumer_zero_activity_report(get_step(CONSUMER_ID))

    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s)")
        for name in FAILURES:
            print(f"  - {name}")
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
