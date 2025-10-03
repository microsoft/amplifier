# Principle #21 - Limited and Domain-Specific by Design

## Plain-Language Definition

Design tools and operations with narrow, well-defined boundaries rather than general-purpose capabilities. Limited, domain-specific tools are more reliable, safer, and easier for AI to use correctly than flexible, general-purpose ones.

## Why This Matters for AI-First Development

When AI agents interact with systems, they must understand what operations are safe, what side effects might occur, and what constraints apply. General-purpose tools like "execute arbitrary code" or "modify any file" force AI agents to reason about unlimited possibilities, increasing the risk of unintended consequences. Limited, domain-specific tools constrain the problem space, making it easier for AI to make correct decisions.

Domain-specific design provides three critical benefits for AI-driven development:

1. **Reduced cognitive load**: A focused tool like "update user profile" requires less context than "execute database query." The AI can reason about a smaller set of possibilities and edge cases, leading to more reliable decisions.

2. **Built-in safety**: Narrow tools embed domain constraints directly into their design. A tool that only updates user profiles can't accidentally delete the entire database. This makes systems safer by default, even when AI makes mistakes.

3. **Clearer intent**: Domain-specific operations make code self-documenting. When an AI uses `validate_and_update_email()` instead of `execute_sql()`, the intent is obvious. This improves maintainability and makes it easier to audit AI-generated code.

Without domain-specific design, AI systems become unpredictable. An AI with access to a general-purpose database client might generate a query that locks tables, corrupts data, or exposes sensitive information. An AI with filesystem access might modify critical system files. An AI with network access might make unbounded external requests. These risks multiply in AI-first systems where autonomous agents make decisions without constant human oversight.

## Implementation Approaches

### 1. **Narrow Function Scope**

Design functions that do one specific thing within a bounded domain:

```python
# Domain-specific functions instead of general-purpose ones
def update_user_email(user_id: str, new_email: str) -> None:
    """Updates only the email field, with validation and audit logging"""
    validate_email_format(new_email)
    check_email_uniqueness(new_email)
    user = get_user(user_id)
    old_email = user.email
    user.email = new_email
    save_user(user)
    log_email_change(user_id, old_email, new_email)
```

This approach works well when you have well-understood domain operations with clear requirements. Success looks like functions that handle all edge cases for their specific domain without requiring callers to know implementation details.

### 2. **Domain-Specific Languages (DSLs)**

Create constrained languages for specific domains:

```python
# Configuration DSL instead of arbitrary Python code
class DeploymentConfig:
    """DSL for deployment that only allows safe operations"""
    def __init__(self):
        self._steps = []

    def deploy_service(self, name: str, version: str):
        self._steps.append(DeploymentStep("deploy", name, version))
        return self

    def run_migration(self, migration_name: str):
        self._steps.append(MigrationStep(migration_name))
        return self

    def health_check(self, endpoint: str, timeout: int = 30):
        self._steps.append(HealthCheckStep(endpoint, timeout))
        return self

# AI can generate: config.deploy_service("api", "v2.1").run_migration("add_users").health_check("/health")
# AI cannot: Arbitrary code execution, file system access, network calls
```

DSLs are ideal when you need to give AI flexibility within strict boundaries. Success means AI can express complex workflows while being physically unable to perform dangerous operations.

### 3. **Constrained Operations with Explicit Allowlists**

Limit operations to an explicit set of allowed actions:

```python
class ConstrainedFileOps:
    """File operations limited to specific directories and file types"""
    ALLOWED_DIRS = ["/app/uploads", "/app/temp"]
    ALLOWED_EXTENSIONS = [".txt", ".json", ".csv"]

    def read_file(self, path: Path) -> str:
        self._validate_path(path)
        return path.read_text()

    def write_file(self, path: Path, content: str) -> None:
        self._validate_path(path)
        path.write_text(content)

    def _validate_path(self, path: Path):
        # Check directory
        if not any(path.is_relative_to(d) for d in self.ALLOWED_DIRS):
            raise ValueError(f"Path {path} not in allowed directories")
        # Check extension
        if path.suffix not in self.ALLOWED_EXTENSIONS:
            raise ValueError(f"Extension {path.suffix} not allowed")
```

Use this approach when you need to prevent entire categories of dangerous operations. Success means AI can perform useful work while being physically blocked from accessing restricted resources.

### 4. **Focused Tool Interfaces**

Design tool interfaces that only expose domain-specific operations:

```python
class UserManagementTool:
    """AI tool focused solely on user management operations"""

    def create_user(self, email: str, name: str, role: str) -> User:
        """Create a new user with standard validation"""
        pass

    def update_user_role(self, user_id: str, new_role: str) -> User:
        """Update only the role field"""
        pass

    def deactivate_user(self, user_id: str, reason: str) -> None:
        """Soft delete with audit trail"""
        pass

    # Notably absent: direct database access, arbitrary field updates,
    # deletion without audit, access to other tables
```

This works best for AI agents that need to perform complex multi-step operations within a single domain. Success looks like agents that can handle user management tasks end-to-end without risk of affecting other parts of the system.

### 5. **Bounded Contexts with Clear Interfaces**

Organize code into bounded contexts with explicit interface contracts:

```python
# Payment processing bounded context
class PaymentProcessor:
    """Handles all payment operations in isolation"""

    def process_payment(self, amount: Decimal, payment_method: PaymentMethod) -> PaymentResult:
        """Process payment - only entry point for payment logic"""
        pass

    def refund_payment(self, payment_id: str, amount: Decimal, reason: str) -> RefundResult:
        """Process refund - encapsulates all refund logic"""
        pass

    # Internal methods are private - not exposed to AI
    def _validate_payment_method(self): pass
    def _charge_card(self): pass
    def _update_balance(self): pass
```

Use bounded contexts when you need to isolate complex domains with many internal operations. Success means AI can perform high-level operations without needing to understand or access internal implementation details.

### 6. **Template-Based Generation**

Provide templates with constrained placeholders:

```python
class EmailTemplate:
    """Email generation with constrained substitution"""

    TEMPLATE = """
    Hello {name},

    Your account status is: {status}

    Login at: {login_url}

    Support: {support_email}
    """

    ALLOWED_FIELDS = {"name", "status", "login_url", "support_email"}

    def generate(self, **fields) -> str:
        # Only allow specific fields
        unknown = set(fields.keys()) - self.ALLOWED_FIELDS
        if unknown:
            raise ValueError(f"Unknown fields: {unknown}")

        return self.TEMPLATE.format(**fields)

# AI can: Populate templates with domain data
# AI cannot: Inject arbitrary HTML, JavaScript, or formatting
```

This approach works well for content generation where you need consistency and safety. Success means AI generates varied content while maintaining format constraints and security boundaries.

## Good Examples vs Bad Examples

### Example 1: Database Operations

**Good:**
```python
class UserRepository:
    """Domain-specific database operations for users only"""

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Fetch a single user by ID"""
        result = self.db.query(
            "SELECT id, email, name, role FROM users WHERE id = %s",
            (user_id,)
        )
        return User.from_row(result) if result else None

    def update_user_email(self, user_id: str, new_email: str) -> None:
        """Update only the email field with validation"""
        if not self._is_valid_email(new_email):
            raise ValueError("Invalid email format")
        self.db.execute(
            "UPDATE users SET email = %s WHERE id = %s",
            (new_email, user_id)
        )

    def list_active_users(self, limit: int = 100) -> List[User]:
        """List active users with pagination"""
        results = self.db.query(
            "SELECT id, email, name, role FROM users WHERE active = true LIMIT %s",
            (limit,)
        )
        return [User.from_row(r) for r in results]
```

**Bad:**
```python
class Database:
    """General-purpose database access - too powerful"""

    def execute_query(self, sql: str, params: tuple = ()) -> List[dict]:
        """Execute any SQL query"""
        return self.db.execute(sql, params)

    def execute_many(self, sql: str, param_list: List[tuple]) -> None:
        """Execute batch queries"""
        self.db.executemany(sql, param_list)

# AI might generate:
# db.execute_query("DELETE FROM users")  # Oops, deleted all users
# db.execute_query("SELECT * FROM sensitive_data")  # Exposed secrets
# db.execute_query("UPDATE users SET role = 'admin'")  # Privilege escalation
```

**Why It Matters:** General-purpose database access is one of the most dangerous capabilities to give an AI. A domain-specific repository constrains operations to safe, validated queries within a single table or domain. The AI can't accidentally (or maliciously) delete data, access unauthorized tables, or create SQL injection vulnerabilities.

### Example 2: File System Operations

