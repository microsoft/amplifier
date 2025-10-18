# Memory Extraction Input - Visual Guide

## What Gets Sent to Claude? EXACTLY THIS:

```
┌─────────────────────────────────────────────────────────────────┐
│                    FULL CONVERSATION (150 messages)              │
│                                                                  │
│  Message 1:   USER: "Let's discuss the architecture"           │
│  Message 2:   ASSISTANT: "Sure, what do you have in mind?"     │
│  Message 3:   USER: "I'm thinking about microservices"         │
│  ...                                                             │
│  Message 100: USER: "What about logging?"                       │
│  Message 101: ASSISTANT: "Structured logging is best"          │
│  ...                                                             │
│  Message 130: <system-reminder>Hook completed</system-reminder> │
│  Message 131: USER: "I prefer JWT for auth"                    │
│  Message 132: ASSISTANT: "JWT is excellent because..."         │
│  Message 133: PostToolUse:Write success                        │
│  Message 134: USER: "What about caching?"                      │
│  Message 135: ASSISTANT: "Redis is a great choice..."          │
│  ...                                                             │
│  Message 150: ASSISTANT: "I'll remember that pattern"          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    🔍 FILTERING STEP
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    FILTERED INPUT (What Gets Sent)               │
│                                                                  │
│  ❌ Messages 1-130:   SKIPPED (old messages)                   │
│  ❌ System messages:  FILTERED OUT                              │
│  ❌ Hook output:      FILTERED OUT                              │
│  ✅ Messages 131-150: KEPT (last 20)                           │
│                                                                  │
│  Result:                                                         │
│  USER: I prefer JWT for auth                                    │
│  ASSISTANT: JWT is excellent because...                         │
│  USER: What about caching?                                      │
│  ASSISTANT: Redis is a great choice...                          │
│  USER: Async DB calls improved performance 40%                  │
│  ASSISTANT: I'll remember that pattern                          │
│                                                                  │
│  Character count: 701 chars                                     │
│  Estimated tokens: ~175 tokens (not 3,550!)                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
               📝 ACTUAL PROMPT TO CLAUDE
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Extract key memories from this conversation that should be      │
│ remembered for future interactions.                              │
│                                                                  │
│ Conversation:                                                    │
│ USER: I prefer JWT for auth                                     │
│ ASSISTANT: JWT is excellent because...                          │
│ USER: What about caching?                                       │
│ ASSISTANT: Redis is a great choice...                           │
│ USER: Async DB calls improved performance 40%                   │
│ ASSISTANT: I'll remember that pattern                           │
│                                                                  │
│ Extract and return as JSON:                                     │
│ {                                                                │
│   "memories": [                                                  │
│     {                                                            │
│       "type": "learning|decision|issue_solved|pattern|preference"│
│       "content": "concise memory content",                       │
│       "importance": 0.0-1.0,                                     │
│       "tags": ["tag1", "tag2"]                                   │
│     }                                                            │
│   ]                                                              │
│ }                                                                │
│                                                                  │
│ Focus on technical decisions, problems solved, user preferences │
│ Return ONLY valid JSON.                                         │
│                                                                  │
│ Total tokens: ~319 tokens                                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                  🤖 CLAUDE RESPONDS
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ {                                                                │
│   "memories": [                                                  │
│     {                                                            │
│       "type": "preference",                                      │
│       "content": "User prefers JWT for authentication",         │
│       "importance": 0.8,                                         │
│       "tags": ["auth", "jwt", "api"]                            │
│     },                                                           │
│     {                                                            │
│       "type": "preference",                                      │
│       "content": "Redis is preferred caching solution",         │
│       "importance": 0.7,                                         │
│       "tags": ["caching", "redis"]                              │
│     },                                                           │
│     {                                                            │
│       "type": "pattern",                                         │
│       "content": "Async DB calls improved performance 40%",     │
│       "importance": 0.9,                                         │
│       "tags": ["performance", "async", "database"]              │
│     }                                                            │
│   ],                                                             │
│   "key_learnings": ["Async improves DB performance"],           │
│   "decisions_made": ["Use JWT", "Use Redis"],                   │
│   "issues_solved": []                                            │
│ }                                                                │
└─────────────────────────────────────────────────────────────────┘
```

## Token Comparison

### Without Filtering (❌ DON'T DO THIS)
```
┌───────────────────────────────────────────┐
│ 150 messages × 200 chars avg = 30K chars │
│ 30K chars ÷ 4 = ~7,500 tokens            │
│ Cost: $0.02 per extraction                │
│ Time: 45-60 seconds                       │
│ Risk: Timeout, irrelevant info            │
└───────────────────────────────────────────┘
```

### With Filtering (✅ AMPLIFIER DOES THIS)
```
┌───────────────────────────────────────────┐
│ 20 messages × 35 chars avg = 700 chars   │
│ 700 chars ÷ 4 = ~175 tokens              │
│ Cost: $0.0004 per extraction              │
│ Time: 3-8 seconds                         │
│ Quality: Focused on recent context       │
└───────────────────────────────────────────┘
```

