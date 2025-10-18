# Memory System Data Examples

## Real Data from Your System

### 📊 Current Statistics
- **Total Memories**: 16
- **Categories**: 5 types
- **Storage**: `.data/memory.json` (15KB)
- **Embeddings**: `.data/embeddings.json` (16 vectors × 384 dimensions)

---

## 1. DECISION Category (4 memories)

**What it stores**: Architecture decisions, technology choices, team agreements

### Example 1: Technology Choice
```json
{
  "id": "0df57fb8-e4be-4bee-a89e-194d3415f6fe",
  "content": "Team decided to use TypeScript for all frontend components",
  "category": "decision",
  "timestamp": "2025-10-15T00:47:41.584323",
  "accessed_count": 0,
  "metadata": {
    "source": "team-meeting"
  }
}
```

**When used**: When someone asks "What language should I use for frontend?"
**AI Response**: "Your team decided to use TypeScript for all frontend components."

### Example 2: Database Choice
```json
{
  "content": "Decided to use PostgreSQL over MongoDB for better transaction support",
  "category": "decision",
  "timestamp": "2025-10-15T00:57:41.489377",
  "metadata": {
    "source": "architecture-meeting",
    "date": "2025-10-15"
  }
}
```

**When used**: When discussing database options
**AI Response**: "You previously decided on PostgreSQL for its transaction support."

### Example 3: Authentication Strategy
```json
{
  "content": "JWT is preferred over session-based auth for API-first architecture due to statelessness, mobile app compatibility, and no server-side session storage",
  "category": "decision",
  "timestamp": "2025-10-17T16:26:32.455817",
  "metadata": {
    "authentication_method": "JWT",
    "rationale": [
      "Microservices support",
      "Mobile app friendly",
      "No server-side storage"
    ],
    "source": "architecture_discussion"
  }
}
```

**When used**: When designing authentication
**AI Response**: "Based on your API-first architecture, you chose JWT because..."

---

## 2. PREFERENCE Category (4 memories)

**What it stores**: User preferences, style choices, personal workflow

### Example 1: UI Preference
```json
{
  "content": "User prefers dark mode for coding environments",
  "category": "preference",
  "timestamp": "2025-10-15T00:47:41.573537",
  "metadata": {
    "source": "user-settings"
  }
}
```

**When used**: When setting up new tools or environments
**AI Response**: "I'll configure this with dark mode, as you prefer."

### Example 2: Code Style
```json
{
  "content": "User prefers 2-space indentation for JavaScript, 4-space for Python",
  "category": "preference",
  "timestamp": "2025-10-15T00:57:41.486550",
  "metadata": {
    "source": "code-review"
  }
}
```

**When used**: When generating code
**AI Response**: *Automatically uses correct indentation without asking*

### Example 3: Technology Preference
```json
{
  "content": "Redis is the preferred caching solution",
  "category": "preference",
  "timestamp": "2025-10-17T16:26:32.456234",
  "metadata": {
    "technology": "Redis",
    "use_case": "Caching",
    "source": "architecture_discussion"
  }
}
```

**When used**: When designing caching layers
**AI Response**: "I'll use Redis for caching, as you prefer."

---

## 3. LEARNING Category (3 memories)

**What it stores**: Technical facts learned, best practices discovered, lessons from experience

### Example 1: API Constraints
```json
{
  "content": "Claude Code API has rate limit of 100 requests per minute",
  "category": "learning",
  "timestamp": "2025-10-15T00:47:41.574955",
  "metadata": {
    "source": "api-docs"
  }
}
```

**When used**: When writing code that calls the API
**AI Response**: "I'll add rate limiting to stay under the 100 req/min limit."

### Example 2: Performance Best Practice
```json
{
  "content": "Always use async/await for database operations - learned from performance issues",
  "category": "learning",
  "timestamp": "2025-10-15T00:57:41.486033",
  "metadata": {
    "source": "debugging",
    "importance": "high"
  }
}
```

**When used**: When writing database code
**AI Response**: "I'll use async/await based on your performance learnings."

### Example 3: Error Handling Lesson
```json
{
  "content": "Always log full error context including request ID and user ID for debugging production issues",
  "category": "learning",
  "timestamp": "2025-10-17T17:00:00",
  "metadata": {
    "source": "production-incident",
    "importance": "critical",
    "incident_id": "INC-2025-042"
  }
}
```

**When used**: When writing error handlers
**AI Response**: "I'll include request ID and user ID in error logs, as you learned from incident INC-2025-042."

---

## 4. ISSUE_SOLVED Category (3 memories)

**What it stores**: Bugs fixed, problems resolved, solutions discovered

### Example 1: Async Pattern Fix
```json
{
  "content": "Successfully resolved async/await pattern for database connections",
  "category": "issue_solved",
  "timestamp": "2025-10-15T00:47:41.582903",
  "metadata": {
    "source": "debugging-session"
  }
}
```

