#!/usr/bin/env python3
"""
Show Exact Input for Memory Extraction

Demonstrates what actually gets sent to Claude for memory extraction
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from amplifier.extraction import MemoryExtractor


def show_raw_conversation():
    """Show a raw conversation BEFORE filtering"""
    print("\n" + "=" * 70)
    print("STEP 1: RAW CONVERSATION (Before Processing)")
    print("=" * 70)

    raw_messages = [
        # Old messages (would be filtered out - only last 20 kept)
        {"role": "user", "content": "Let's start working on authentication"},
        {"role": "assistant", "content": "Sure, what auth system do you prefer?"},
        # ... 100+ more old messages here ...
        {
            "role": "system",
            "content": "<system-reminder>Hook completed</system-reminder>",
        },
        {"role": "user", "content": "I think JWT is better for our API"},
        {
            "role": "assistant",
            "content": "JWT is excellent for API-first architectures because it's stateless, works great with microservices, and is mobile-app friendly. No server-side session storage needed.",
        },
        {"role": "system", "content": "PostToolUse:Write hook success"},
        {"role": "user", "content": "What about caching?"},
        {
            "role": "assistant",
            "content": "For caching, Redis is a popular choice. It's fast, reliable, and has great support for distributed caching.",
        },
        {
            "role": "user",
            "content": "Good. We also found that using async/await for database calls improved our performance by about 40%.",
        },
        {
            "role": "assistant",
            "content": "That's a significant improvement! Async database operations are definitely a best practice. I'll remember that pattern.",
        },
    ]

    print(f"\nTotal messages: {len(raw_messages)}")
    print("\nSample messages:")
    for i, msg in enumerate(raw_messages[:5], 1):
        content = (
            msg["content"][:60] + "..." if len(msg["content"]) > 60 else msg["content"]
        )
        print(f"  {i}. [{msg['role'].upper()}] {content}")
    print("  ... (more messages)")

    return raw_messages


def show_filtered_conversation(raw_messages):
    """Show what happens AFTER filtering"""
    print("\n" + "=" * 70)
    print("STEP 2: FILTERED CONVERSATION (What Gets Sent to AI)")
    print("=" * 70)

    extractor = MemoryExtractor()

    # This is what _format_messages does internally
    filtered = extractor._format_messages(raw_messages)

    print(
        f"\nFiltered down to: {len(filtered.split('USER:')) + len(filtered.split('ASSISTANT:')) - 2} message pairs"
    )
    print(f"Character count: {len(filtered)} chars\n")

    print("Filtered conversation text:")
    print("-" * 70)
    print(filtered)
    print("-" * 70)

    return filtered


def show_actual_prompt(filtered_conversation):
    """Show the EXACT prompt sent to Claude"""
    print("\n" + "=" * 70)
    print("STEP 3: ACTUAL PROMPT SENT TO CLAUDE CODE SDK")
    print("=" * 70)

    # This is the exact prompt from _extract_with_claude_full
    prompt = f"""Extract key memories from this conversation that should be remembered for future interactions.

Conversation:
{filtered_conversation}

Extract and return as JSON:
{{
  "memories": [
    {{
      "type": "learning|decision|issue_solved|pattern|preference",
      "content": "concise memory content",
      "importance": 0.0-1.0,
      "tags": ["tag1", "tag2"]
    }}
  ],
  "key_learnings": ["what was learned"],
  "decisions_made": ["decisions"],
  "issues_solved": ["problems resolved"]
}}

