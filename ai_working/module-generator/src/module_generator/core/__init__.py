"""Core module for Module Generator.

Provides the Claude SDK interface and other core functionality.
"""

from .clarification import AutoClarificationHandler
from .clarification import ClarificationStrategy
from .clarification import HybridClarificationHandler
from .clarification import InteractiveClarificationHandler
from .claude_sdk import check_cli_available
from .claude_sdk import query_claude
from .claude_sdk import query_claude_sync
from .claude_sdk import strip_markdown
from .claude_sdk_multi import MultiTurnClaudeSDK
from .claude_sdk_multi import MultiTurnOptions
from .claude_sdk_multi import SimplifiedMultiTurnSDK
from .conversation import ConversationContext
from .conversation import ConversationManager
from .conversation import ConversationState
from .conversation import Message
from .dialogue import DialogueController
from .dialogue import DialogueResult
from .response_parser import ParsedCode
from .response_parser import ParsedQuestion
from .response_parser import ParsedResponse
from .response_parser import ResponseParser

__all__ = [
    # Original SDK functions
    "check_cli_available",
    "query_claude",
    "query_claude_sync",
    "strip_markdown",
    # Multi-turn SDK
    "MultiTurnClaudeSDK",
    "MultiTurnOptions",
    "SimplifiedMultiTurnSDK",
    # Conversation management
    "ConversationManager",
    "ConversationState",
    "ConversationContext",
    "Message",
    # Response parsing
    "ResponseParser",
    "ParsedResponse",
    "ParsedCode",
    "ParsedQuestion",
    # Clarification handling
    "ClarificationStrategy",
    "AutoClarificationHandler",
    "InteractiveClarificationHandler",
    "HybridClarificationHandler",
    # Dialogue control
    "DialogueController",
    "DialogueResult",
]
