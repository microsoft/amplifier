"""Custom exceptions for Tool Builder."""


class ToolBuilderError(Exception):
    """Base exception for Tool Builder."""


class CCSDKRequiredError(ToolBuilderError):
    """Raised when Claude Code SDK is required but not available."""

    def __init__(self):
        super().__init__(
            "\n❌ Claude Code SDK is REQUIRED for Tool Builder\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "The Tool Builder requires Claude Code SDK to function.\n"
            "NO fallback or alternative approach is available.\n\n"
            "To use Tool Builder:\n"
            "1. Ensure you're running in Claude Code environment\n"
            "2. Verify claude CLI is installed:\n"
            "   npm install -g @anthropic-ai/claude-code\n"
            "3. Check with: which claude\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        )


class SessionError(ToolBuilderError):
    """Raised when session operations fail."""


class ValidationError(ToolBuilderError):
    """Raised when input validation fails."""


class MicrotaskError(ToolBuilderError):
    """Raised when a microtask fails."""
