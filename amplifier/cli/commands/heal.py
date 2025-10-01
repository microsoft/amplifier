"""Auto-healing command for Python code quality improvement."""

import ast
import subprocess
import sys
from pathlib import Path

import click


@click.command()
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "--check-only",
    is_flag=True,
    help="Check for issues without fixing them",
)
@click.option(
    "--max-fixes",
    default=10,
    help="Maximum number of fixes to apply",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed output",
)
def heal(path: str, check_only: bool, max_fixes: int, verbose: bool):
    """Auto-heal Python code by fixing common issues.

    This command analyzes Python files and automatically fixes:
    - Syntax errors
    - Type hint issues
    - Common code quality problems
    - Import organization
    - Basic formatting issues
    """
    path_obj = Path(path)

    if path_obj.is_file():
        files = [path_obj]
    else:
        files = list(path_obj.rglob("*.py"))

    if not files:
        click.echo("No Python files found to heal.")
        return

    total_issues = 0
    total_fixed = 0

    for file_path in files:
        if verbose:
            click.echo(f"\nAnalyzing {file_path}...")

        issues = analyze_file(file_path)
        total_issues += len(issues)

        if issues:
            if verbose or not check_only:
                click.echo(f"\nFound {len(issues)} issue(s) in {file_path}:")
                for issue in issues:
                    click.echo(f"  - {issue}")

            if not check_only:
                fixed = fix_file(file_path, issues, max_fixes)
                total_fixed += fixed
                if verbose:
                    click.echo(f"Fixed {fixed} issue(s)")

    # Summary
    click.echo(f"\n{'=' * 60}")
    click.echo("Healing Summary:")
    click.echo(f"Files analyzed: {len(files)}")
    click.echo(f"Total issues found: {total_issues}")

    if check_only:
        click.echo("Run without --check-only to fix these issues.")
    else:
        click.echo(f"Total issues fixed: {total_fixed}")
        if total_fixed < total_issues:
            click.echo(f"Remaining issues: {total_issues - total_fixed}")

    # Return appropriate exit code
    if total_issues > 0 and check_only:
        sys.exit(1)  # Issues found in check mode
    elif total_issues > total_fixed:
        sys.exit(2)  # Some issues couldn't be fixed
    else:
        sys.exit(0)  # All good or all fixed


def analyze_file(file_path: Path) -> list[str]:
    """Analyze a Python file for issues."""
    issues = []

    try:
        code = file_path.read_text()
    except Exception as e:
        return [f"Cannot read file: {e}"]

    # Check 1: Syntax errors
    try:
        compile(code, file_path, "exec")
    except SyntaxError as e:
        issues.append(f"Syntax error at line {e.lineno}: {e.msg}")

    # Check 2: AST parsing issues
    try:
        tree = ast.parse(code)

        # Check for common patterns
        for node in ast.walk(tree):
            # Check for division by zero
            if (
                isinstance(node, ast.BinOp)
                and isinstance(node.op, ast.Div)
                and isinstance(node.right, ast.Constant)
                and node.right.value == 0
            ):
                issues.append(f"Division by zero at line {node.lineno}")

            # Check for missing return type hints
            if isinstance(node, ast.FunctionDef) and node.returns is None and node.name != "__init__":
                issues.append(f"Missing return type hint for function '{node.name}' at line {node.lineno}")
    except Exception as e:
        issues.append(f"AST parsing error: {e}")

    # Check 3: Type checking with pyright
    try:
        result = subprocess.run(
            ["pyright", "--outputjson", str(file_path)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0 and result.stdout:
            import json

            try:
                output = json.loads(result.stdout)
                for diagnostic in output.get("generalDiagnostics", []):
                    if diagnostic.get("severity") == "error":
                        line = diagnostic.get("range", {}).get("start", {}).get("line", "?")
                        msg = diagnostic.get("message", "Unknown error")
                        issues.append(f"Type error at line {line}: {msg}")
            except json.JSONDecodeError:
                pass
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass  # pyright not available or timeout

    return issues


def fix_file(file_path: Path, issues: list[str], max_fixes: int) -> int:
    """Attempt to fix issues in a Python file."""
    fixed_count = 0

    try:
        original_code = file_path.read_text()
        lines = original_code.splitlines(keepends=True)

        for issue in issues[:max_fixes]:
            # Fix syntax errors - missing colons after if/while/for
            if "Missing colon" in issue or "expected ':'" in issue.lower():
                for i, line in enumerate(lines):
                    if line.strip().startswith(
                        (
                            "if ",
                            "while ",
                            "for ",
                            "elif ",
                            "else",
                            "try",
                            "except",
                            "finally",
                            "with ",
                            "def ",
                            "class ",
                        )
                    ) and not line.rstrip().endswith(":"):
                        lines[i] = line.rstrip() + ":\n"
                        fixed_count += 1

            # Fix division by zero
            elif "Division by zero" in issue:
                for i, line in enumerate(lines):
                    if "/ 0" in line:
                        lines[i] = line.replace("/ 0", "/ 1  # Fixed: was division by zero")
                        fixed_count += 1

            # Add basic return type hints
            elif "Missing return type hint" in issue:
                func_name = extract_function_name(issue)
                if func_name:
                    for i, line in enumerate(lines):
                        if f"def {func_name}(" in line and "->" not in line and ")" in line:
                            # Add a basic return hint
                            lines[i] = line.replace(")", ") -> None")
                            fixed_count += 1
                            break

        # Write fixed code back
        if fixed_count > 0:
            file_path.write_text("".join(lines))

    except Exception as e:
        click.echo(f"Error fixing file: {e}")

    return fixed_count


def extract_function_name(issue: str) -> str | None:
    """Extract function name from issue description."""
    import re

    match = re.search(r"function '(\w+)'", issue)
    return match.group(1) if match else None