**Savings: 97% fewer tokens, 98% cheaper, 90% faster** 🎯

## Configuration Controls

### `.env` or Environment Variables

```bash
# How many recent messages to include
MEMORY_EXTRACTION_MAX_MESSAGES=20  # Default: 20

# Max characters per message (truncation)
MEMORY_EXTRACTION_MAX_CONTENT_LENGTH=500  # Default: 500

# Which model to use
MEMORY_EXTRACTION_MODEL=claude-3-5-haiku-20241022  # Fast & cheap

# Timeout safety
MEMORY_EXTRACTION_TIMEOUT=120  # 2 minutes max
```

### Adjusting for Different Needs

#### More Context (costs more):
```bash
MEMORY_EXTRACTION_MAX_MESSAGES=50
MEMORY_EXTRACTION_MAX_CONTENT_LENGTH=1000
# Result: ~1,250 tokens, $0.003 per extraction
```

#### Minimal Context (costs less):
```bash
MEMORY_EXTRACTION_MAX_MESSAGES=10
MEMORY_EXTRACTION_MAX_CONTENT_LENGTH=300
# Result: ~75 tokens, $0.0002 per extraction
```

#### Better Quality (costs more):
```bash
MEMORY_EXTRACTION_MODEL=claude-3-5-sonnet-20241022
# Same token count, but 4x more expensive
```

## Real Example Output

### Input Conversation (after filtering)
```
USER: I prefer JWT for authentication
ASSISTANT: JWT is excellent for API-first architectures because it's
stateless, works great with microservices, and is mobile-app friendly.

USER: What about caching?
ASSISTANT: Redis is a great choice for caching.

USER: We found async/await improved DB performance by 40%
ASSISTANT: That's significant! I'll remember that pattern.
```

**Stats**: 175 tokens

### Extracted Memories
```json
{
  "memories": [
    {
      "type": "preference",
      "content": "User prefers JWT for authentication",
      "importance": 0.8,
      "tags": ["auth", "jwt"]
    },
    {
      "type": "preference",
      "content": "Redis is preferred caching solution",
      "importance": 0.7,
      "tags": ["caching", "redis"]
    },
    {
      "type": "pattern",
      "content": "Async DB calls improved performance 40%",
      "importance": 0.9,
      "tags": ["performance", "async", "database"]
    }
  ]
}
```

**Stats**: ~150 tokens output

**Total Cost**: 175 input + 150 output = 325 tokens = **$0.0008** (less than 0.1¢)

## Filtering Logic (Code Level)

### What Gets Filtered Out

```python
# From amplifier/extraction/core.py

def _is_system_message(self, content: str) -> bool:
    """Check if content should be filtered"""

    system_patterns = [
        r"^PostToolUse:",           # Hook output
        r"^PreToolUse:",            # Hook output
        r"^\[.*HOOK\]",             # Hook markers
        r"^Hook (started|completed)", # Hook status
        r"^Running.*make check",    # Build commands
        r"^Using directory of",     # System info
        r"^Extract key memories",   # Previous prompts
    ]

    return any(re.match(pattern, content) for pattern in system_patterns)
```

### What Gets Kept

```python
def _format_messages(self, messages: list) -> str:
    """Format messages for extraction"""

    formatted = []

    # Only last N messages
    messages_to_process = messages[-20:]  # ← Configuration

    for msg in messages_to_process:
        role = msg.get("role")

        # Keep only user/assistant
        if role not in ["user", "assistant"]:
            continue

        content = msg.get("content", "")

        # Truncate long messages
        if len(content) > 500:  # ← Configuration
            content = content[:500] + "..."

        # Filter system noise
        if self._is_system_message(content):
            continue

        formatted.append(f"{role.upper()}: {content}")

    return "\n\n".join(formatted)
```

## Summary: The Input is MINIMAL

```
150-message conversation
         ↓
    FILTER
         ↓
Last 20 messages only
         ↓
    TRUNCATE
         ↓
Max 500 chars each
         ↓
   FILTER NOISE
         ↓
Remove system messages
         ↓
     RESULT
         ↓
~700 chars, ~175 tokens
         ↓
   COST: $0.0004
```

**The key**: You're NOT dumping the entire conversation! Only the **last 20 filtered messages** get sent.

## Try It Yourself

```bash
# See exactly what gets sent
python show_extraction_input.py

# Run actual extraction
python demo_memory_system.py

# Check the logs
# Look for: "[EXTRACTION] Processing X of Y total messages"
```

The logs show you exactly what's happening:
- `Processing 20 of 150 total messages` ← Only last 20!
- `Formatted 18 messages for extraction` ← After filtering
- `Character count: 701 chars` ← Final size
