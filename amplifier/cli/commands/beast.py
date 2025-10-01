"""BEAST Framework CLI commands for Amplifier."""

import json
import sys
import time
from pathlib import Path

import click

from amplifier.beast.continuous_validation import ContinuousValidator
from amplifier.beast.contracts import BehavioralContract
from amplifier.beast.contracts import ContractVerifier
from amplifier.beast.example_contracts import CommandExistsContract
from amplifier.beast.example_contracts import create_amplifier_contracts
from amplifier.beast.mutation_testing import quick_mutation_test


def load_project_contracts() -> list[BehavioralContract]:
    """Load contracts for the current project."""
    # Check if we're in the Amplifier project
    if Path("amplifier/__init__.py").exists():
        return create_amplifier_contracts()

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


@click.group()
def beast():
    """BEAST Framework - AI-resistant behavioral testing."""
    pass


@beast.command()
@click.option("--contract", help='Specific contract to run (e.g., "cmd:python")')
@click.option("--verbose", is_flag=True, help="Verbose output")
@click.option("--output", help="Output report to JSON file")
def run(contract, verbose, output):
    """Run behavioral contracts."""
    click.echo("=" * 60)
    click.echo("BEAST FRAMEWORK - BEHAVIORAL CONTRACT VERIFICATION")
    click.echo("=" * 60)

    contracts = load_project_contracts()

    # Filter if specific contract requested
    if contract:
        contracts = [c for c in contracts if contract in c.name]
        if not contracts:
            click.echo(f"No contract matching '{contract}' found", err=True)
            sys.exit(1)

    click.echo(f"\nLoaded {len(contracts)} contracts\n")

    # Run verification
    verifier = ContractVerifier()
    for c in contracts:
        verifier.add_contract(c)

    report = verifier.verify_all(verbose=verbose)

    # Save report if requested
    if output:
        with open(output, "w") as f:
            clean_report = {"summary": report["summary"], "results": report["results"]}
            json.dump(clean_report, f, indent=2)
        click.echo(f"\nReport saved to {output}")

    # Return appropriate exit code
    sys.exit(0 if report["summary"]["failed"] == 0 else 1)


@beast.command()
@click.option("--quick", is_flag=True, help="Run quick mutation test")
@click.option("--source", help="Source directory for mutations")
def mutate(quick, source):
    """Run mutation testing."""
    if quick:
        click.echo("Running quick mutation test...")
        quick_mutation_test()
    else:
        click.echo("Full mutation testing not yet implemented")
        click.echo("Use --quick for a demonstration")


@beast.command()
@click.option("--interval", type=int, default=300, help="Validation interval in seconds (default: 300)")
@click.option("--db", default="beast_history.db", help="Database file for history (default: beast_history.db)")
def watch(interval, db):
    """Run continuous validation."""
    click.echo("=" * 60)
    click.echo("CONTINUOUS VALIDATION")
    click.echo("=" * 60)

    validator = ContinuousValidator(interval_seconds=interval, history_db=db)

    # Load contracts
    contracts = load_project_contracts()
    validator.contracts = contracts

    click.echo(f"\nMonitoring {len(contracts)} contracts")
    click.echo(f"Interval: {interval} seconds")
    click.echo(f"History: {db}")
    click.echo("\nPress Ctrl+C to stop...")

    try:
        validator.start()
        # Keep running until interrupted
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        click.echo("\nStopping...")
        validator.stop()


@beast.command("list")
def list_contracts():
    """List available contracts."""
    click.echo("Available Contracts:")
    click.echo("=" * 40)

    contracts = load_project_contracts()
    for contract in contracts:
        click.echo(f"  • {contract.name}")

    click.echo(f"\nTotal: {len(contracts)} contracts")
