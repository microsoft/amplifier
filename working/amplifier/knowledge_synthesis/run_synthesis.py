#!/usr/bin/env python3
"""
Run knowledge synthesis - simple runner for Makefile.
"""

import argparse
import os
import sys

from amplifier.utils.notifications import send_notification

from .synthesis_engine import SynthesisEngine


def main():
    """Run synthesis and print summary."""
    # Parse arguments
    parser = argparse.ArgumentParser(description="Run knowledge synthesis")
    parser.add_argument("--notify", action="store_true", help="Send desktop notifications")
    args = parser.parse_args()

    try:
        # Initialize synthesis engine
        engine = SynthesisEngine()

        # Run synthesis
        results = engine.run_synthesis()

        # Print summary
        engine.print_summary(results)

        # Send completion notification
        if args.notify:
            entity_count = len(results.get("entity_resolutions", []))
            tension_count = len(results.get("contradictions", []))
            insight_count = len(results.get("emergent_insights", []))

            send_notification(
                title="Amplifier",
                message=f"Found {entity_count} entities, {tension_count} tensions, {insight_count} insights",
                cwd=os.getcwd(),
            )

        return 0

    except KeyboardInterrupt:
        if args.notify:
            send_notification(
                title="Amplifier",
                message="Synthesis interrupted by user",
                cwd=os.getcwd(),
            )
        return 1

    except Exception as e:
        if args.notify:
            send_notification(
                title="Amplifier",
                message=f"Synthesis failed: {str(e)[:100]}",
                cwd=os.getcwd(),
            )
        raise


if __name__ == "__main__":
    sys.exit(main())
