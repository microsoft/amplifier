#!/usr/bin/env python3
"""
Codex session monitor helper script - provides command-line access to token monitoring.
Standalone script for checking token usage and requesting termination.
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add amplifier to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from amplifier.session_monitor.token_tracker import TokenTracker
    from amplifier.session_monitor.models import TerminationRequest, TerminationReason, TerminationPriority
except ImportError as e:
    print(f"Failed to import session monitor modules: {e}", file=sys.stderr)
    # Exit gracefully to not break wrapper
    sys.exit(1)


def check_token_budget():
    """Check current token usage and print status to stdout.

    Returns:
        Exit code: 0=OK, 1=warning, 2=critical
    """
    try:
        workspace_id = get_workspace_id()
        tracker = TokenTracker()
        usage = tracker.get_current_usage(workspace_id)

        if usage.source == 'no_files':
            print(f"No session files found for workspace '{workspace_id}'")
            return 0

        # Determine status
        if usage.usage_pct >= 90:
            status = "CRITICAL"
            exit_code = 2
        elif usage.usage_pct >= 80:
            status = "WARNING"
            exit_code = 1
        else:
            status = "OK"
            exit_code = 0

        print(f"Token Status: {status}")
        print(f"Estimated tokens: {usage.estimated_tokens:,}")
        print(f"Usage percentage: {usage.usage_pct:.1f}%")
        print(f"Source: {usage.source}")

        return exit_code

    except Exception as e:
        print(f"Error checking token budget: {e}", file=sys.stderr)
        return 1


def request_termination(reason, continuation_cmd, priority='graceful'):
    """Create a termination request file.

    Args:
        reason: Termination reason
        continuation_cmd: Command to restart session
        priority: Termination priority
    """
    try:
        workspace_id = get_workspace_id()

        # Get current token usage
        tracker = TokenTracker()
        usage = tracker.get_current_usage(workspace_id)

        # Get current process ID
        pid = os.getpid()

        # Validate inputs
        try:
            termination_reason = TerminationReason(reason)
            termination_priority = TerminationPriority(priority)
        except ValueError as e:
            print(f"Invalid reason or priority: {e}", file=sys.stderr)
            print(f"Valid reasons: {[r.value for r in TerminationReason]}", file=sys.stderr)
            print(f"Valid priorities: {[p.value for p in TerminationPriority]}", file=sys.stderr)
            sys.exit(1)

        # Create termination request
        request = TerminationRequest(
            reason=termination_reason,
            continuation_command=continuation_cmd,
            priority=termination_priority,
            token_usage_pct=usage.usage_pct,
            pid=pid,
            workspace_id=workspace_id
        )

        # Write to file
        workspace_dir = Path(".codex/workspaces") / workspace_id
        workspace_dir.mkdir(parents=True, exist_ok=True)
        request_file = workspace_dir / "termination-request"

        with open(request_file, 'w') as f:
            json.dump(request.model_dump(), f, indent=2)

        print(f"✓ Termination request created: {request_file}")
        print(f"  Reason: {reason}")
        print(f"  Priority: {priority}")
        print(f"  Token usage: {usage.usage_pct:.1f}%")
        print(f"  Continuation: {continuation_cmd}")

    except Exception as e:
        print(f"Error creating termination request: {e}", file=sys.stderr)
        sys.exit(1)


def get_workspace_id():
    """Auto-detect workspace ID from current directory or environment variables.

    Returns:
        Workspace identifier string
    """
    # Check environment variable first
    workspace_id = os.getenv("CODEX_WORKSPACE_ID")
    if workspace_id:
        return workspace_id

    # Use current directory name
    return Path.cwd().name


def main():
    parser = argparse.ArgumentParser(description="Session monitor helper for token tracking")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # check-tokens command
    subparsers.add_parser('check-tokens', help='Check current token usage')

    # request-termination command
    term_parser = subparsers.add_parser('request-termination', help='Request session termination')
    term_parser.add_argument('--reason', required=True,
                           choices=[r.value for r in TerminationReason],
                           help='Reason for termination')
    term_parser.add_argument('--continuation-command', required=True,
                           help='Command to restart the session')
    term_parser.add_argument('--priority',
                           choices=[p.value for p in TerminationPriority],
                           default='graceful',
                           help='Termination priority')

    args = parser.parse_args()

    if args.command == 'check-tokens':
        exit_code = check_token_budget()
        sys.exit(exit_code)
    elif args.command == 'request-termination':
        request_termination(args.reason, args.continuation_command, args.priority)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()