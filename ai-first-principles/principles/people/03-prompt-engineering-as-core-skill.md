# Principle #03 - Prompt Engineering as Core Skill

## Plain-Language Definition

Prompt engineering is the skill of crafting clear, specific instructions for AI systems to get the results you want. Good prompts get good results; bad prompts waste time, money, and produce unusable output.

## Why This Matters for AI-First Development

In AI-first development, prompt engineering isn't a nice-to-have skill - it's foundational. The quality of your prompts directly determines the quality of the code, architecture, and documentation AI agents produce. A well-crafted prompt can generate production-ready code in seconds; a vague prompt can generate pages of unusable code that takes hours to fix.

Prompt engineering becomes even more critical in AI-first systems because:

1. **Compounding effects**: A bad prompt early in development creates technical debt that cascades through the entire system. When AI generates code based on unclear instructions, that code becomes the foundation for future AI-generated code, amplifying errors.

2. **Scale of automation**: In traditional development, a misunderstood requirement might waste a few hours of one developer's time. In AI-first development, a bad prompt can spawn thousands of lines of incorrect code across dozens of files in minutes, requiring extensive cleanup.

3. **Feedback loop quality**: The faster you can iterate with AI, the faster you learn and build. Good prompts create tight feedback loops where you can validate results immediately and refine. Bad prompts create long, frustrating cycles of debugging and re-prompting.

Without strong prompt engineering skills, developers become bottlenecks in their own AI-first workflow. They spend more time fixing AI-generated mistakes than they would have spent writing code manually. With strong skills, they become force multipliers - directing AI agents to handle complex tasks while they focus on architecture and strategy.

## Implementation Approaches

### 1. **Clear Context Setting**

Begin every prompt with explicit context about what you're building, the current state, and constraints:

```
We're building a REST API for user authentication using FastAPI and PostgreSQL.
Current state: Database models exist, need to implement login endpoint.
Constraints: Must use JWT tokens, password hashing with bcrypt, rate limiting.
```

Provide just enough context for the AI to understand the environment without overwhelming it. Include: project type, tech stack, current state, and specific constraints.

### 2. **Specific, Actionable Instructions**

Replace vague requests with precise, step-by-step instructions:

**Vague**: "Make the API better"
**Specific**: "Add input validation to the `/api/users` POST endpoint. Validate: email format, password length (min 8 chars), username alphanumeric only. Return 400 with field-specific error messages."

Break complex tasks into discrete steps. Each instruction should be independently verifiable.

### 3. **Examples and Constraints**

Show the AI exactly what success looks like through examples:

```
Create a function to parse user input. Example inputs:
- "user@example.com" -> valid
- "invalid.email" -> error: "Invalid email format"
- "" -> error: "Email required"

Constraints:
- No external libraries for validation
- Must return tuple (is_valid: bool, error_message: str)
- Handle None input gracefully
```

Examples eliminate ambiguity. Constraints prevent the AI from making assumptions you don't want.

### 4. **Iterative Refinement Pattern**

Use a three-stage refinement process:

1. **Broad request**: "Create a caching layer for database queries"
2. **Review and refine**: Examine the output, identify gaps
3. **Specific fixes**: "Add TTL configuration, implement cache invalidation on write operations, add metrics for hit/miss ratio"

Don't expect perfection on the first prompt. Plan for iteration - start broad to see the AI's approach, then refine with specific corrections.

### 5. **Format and Structure Specifications**

Explicitly specify the output format you need:

```
Generate database migration script with this structure:
1. Comment block with migration description
2. Up migration: CREATE TABLE with columns
3. Down migration: DROP TABLE
4. Use PostgreSQL syntax
5. Include timestamp in filename

File format: YYYYMMDD_HHMMSS_description.sql
```

When you need specific formatting, file structure, or naming conventions, state them explicitly.

### 6. **Error Handling and Edge Cases**

Tell the AI what can go wrong and how to handle it:

```
Create file upload handler. Handle these cases:
- File too large (>10MB) -> return 413 error
- Invalid file type -> return 415 error
- Disk full -> log error, return 507 error
- Duplicate filename -> append timestamp to make unique
- Network interruption during upload -> cleanup partial files
```

