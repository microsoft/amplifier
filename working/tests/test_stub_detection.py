#!/usr/bin/env python3
"""Test for detecting and preventing stub/placeholder code generation."""

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class StubViolation:
    """Record of a detected stub or placeholder."""

    file_path: str
    line_number: int
    violation_type: str
    content: str


class StubDetector:
    """Detect stub, placeholder, and fake implementation patterns."""

    # Patterns that indicate stubs/placeholders
    STUB_PATTERNS = [
        (r"raise\s+NotImplementedError", "NotImplementedError"),
        (r"#\s*TODO[:\s]", "TODO comment"),
        (r"#\s*FIXME[:\s]", "FIXME comment"),
        (r"#\s*HACK[:\s]", "HACK comment"),
        (r"^\s*pass\s*$", "Empty pass statement"),
        (r"^\s*\.\.\.\s*$", "Ellipsis placeholder"),
        (r'return\s+["\']not\s+implemented', "Not implemented return"),
        (r"return\s+\{\s*\}\s*#.*stub", "Empty dict stub"),
        (r"return\s+\[\s*\]\s*#.*stub", "Empty list stub"),
        (r"return\s+None\s*#.*later", "Deferred implementation"),
        (r"mock_", "Mock implementation"),
        (r"fake_", "Fake implementation"),
        (r"dummy_", "Dummy implementation"),
        (r"placeholder", "Placeholder marker"),
        (r"stub_", "Stub marker"),
        (r"coming\s+soon", "Coming soon marker"),
        (r"will\s+implement", "Future implementation"),
    ]

    def scan_content(self, content: str, filename: str = "unknown") -> list[StubViolation]:
        """Scan content for stub patterns."""
        violations = []
        lines = content.split("\n")

        for line_num, line in enumerate(lines, 1):
            for pattern, violation_type in self.STUB_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    violations.append(
                        StubViolation(
                            file_path=filename,
                            line_number=line_num,
                            violation_type=violation_type,
                            content=line.strip(),
                        )
                    )

        return violations

    def scan_file(self, file_path: Path) -> list[StubViolation]:
        """Scan a file for stub patterns."""
        if not file_path.exists():
            return []

        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        return self.scan_content(content, str(file_path))

    def generate_report(self, violations: list[StubViolation]) -> str:
        """Generate a human-readable report of violations."""
        if not violations:
            return "✓ No stubs or placeholders detected"

        report = f"✗ Found {len(violations)} stub violations:\n"
        report += "=" * 60 + "\n"

        for v in violations:
            report += f"\n{v.file_path}:{v.line_number}\n"
            report += f"  Type: {v.violation_type}\n"
            report += f"  Line: {v.content}\n"

        return report


def test_stub_detection():
    """Test that the detector catches common stub patterns."""
    detector = StubDetector()

    print("Testing Stub Detection")
    print("=" * 60)

    # Example of stub-filled code that should fail
    stub_code = '''
class UserService:
    def __init__(self):
        # TODO: Initialize database connection
        self.db = None
        self.cache = {}  # FIXME: Replace with Redis

    def get_user(self, user_id):
        """Get user by ID"""
        raise NotImplementedError("Database integration pending")

    def create_user(self, data):
        # Will implement after auth is ready
        pass

    def delete_user(self, user_id):
        return "not implemented yet"

    def get_mock_users(self):
        # Placeholder data for testing
        return [
            {"id": 1, "name": "fake_user1"},
            {"id": 2, "name": "dummy_user2"}
        ]

    def coming_soon_feature(self):
        """This feature is coming soon"""
        ...
'''

    violations = detector.scan_content(stub_code, "user_service.py")
    report = detector.generate_report(violations)

    print("\n1. Stub-filled code (should FAIL):")
    print(report)
    assert len(violations) > 0, "Should detect multiple violations"

    # Example of clean, working code
    clean_code = '''
class UserService:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.users = self._load_users()

    def _load_users(self) -> dict:
        """Load users from JSON file."""
        if not self.db_path.exists():
            return {}
        with open(self.db_path, 'r') as f:
            return json.load(f)

    def get_user(self, user_id: str):
        """Get user by ID or raise KeyError."""
        if user_id not in self.users:
            raise KeyError(f"User {user_id} not found")
        return self.users[user_id]

    def create_user(self, user_id: str, data: dict):
        """Create a new user."""
        if user_id in self.users:
            raise ValueError(f"User {user_id} already exists")
        self.users[user_id] = data
        self._save_users()
        return data

    def _save_users(self):
        """Persist users to disk."""
        with open(self.db_path, 'w') as f:
            json.dump(self.users, f)
'''

    violations = detector.scan_content(clean_code, "user_service_clean.py")
    report = detector.generate_report(violations)

    print("\n2. Clean, working code (should PASS):")
    print(report)
    assert len(violations) == 0, "Should have no violations"

    print("\n" + "=" * 60)
    print("Test Summary:")
    print("✓ Detector correctly identifies stub patterns")
    print("✓ Clean code passes validation")


def demonstrate_stub_triggers():
    """Show prompts that trigger stub creation."""

    print("\nPrompts That Trigger Stub Creation")
    print("=" * 60)

    bad_prompts = [
        {
            "prompt": "Build a comprehensive user management system with authentication, authorization, and social login",
            "why_stubs": "Too vague, too many features at once",
        },
        {
            "prompt": "Create an API that handles all CRUD operations for any data type",
            "why_stubs": "Overly generic, no concrete specifications",
        },
        {
            "prompt": "Implement a data pipeline that works with any data source",
            "why_stubs": "Impossible to implement without specifics",
        },
    ]

    good_prompts = [
        {
            "prompt": "Create a function that reads user data from users.json and returns it as a dict",
            "why_works": "Specific, concrete, achievable",
        },
        {
            "prompt": "Write a UserService class that stores users in a JSON file with get/create/delete methods",
            "why_works": "Clear requirements, defined scope",
        },
    ]

    print("\nBAD PROMPTS (trigger stubs):")
    for p in bad_prompts:
        print(f"\nPrompt: {p['prompt']}")
        print(f"Why stubs: {p['why_stubs']}")

    print("\n\nGOOD PROMPTS (produce working code):")
    for p in good_prompts:
        print(f"\nPrompt: {p['prompt']}")
        print(f"Why works: {p['why_works']}")


if __name__ == "__main__":
    test_stub_detection()
    demonstrate_stub_triggers()

    print("\n" + "=" * 60)
    print("ZERO-BS PRINCIPLE:")
    print("✗ Without instructions: Agents create stubs when requirements are vague")
    print("✓ With instructions: Agents either build working code or ask for clarification")
