# Principle #49 - Tool Use & Function Calling

## Plain-Language Definition

Tool use and function calling enable AI agents to interact with external systems by executing predefined functions based on natural language instructions. Instead of just generating text, agents can query databases, call APIs, manipulate files, perform calculations, and orchestrate complex workflows through a catalog of well-defined tools.

## Why This Matters for AI-First Development

When AI agents build and maintain systems, they need more than language generation—they need the ability to act. Tool use transforms agents from passive observers into active participants in software development. An agent that can only generate code suggestions is limited; an agent that can execute tests, query documentation, modify files, and deploy changes becomes a true development partner.

Tool use provides three critical capabilities for AI-driven development:

1. **Grounding in reality**: Tools connect agents to actual system state. Instead of hallucinating file contents or API responses, agents can retrieve real data, making their decisions based on facts rather than assumptions. This grounding is essential for reliable code generation and system modification.

2. **Action at scale**: Tools enable agents to perform thousands of operations that would take humans hours or days. An agent with file system access can refactor an entire codebase, analyze hundreds of logs, or validate configurations across dozens of services—all while maintaining consistency and following defined patterns.

3. **Iterative refinement through feedback**: When tools return results, agents can observe outcomes and adjust their approach. A test failure becomes feedback for code improvement. An API error message guides retry logic. This create-observe-refine loop is how agents learn to solve problems effectively.

Without effective tool use, AI agents remain theoretical. They can describe what should be done but can't actually do it. They can suggest fixes but can't verify them. They can generate code but can't test it. Poor tool design leads to agents that call the wrong functions, pass malformed parameters, ignore error messages, or make thousands of unnecessary API calls. The difference between an effective agent and a frustrating one often comes down to how well its tools are designed and documented.

## Implementation Approaches

### 1. **Structured Tool Definitions with JSON Schema**

Define tools using explicit schemas that specify input parameters, output formats, and behavior:

```python
from pydantic import BaseModel, Field
from typing import Optional, List

class SearchCodeParams(BaseModel):
    """Parameters for searching codebase."""
    pattern: str = Field(
        description="Regex pattern to search for. Use proper escaping."
    )
    file_types: Optional[List[str]] = Field(
        default=None,
        description="File extensions to search (e.g., ['.py', '.js']). Omit for all files."
    )
    case_sensitive: bool = Field(
        default=False,
        description="Whether pattern matching is case-sensitive"
    )

def search_code(pattern: str, file_types: Optional[List[str]] = None,
                case_sensitive: bool = False) -> dict:
    """
    Search codebase for pattern matches.

    Returns dictionary with 'matches' (list of {file, line, content})
    and 'total_count' (int). Limited to 100 matches.
    """
    # Implementation
    pass
```

**When to use**: When building new tools or refactoring existing ones. Strong typing prevents parameter errors and makes tool behavior predictable.

**Success looks like**: Agents rarely call tools with invalid parameters. Type errors are caught before execution, not during.

### 2. **Namespaced Tool Collections**

Group related tools under common prefixes to help agents select the right function:

```python
# File operations namespace
def file_read(path: str) -> str: pass
def file_write(path: str, content: str) -> None: pass
def file_search(directory: str, pattern: str) -> List[str]: pass

# Database operations namespace
def db_query(sql: str) -> List[dict]: pass
def db_execute(sql: str) -> int: pass
def db_schema(table: str) -> dict: pass

# API operations namespace
def api_get(endpoint: str) -> dict: pass
def api_post(endpoint: str, data: dict) -> dict: pass
def api_list(service: str) -> List[str]: pass
```

**When to use**: When you have more than 10-15 tools, or when tools from different services might overlap in functionality (e.g., multiple search tools).

**Success looks like**: Agents naturally select the right tool family, reducing confusion between similar operations from different services.

### 3. **Concise vs Detailed Response Modes**

Allow agents to control the verbosity of tool responses:

