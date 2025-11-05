#!/usr/bin/env python3
"""
Example demonstrating document type support in Knowledge Mining System.

This shows how to use different document types for optimized extraction.
"""

from amplifier.config.paths import paths
from amplifier.knowledge_mining.knowledge_assistant import KnowledgeAssistant


def demo_document_types():
    """Demonstrate processing different document types."""
    assistant = KnowledgeAssistant()

    # Example 1: Process API documentation
    api_content = """
    # REST API Documentation

    ## GET /api/users
    Returns a list of users.

    Parameters:
    - limit: Maximum number of users to return
    - offset: Pagination offset

    Response: 200 OK
    {
        "users": [...],
        "total": 100
    }
    """

    result = assistant.process_article(
        api_content,
        title="User API",
        source="api_docs.md",
        document_type="api_docs",  # Specify API docs type for optimized extraction
    )
    print(f"API Docs: Extracted {result['concepts_extracted']} concepts")

    # Example 2: Process meeting transcript
    meeting_content = """
    # Team Meeting Notes

    Attendees: Alice, Bob, Charlie

    Decisions:
    - Adopt TypeScript for frontend
    - Move to weekly sprints

    Action Items:
    - Alice: Set up TypeScript config
    - Bob: Create sprint templates
    """

    result = assistant.process_article(
        meeting_content,
        title="Team Sync",
        source="meeting_notes.md",
        document_type="meeting",  # Meeting type focuses on decisions and actions
    )
    print(f"Meeting: Extracted {result['insights_captured']} insights")

    # Example 3: Auto-detection (general type)
    # The system will detect the document type based on content
    unknown_content = """
    # Building Scalable Systems

    When designing distributed systems, consider these patterns...
    """

    result = assistant.process_article(
        unknown_content,
        title="Systems Design",
        source="article.md",
        document_type="general",  # Let system auto-detect
    )
    print("Auto-detect: Processed as general document")


def process_directory_by_type():
    """Process a directory with specific document type."""
    assistant = KnowledgeAssistant()

    # Process all files in a directory as API documentation
    api_docs_dir = paths.data_dir / "api_documentation"
    if api_docs_dir.exists():
        results = assistant.process_directory(
            api_docs_dir,
            pattern="*.md",
            document_type="api_docs",  # All files treated as API docs
        )
        print(f"Processed {len(results)} API documentation files")

    # Process meeting notes directory
    meetings_dir = paths.data_dir / "meeting_notes"
    if meetings_dir.exists():
        results = assistant.process_directory(
            meetings_dir,
            pattern="*.md",
            document_type="meeting",  # All files treated as meeting notes
        )
        print(f"Processed {len(results)} meeting transcript files")


if __name__ == "__main__":
    print("Document Type Support Examples")
    print("=" * 50)

    # Note: These examples require Claude Code SDK to be configured
    try:
        demo_document_types()
        print("\n" + "=" * 50)
        process_directory_by_type()
    except RuntimeError as e:
        print(f"\nNote: {e}")
        print("Configure Claude Code SDK to run these examples.")