**Good:**
```python
class DocumentStore:
    """Domain-specific document storage with built-in constraints"""

    ALLOWED_DIR = Path("/app/documents")
    ALLOWED_EXTENSIONS = {".txt", ".md", ".json"}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    def save_document(self, filename: str, content: str, user_id: str) -> Path:
        """Save a document with validation and user isolation"""
        # Validate filename
        if not self._is_safe_filename(filename):
            raise ValueError("Invalid filename")

        # Check extension
        path = Path(filename)
        if path.suffix not in self.ALLOWED_EXTENSIONS:
            raise ValueError(f"File type {path.suffix} not allowed")

        # Check size
        if len(content.encode()) > self.MAX_FILE_SIZE:
            raise ValueError("File too large")

        # Save to user's subdirectory
        user_dir = self.ALLOWED_DIR / user_id
        user_dir.mkdir(parents=True, exist_ok=True)
        full_path = user_dir / filename

        full_path.write_text(content)
        return full_path

    def read_document(self, filename: str, user_id: str) -> str:
        """Read a document with user isolation"""
        full_path = self.ALLOWED_DIR / user_id / filename
        if not full_path.exists():
            raise FileNotFoundError(f"Document {filename} not found")
        return full_path.read_text()

    def _is_safe_filename(self, filename: str) -> bool:
        """Check for path traversal attempts"""
        return ".." not in filename and "/" not in filename and "\\" not in filename
```

**Bad:**
```python
class FileSystem:
    """General-purpose file operations - dangerous"""

    def read_file(self, path: str) -> str:
        """Read any file"""
        return Path(path).read_text()

    def write_file(self, path: str, content: str) -> None:
        """Write to any file"""
        Path(path).write_text(content)

    def delete_file(self, path: str) -> None:
        """Delete any file"""
        Path(path).unlink()

    def list_directory(self, path: str) -> List[str]:
        """List any directory"""
        return [f.name for f in Path(path).iterdir()]

# AI might generate:
# fs.read_file("/etc/passwd")  # Read system files
# fs.write_file("/app/config.py", malicious_code)  # Overwrite code
# fs.delete_file("/app/database.db")  # Delete critical data
# fs.list_directory("/home/admin")  # Browse private directories
```

**Why It Matters:** Unrestricted filesystem access is a critical vulnerability. AI agents need to read and write files, but they should only access specific directories with specific file types. The domain-specific DocumentStore enforces these constraints at the interface level, making it impossible for AI to access system files or traverse directories.

### Example 3: Configuration Management

**Good:**
```python
class FeatureFlags:
    """Domain-specific feature flag management"""

    VALID_FLAGS = {
        "new_ui_enabled": bool,
        "max_upload_size": int,
        "notification_delay": int,
        "beta_features": list,
    }

    def __init__(self, config_store: ConfigStore):
        self.store = config_store

    def get_flag(self, flag_name: str) -> Any:
        """Get a feature flag value with type validation"""
        if flag_name not in self.VALID_FLAGS:
            raise ValueError(f"Unknown feature flag: {flag_name}")

        value = self.store.get(f"feature_flags.{flag_name}")
        expected_type = self.VALID_FLAGS[flag_name]

        if not isinstance(value, expected_type):
            raise TypeError(f"Flag {flag_name} must be {expected_type}")

        return value

    def set_flag(self, flag_name: str, value: Any) -> None:
        """Set a feature flag with validation"""
        if flag_name not in self.VALID_FLAGS:
            raise ValueError(f"Unknown feature flag: {flag_name}")

        expected_type = self.VALID_FLAGS[flag_name]
        if not isinstance(value, expected_type):
            raise TypeError(f"Flag {flag_name} must be {expected_type}")

        # Additional validation for specific flags
        if flag_name == "max_upload_size" and value < 0:
            raise ValueError("max_upload_size must be positive")

        self.store.set(f"feature_flags.{flag_name}", value)

    def list_flags(self) -> Dict[str, Any]:
        """List all feature flags"""
        return {name: self.get_flag(name) for name in self.VALID_FLAGS}
```

**Bad:**
```python
class Configuration:
    """General-purpose configuration - too flexible"""

    def __init__(self, config_store: ConfigStore):
        self.store = config_store

    def get(self, key: str) -> Any:
        """Get any configuration value"""
        return self.store.get(key)

    def set(self, key: str, value: Any) -> None:
        """Set any configuration value"""
        self.store.set(key, value)

    def delete(self, key: str) -> None:
        """Delete any configuration value"""
        self.store.delete(key)

# AI might generate:
# config.set("database.host", "attacker.com")  # Redirect database
# config.set("admin.password", "hacked")  # Change credentials
# config.delete("security.enabled")  # Disable security
# config.get("api_keys.stripe")  # Expose secrets
```

