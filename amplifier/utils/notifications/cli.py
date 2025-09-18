"""
CLI interface for notification system.
"""

import argparse
import json
import sys

from .core import NotificationSender
from .models import ClaudeCodeHookInput
from .models import NotificationRequest


def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(description="Send desktop notifications")
    parser.add_argument("message", nargs="?", help="Notification message")
    parser.add_argument("-t", "--title", default="Claude Code", help="Notification title")
    parser.add_argument("-s", "--subtitle", help="Notification subtitle (e.g., project name)")
    parser.add_argument("--session-id", help="Session ID for tracking")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--hook", action="store_true", help="Read Claude Code hook JSON from stdin")
    parser.add_argument("--test", action="store_true", help="Test notification on current platform")

    args = parser.parse_args()

    # Test mode
    if args.test:
        sender = NotificationSender(debug=True)
        request = NotificationRequest(
            message="Test notification from amplifier notification system",
            title="Test Notification",
            subtitle="Test Project",
            debug=True,
        )
        response = sender.send(request)
        print(f"Platform: {response.platform}")
        print(f"Success: {response.success}")
        if response.error:
            print(f"Error: {response.error}")
        if response.fallback_used:
            print("Fallback to console was used")
        if response.debug_log:
            print("\nDebug log:")
            print(response.debug_log)
        return

    # Hook mode - read JSON from stdin
    if args.hook:
        try:
            json_input = sys.stdin.read()
            hook_data = ClaudeCodeHookInput.model_validate_json(json_input)

            # Extract project name from cwd
            sender = NotificationSender(debug=args.debug)
            project_name = None
            if hook_data.cwd:
                project_name = sender._get_project_name(hook_data.cwd)

            # Create notification request
            request = NotificationRequest(
                message=hook_data.message or "Notification",
                title="Claude Code",
                subtitle=project_name,
                session_id=hook_data.session_id,
                debug=args.debug,
            )

            response = sender.send(request)
            if args.debug and response.debug_log:
                print(response.debug_log, file=sys.stderr)

            sys.exit(0 if response.success else 1)

        except json.JSONDecodeError as e:
            print(f"Error parsing JSON input: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    # Normal CLI mode
    if not args.message:
        parser.error("Message is required unless using --hook or --test mode")

    sender = NotificationSender(debug=args.debug)
    request = NotificationRequest(
        message=args.message,
        title=args.title,
        subtitle=args.subtitle,
        session_id=args.session_id,
        debug=args.debug,
    )

    response = sender.send(request)
    if args.debug and response.debug_log:
        print(response.debug_log, file=sys.stderr)

    sys.exit(0 if response.success else 1)


if __name__ == "__main__":
    main()
