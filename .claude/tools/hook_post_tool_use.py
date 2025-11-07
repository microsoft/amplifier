#!/usr/bin/env python3
"""
Claude Code hook for PostToolUse events - minimal wrapper for claim validation.
Reads JSON from stdin, calls amplifier modules, writes JSON to stdout.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add amplifier to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import logger from the same directory
sys.path.insert(0, str(Path(__file__).parent))
from hook_logger import HookLogger

logger = HookLogger("post_tool_use")

try:
    from amplifier.memory import MemoryStore
    from amplifier.validation import ClaimValidator

    # Import token tracker if available
    try:
        from amplifier.session_monitor.token_tracker import TokenTracker

        TOKEN_MONITORING_AVAILABLE = True
    except ImportError:
        TOKEN_MONITORING_AVAILABLE = False
        logger.debug("Token monitoring not available")
except ImportError as e:
    logger.error(f"Failed to import amplifier modules: {e}")
    # Exit gracefully to not break hook chain
    json.dump({}, sys.stdout)
    sys.exit(0)


async def main():
    """Read input, validate claims, return warnings if contradictions found"""
    try:
        # Check if memory system is enabled
        import os

        memory_enabled = os.getenv("MEMORY_SYSTEM_ENABLED", "false").lower() in ["true", "1", "yes"]
        if not memory_enabled:
            logger.info("Memory system disabled via MEMORY_SYSTEM_ENABLED env var")
            # Return empty response and exit gracefully
            json.dump({}, sys.stdout)
            return

        logger.info("Starting claim validation")
        logger.cleanup_old_logs()  # Clean up old logs on each run

        # Read JSON input
        raw_input = sys.stdin.read()
        logger.info(f"Received input length: {len(raw_input)}")

        input_data = json.loads(raw_input)

        # Extract message
        message = input_data.get("message", {})
        role = message.get("role", "")
        content = message.get("content", "")

        logger.debug(f"Message role: {role}")
        logger.debug(f"Content length: {len(content)}")

        # Skip if not assistant message or too short
        if role != "assistant" or not content or len(content) < 50:
            logger.info(f"Skipping: role={role}, content_len={len(content)}")
            json.dump({}, sys.stdout)
            return

        # Initialize modules
        logger.info("Initializing store and validator")
        store = MemoryStore()
        validator = ClaimValidator()

        # Get all memories for validation
        memories = store.get_all()
        logger.info(f"Total memories for validation: {len(memories)}")

        # Validate text for claims
        logger.info("Validating text for claims")
        validation_result = validator.validate_text(content, memories)
        logger.info(f"Has contradictions: {validation_result.has_contradictions}")
        logger.info(f"Claims found: {len(validation_result.claims)}")

        # Build response if contradictions found
        output = {}
        if validation_result.has_contradictions:
            warnings = []
            for claim_validation in validation_result.claims:
                if claim_validation.contradicts and claim_validation.confidence > 0.6:
                    claim_text = claim_validation.claim[:100]
                    warnings.append(f"⚠️ Claim may be incorrect: '{claim_text}...'")

                    if claim_validation.evidence:
                        evidence = claim_validation.evidence[0][:150]
                        warnings.append(f"   Memory says: {evidence}")

            if warnings:
                output = {
                    "warning": "\n".join(warnings),
                    "metadata": {
                        "contradictionsFound": sum(1 for c in validation_result.claims if c.contradicts),
                        "claimsChecked": len(validation_result.claims),
                        "source": "amplifier_validation",
                    },
                }

        json.dump(output, sys.stdout)

        if output:
            logger.info(f"Returned {len(warnings) if 'warnings' in locals() else 0} warnings")
        else:
            logger.info("No contradictions found")

        # Token monitoring (if available)
        if TOKEN_MONITORING_AVAILABLE:
            token_monitoring_enabled = os.getenv("TOKEN_MONITORING_ENABLED", "true").lower() in ["true", "1", "yes"]
            if token_monitoring_enabled:
                try:
                    logger.debug("Checking token usage")
                    tracker = TokenTracker()

                    # Auto-detect workspace from current directory
                    workspace_id = Path.cwd().name
                    usage = tracker.get_current_usage(workspace_id)

                    if usage.source != "no_files":
                        # Log token usage
                        logger.info(f"Token usage: {usage.usage_pct:.1f}% ({usage.estimated_tokens:,} tokens)")

                        # Check thresholds and take action
                        if usage.usage_pct >= 90:
                            # Critical - create termination request
                            logger.warning(
                                f"Token usage critical ({usage.usage_pct:.1f}%), creating termination request"
                            )
                            try:
                                import os

                                from amplifier.session_monitor.models import TerminationPriority
                                from amplifier.session_monitor.models import TerminationReason
                                from amplifier.session_monitor.models import TerminationRequest

                                request = TerminationRequest(
                                    reason=TerminationReason.TOKEN_LIMIT_APPROACHING,
                                    continuation_command="claude --continue-session",  # Generic continuation
                                    priority=TerminationPriority.GRACEFUL,
                                    token_usage_pct=usage.usage_pct,
                                    pid=os.getpid(),
                                    workspace_id=workspace_id,
                                )

                                # Write to file
                                workspace_dir = Path(".codex/workspaces") / workspace_id
                                workspace_dir.mkdir(parents=True, exist_ok=True)
                                request_file = workspace_dir / "termination-request"

                                with open(request_file, "w") as f:
                                    json.dump(request.model_dump(), f, indent=2)

                                logger.info(f"Termination request created: {request_file}")

                            except Exception as e:
                                logger.error(f"Failed to create termination request: {e}")

                        elif usage.usage_pct >= 80:
                            # Warning - log to stderr for user visibility
                            warning_msg = (
                                f"⚠️ Token usage high: {usage.usage_pct:.1f}% ({usage.estimated_tokens:,} tokens)"
                            )
                            print(warning_msg, file=sys.stderr)
                            logger.warning(warning_msg)

                            # Also write to warning file
                            try:
                                workspace_dir = Path(".codex/workspaces") / workspace_id
                                workspace_dir.mkdir(parents=True, exist_ok=True)
                                warning_file = workspace_dir / "token_warning.txt"

                                with open(warning_file, "a") as f:
                                    f.write(f"{usage.timestamp.isoformat()}: {warning_msg}\n")

                            except Exception as e:
                                logger.error(f"Failed to write warning file: {e}")

                        # Record usage in history
                        try:
                            history_file = Path(".codex/workspaces") / workspace_id / "token_history.jsonl"
                            history_file.parent.mkdir(parents=True, exist_ok=True)

                            history_entry = {
                                "timestamp": usage.timestamp.isoformat(),
                                "estimated_tokens": usage.estimated_tokens,
                                "usage_pct": usage.usage_pct,
                                "source": usage.source,
                            }

                            with open(history_file, "a") as f:
                                f.write(json.dumps(history_entry) + "\n")

                        except Exception as e:
                            logger.error(f"Failed to record token history: {e}")

                except Exception as e:
                    logger.error(f"Error during token monitoring: {e}")

    except Exception as e:
        logger.exception("Error during claim validation", e)
        json.dump({}, sys.stdout)


if __name__ == "__main__":
    asyncio.run(main())