**Why It Matters:** Configuration systems control critical application behavior. A general-purpose config interface allows AI to modify any setting, potentially disabling security, exposing secrets, or breaking the application. Domain-specific feature flags constrain AI to a predefined set of safe toggles with type validation.

### Example 4: API Client Design

**Good:**
```python
class GitHubIssueClient:
    """Domain-specific GitHub client focused only on issues"""

    def __init__(self, repo: str, token: str):
        self.repo = repo
        self.token = token
        self.base_url = f"https://api.github.com/repos/{repo}"

    def create_issue(self, title: str, body: str, labels: List[str] = None) -> Issue:
        """Create a new issue with validation"""
        if not title or len(title) > 256:
            raise ValueError("Title must be 1-256 characters")

        payload = {
            "title": title,
            "body": body or "",
            "labels": labels or []
        }

        response = self._post(f"{self.base_url}/issues", json=payload)
        return Issue.from_dict(response)

    def add_comment(self, issue_number: int, comment: str) -> Comment:
        """Add a comment to an existing issue"""
        if not comment:
            raise ValueError("Comment cannot be empty")

        payload = {"body": comment}
        response = self._post(
            f"{self.base_url}/issues/{issue_number}/comments",
            json=payload
        )
        return Comment.from_dict(response)

    def list_issues(self, state: str = "open", limit: int = 30) -> List[Issue]:
        """List issues with pagination"""
        if state not in ["open", "closed", "all"]:
            raise ValueError("State must be 'open', 'closed', or 'all'")

        params = {"state": state, "per_page": min(limit, 100)}
        response = self._get(f"{self.base_url}/issues", params=params)
        return [Issue.from_dict(i) for i in response]

    def _get(self, url: str, **kwargs):
        """Internal method for GET requests"""
        return requests.get(url, headers=self._headers(), **kwargs).json()

    def _post(self, url: str, **kwargs):
        """Internal method for POST requests"""
        return requests.post(url, headers=self._headers(), **kwargs).json()

    def _headers(self):
        return {"Authorization": f"token {self.token}"}
```

**Bad:**
```python
class GitHubClient:
    """General-purpose GitHub client - too powerful"""

    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.github.com"

    def request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Make any HTTP request to GitHub API"""
        url = f"{self.base_url}/{endpoint}"
        headers = {"Authorization": f"token {self.token}"}

        response = requests.request(method, url, headers=headers, **kwargs)
        return response.json()

# AI might generate:
# client.request("DELETE", "repos/company/critical-repo")  # Delete repository
# client.request("POST", "repos/company/repo/collaborators/attacker")  # Add collaborator
# client.request("PATCH", "repos/company/repo", json={"private": False})  # Make repo public
# client.request("GET", "user/keys")  # Access SSH keys
```

**Why It Matters:** API clients often have authentication tokens with broad permissions. A general-purpose client gives AI access to all API endpoints, including destructive operations. A domain-specific client exposes only safe operations with validation, making it impossible to accidentally delete repositories or modify permissions.

### Example 5: Code Generation

**Good:**
```python
class SQLQueryBuilder:
    """Domain-specific SQL builder with safety constraints"""

    def __init__(self, table: str):
        if not self._is_valid_identifier(table):
            raise ValueError("Invalid table name")
        self.table = table
        self._select_fields = []
        self._where_conditions = []
        self._limit = None

    def select(self, *fields: str):
        """Add fields to SELECT clause"""
        for field in fields:
            if not self._is_valid_identifier(field):
                raise ValueError(f"Invalid field name: {field}")
        self._select_fields.extend(fields)
        return self

    def where(self, field: str, operator: str, value: Any):
        """Add WHERE condition with parameterization"""
        if not self._is_valid_identifier(field):
            raise ValueError(f"Invalid field name: {field}")
        if operator not in ["=", "!=", ">", "<", ">=", "<=", "LIKE"]:
            raise ValueError(f"Invalid operator: {operator}")

        self._where_conditions.append((field, operator, value))
        return self

    def limit(self, count: int):
        """Add LIMIT clause"""
        if count < 1 or count > 1000:
            raise ValueError("Limit must be between 1 and 1000")
        self._limit = count
        return self

    def build(self) -> Tuple[str, tuple]:
        """Build parameterized query (returns SQL and params)"""
        if not self._select_fields:
            raise ValueError("Must specify SELECT fields")

        fields = ", ".join(self._select_fields)
        query = f"SELECT {fields} FROM {self.table}"

        params = []
        if self._where_conditions:
            conditions = []
            for field, op, value in self._where_conditions:
                conditions.append(f"{field} {op} %s")
                params.append(value)
            query += " WHERE " + " AND ".join(conditions)

        if self._limit:
            query += f" LIMIT {self._limit}"

        return query, tuple(params)

    def _is_valid_identifier(self, name: str) -> bool:
        """Validate SQL identifiers to prevent injection"""
        return name.replace("_", "").isalnum()

# Usage:
query, params = (
    SQLQueryBuilder("users")
    .select("id", "email", "name")
    .where("active", "=", True)
    .where("role", "=", "admin")
    .limit(10)
    .build()
)
# Result: ("SELECT id, email, name FROM users WHERE active = %s AND role = %s LIMIT 10", (True, "admin"))
```

