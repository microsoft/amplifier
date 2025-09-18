# Core Improvement: Better Error Types

> **Source Branch**: `generator-from-code-cdx`
> **Created**: 2025-09-18
> **Status**: Phase 1 COMPLETED ✅ (items 1-3) - Phase 2+ specification
> **Context**: Core toolkit improvement specifications from module_generator analysis


## Priority: 🟢 Valuable (P3)

## Problem Statement

The toolkit uses generic error types that don't provide enough information for debugging. The module generator imports specific SDK exceptions that give clearer failure diagnosis.

## Current Implementation

```python
# Generic errors
class SessionError(Exception):
    """Base exception for session errors."""

class SDKNotAvailableError(SessionError):
    """Raised when Claude CLI/SDK is not available."""
```

## Proposed Solution

### Import and Use Specific SDK Exceptions

```python
# ccsdk_toolkit/core/errors.py
"""Enhanced error types for better debugging."""

# Import SDK-specific errors when available
try:
    from claude_code_sdk import (
        ClaudeSDKError,
        CLINotFoundError,
        ProcessError,
        AuthenticationError,
        RateLimitError,
        NetworkError,
    )
    SDK_ERRORS_AVAILABLE = True
except ImportError:
    # Fallback definitions
    SDK_ERRORS_AVAILABLE = False
    ClaudeSDKError = Exception
    CLINotFoundError = Exception
    ProcessError = Exception
    AuthenticationError = Exception
    RateLimitError = Exception
    NetworkError = Exception

# Toolkit-specific errors
class SessionError(ClaudeSDKError if SDK_ERRORS_AVAILABLE else Exception):
    """Base exception for session errors."""
    pass

class ConfigurationError(SessionError):
    """Raised when session configuration is invalid."""
    pass

class ProgressEvaluationError(SessionError):
    """Raised when progress evaluation fails."""
    pass

class SessionNotFoundError(SessionError):
    """Raised when attempting to resume non-existent session."""
    pass

class OperationCancelledError(SessionError):
    """Raised when operation is cancelled by user or evaluator."""
    def __init__(self, reason: str, partial_result: str = ""):
        super().__init__(reason)
        self.reason = reason
        self.partial_result = partial_result
```

### Enhanced Error Handling

```python
# ccsdk_toolkit/core/session.py
async def query(self, prompt: str) -> SessionResponse:
    try:
        # ... execute query ...
    except CLINotFoundError as e:
        # Specific handling for missing CLI
        return SessionResponse(
            error=f"Claude CLI not found: {e}\n"
                  f"Install with: npm install -g @anthropic-ai/claude-code"
        )
    except AuthenticationError as e:
        return SessionResponse(
            error=f"Authentication failed: {e}\n"
                  f"Check your ANTHROPIC_API_KEY environment variable"
        )
    except RateLimitError as e:
        return SessionResponse(
            error=f"Rate limit exceeded: {e}\n"
                  f"Consider adding delays between requests"
        )
    except NetworkError as e:
        return SessionResponse(
            error=f"Network error: {e}\n"
                  f"Check your internet connection"
        )
    except ProcessError as e:
        # Generic process error
        return SessionResponse(
            error=f"Process error: {e}"
        )
    except Exception as e:
        # Catch-all for unexpected errors
        return SessionResponse(
            error=f"Unexpected error: {type(e).__name__}: {e}"
        )
```

### Diagnostic Error Information

```python
# ccsdk_toolkit/core/models.py
from dataclasses import dataclass
from traceback import TracebackException

@dataclass
class ErrorDetails:
    """Detailed error information for debugging."""
    error_type: str
    message: str
    traceback: str | None = None
    suggestions: list[str] | None = None
    partial_result: str | None = None

class SessionResponse(BaseModel):
    content: str = Field(default="")
    metadata: SessionMetadata = Field(default_factory=SessionMetadata)
    error: str | None = Field(default=None)
    error_details: ErrorDetails | None = Field(default=None)

    @classmethod
    def from_error(cls, error: Exception, partial_result: str = "") -> "SessionResponse":
        """Create response from an exception."""
        import traceback

        error_type = type(error).__name__
        suggestions = []

        # Add specific suggestions based on error type
        if isinstance(error, CLINotFoundError):
            suggestions = [
                "Install Claude CLI: npm install -g @anthropic-ai/claude-code",
                "Verify installation: which claude"
            ]
        elif isinstance(error, AuthenticationError):
            suggestions = [
                "Set ANTHROPIC_API_KEY environment variable",
                "Check API key validity",
                "Verify API key permissions"
            ]
        elif isinstance(error, RateLimitError):
            suggestions = [
                "Add delays between requests",
                "Reduce parallel requests",
                "Consider upgrading API plan"
            ]

        return cls(
            content=partial_result,
            error=str(error),
            error_details=ErrorDetails(
                error_type=error_type,
                message=str(error),
                traceback=traceback.format_exc(),
                suggestions=suggestions,
                partial_result=partial_result if partial_result else None
            )
        )
```

## Usage Patterns

### Pattern 1: Specific Error Handling

```python
async def safe_query(prompt: str) -> str:
    """Query with specific error handling."""
    options = SessionOptions(max_turns=5)

    async with ClaudeSession(options) as session:
        response = await session.query(prompt)

        if response.error_details:
            match response.error_details.error_type:
                case "CLINotFoundError":
                    print("Please install Claude CLI first")
                    print("\n".join(response.error_details.suggestions))
                    sys.exit(1)
                case "RateLimitError":
                    print("Rate limited, waiting 60 seconds...")
                    await asyncio.sleep(60)
                    return await safe_query(prompt)  # Retry
                case "AuthenticationError":
                    print("Authentication failed. Please check your API key.")
                    sys.exit(1)
                case _:
                    print(f"Error: {response.error}")
                    if response.error_details.partial_result:
                        print(f"Partial result: {response.error_details.partial_result}")

        return response.content
```

### Pattern 2: Error Recovery

```python
class RobustSession:
    """Session with automatic error recovery."""

    async def query_with_recovery(self, prompt: str, max_retries: int = 3):
        for attempt in range(max_retries):
            try:
                response = await self.query(prompt)
                if response.success:
                    return response

                # Handle specific errors
                if response.error_details:
                    if response.error_details.error_type == "NetworkError":
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    elif response.error_details.error_type == "RateLimitError":
                        await asyncio.sleep(60)  # Wait for rate limit
                        continue

                # Non-recoverable error
                return response

            except Exception as e:
                if attempt == max_retries - 1:
                    return SessionResponse.from_error(e)

        return SessionResponse(error="Max retries exceeded")
```

## Module Generator Pattern

```python
# sdk_client.py
try:
    from claude_code_sdk import (
        ClaudeSDKError,
        CLINotFoundError,
        ProcessError,
    )
except Exception:
    # Fallback handling
```

## Testing Requirements

- Test specific error types are raised correctly
- Verify error suggestions are appropriate
- Test partial results are preserved
- Ensure error recovery patterns work

## Success Criteria

- Errors clearly indicate what went wrong
- Actionable suggestions provided
- Partial results preserved when possible
- Recovery patterns well-documented

## Philosophy Note

Good error handling transforms frustrating failures into learning opportunities. Clear error messages with actionable suggestions enable users to solve problems independently.