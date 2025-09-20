#!/usr/bin/env python3
"""
Claude Code notification hook adapter.
Reads JSON from stdin and sends desktop notifications using the amplifier notification module.
"""

import json
import os
import sys
from pathlib import Path

# Add parent directory to path to import amplifier module
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))

from amplifier.utils.notifications.core import NotificationSender  # noqa: E402
from amplifier.utils.notifications.models import ClaudeCodeHookInput  # noqa: E402
from amplifier.utils.notifications.models import NotificationRequest  # noqa: E402


def main():
    """Main entry point for hook."""
    try:
        # Read JSON from stdin
        json_input = sys.stdin.read()

        # Parse hook data
        hook_data = ClaudeCodeHookInput.model_validate_json(json_input)

        # Check for debug mode (can be set via environment variable)
        debug = os.environ.get("CLAUDE_HOOK_DEBUG", "").lower() in ("true", "1", "yes")

        # Create sender and extract project name
        sender = NotificationSender(debug=debug)
        project_name = None
        if hook_data.cwd:
            project_name = sender._get_project_name(hook_data.cwd)

        # Create and send notification
        request = NotificationRequest(
            message=hook_data.message or "Notification",
            title="Claude Code",
            subtitle=project_name,
            session_id=hook_data.session_id,
            debug=debug,
        )

        response = sender.send(request)

        # Print debug info if enabled
        if debug and response.debug_log:
            print(f"[DEBUG] {response.debug_log}", file=sys.stderr)

        # Exit with appropriate code
        sys.exit(0 if response.success else 1)

    except json.JSONDecodeError as e:
        print(f"Error parsing JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error in notification hook: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