**Bad:**
```python
class SQLExecutor:
    """General-purpose SQL execution - dangerous"""

    def execute(self, sql: str) -> List[dict]:
        """Execute any SQL query"""
        cursor = self.db.cursor()
        cursor.execute(sql)
        return cursor.fetchall()

    def execute_many(self, sql: str) -> None:
        """Execute multiple SQL statements"""
        for statement in sql.split(";"):
            if statement.strip():
                self.execute(statement)

# AI might generate:
# executor.execute("SELECT * FROM users; DROP TABLE users;")  # SQL injection
# executor.execute("UPDATE users SET password = 'hacked'")  # Mass update
# executor.execute("GRANT ALL PRIVILEGES ON *.* TO 'attacker'@'%'")  # Privilege escalation
# executor.execute_many(malicious_sql_script)  # Execute arbitrary SQL
```

**Why It Matters:** SQL injection is one of the most common and dangerous vulnerabilities. Giving AI the ability to generate arbitrary SQL is asking for trouble. A domain-specific query builder constrains the AI to safe operations with parameterized queries, making SQL injection physically impossible while still allowing flexible query construction.

## Related Principles

- **[Principle #25 - Simple Interfaces by Design](25-minimize-blast-radius.md)** - Limited tools naturally minimize blast radius by constraining what can be affected when things go wrong. Domain-specific operations can only impact their specific domain, preventing cascading failures.

- **[Principle #14 - Context Management as Discipline](../governance/14-context-aware-guardrails.md)** - Domain-specific design is a form of guardrail. By limiting what's possible at the interface level, you create automatic constraints that don't require AI to make safety decisions.

- **[Principle #29 - Tool Ecosystems as Extensions](29-safe-defaults-explicit-overrides.md)** - Domain-specific tools embody safe defaults. The interface only exposes safe operations; dangerous operations aren't available even as overrides.

- **[Principle #35 - Least-Privilege Automation with Scoped Permissions](35-automation-human-checkpoints.md)** - Limited tools make automated operations safer and reduce the number of human checkpoints needed. When tools can only perform safe operations, more automation can proceed without human review.

- **[Principle #41 - Adaptive Sandboxing with Explicit Approvals](../governance/41-verifiable-constraints.md)** - Domain-specific interfaces are verifiable constraints. You can prove that certain operations are impossible by examining the tool's interface rather than auditing all usage.

- **[Principle #03 - Small, Focused Agents Over God Mode](../people/03-small-focused-agents.md)** - This principle applies to tools what Principle #3 applies to agents. Just as focused agents are more reliable than general-purpose ones, focused tools are safer and more predictable than general-purpose ones.

## Common Pitfalls

1. **Leaky Abstractions**: Creating domain-specific tools that expose underlying implementation details, defeating the purpose of the constraint.
   - Example: `user_repo.execute_raw_sql(query)` method in an otherwise domain-specific repository.
   - Impact: AI can bypass all domain constraints by using the "escape hatch," making the limited interface pointless.

2. **Over-Constraining to Uselessness**: Making tools so narrow that they can't accomplish real work, forcing developers to work around them.
   - Example: A file tool that can only write files named "output.txt" in one directory.
   - Impact: Developers bypass the tool entirely, building their own general-purpose alternatives that lack safety features.

3. **Inconsistent Constraint Enforcement**: Some tools in the system are constrained while others are general-purpose, creating confusion about what's safe.
   - Example: Domain-specific `UserRepository` alongside general-purpose `Database.execute()`.
   - Impact: AI uses whichever tool is more convenient, often choosing the dangerous general-purpose option.

4. **Missing Essential Operations**: Domain-specific tools that don't cover common use cases, forcing workarounds.
   - Example: Email tool that can send emails but can't attach files or use templates.
   - Impact: Real work requires multiple tools or hacks, increasing complexity and error potential.

5. **Documentation Doesn't Match Reality**: Tools documented as "limited" but with hidden general-purpose capabilities or vice versa.
   - Example: API client documented as "read-only" but has undocumented mutation methods.
   - Impact: AI makes incorrect assumptions about safety, leading to unexpected behavior.

6. **Failing to Version Constraints**: Changing what operations a domain-specific tool allows without versioning, breaking existing code.
   - Example: Adding a new required parameter to every method in a previously simple tool.
   - Impact: Code that worked yesterday breaks today, and AI-generated code becomes unreliable.

7. **Building Too Many Tiny Tools**: Creating hundreds of ultra-specific tools instead of well-designed domain-specific ones.
   - Example: Separate tools for `update_user_email`, `update_user_name`, `update_user_phone`, etc.
   - Impact: Tool proliferation creates cognitive overhead and maintenance burden without meaningful safety benefits.

## Tools & Frameworks

### Domain-Specific Language Frameworks
- **Lark**: Python library for building parsers for domain-specific languages with grammar-based validation
- **ANTLR**: Powerful parser generator for creating DSLs with complex syntax and strong type systems
- **pyparsing**: Python library for building recursive descent parsers, ideal for configuration DSLs
- **Jinja2**: Template engine that can be constrained to create safe content generation DSLs

### API Design Tools
- **FastAPI**: Python framework with strong typing and automatic validation, ideal for constrained API design
- **GraphQL**: Query language that provides schema-based constraints on what clients can request
- **gRPC**: Protocol buffer-based RPC framework with strong type definitions and service boundaries
- **JSON Schema**: Specification for constraining and documenting JSON APIs with validation rules

### Configuration Management
- **Pydantic**: Python library for data validation using type annotations, perfect for constrained configuration
- **StrictYAML**: YAML parser that enforces strict validation rules and prevents common configuration errors
- **Dynaconf**: Configuration management with environment-specific validation and schema enforcement
- **python-decouple**: Strict separation of settings from code with type validation

### Database Access Patterns
- **SQLAlchemy ORM**: Object-relational mapper that creates domain-specific models instead of raw SQL
- **Django ORM**: High-level ORM with model-based constraints and built-in validation
- **Prisma**: Type-safe database client with schema-based query building
- **Peewee**: Lightweight ORM focused on simple domain models with clear boundaries

### Code Generation Tools
- **Jinja2 Templates**: Safe template rendering with sandboxed execution environments
- **dataclasses**: Python's built-in library for creating simple, constrained data structures
- **attrs**: Library for defining classes with automatic validation and constraint enforcement
- **marshmallow**: Object serialization with schema-based validation and domain constraints

## Implementation Checklist

When implementing this principle, ensure:

- [ ] Tools have clearly defined, documented boundaries for their domain of operation
- [ ] Operations that fall outside tool boundaries are physically impossible, not just discouraged
- [ ] Each tool's interface explicitly states what it can and cannot do
- [ ] Validation happens at the tool interface, not relying on caller responsibility
- [ ] Error messages clearly indicate when operations exceed domain boundaries
- [ ] Documentation includes both capabilities and explicit limitations
- [ ] General-purpose "escape hatches" are removed or require explicit elevated permissions
- [ ] Tools use allowlists (what's permitted) rather than denylists (what's forbidden)
- [ ] Domain constraints are enforced at the type level where possible
- [ ] Tools have integration tests that verify constraints can't be bypassed
- [ ] Tool interfaces are versioned and breaking changes are clearly communicated
- [ ] Common workflows are possible within domain constraints without workarounds

## Metadata

**Category**: Technology
**Principle Number**: 21
**Related Patterns**: Repository Pattern, Facade Pattern, Template Method, Domain-Driven Design, Principle of Least Privilege
**Prerequisites**: Understanding of abstraction, interface design, security principles
**Difficulty**: Medium
**Impact**: High

---

**Status**: Complete
**Last Updated**: 2025-09-30
**Version**: 1.0