```python
from enum import Enum

class ResponseFormat(str, Enum):
    CONCISE = "concise"  # Human-readable summary
    DETAILED = "detailed"  # Full technical details
    IDS_ONLY = "ids"  # Just identifiers for chaining

def search_users(
    query: str,
    format: ResponseFormat = ResponseFormat.CONCISE
) -> dict:
    """Search users by name or email.

    CONCISE: Returns name, email (72 tokens avg)
    DETAILED: Includes ID, created_at, roles, metadata (206 tokens avg)
    IDS_ONLY: Just user IDs for further operations (15 tokens avg)
    """
    users = db.search(query)

    if format == ResponseFormat.IDS_ONLY:
        return {"user_ids": [u.id for u in users]}
    elif format == ResponseFormat.DETAILED:
        return {"users": [u.to_dict() for u in users]}
    else:  # CONCISE
        return {"users": [{"name": u.name, "email": u.email} for u in users]}
```

**When to use**: For tools that return variable amounts of data, especially when some calls are exploratory (need summaries) vs targeted (need full details).

**Success looks like**: Agents spend fewer tokens on tool responses while still getting necessary information. Context windows last longer.

### 4. **Helpful Error Messages with Recovery Guidance**

Design error responses to guide agents toward correct usage:

```python
def deploy_service(service_name: str, version: str) -> dict:
    """Deploy a service to production."""

    # Validate service exists
    if not service_exists(service_name):
        return {
            "error": "SERVICE_NOT_FOUND",
            "message": f"Service '{service_name}' does not exist",
            "suggestion": "Use list_services() to see available services",
            "available_services": list_services()[:5]  # Show first 5
        }

    # Validate version format
    if not is_valid_version(version):
        return {
            "error": "INVALID_VERSION",
            "message": f"Version '{version}' is not valid",
            "suggestion": "Use semantic versioning format (e.g., '1.2.3')",
            "example": "deploy_service('api-gateway', '2.1.0')"
        }

    # Proceed with deployment
    result = perform_deployment(service_name, version)
    return {"status": "deployed", "service": service_name, "version": version}
```

**When to use**: For all tools where parameter validation can fail or where agents might misunderstand tool capabilities.

**Success looks like**: Agents self-correct based on error messages without human intervention. Fewer repeated parameter errors.

### 5. **Token-Efficient Results with Pagination**

Limit response sizes and provide continuation mechanisms:

```python
def search_logs(
    query: str,
    max_results: int = 50,
    include_context: bool = True
) -> dict:
    """Search application logs.

    Args:
        max_results: Limit results (1-100, default 50)
        include_context: Include surrounding log lines (adds ~30% tokens)
    """
    if max_results > 100:
        max_results = 100  # Hard cap

    matches = perform_search(query)
    limited = matches[:max_results]

    response = {
        "matches": limited,
        "total_found": len(matches),
        "returned": len(limited)
    }

    if len(matches) > max_results:
        response["truncated"] = True
        response["suggestion"] = (
            f"Results limited to {max_results}. Found {len(matches)} total. "
            f"Use more specific query or filter by time range."
        )

    return response
```

**When to use**: For any tool that queries or retrieves collections of items (logs, files, records, search results).

**Success looks like**: Responses stay under 25,000 tokens. Agents naturally refine queries when results are truncated.

### 6. **Parallel Tool Execution Patterns**

Enable agents to call multiple tools simultaneously when operations are independent:

```python
from typing import List, Dict, Any
import asyncio

async def execute_tools_parallel(tool_calls: List[Dict[str, Any]]) -> List[Any]:
    """Execute multiple tool calls in parallel.

    Args:
        tool_calls: List of {tool_name, parameters} dicts

    Returns:
        List of results in same order as tool_calls
    """
    async def call_tool(tool_info):
        tool_name = tool_info["tool_name"]
        params = tool_info["parameters"]
        return await TOOL_REGISTRY[tool_name](**params)

    tasks = [call_tool(tc) for tc in tool_calls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results

# Example: Agent can request parallel execution
parallel_request = [
    {"tool_name": "file_read", "parameters": {"path": "src/main.py"}},
    {"tool_name": "file_read", "parameters": {"path": "tests/test_main.py"}},
    {"tool_name": "db_schema", "parameters": {"table": "users"}}
]
results = await execute_tools_parallel(parallel_request)
```

**When to use**: When building agent frameworks that support multi-step workflows where some operations don't depend on each other.

**Success looks like**: Agents complete multi-step tasks faster. Read operations happen in parallel before analysis begins.

## Good Examples vs Bad Examples

### Example 1: File Search Tool Definition

