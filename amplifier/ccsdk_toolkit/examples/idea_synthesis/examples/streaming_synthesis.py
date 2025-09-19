#!/usr/bin/env python3
"""
Example: Streaming Idea Synthesis

Demonstrates:
- Natural completion for long-running synthesis
- Real-time streaming output for visibility
- High max_turns for complex reasoning
- Progress callbacks for custom handling
"""

import asyncio

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionOptions


async def run_streaming_synthesis():
    """Example of using streaming synthesis for long-running operations."""

    print("=" * 60)
    print("STREAMING SYNTHESIS EXAMPLE")
    print("Demonstrates: Natural completion, streaming output, progress tracking")
    print("=" * 60)

    # Example 1: Simple streaming with natural completion
    print("\n1. Long-running synthesis with streaming output:")
    print("-" * 40)

    options = SessionOptions(
        system_prompt="You are a synthesis expert. Process complex documents thoroughly.",
        stream_output=True,  # Enable streaming for visibility
        max_turns=1,
    )

    async with ClaudeSession(options) as session:
        response = await session.query(
            "Analyze these key themes and count slowly from 1 to 10:\n"
            "- Trust through visibility\n"
            "- Natural completion over artificial limits\n"
            "- Progress tracking for confidence\n\n"
            "For each number, briefly explain one aspect of these themes."
        )

        print("\n\nResponse completed!")
        print(f"Total length: {len(response.content)} characters")
        if response.metadata:
            print(f"Metadata: {response.metadata}")

    # Example 2: Complex multi-turn reasoning
    print("\n\n2. Complex multi-turn synthesis (>100 turns supported):")
    print("-" * 40)

    # Track chunks for analysis
    chunks_received = []

    def progress_tracker(chunk: str):
        """Track progress without printing (for non-visual tracking)."""
        chunks_received.append(chunk)
        # Could update a progress bar, send to logging, etc.
        print(".", end="", flush=True)  # Simple progress indicator

    options = SessionOptions(
        system_prompt="You are analyzing complex interconnected ideas.",
        stream_output=False,  # Don't stream to stdout
        progress_callback=progress_tracker,  # Custom progress handling
        max_turns=150,  # High turn count for complex operations
    )

    async with ClaudeSession(options) as session:
        print("Processing", end="")
        response = await session.query(
            "Briefly list 5 key principles of the 'trust through visibility' philosophy. "
            "Keep it concise - just the principle names."
        )

        print("\n\nResponse completed!")
        print(f"Chunks received: {len(chunks_received)}")
        print(f"Response:\n{response.content}")

    # Example 3: Combining with the enhanced claude_helper
    print("\n\n3. Using enhanced query helper with streaming:")
    print("-" * 40)

    from amplifier.ccsdk_toolkit.examples.idea_synthesis.utils import query_claude_streaming

    print("Streaming synthesis:")
    result = await query_claude_streaming(
        prompt="Create a brief synthesis of these concepts:\n"
        "1. Watching progress provides confidence\n"
        "2. Natural completion allows operations to finish\n"
        "3. Trust emerges from visibility\n\n"
        "Synthesize into 2-3 sentences.",
        system_prompt="You are a concise synthesis expert.",
        on_chunk=lambda chunk: print(chunk, end="", flush=True),
    )

    print(f"\n\nFinal result length: {len(result)} characters")

    print("\n" + "=" * 60)
    print("STREAMING SYNTHESIS EXAMPLE COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_streaming_synthesis())