**When used**: When similar async issues arise
**AI Response**: "This looks like the async/await pattern issue you solved before."

### Example 2: JWT Bug Fix
```json
{
  "content": "Fixed JWT token expiration bug by adding timezone awareness to datetime comparisons",
  "category": "issue_solved",
  "timestamp": "2025-10-15T00:57:41.489718",
  "metadata": {
    "source": "bug-fix",
    "severity": "critical"
  }
}
```

**When used**: When encountering token expiration issues
**AI Response**: "Check datetime timezone handling - you fixed a similar JWT bug this way."

### Example 3: Memory Leak Solution
```json
{
  "content": "Resolved memory leak by properly closing database connections in finally blocks",
  "category": "issue_solved",
  "timestamp": "2025-10-17T17:15:00",
  "metadata": {
    "source": "performance-debugging",
    "fix_commit": "abc123def",
    "memory_reduction": "85%"
  }
}
```

**When used**: When debugging memory issues
**AI Response**: "This could be unclosed connections - you reduced memory 85% by using finally blocks."

---

## 5. PATTERN Category (2 memories)

**What it stores**: Recurring patterns, code standards, architectural patterns

### Example 1: Security Pattern
```json
{
  "content": "Pattern: Always validate user input on both client and server side",
  "category": "pattern",
  "timestamp": "2025-10-15T00:57:41.486783",
  "metadata": {
    "source": "security-review"
  }
}
```

**When used**: When implementing input handling
**AI Response**: "I'll add validation on both client and server, following your security pattern."

### Example 2: Performance Pattern
```json
{
  "content": "Async/await database calls improved performance by 40%",
  "category": "pattern",
  "timestamp": "2025-10-17T16:26:32.456567",
  "metadata": {
    "performance_improvement": 40,
    "technique": "Async database calls",
    "source": "architecture_discussion"
  }
}
```

**When used**: When optimizing database code
**AI Response**: "Based on your 40% improvement with async, I'll use that pattern here."

### Example 3: Error Handling Pattern
```json
{
  "content": "Pattern: Use circuit breaker for external API calls with 3 retries and exponential backoff",
  "category": "pattern",
  "timestamp": "2025-10-17T17:20:00",
  "metadata": {
    "source": "reliability-engineering",
    "retry_count": 3,
    "backoff_strategy": "exponential"
  }
}
```

**When used**: When integrating external APIs
**AI Response**: "I'll implement circuit breaker with 3 retries and exponential backoff, as per your pattern."

---

## Real-World Scenarios

### Scenario 1: New Developer Onboarding

**Conversation:**
```
New Dev: "What coding standards should I follow?"
```

**Memory Search Finds:**
- Preference: "2-space indentation for JavaScript, 4-space for Python"
- Decision: "Team decided to use TypeScript for all frontend components"
- Pattern: "Always validate user input on both client and server side"

**AI Response:**
```
Based on team standards:
• Use TypeScript for all frontend components
• JavaScript: 2-space indentation
• Python: 4-space indentation
• Always validate input on both client and server
```

### Scenario 2: Debugging Production Issue

**Conversation:**
```
Developer: "Users are reporting JWT authentication failures"
```

**Memory Search Finds:**
- Issue Solved: "Fixed JWT token expiration bug by adding timezone awareness..."
- Learning: "Always log full error context including request ID and user ID..."

**AI Response:**
```
Check these areas based on past issues:
1. Datetime timezone handling (fixed similar JWT bug before)
2. Ensure error logs include request ID and user ID
3. Review token expiration logic for timezone problems
```

### Scenario 3: Architecture Design

**Conversation:**
```
Developer: "Design a caching layer for the user service"
```

**Memory Search Finds:**
- Preference: "Redis is the preferred caching solution"
- Pattern: "Async/await database calls improved performance by 40%"
- Decision: "JWT is preferred for API-first architecture..."

**AI Response:**
```
Recommended approach based on your preferences:
• Use Redis for distributed caching
• Implement async cache operations (40% perf boost)
• Design stateless cache keys for API-first architecture
• Consider JWT token data in cache key design
```

---

## How Semantic Search Works

### Query: "authentication methods"

**Embeddings Comparison:**
```
Query vector:      [0.23, -0.45, 0.78, ...] (384 dimensions)

Memory 1 (JWT):    [0.24, -0.43, 0.76, ...]  → Similarity: 0.389 ✓
Memory 2 (Input):  [0.15, -0.22, 0.55, ...]  → Similarity: 0.310
Memory 3 (Redis):  [0.08, -0.12, 0.34, ...]  → Similarity: 0.102
```

**Result**: JWT decision ranks highest even though query didn't mention "JWT"

### Query: "how to handle errors"