**Good:**
```python
def search_files(
    pattern: str,
    directory: str = ".",
    file_extensions: Optional[List[str]] = None,
    case_sensitive: bool = False,
    max_results: int = 100
) -> dict:
    """
    Search files for text pattern using regex.

    Args:
        pattern: Regular expression pattern (e.g., 'def.*\\(.*\\):' for Python functions)
        directory: Starting directory (default: current directory)
        file_extensions: Filter by extensions (e.g., ['.py', '.js']). None = all files.
        case_sensitive: Whether pattern matching is case-sensitive
        max_results: Maximum matches to return (1-1000, default 100)

    Returns:
        {
            "matches": [{"file": str, "line": int, "content": str}],
            "total_found": int,
            "truncated": bool
        }

    Example:
        search_files(pattern='TODO', file_extensions=['.py'], max_results=10)
    """
    pass
```

**Bad:**
```python
def search(q: str, d: str = None, ext: list = None) -> list:
    """Search for pattern in files."""
    # Unclear what 'q', 'd', 'ext' mean
    # No indication of regex support
    # Return type too vague
    # No example usage
    pass
```

**Why It Matters:** The good example provides clear parameter names, detailed descriptions, expected formats, and usage examples. Agents can call this tool correctly on first try. The bad example requires agents to guess or experiment, leading to errors.

### Example 2: API Call Error Handling

**Good:**
```python
def call_external_api(endpoint: str, method: str = "GET",
                     data: Optional[dict] = None) -> dict:
    """Call external REST API."""
    try:
        response = requests.request(method, endpoint, json=data)
        response.raise_for_status()
        return {"success": True, "data": response.json()}

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return {
                "error": "NOT_FOUND",
                "message": f"Endpoint {endpoint} does not exist",
                "suggestion": "Verify the endpoint path. Use list_endpoints() to see available paths.",
                "status_code": 404
            }
        elif e.response.status_code == 401:
            return {
                "error": "UNAUTHORIZED",
                "message": "Authentication required",
                "suggestion": "Check that API credentials are configured correctly",
                "status_code": 401
            }
        return {"error": "HTTP_ERROR", "message": str(e), "status_code": e.response.status_code}
```

**Bad:**
```python
def call_external_api(endpoint: str, method: str = "GET",
                     data: Optional[dict] = None) -> dict:
    """Call external REST API."""
    response = requests.request(method, endpoint, json=data)
    response.raise_for_status()  # Throws exception, agent can't handle
    return response.json()
```

**Why It Matters:** The good example catches errors and returns structured information that agents can act on. The bad example throws exceptions that interrupt agent execution. Agents need error information as data, not as exceptions.

### Example 3: Database Query Results

**Good:**
```python
def query_database(
    sql: str,
    format: ResponseFormat = ResponseFormat.CONCISE
) -> dict:
    """Execute SQL query and return results.

    CONCISE: Returns row count and first 5 rows (fast, low token count)
    DETAILED: Returns all rows with column types (comprehensive)
    """
    results = db.execute(sql)

    if format == ResponseFormat.CONCISE:
        return {
            "row_count": len(results),
            "sample_rows": results[:5],
            "truncated": len(results) > 5,
            "columns": list(results[0].keys()) if results else []
        }
    else:  # DETAILED
        return {
            "rows": results,
            "row_count": len(results),
            "columns": get_column_info(results)
        }
```

**Bad:**
```python
def query_database(sql: str) -> List[dict]:
    """Execute SQL query."""
    return db.execute(sql)  # Returns all rows, could be thousands
    # No indication of size
    # No way to request summary
    # No column information
```

**Why It Matters:** Large result sets consume agent context windows. The good example provides control over verbosity and prevents context overflow. The bad example might return 10,000 rows when agent only needed to verify data exists.

### Example 4: Tool Parameter Validation

**Good:**
```python
def deploy_application(
    app_name: str,
    environment: str,
    version: str
) -> dict:
    """Deploy application to specified environment."""

    # Validate inputs with helpful feedback
    valid_envs = ["dev", "staging", "production"]
    if environment not in valid_envs:
        return {
            "error": "INVALID_ENVIRONMENT",
            "message": f"Environment must be one of: {valid_envs}",
            "provided": environment,
            "suggestion": f"Did you mean '{find_closest_match(environment, valid_envs)}'?"
        }

    if not app_exists(app_name):
        return {
            "error": "APP_NOT_FOUND",
            "available_apps": list_apps()[:10],
            "suggestion": "Use list_apps() to see all applications"
        }

    # Proceed with deployment
    return deploy(app_name, environment, version)
```

