#!/usr/bin/env python3
"""
BEAST Framework CLI - Run behavioral contracts for any project.
"""

import argparse
import json
import sys
from pathlib import Path

from .contracts import BehavioralContract
from .contracts import ContractVerifier
from .example_contracts import CommandExistsContract
from .mutation_testing import quick_mutation_test


def create_parser():
    """Create argument parser for BEAST CLI."""
    parser = argparse.ArgumentParser(
        prog="beast",
        description="BEAST Framework - AI-resistant behavioral testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  beast run                     # Run all contracts
  beast run --contract cmd:uv   # Run specific contract
  beast mutate                  # Run mutation testing
  beast watch                   # Continuous validation
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run behavioral contracts")
    run_parser.add_argument("--contract", help='Specific contract to run (e.g., "cmd:python")')
    run_parser.add_argument("--verbose", action="store_true", help="Verbose output")
    run_parser.add_argument("--output", help="Output report to JSON file")

    # Mutate command
    mutate_parser = subparsers.add_parser("mutate", help="Run mutation testing")
    mutate_parser.add_argument("--quick", action="store_true", help="Run quick mutation test")
    mutate_parser.add_argument("--source", help="Source directory for mutations")

    # Watch command
    watch_parser = subparsers.add_parser("watch", help="Continuous validation")
    watch_parser.add_argument("--interval", type=int, default=300, help="Validation interval in seconds (default: 300)")
    watch_parser.add_argument(
        "--db", default="beast_history.db", help="Database file for history (default: beast_history.db)"
    )

    # List command
    subparsers.add_parser("list", help="List available contracts")

    return parser


def load_project_contracts() -> list[BehavioralContract]:
    """Load contracts for the current project."""
    # Check if we're in the Amplifier project
    if Path("amplifier/__init__.py").exists():
        # Use REAL contracts that test actual behavior
        from .amplifier_contracts import create_real_amplifier_contracts

        return create_real_amplifier_contracts()

    # Check for a beast_contracts.py file
    if Path("beast_contracts.py").exists():
        import importlib.util

        spec = importlib.util.spec_from_file_location("beast_contracts", "beast_contracts.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if hasattr(module, "create_contracts"):
            return module.create_contracts()

    # Default: just check basic commands
    return [
        CommandExistsContract("python"),
        CommandExistsContract("git"),
    ]


def run_contracts(args):
    """Run behavioral contracts."""
    print("=" * 60)
    print("BEAST FRAMEWORK - BEHAVIORAL CONTRACT VERIFICATION")
    print("=" * 60)

    contracts = load_project_contracts()

    # Filter if specific contract requested
    if args.contract:
        contracts = [c for c in contracts if args.contract in c.name]
        if not contracts:
            print(f"No contract matching '{args.contract}' found")
            return 1

    print(f"\nLoaded {len(contracts)} contracts\n")

    # Run verification
    verifier = ContractVerifier()
    for contract in contracts:
        verifier.add_contract(contract)

    report = verifier.verify_all(verbose=args.verbose)

    # Save report if requested
    if args.output:
        with open(args.output, "w") as f:
            clean_report = {"summary": report["summary"], "results": report["results"]}
            json.dump(clean_report, f, indent=2)
        print(f"\nReport saved to {args.output}")

    # Return appropriate exit code
    return 0 if report["summary"]["failed"] == 0 else 1


def run_mutation(args):
    """Run mutation testing."""
    if args.quick:
        print("Running quick mutation test...")
        quick_mutation_test()
    else:
        print("Full mutation testing not yet implemented")
        print("Use --quick for a demonstration")
    return 0


def run_watch(args):
    """Run continuous validation."""
    from .continuous_validation import ContinuousValidator

    print("=" * 60)
    print("CONTINUOUS VALIDATION")
    print("=" * 60)

    validator = ContinuousValidator(interval_seconds=args.interval, history_db=args.db)

    # Load contracts
    contracts = load_project_contracts()
    validator.contracts = contracts

    print(f"\nMonitoring {len(contracts)} contracts")
    print(f"Interval: {args.interval} seconds")
    print(f"History: {args.db}")
    print("\nPress Ctrl+C to stop...")

    try:
        validator.start()
        # Keep running until interrupted
        import time

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        validator.stop()

    return 0


def list_contracts(args):
    """List available contracts."""
    print("Available Contracts:")
    print("=" * 40)

    contracts = load_project_contracts()
    for contract in contracts:
        print(f"  • {contract.name}")

    print(f"\nTotal: {len(contracts)} contracts")
    return 0


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "run":
        return run_contracts(args)
    if args.command == "mutate":
        return run_mutation(args)
    if args.command == "watch":
        return run_watch(args)
    if args.command == "list":
        return list_contracts(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
