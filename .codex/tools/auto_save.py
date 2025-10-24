#!/usr/bin/env python3
"""
Auto-save utility for periodic transcript saves.
Called by amplify-codex.sh every 10 minutes during active sessions.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from amplifier.core.backend import BackendFactory  # noqa: E402


def main():
    """Run periodic transcript save"""
    try:
        # Get backend
        backend = BackendFactory.create(backend_type="codex")

        # Export transcript
        result = backend.export_transcript()

        if result:
            print(f"Transcript auto-saved: {result}")
        else:
            print("No transcript to save")

    except Exception as e:
        print(f"Auto-save failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