**Bad:**
```python
def deploy_application(app_name: str, environment: str, version: str) -> dict:
    """Deploy application."""
    # No validation
    return deploy(app_name, environment, version)  # Fails cryptically on invalid input
```

**Why It Matters:** Input validation with helpful messages guides agents toward correct usage. The bad example fails silently or with cryptic errors, forcing agents to guess correct values.

### Example 5: File Operations with Idempotency

**Good:**
```python
def write_file(path: str, content: str, create_dirs: bool = True) -> dict:
    """
    Write content to file, replacing if exists.

    Idempotent: writing same content multiple times produces same result.
    """
    file_path = Path(path)

    if create_dirs:
        file_path.parent.mkdir(parents=True, exist_ok=True)

    file_path.write_text(content)

    return {
        "success": True,
        "path": str(file_path),
        "size_bytes": len(content),
        "created": not file_path.existed_before_write  # Track for agent awareness
    }
```

**Bad:**
```python
def append_to_file(path: str, content: str) -> None:
    """Append content to file."""
    with open(path, 'a') as f:  # Append mode
        f.write(content)
    # Not idempotent - multiple calls accumulate content
    # No feedback about what happened
```

**Why It Matters:** The good example is idempotent (safe to retry) and provides feedback. The bad example breaks on retry, causing data duplication when agents encounter errors.

## Related Principles

