"""CLI interface for auto-healing."""

import argparse
import logging
from pathlib import Path

from amplifier.tools.auto_healer import heal_batch


def main() -> None:
    """Run auto-healing CLI."""
    args = _parse_args()
    logging.basicConfig(level=logging.INFO)

    results = heal_batch(args.max, args.threshold, args.project_root)
    _print_results(results)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Auto-heal Python modules")
    parser.add_argument("--max", type=int, default=1, help="Max modules to heal")
    parser.add_argument("--threshold", type=float, default=70, help="Health threshold")
    parser.add_argument("--project-root", type=Path, default=Path("."), help="Project root directory")
    return parser.parse_args()


def _print_results(results) -> None:
    for r in results:
        status = "✅" if r.status == "success" else "❌"
        print(f"{status} {Path(r.module_path).name}: {r.status}")


if __name__ == "__main__":
    main()