**Finds:**
```
1. Learning: "Always log full error context..." (0.612)
2. Pattern: "Circuit breaker for external APIs..." (0.543)
3. Issue: "Resolved memory leak..." (0.398)
```

**AI Uses All Three:**
```
Error handling recommendations:
1. Log request ID and user ID (from production learnings)
2. Use circuit breaker pattern for external calls
3. Ensure proper resource cleanup in finally blocks
```

---

## Storage Formats

### memory.json Structure
```json
{
  "memories": [
    {
      "id": "uuid",
      "content": "memory text",
      "category": "one of 5 categories",
      "timestamp": "ISO 8601 datetime",
      "accessed_count": 0,
      "metadata": {
        "source": "where it came from",
        "custom": "any additional data"
      }
    }
  ],
  "metadata": {
    "version": "2.0",
    "count": 16,
    "created": "2025-10-15T00:47:41",
    "last_updated": "2025-10-17T16:26:32"
  },
  "key_learnings": ["important facts"],
  "decisions_made": ["team decisions"],
  "issues_solved": ["problems fixed"]
}
```

### embeddings.json Structure
```json
{
  "45683b68-f001-4d8f-a9e2-d232f7f5a37f": [
    0.06306293606758118,
    -0.0354793481528759,
    0.0018689390271902084,
    ...381 more numbers...
  ],
  "uuid2": [...384 numbers...],
  "uuid3": [...384 numbers...]
}
```

---

## Metadata Examples

### Simple Metadata
```json
{
  "source": "user-settings"
}
```

### Rich Metadata
```json
{
  "source": "architecture-meeting",
  "date": "2025-10-15",
  "participants": ["alice", "bob"],
  "rationale": ["reason1", "reason2"],
  "alternatives_considered": ["option1", "option2"]
}
```

### Quantitative Metadata
```json
{
  "performance_improvement": 40,
  "technique": "Async database calls",
  "measured_date": "2025-10-17",
  "benchmark_results": {
    "before": "100ms",
    "after": "60ms"
  }
}
```

### Incident Tracking Metadata
```json
{
  "source": "production-incident",
  "incident_id": "INC-2025-042",
  "severity": "critical",
  "fix_commit": "abc123def",
  "root_cause": "timezone handling",
  "affected_users": 1250
}
```

---

## Lifecycle Example

### Day 1: Extract
```
Conversation: "We decided to use PostgreSQL for better transactions"
  ↓
AI extracts: Decision memory
  ↓
Stored with metadata: {"source": "architecture-meeting", "date": "2025-10-15"}
```

### Day 5: Use
```
Question: "What database should I use for the billing service?"
  ↓
Search finds: PostgreSQL decision (similarity: 0.678)
  ↓
AI responds: "Your team chose PostgreSQL for transaction support"
  ↓
accessed_count: 0 → 1
```

### Day 30: Pattern Emerges
```
Multiple queries about databases
  ↓
accessed_count: 15 (high usage)
  ↓
System recognizes: Important memory
  ↓
Protected from rotation (kept in top 1000)
```

---

## Tips for Good Memories

### ✅ Good Memory Content
```json
{
  "content": "Team decided to use PostgreSQL over MongoDB for better transaction support in the billing system",
  "category": "decision",
  "metadata": {
    "source": "architecture-meeting",
    "alternatives": ["MongoDB", "MySQL"],
    "deciding_factors": ["ACID compliance", "complex queries"]
  }
}
```
**Why**: Specific, includes context, explains reasoning

### ❌ Poor Memory Content
```json
{
  "content": "We use Postgres",
  "category": "decision",
  "metadata": {}
}
```
**Why**: Too vague, no context, no reasoning

### ✅ Good Pattern Memory
```json
{
  "content": "Pattern: All external API calls use circuit breaker with 3 retries, exponential backoff (1s, 2s, 4s), and 30s timeout",
  "category": "pattern",
  "metadata": {
    "source": "reliability-engineering",
    "applies_to": ["payment-api", "notification-api", "user-api"]
  }
}
```
**Why**: Specific parameters, clear application

### ❌ Poor Pattern Memory
```json
{
  "content": "Use retries",
  "category": "pattern"
}
```
**Why**: Too generic, no specifics

---

## Summary

Your memory system currently stores:
- **4 Decisions**: Technology choices, architecture decisions
- **4 Preferences**: Personal workflow, coding style, tool choices
- **3 Learnings**: Technical facts, best practices
- **3 Issues Solved**: Bug fixes, solutions
- **2 Patterns**: Code patterns, architectural patterns

Each memory includes:
- **Unique ID**: For tracking and referencing
- **Timestamp**: When it was learned
- **Category**: Type of information
- **Metadata**: Additional context
- **Access Count**: Usage tracking for importance

The semantic search converts all text to 384-dimensional vectors, enabling finding relevant memories even when query words don't match exactly.
