#!/usr/bin/env python3
"""
Feature Demo #3: Knowledge Extraction
Shows how Amplifier extracts structured knowledge from documents
"""
import asyncio
import sys
from pathlib import Path


# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from amplifier.extraction import MemoryExtractor


async def main():
    print("\n" + "=" * 70)
    print("📚 FEATURE #3: KNOWLEDGE EXTRACTION")
    print("=" * 70)

    print("\n📋 What is Knowledge Extraction?")
    print("   Instead of manually noting important information,")
    print("   Amplifier uses AI to automatically extract:")
    print("   • Key learnings from documentation")
    print("   • Decisions and their rationale")
    print("   • Best practices and patterns")
    print("   • Problem solutions")
    print("   • User preferences")

    # Example documents
    print("\n" + "-" * 70)
    print("📄 EXAMPLE: Extracting from a Project Discussion")
    print("-" * 70)

    conversation = """
    Meeting Notes - API Design Review (Oct 15, 2025)

    We discussed the authentication system design. After evaluating
    several options, the team decided to use JWT tokens instead of
    session-based authentication because:

    1. Better scalability for our microservices architecture
    2. Reduced server-side state management
    3. Easier to implement mobile app support

    Important constraints:
    - Tokens expire after 15 minutes
    - Refresh tokens valid for 7 days
    - Must use RS256 (not HS256) for better security

    Sarah discovered that we need timezone-aware datetime comparisons
    when validating token expiration - this was causing intermittent
    auth failures in production.

    Action items:
    - All API endpoints must validate JWT in middleware
    - Frontend should auto-refresh tokens when < 5 min remaining
    - Add rate limiting: 100 requests/min per user
    """

    print("\n📖 Source Document:")
    print("─" * 70)
    print(conversation)
    print("─" * 70)

    print("\n🔬 Extracting knowledge with AI...")
    print("   (This uses Claude Code SDK to analyze the text)\n")

    # Note: Extraction requires Claude Code SDK and API access
    # For demo purposes, we'll show what WOULD be extracted
    print("⚙️  Checking if extraction is available...")

    try:
        extractor = MemoryExtractor()
        print("✅ Memory extractor initialized")
        print(f"   SDK available: {extractor.sdk is not None}")

        # Check if we can actually extract
        if extractor.sdk is not None:
            print("\n🤖 Running AI extraction...")
            memories = await extractor.extract_memories(conversation)

            if memories:
                print(f"✅ Extracted {len(memories)} memories!\n")

                for i, mem in enumerate(memories, 1):
                    print(f"Memory {i}:")
                    print(f"   Category: {mem.category}")
                    print(f"   Content: {mem.content}")
                    if mem.metadata:
                        print(f"   Metadata: {mem.metadata}")
                    print()
            else:
                print("⚠️  No memories extracted (AI returned empty)")
        else:
            print("⚠️  SDK not available - showing expected output instead\n")
            show_expected_extraction()

    except Exception as e:
        print(f"ℹ️  Extraction unavailable: {str(e)[:100]}")
        print("\n📝 Here's what WOULD be extracted:\n")
        show_expected_extraction()

    # Show the workflow
    print("\n" + "=" * 70)
    print("🔄 EXTRACTION WORKFLOW")
    print("=" * 70)
    print()
    print("1. 📁 Scan content directories")
    print("   make content-scan")
    print()
    print("2. 🔍 Extract knowledge from all documents")
    print("   make knowledge-sync")
    print()
    print("3. 💡 Synthesize patterns across knowledge")
    print("   make knowledge-synthesize")
    print()
    print("4. ❓ Query the knowledge base")
    print("   make knowledge-query Q='your question'")

    print("\n" + "=" * 70)
    print("✅ Knowledge Extraction Demo Complete!")
    print("=" * 70)

    print("\n💡 Key Takeaways:")
    print("   1. AI automatically identifies important information")
    print("   2. Categorizes knowledge by type (learning, decision, etc.)")
    print("   3. Works on any text: docs, meeting notes, code comments")
    print("   4. Builds a searchable knowledge base over time")
    print("   5. No manual note-taking required!")

    print("\n🎓 Real-World Usage:")
    print("   • Extract from project documentation")
    print("   • Process meeting notes automatically")
    print("   • Learn from bug fix discussions")
    print("   • Capture design decisions with rationale")
    print("   • Build team knowledge base")

    print("\n🔧 Try it yourself:")
    print("   1. Add your docs to AMPLIFIER_CONTENT_DIRS")
    print("   2. Run: make knowledge-sync")
    print("   3. Query: make knowledge-query Q='your topic'")
    print()


def show_expected_extraction():
    """Show what would be extracted from the example"""
    print("Expected Extracted Memories:")
    print("─" * 70)

    expected = [
        {
            "category": "decision",
            "content": "Decided to use JWT tokens instead of session-based auth for better scalability in microservices architecture",
            "metadata": {"source": "api-design-review", "date": "2025-10-15"}
        },
        {
            "category": "learning",
            "content": "JWT tokens should use RS256 algorithm (not HS256) for better security",
            "metadata": {"source": "security-requirement"}
        },
        {
            "category": "issue_solved",
            "content": "Fixed intermittent auth failures by using timezone-aware datetime for token expiration validation",
            "metadata": {"source": "production-bug", "severity": "high"}
        },
        {
            "category": "pattern",
            "content": "API endpoints must validate JWT in middleware layer",
            "metadata": {"source": "architecture-pattern"}
        },
        {
            "category": "preference",
            "content": "Token expiration: 15 min for access tokens, 7 days for refresh tokens",
            "metadata": {"source": "config-decision"}
        },
        {
            "category": "learning",
            "content": "API rate limit set to 100 requests per minute per user",
            "metadata": {"source": "api-limits"}
        }
    ]

    for i, mem in enumerate(expected, 1):
        print(f"\n   {i}. [{mem['category'].upper()}]")
        print(f"      {mem['content']}")
        print(f"      Metadata: {mem['metadata']}")

    print("\n─" * 70)
    print(f"Total: {len(expected)} memories extracted from one document!")


if __name__ == "__main__":
    asyncio.run(main())