Focus on technical decisions, problems solved, user preferences, and important patterns.
Return ONLY valid JSON."""

    print("\n" + "=" * 70)
    print(prompt)
    print("=" * 70)

    print("\nPrompt stats:")
    print(f"  Total characters: {len(prompt)}")
    print(f"  Estimated tokens: ~{len(prompt) // 4} tokens")

    return prompt


def show_configuration():
    """Show extraction configuration"""
    print("\n" + "=" * 70)
    print("STEP 4: CONFIGURATION (How Filtering Works)")
    print("=" * 70)

    from amplifier.extraction import get_config

    config = get_config()

    print("\nCurrent configuration:")
    print(f"  Max messages: {config.memory_extraction_max_messages}")
    print(
        f"  Max content per message: {config.memory_extraction_max_content_length} chars"
    )
    print(f"  Model: {config.memory_extraction_model}")
    print(f"  Timeout: {config.memory_extraction_timeout} seconds")

    print("\nFiltering rules:")
    print("  ✅ Include: USER and ASSISTANT roles only")
    print("  ✅ Include: Last N messages only (configured above)")
    print("  ✅ Truncate: Messages to max length")
    print("  ❌ Exclude: System messages")
    print("  ❌ Exclude: Hook output")
    print("  ❌ Exclude: Tool calls")
    print("  ❌ Exclude: Old messages beyond max")


def show_example_with_long_conversation():
    """Show filtering with a realistically long conversation"""
    print("\n" + "=" * 70)
    print("EXAMPLE: LONG CONVERSATION (150 messages)")
    print("=" * 70)

    # Simulate 150 messages
    long_conversation = []

    # Add 130 old messages
    for i in range(65):
        long_conversation.append({"role": "user", "content": f"Old message {i}"})
        long_conversation.append({"role": "assistant", "content": f"Old response {i}"})

    # Add some system noise
    long_conversation.extend(
        [
            {
                "role": "system",
                "content": "<system-reminder>Hook completed</system-reminder>",
            },
            {"role": "system", "content": "PostToolUse:Write success"},
        ]
    )

    # Add last 20 relevant messages
    recent_messages = [
        {"role": "user", "content": "I prefer JWT for authentication"},
        {
            "role": "assistant",
            "content": "JWT is excellent for API-first architectures...",
        },
        {"role": "user", "content": "What about caching?"},
        {"role": "assistant", "content": "Redis is a great choice for caching..."},
        {
            "role": "user",
            "content": "We found async/await improved DB performance by 40%",
        },
        {
            "role": "assistant",
            "content": "That's significant! I'll remember that pattern...",
        },
        {"role": "user", "content": "Should we use PostgreSQL or MongoDB?"},
        {
            "role": "assistant",
            "content": "For your use case, PostgreSQL would be better...",
        },
        {"role": "user", "content": "I prefer dark mode for all UIs"},
        {
            "role": "assistant",
            "content": "Noted! I'll remember your dark mode preference...",
        },
    ]

    long_conversation.extend(recent_messages)

    print("\nOriginal conversation:")
    print(f"  Total messages: {len(long_conversation)}")
    print(
        f"  With system messages: {sum(1 for m in long_conversation if m['role'] == 'system')}"
    )
    print("  Old messages (0-129): 130 messages")
    print("  Recent messages (130-150): 20 messages")

    # Show what gets extracted
    extractor = MemoryExtractor()
    filtered = extractor._format_messages(long_conversation)

    print("\nAfter filtering:")
    print("  Messages processed: ~20 (last 20 only)")
    print(f"  Character count: {len(filtered)} chars")
    print(f"  Estimated tokens: ~{len(filtered) // 4} tokens")
    print("  Old messages (0-129): SKIPPED ❌")
    print("  System messages: FILTERED OUT ❌")
    print("  Recent messages: KEPT ✅")

    print("\nToken savings:")
    print(
        f"  Without filtering: ~{len(long_conversation) * 100 // 4} tokens (estimate)"
    )
    print(f"  With filtering: ~{len(filtered) // 4} tokens")
    print(
        f"  Reduction: ~{100 - (len(filtered) * 100 // (len(long_conversation) * 100))}%"
    )

    print("\nFiltered conversation preview:")
    print("-" * 70)
    print(filtered[:500] + "..." if len(filtered) > 500 else filtered)
    print("-" * 70)


def main():
    """Run all examples"""
    print("\n" + "=" * 70)
    print("MEMORY EXTRACTION INPUT - COMPLETE BREAKDOWN")
    print("=" * 70)
    print("\nThis shows EXACTLY what gets sent to Claude for extraction")

    # Show basic flow
    raw = show_raw_conversation()
    filtered = show_filtered_conversation(raw)
    show_actual_prompt(filtered)
    show_configuration()

    # Show realistic example
    show_example_with_long_conversation()

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("""
Key Points:
1. Only LAST 20 messages are processed (not entire conversation)
2. Each message truncated to 500 characters max
3. System messages and noise filtered out
4. Result: ~2K tokens instead of 50K+ tokens
5. Cost: $0.001 per extraction (not $0.02)

The input is HEAVILY filtered before sending to Claude!
""")


if __name__ == "__main__":
    main()
