#!/usr/bin/env python3
"""
Extract REAL memories from current Claude Code session

Uses actual session files from ~/.claude/projects/
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from amplifier.extraction import MemoryExtractor
from amplifier.memory import MemoryStore
from amplifier.search import MemorySearcher


def find_session_directory():
    """Find the current Claude Code session directory"""
    # For amplifier project
    project_dir = (
        Path.home() / ".claude" / "projects" / "-Users-max-Documents-GitHub-amplifier"
    )

    if project_dir.exists():
        return project_dir

    # Try to find it
    projects_dir = Path.home() / ".claude" / "projects"
    if projects_dir.exists():
        # Find directory with most recent activity
        dirs = [
            d for d in projects_dir.iterdir() if d.is_dir() and "amplifier" in d.name
        ]
        if dirs:
            return max(dirs, key=lambda d: d.stat().st_mtime)

    return None


def load_real_messages(session_dir: Path, limit: int = 50):
    """Load REAL messages from Claude Code session files"""
    print(f"\n📁 Reading from: {session_dir}")

    # Find all .jsonl files
    jsonl_files = list(session_dir.glob("*.jsonl"))
    print(f"📊 Found {len(jsonl_files)} message files")

    messages = []
    for jsonl_file in jsonl_files:
        try:
            with open(jsonl_file) as f:
                # Each line is a JSON object
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        # Extract message from wrapper
                        if "message" in data:
                            msg = data["message"]
                            msg["timestamp"] = data.get("timestamp")
                            msg["sessionId"] = data.get("sessionId")
                            messages.append(msg)
        except Exception as e:
            print(f"⚠️  Error reading {jsonl_file.name}: {e}")
            continue

    # Sort by timestamp if available
    def get_timestamp(msg):
        ts = (
            msg.get("timestamp") or msg.get("created_at") or "2000-01-01T00:00:00+00:00"
        )
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            # Ensure all datetimes are timezone-aware
            if dt.tzinfo is None:
                from datetime import timezone

                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, AttributeError):
            from datetime import timezone

            return datetime.min.replace(tzinfo=timezone.utc)

    messages.sort(key=get_timestamp)

    print(f"✅ Loaded {len(messages)} messages total")
    print(f"📅 Using last {limit} messages")

    return messages[-limit:]


async def extract_from_real_session():
    """Extract memories from REAL session data"""
    print("\n" + "=" * 70)
    print("EXTRACTING MEMORIES FROM REAL CLAUDE CODE SESSION")
    print("=" * 70)

    # Find session directory
    session_dir = find_session_directory()
    if not session_dir:
        print("\n❌ Could not find Claude Code session directory")
        return

    # Load real messages (use more for better context)
    messages = load_real_messages(session_dir, limit=200)

    if not messages:
        print("\n❌ No messages found in session")
        return

    print("\n" + "=" * 70)
    print("REAL MESSAGES FROM THIS SESSION")
    print("=" * 70)

    # Show sample of real messages
    print("\nShowing last 5 messages:")
    for i, msg in enumerate(messages[-5:], 1):
        role = msg.get("role", "unknown")
        content = msg.get("content", "")

        # Handle structured content
        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
            content = " ".join(text_parts)

        content_preview = content[:100] + "..." if len(content) > 100 else content
        print(f"\n{i}. [{role.upper()}]")
        print(f"   {content_preview}")

    # Extract memories using AI
    print("\n" + "=" * 70)
    print("EXTRACTING MEMORIES WITH AI")
    print("=" * 70)

    try:
        extractor = MemoryExtractor()

        print("\n🤖 Sending to Claude Code SDK for extraction...")
        print(f"   Processing {len(messages)} messages")

        result = await extractor.extract_from_messages(messages)

        if not result or "memories" not in result:
            print("\n⚠️  No memories extracted")
            return []

        memories = result["memories"]
        print(f"\n✅ Extracted {len(memories)} memories from REAL conversation\n")

        # Show extracted memories
        print("=" * 70)
        print("REAL EXTRACTED MEMORIES")
        print("=" * 70)

        for i, mem in enumerate(memories, 1):
            print(f"\n{i}. [{mem.get('type', 'unknown').upper()}]")
            print(f"   Content: {mem.get('content', 'N/A')}")
            print(f"   Importance: {mem.get('importance', 0)}")
            if mem.get("tags"):
                print(f"   Tags: {', '.join(mem.get('tags', []))}")

        return memories

    except RuntimeError as e:
        print(f"\n⚠️  Extraction requires Claude Code SDK: {e}")
        print("\nUsing fallback: showing what WOULD be extracted from real messages...")

        # Show what would be sent
        print("\n" + "=" * 70)
        print("REAL CONVERSATION THAT WOULD BE SENT FOR EXTRACTION")
        print("=" * 70)

        formatted = extractor._format_messages(messages)
        print(formatted[:1000] + "\n..." if len(formatted) > 1000 else formatted)
        print("\n📊 Stats:")
        print(f"   Characters: {len(formatted)}")
        print(f"   Estimated tokens: ~{len(formatted) // 4}")

        return []


async def store_real_memories(memories):
    """Store the real extracted memories"""
    if not memories:
        print("\n⚠️  No memories to store")
        return

    print("\n" + "=" * 70)
    print("STORING REAL MEMORIES")
    print("=" * 70)

    store = MemoryStore(data_dir=Path(".data"))

    print(f"\n💾 Current memory count: {len(store.get_all())}")

    # Convert to Memory objects and store
    from amplifier.memory import Memory

    # Map extracted categories to valid Memory categories
    category_map = {
        "philosophy": "pattern",  # Philosophy → pattern
        "approach": "pattern",  # Approach → pattern
        "best_practice": "pattern",  # Best practice → pattern
    }

    stored_count = 0
    for mem_data in memories:
        extracted_category = mem_data.get("type", "learning")
        # Map to valid category if needed
        valid_category = category_map.get(extracted_category, extracted_category)

        # Ensure it's a valid category, default to 'learning'
        if valid_category not in [
            "learning",
            "decision",
            "issue_solved",
            "preference",
            "pattern",
        ]:
            valid_category = "learning"

        memory = Memory(
            content=mem_data.get("content", ""),
            category=valid_category,  # type: ignore
            metadata={
                "importance": mem_data.get("importance", 0.5),
                "tags": mem_data.get("tags", []),
                "source": "real_conversation",
                "extracted_at": datetime.now().isoformat(),
                "original_type": extracted_category,  # Preserve original
            },
        )

        stored = store.add_memory(memory)
        stored_count += 1
        print(f"   ✓ Stored: {stored.id[:8]}... - {stored.content[:60]}...")

    print(f"\n✅ Stored {stored_count} new memories")
    print(f"💾 Total memories now: {len(store.get_all())}")

    return store


async def search_real_memories(store):
    """Search the real memories"""
    print("\n" + "=" * 70)
    print("SEARCHING REAL MEMORIES")
    print("=" * 70)

    searcher = MemorySearcher(data_dir=Path(".data"))

    queries = [
        "amplifier memory system",
        "how extraction works",
        "where data comes from",
    ]

    all_memories = store.get_all()

    for query in queries:
        print(f"\n🔍 Query: '{query}'")
        print("-" * 70)

        results = searcher.search(query, all_memories, limit=3)

        if not results:
            print("   No results found")
            continue

        for i, result in enumerate(results, 1):
            print(f"\n{i}. Score: {result.score:.3f} ({result.match_type})")
            print(f"   Category: {result.memory.category}")
            print(f"   Content: {result.memory.content[:80]}...")
            if result.memory.metadata.get("source") == "real_conversation":
                print("   ✨ From THIS conversation!")


async def main():
    """Run complete extraction from real session data"""
    print("\n" + "=" * 70)
    print("REAL MEMORY EXTRACTION FROM CLAUDE CODE SESSION")
    print("=" * 70)
    print("\nThis extracts REAL memories from the ACTUAL conversation")
    print("happening right now in this Claude Code session!")

    # Extract from real session
    memories = await extract_from_real_session()

    # Store real memories
    store = await store_real_memories(memories)

    # Search real memories
    if store:
        await search_real_memories(store)

    print("\n" + "=" * 70)
    print("✨ COMPLETE - REAL DATA ONLY")
    print("=" * 70)
    print("\nAll data came from:")
    print("  ~/.claude/projects/-Users-max-Documents-GitHub-amplifier/")
    print("  (The actual session files from THIS conversation)")


if __name__ == "__main__":
    asyncio.run(main())