- **[Principle #48 - Chain-of-Thought Reasoning](48-chain-of-thought-reasoning.md)** - Tools enable agents to ground reasoning in external facts. Chain-of-thought helps agents decide which tools to call and in what order.

- **[Principle #52 - Multi-Agent Orchestration](52-multi-agent-orchestration.md)** - Tool use enables agents to coordinate actions. Each agent uses tools to communicate results and trigger downstream operations.

- **[Principle #31 - Idempotency by Design](31-idempotency-by-design.md)** - Tools must be idempotent so agents can safely retry operations. Tool design should assume calls may be retried on failure.

- **[Principle #29 - Tool Ecosystems and MCP](29-tool-ecosystems-mcp.md)** - Model Context Protocol provides standardized way to define and discover tools. Tool implementations should follow MCP conventions.

- **[Principle #32 - Error Recovery Patterns](32-error-recovery-patterns.md)** - Tool error responses should enable recovery. Return structured errors that agents can handle programmatically.

- **[Principle #26 - Stateless by Default](26-stateless-by-default.md)** - Stateless tools are easier for agents to reason about. Each tool call should be independent when possible.

## Common Pitfalls

1. **Vague Tool Descriptions**
   - Example: `def process_data(data): """Process the data."""`
   - Impact: Agents don't know what "process" means, what data format is expected, or what output to expect. Results in trial-and-error tool calling.
   - How to avoid: Write descriptions like you're explaining to a junior developer. Include input format, output format, side effects, and examples.

2. **Returning Technical IDs Instead of Human-Readable Values**
   - Example: Returning `user_uuid='f47ac10b-58cc-4372-a567-0e02b2c3d479'` instead of `user_name='jane@example.com'`
   - Impact: Agents can't reason about UUIDs naturally. They hallucinate or ignore identifier fields.
   - How to avoid: Return semantic identifiers (names, emails, readable codes) for agent reasoning, with technical IDs available in "detailed" mode.

3. **No Token Limits on Tool Responses**
   - Example: `list_files()` returns all 5,000 files in directory consuming 50,000 tokens
   - Impact: Single tool call exhausts agent's context window, preventing further reasoning or tool use.
   - How to avoid: Implement max_results parameters (default to ~50-100), pagination, and truncation warnings.

4. **Throwing Exceptions Instead of Returning Error Data**
   - Example: Tool raises `FileNotFoundError` when file doesn't exist
   - Impact: Exception breaks agent execution. Agent can't learn from error or try alternative approaches.
   - How to avoid: Catch exceptions and return structured error objects with suggestions for recovery.

5. **Overlapping Tool Functionality Without Clear Boundaries**
   - Example: Having both `search_users()`, `find_users()`, and `get_users()` that do similar things
   - Impact: Agents get confused about which tool to use, making wrong choices or trying all three.
   - How to avoid: Consolidate similar tools. Use namespacing and clear naming conventions to distinguish tool purposes.

6. **Missing Examples in Tool Documentation**
   - Example: Tool description explains parameters but doesn't show actual usage
   - Impact: Agents must guess correct parameter combinations, leading to syntax errors or semantic mistakes.
   - How to avoid: Include 1-2 example calls in every tool description showing common use cases.

7. **Side Effects Not Documented**
   - Example: `update_config()` also restarts services, but doesn't mention this
   - Impact: Agents call tools without understanding full consequences, causing unintended system changes.
   - How to avoid: Explicitly document all side effects, including state changes, external calls, and performance implications.

## Tools & Frameworks

### Function Calling APIs
- **[OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)**: JSON schema-based tool definitions with automatic parameter extraction
- **[Anthropic Tool Use](https://docs.anthropic.com/en/docs/build-with-claude/tool-use)**: Structured tool definitions with XML and JSON support
- **[Google Function Calling](https://ai.google.dev/gemini-api/docs/function-calling)**: Similar to OpenAI with Gemini-specific optimizations

### Agent Frameworks
- **[LangChain Tools](https://python.langchain.com/docs/modules/tools/)**: Pre-built tool library and custom tool creation framework
- **[LlamaIndex Tools](https://docs.llamaindex.ai/en/stable/module_guides/deploying/agents/tools/)**: Tools optimized for data retrieval and RAG workflows
- **[AutoGPT](https://github.com/Significant-Gravitas/AutoGPT)**: Agent with extensive tool library for autonomous operation
- **[Model Context Protocol (MCP)](https://modelcontextprotocol.io/)**: Standardized protocol for tool definitions and discovery

### Tool Development Libraries
- **[Pydantic](https://docs.pydantic.dev/)**: Strong typing for tool parameter validation
- **[FastAPI](https://fastapi.tiangolo.com/)**: Tool endpoints with automatic OpenAPI schema generation
- **[Instructor](https://python.useinstructor.com/)**: Structured outputs from LLM calls with validation

### Testing & Validation
- **[pytest-mock](https://pytest-mock.readthedocs.io/)**: Mock tool calls during agent testing
- **[VCR.py](https://vcrpy.readthedocs.io/)**: Record and replay tool API calls
- **[Hypothesis](https://hypothesis.readthedocs.io/)**: Property-based testing for tool behavior

### Observability
- **[LangSmith](https://www.langchain.com/langsmith)**: Trace tool calls and agent execution
- **[Weights & Biases](https://wandb.ai/)**: Log tool usage metrics and performance
- **[Helicone](https://www.helicone.ai/)**: Monitor tool call success rates and latency

## Implementation Checklist

When implementing this principle, ensure:

- [ ] All tool names are clear, descriptive, and follow consistent naming conventions (e.g., `verb_noun` pattern)
- [ ] Tool descriptions include input parameters, output format, side effects, and usage examples
- [ ] Parameters use strong typing (JSON Schema, Pydantic, TypeScript interfaces) with validation
- [ ] Tool responses have token limits (max 25,000 tokens) with pagination for larger results
- [ ] Error responses return structured data (not exceptions) with actionable recovery suggestions
- [ ] Tools support both "concise" and "detailed" response modes for context efficiency
- [ ] Idempotent operations are clearly marked and tested for safe retry behavior
- [ ] Tool documentation specifies whether operations are read-only vs state-changing
- [ ] Related tools are namespaced (e.g., `file_*`, `db_*`, `api_*`) to help agents categorize
- [ ] Each tool has at least one example call in its documentation
- [ ] Tools validate inputs and return helpful error messages for invalid parameters
- [ ] Tool response formats are consistent (all tools return `{"success": bool, "data": ...}` structure)
- [ ] Large result sets include truncation warnings and guidance for refinement
- [ ] Tools that call external APIs handle timeouts and network errors gracefully
- [ ] Tool registry is discoverable (agents can list available tools with descriptions)

## Metadata

**Category**: Technology
**Principle Number**: 49
**Related Patterns**: Function Calling, ReAct, Tool Augmented LLMs, MCP, Agent Workflows
**Prerequisites**: Understanding of API design, JSON schemas, error handling, async operations
**Difficulty**: Medium
**Impact**: High

---

**Status**: Complete
**Last Updated**: 2025-09-30
**Version**: 1.0