Listing edge cases ensures the AI generates robust code rather than just the happy path.

## Good Examples vs Bad Examples

### Example 1: API Endpoint Creation

**Good:**
```
Create a FastAPI endpoint for user registration.

Path: POST /api/register
Request body: {"email": string, "password": string, "username": string}
Response: 201 with {"user_id": uuid, "email": string, "username": string}

Requirements:
- Validate email format (RFC 5322)
- Password must be 8+ chars, contain number and special char
- Username must be 3-20 alphanumeric chars
- Hash password with bcrypt (cost=12)
- Return 400 with field-specific errors for validation failures
- Return 409 if email already exists
- Include rate limiting (5 requests per minute per IP)

Error response format: {"error": string, "details": {field: error_message}}
```

**Bad:**
```
Create an API endpoint for registering users. Make sure it's secure and validates the input properly.
```

**Why It Matters:** The good prompt specifies exact paths, data structures, validation rules, error handling, and security requirements. The AI can generate production-ready code. The bad prompt leaves the AI guessing about formats, validation rules, error handling, and security measures - likely requiring multiple rounds of clarification and fixes.

### Example 2: Code Refactoring

**Good:**
```
Refactor the UserService class to use dependency injection.

Current structure:
- UserService directly instantiates DatabaseClient
- UserService directly instantiates EmailClient
- Makes testing difficult (can't mock dependencies)

Target structure:
- Accept DatabaseClient and EmailClient in __init__
- Store as instance variables
- Update all methods to use injected clients
- Add type hints for all parameters
- Keep existing method signatures unchanged

Example:
```python
# Current
class UserService:
    def __init__(self):
        self.db = DatabaseClient()  # <- remove

# Target
class UserService:
    def __init__(self, db: DatabaseClient, email: EmailClient):
        self.db = db
        self.email = email
```
```

**Bad:**
```
Refactor the UserService class to be more testable. Use dependency injection and best practices.
```

**Why It Matters:** The good prompt shows the exact transformation needed with before/after examples. It specifies what to change and what to preserve. The bad prompt assumes the AI understands what "more testable" means and which "best practices" to apply, likely resulting in over-engineering or incomplete refactoring.

### Example 3: Database Schema Design

**Good:**
```
Create PostgreSQL schema for blog posts and comments.

Tables:
1. posts
   - id: uuid primary key default gen_random_uuid()
   - author_id: uuid not null (foreign key to users.id)
   - title: varchar(200) not null
   - content: text not null
   - published_at: timestamp with time zone
   - created_at: timestamp default now()
   - updated_at: timestamp default now()

2. comments
   - id: uuid primary key default gen_random_uuid()
   - post_id: uuid not null (foreign key to posts.id cascade on delete)
   - author_id: uuid not null (foreign key to users.id)
   - content: text not null (max 1000 chars)
   - created_at: timestamp default now()

Indexes:
- posts: (author_id), (published_at DESC)
- comments: (post_id, created_at DESC)

Constraints:
- Prevent duplicate comments (same author_id, post_id, content within 1 minute)
```

**Bad:**
```
Create a database schema for a blog with posts and comments. Include all the fields you think we'll need and make sure it's normalized.
```

**Why It Matters:** The good prompt specifies exact column names, types, constraints, relationships, and indexes. The AI generates a complete, production-ready schema. The bad prompt forces the AI to guess at requirements, likely resulting in missing fields, wrong types, or over-normalized structures that don't match actual needs.

### Example 4: Test Suite Generation

**Good:**
```
Create pytest test suite for the calculate_discount() function.

Function signature:
```python
def calculate_discount(
    price: Decimal,
    discount_percent: int,
    user_tier: str
) -> Decimal:
    """Apply discount with tier-based caps"""
```

Test cases:
1. Basic discount: price=100, discount=10%, tier="standard" -> 90.00
2. Tier cap: price=100, discount=50%, tier="standard" -> 80.00 (max 20% for standard)
3. VIP tier: price=100, discount=50%, tier="vip" -> 50.00 (no cap)
4. Zero discount: price=100, discount=0%, tier="standard" -> 100.00
5. Edge cases:
   - Negative price -> raise ValueError
   - Discount > 100% -> raise ValueError
   - Invalid tier -> raise ValueError
   - Price=0 -> return 0

Test structure:
- One test class: TestCalculateDiscount
- Descriptive test names: test_applies_basic_discount_correctly
- Use pytest.mark.parametrize for similar cases
- Include docstrings explaining business logic
```

**Bad:**
```
Write tests for the discount calculation function. Cover edge cases and make sure it works correctly.
```

**Why It Matters:** The good prompt provides the function signature, expected behaviors, specific test cases with inputs and outputs, and test structure requirements. The AI generates a comprehensive test suite. The bad prompt leaves the AI guessing what "edge cases" matter and what "works correctly" means, likely producing incomplete coverage or testing irrelevant scenarios.

### Example 5: Documentation Generation

**Good:**
```
Create API documentation for the /api/orders endpoint.

Format: OpenAPI 3.0 YAML

Endpoint: GET /api/orders
Description: Retrieve user's order history with pagination

Query parameters:
- page: integer, default 1, min 1
- limit: integer, default 20, min 1, max 100
- status: string, optional, enum [pending, shipped, delivered, cancelled]
- start_date: string, optional, format ISO-8601 (YYYY-MM-DD)
- end_date: string, optional, format ISO-8601

Response 200:
```json
{
  "orders": [
    {
      "id": "uuid",
      "status": "string",
      "total": "number",
      "created_at": "ISO-8601 timestamp"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total_pages": 5,
    "total_items": 98
  }
}
```

Errors:
- 400: Invalid query parameters (include field-specific messages)
- 401: Authentication required
- 403: User cannot access these orders

Include examples for:
- Default pagination (no params)
- Filtered by status
- Date range query
```

**Bad:**
```
Document the orders API endpoint. Include all the usual stuff like parameters, responses, and errors.
```

**Why It Matters:** The good prompt specifies the documentation format, exact parameter details, response structure, error cases, and required examples. The AI generates complete, accurate documentation. The bad prompt assumes the AI knows what "usual stuff" means and what level of detail is needed, likely producing generic, incomplete documentation.

## Related Principles

- **[Principle #17 - Prompt Versioning and Testing](../technology/17-ai-tool-selection.md)** - Different AI tools respond differently to prompts; effective prompt engineering requires understanding each tool's strengths and prompt styles

- **[Principle #14 - Context Management as Discipline](../process/14-specification-before-implementation.md)** - Good specifications are effectively detailed prompts; writing specs trains prompt engineering skills

- **[Principle #16 - Docs Define, Not Describe](../process/16-human-review-decision-points.md)** - Effective prompts include review checkpoints; telling AI when to pause for human validation prevents wasted work

- **[Principle #25 - Simple Interfaces by Design](../technology/25-contract-first-api-design.md)** - API contracts are prompts for implementation; learning to write clear contracts improves prompt engineering

- **[Principle #05 - AI Agents as Team Members](05-ai-agents-as-team-members.md)** - Treating AI as team members means writing prompts like you'd write tickets for developers - clear, complete, actionable

- **[Principle #21 - Limited and Domain-Specific by Design](../process/21-decomposition-discipline.md)** - Breaking work into small pieces is prompt engineering; each piece becomes a focused, effective prompt

## Common Pitfalls

1. **Assuming Context the AI Doesn't Have**: Writing prompts as if the AI remembers everything from previous conversations or has access to your entire codebase.
   - Example: "Update the validation logic" without specifying which validation, in which file, or what to change
   - Impact: AI guesses wrong location or implementation, generates code that doesn't integrate with existing system

2. **Vague Success Criteria**: Not defining what "better", "optimized", or "fixed" means concretely.
   - Example: "Optimize this function" without specifying whether you care about speed, memory, readability, or maintainability
   - Impact: AI optimizes for the wrong dimension, potentially making the code worse for your actual needs

3. **Missing Error Handling Requirements**: Only describing the happy path without specifying edge cases or failure modes.
   - Example: "Create a file upload function" without mentioning size limits, file type validation, or error handling
   - Impact: Generated code works for basic cases but fails in production with unhelpful error messages

4. **Overloading Single Prompts**: Cramming multiple unrelated requests into one prompt, forcing the AI to juggle too many tasks.
   - Example: "Create the API endpoint, write tests, update documentation, and refactor the database layer to use this new approach"
   - Impact: AI does all tasks poorly rather than any well; produces unfocused, inconsistent results

5. **Not Providing Examples**: Describing requirements in abstract terms without concrete examples of inputs, outputs, or formats.
   - Example: "Validate user input appropriately" instead of showing specific valid and invalid examples
   - Impact: AI's interpretation of "appropriate" rarely matches your actual requirements

6. **Ignoring Format Specifications**: Expecting the AI to infer file structures, naming conventions, or code organization.
   - Example: "Generate database migrations" without specifying filename format, up/down structure, or SQL dialect
   - Impact: Generated files don't match project conventions, requiring manual reformatting

7. **No Iteration Plan**: Expecting perfect results from first prompt and getting frustrated when refinement is needed.
   - Example: Writing one massive prompt with every detail, then abandoning AI when it's not perfect
   - Impact: Wasted time on over-specified initial prompts; missing opportunities to iterate toward better solutions

## Tools & Frameworks

### Prompt Libraries and Templates
- **LangChain PromptTemplate**: Reusable prompt templates with variable interpolation for consistent prompt structure
- **OpenAI Cookbook**: Curated collection of effective prompt patterns for different tasks
- **Anthropic Prompt Library**: Task-specific prompt templates optimized for Claude models

### Prompt Engineering Platforms
- **PromptPerfect**: Tool for optimizing and testing prompts across multiple AI models
- **Humanloop**: Prompt management with versioning, A/B testing, and performance tracking
- **Dust**: Collaborative prompt engineering with team sharing and iteration history

### IDE Integration
- **GitHub Copilot**: Context-aware code suggestions that respond to code comments as prompts
- **Cursor**: IDE with built-in AI chat using surrounding code as automatic context
- **Continue**: Open-source IDE extension supporting multiple LLMs with prompt customization

### Testing and Validation
- **PromptFoo**: Framework for testing prompt variations and measuring output quality
- **LangSmith**: Debugging and testing tool for LLM applications with prompt tracing
- **Weight & Biases Prompts**: Experiment tracking for prompt engineering iterations

### Documentation and Learning
- **Learn Prompting**: Comprehensive guide with examples and best practices
- **OpenAI Playground**: Interactive environment for experimenting with prompts and parameters
- **Anthropic Workbench**: Prompt development environment with model comparison features

## Implementation Checklist

When implementing this principle, ensure:

- [ ] Every prompt includes explicit context about the current state and environment
- [ ] Complex tasks are broken into discrete, focused prompts rather than one massive request
- [ ] Success criteria are defined concretely with examples of expected outputs
- [ ] Edge cases and error handling requirements are explicitly specified
- [ ] Format and structure requirements (file naming, code organization) are stated clearly
- [ ] Examples of desired input/output behavior are included for complex logic
- [ ] Constraints and non-requirements are listed to prevent over-engineering
- [ ] Prompts include verification criteria so AI can self-check its output
- [ ] Iteration is planned - prompts start broad and refine based on results
- [ ] Technical terms are defined to prevent ambiguity (e.g., "idempotent" vs "immutable")
- [ ] Type hints, schemas, or interface definitions are provided for data structures
- [ ] Prompt templates are created for repetitive tasks to ensure consistency

## Metadata

**Category**: People
**Principle Number**: 03
**Related Patterns**: Chain of Thought Prompting, Few-Shot Learning, Prompt Chaining, Retrieval-Augmented Generation
**Prerequisites**: Understanding of AI capabilities and limitations, familiarity with target domain (e.g., programming languages, frameworks)
**Difficulty**: Medium
**Impact**: High

---

**Status**: Complete
**Last Updated**: 2025-09-30
**Version**: 1.0