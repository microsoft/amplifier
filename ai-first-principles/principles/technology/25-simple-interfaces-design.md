# Principle #25 - Simple Interfaces by Design

## Plain-Language Definition

An interface is simple when it has the minimum number of methods necessary, uses clear names that explain intent, and makes correct usage obvious while making incorrect usage difficult. Simple interfaces are easier to understand, implement, and use correctly than complex ones.

## Why This Matters for AI-First Development

AI agents generate code by pattern matching against their training data and the specifications they receive. When interfaces are complex—with many methods, ambiguous parameters, or clever abstractions—AI agents struggle to generate correct implementations. They might call the wrong method, pass parameters in the wrong order, or misunderstand the intended usage pattern.

Simple interfaces directly address this challenge by reducing the cognitive load required to understand and use them. When an interface has three clear methods instead of fifteen, an AI agent can more reliably choose the right one. When method names are explicit about their purpose, the agent doesn't have to guess intent. When parameters are focused and self-documenting, the agent can generate correct calls without extensive context.

The regeneration pattern central to AI-first development depends heavily on interface simplicity. When you regenerate a component, you need confidence that it will integrate correctly with the rest of the system. Simple, stable interfaces provide that confidence. Complex interfaces create uncertainty—will the regenerated component understand all the edge cases? Will it handle the implicit contracts? Simple interfaces eliminate these questions by making contracts explicit and minimal.

Without simple interfaces, AI-generated code becomes brittle and error-prone. An agent might generate code that works in the happy path but fails in edge cases because the interface's complexity hid important constraints. Or it might over-engineer a solution, adding unnecessary abstraction layers because the interface suggested more complexity than actually exists. These problems compound in AI-first systems where code is frequently regenerated, because each regeneration is an opportunity to misunderstand a complex interface.

## Implementation Approaches

### 1. **Minimal Method Counts**

Keep interfaces focused on a single responsibility with the fewest methods possible:
- Start with one method per core operation
- Only add methods when the abstraction genuinely needs them
- Resist the urge to add convenience methods—prefer explicit composition
- If an interface grows beyond 5-7 methods, consider splitting it

**When to use:** Always start here. Default to fewer methods until you have concrete evidence that more are needed.

**Success looks like:** An interface that feels "obvious" to use. Users shouldn't need to read documentation to understand which method to call.

### 2. **Clear, Explicit Naming**

Method and parameter names should communicate intent without ambiguity:
- Use verbs that describe exactly what happens: `create_user` not `process`
- Avoid abbreviations unless they're universally understood: `http` yes, `proc` no
- Include the object type in the name when it matters: `send_email` not `send`
- Make side effects visible in the name: `save_and_publish` not `save`

**When to use:** For every method, parameter, and interface in your system.

**Success looks like:** Someone unfamiliar with your codebase can read a method call and understand what will happen.

### 3. **Focused Interfaces Over Swiss-Army Knives**

Create multiple focused interfaces rather than one that does everything:
- Prefer `Reader` and `Writer` over `FileHandler`
- Split `UserManager` into `UserCreator`, `UserAuthenticator`, `UserProfileUpdater`
- Each interface should have one clear purpose
- Clients depend only on the interfaces they actually use

**When to use:** When you find yourself adding "and" to an interface description ("manages users and sends notifications"), split it.

**Success looks like:** Interfaces that can be mocked with 5 lines of code for testing.

### 4. **Avoid Boolean Parameters**

Boolean parameters create ambiguity and force users to remember what `True` means:
- Replace `delete_user(user_id, True)` with `delete_user_permanently(user_id)`
- Replace `send_email(to, body, False)` with `send_email_without_tracking(to, body)`
- Use enums for multi-state options: `Priority.HIGH` instead of `priority=1`
- Create separate methods for different behaviors

**When to use:** Whenever you're tempted to add a boolean flag to a method.

**Success looks like:** Method calls that read like English: `notify_urgently(message)` not `notify(message, urgent=True)`.

### 5. **Explicit Over Clever**

Choose straightforward implementations over elegant abstractions:
- Prefer explicit chaining over magic: `builder.set_name("x").set_age(30).build()` over `builder("x", age=30)`
- Avoid operator overloading unless the metaphor is perfect (e.g., `+` for numeric types)
- Don't hide control flow: explicit `if` statements beat metaclass magic
- Make dependencies explicit: pass them as parameters rather than using global state

**When to use:** When you're considering a "clever" solution that reduces line count but increases cognitive load.

**Success looks like:** Code that AI agents (and junior developers) can read and immediately understand without tracing through layers of abstraction.

### 6. **Single Responsibility Parameters**

Each parameter should have exactly one job:
- Avoid dictionary parameters that accept arbitrary keys: `create_user(name="x", email="y@z")` beats `create_user({"name": "x", "email": "y@z"})`
- Don't overload parameter meanings: if `None` means "use default" and `""` means "clear value", you have two meanings
- Use separate parameters for separate concerns
- Make required parameters explicit, optional parameters truly optional

**When to use:** When designing any function or method signature.

**Success looks like:** Parameters that have clear types and single, obvious meanings.

## Good Examples vs Bad Examples

### Example 1: User Creation Interface

**Good:**
```python
class UserCreator:
    """Creates new user accounts with validation."""

    def create_user(self, email: str, password: str) -> User:
        """Create a new user account with email and password."""
        self._validate_email(email)
        self._validate_password(password)
        user = User(email=email, password_hash=self._hash_password(password))
        self._save(user)
        return user

    def _validate_email(self, email: str) -> None:
        if "@" not in email:
            raise ValueError(f"Invalid email: {email}")

    def _validate_password(self, password: str) -> None:
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")

    def _hash_password(self, password: str) -> str:
        # Simple example - use proper hashing in production
        return hashlib.sha256(password.encode()).hexdigest()

    def _save(self, user: User) -> None:
        # Save to database
        pass
```

**Bad:**
```python
class UserManager:
    """Manages all user operations."""

    def process(self, operation: str, data: dict, options: dict = None) -> any:
        """Process a user operation with given data and options."""
        options = options or {}
        if operation == "create":
            if options.get("validate", True):
                if not self._validate(data, options.get("strict", False)):
                    return None
            return self._do_create(data, options.get("send_email", True))
        elif operation == "update":
            # ... more branching logic
            pass
        # ... more operations

    def _validate(self, data: dict, strict: bool) -> bool:
        # What does strict mean? What fields are required?
        pass

    def _do_create(self, data: dict, send_email: bool) -> User:
        # What keys should data contain? What happens if they're missing?
        pass
```

**Why It Matters:** The good example has one clear method with explicit parameters. An AI agent generating a call knows exactly what to pass and what will happen. The bad example forces the agent to understand multiple layers of conditional logic and remember what string constants and dictionary keys are valid. This leads to errors where the agent passes `{"email": "x", "pass": "y"}` instead of `{"email": "x", "password": "y"}`, and the error might not be caught until runtime.

### Example 2: File Storage Interface

**Good:**
```python
class FileStore:
    """Stores and retrieves files from disk."""

    def save_file(self, file_path: Path, content: bytes) -> None:
        """Save content to the specified file path."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(content)

    def load_file(self, file_path: Path) -> bytes:
        """Load and return the file content."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        return file_path.read_bytes()

    def delete_file(self, file_path: Path) -> None:
        """Delete the file if it exists."""
        file_path.unlink(missing_ok=True)

    def file_exists(self, file_path: Path) -> bool:
        """Check if the file exists."""
        return file_path.exists()
```

**Bad:**
```python
class FileManager:
    """Manages file operations with advanced features."""

    def handle_file(
        self,
        path: str,
        content: bytes = None,
        mode: str = "r",
        create_dirs: bool = True,
        overwrite: bool = True,
        backup: bool = False,
        compress: bool = False
    ) -> bytes | bool | None:
        """Handle file operations based on mode and options.

        Args:
            path: File path
            content: Content to write (for write modes)
            mode: 'r' for read, 'w' for write, 'd' for delete, 'e' for exists
            create_dirs: Create parent directories
            overwrite: Allow overwriting existing files
            backup: Create backup before overwriting
            compress: Use compression for storage

        Returns:
            File content for read, True/False for exists, None for write/delete
        """
        # 100+ lines of branching logic
        pass
```

**Why It Matters:** The good example makes it impossible to call the wrong operation. Want to save a file? Call `save_file()`. The bad example requires remembering that `mode="w"` means write, and that you need to pass `content` for writes but not reads. An AI agent will regularly generate incorrect calls like `handle_file(path, mode="w")` (missing content) or `handle_file(path, content, mode="r")` (content ignored). The return type ambiguity (`bytes | bool | None`) makes it even harder to use correctly.

### Example 3: Email Notification Service

**Good:**
```python
class EmailNotifier:
    """Sends email notifications to users."""

    def send_welcome_email(self, user_email: str, user_name: str) -> None:
        """Send welcome email to new user."""
        subject = f"Welcome to our service, {user_name}!"
        body = self._render_welcome_template(user_name)
        self._send_email(user_email, subject, body)

    def send_password_reset_email(self, user_email: str, reset_token: str) -> None:
        """Send password reset email with reset token."""
        subject = "Password Reset Request"
        body = self._render_reset_template(reset_token)
        self._send_email(user_email, subject, body)

    def send_notification_email(self, user_email: str, notification: str) -> None:
        """Send general notification email."""
        subject = "Notification"
        body = notification
        self._send_email(user_email, subject, body)

    def _send_email(self, to: str, subject: str, body: str) -> None:
        # Actual email sending logic
        pass

    def _render_welcome_template(self, user_name: str) -> str:
        return f"Hello {user_name}, welcome to our service!"

    def _render_reset_template(self, reset_token: str) -> str:
        return f"Click here to reset your password: https://example.com/reset?token={reset_token}"
```

**Bad:**
```python
class NotificationService:
    """Sends notifications via multiple channels."""

    def send(
        self,
        recipient: str | list[str],
        message: str | dict,
        notification_type: str = "email",
        priority: int = 0,
        schedule: datetime = None,
        metadata: dict = None
    ) -> bool | dict:
        """Send notification with various options.

        Args:
            recipient: Email address, phone number, or list of recipients
            message: Message string or template dict
            notification_type: "email", "sms", "push", "slack"
            priority: 0=low, 1=normal, 2=high, 3=urgent
            schedule: When to send (None = immediate)
            metadata: Additional context for templates

        Returns:
            True if sent immediately, dict with job_id if scheduled
        """
        # What template keys are valid? What recipient format for each type?
        # What happens if you pass phone number with notification_type="email"?
        pass
```

**Why It Matters:** The good example makes the common cases trivial—an AI agent can generate `send_welcome_email(user.email, user.name)` without thinking. The bad example requires understanding the relationship between `notification_type`, `recipient` format, and `message` structure. An AI agent will generate calls like `send(user.email, "Welcome!", notification_type="sms")` (email used for SMS) or `send(user.phone, {"template": "welcome"}, priority=5)` (invalid priority). Each call site becomes a potential bug.

### Example 4: Configuration Management

**Good:**
```python
class AppConfig:
    """Application configuration with explicit settings."""

    def __init__(self, database_url: str, api_key: str, debug_mode: bool):
        self.database_url = database_url
        self.api_key = api_key
        self.debug_mode = debug_mode

    @classmethod
    def from_environment(cls) -> "AppConfig":
        """Load configuration from environment variables."""
        database_url = os.environ["DATABASE_URL"]
        api_key = os.environ["API_KEY"]
        debug_mode = os.environ.get("DEBUG", "false").lower() == "true"
        return cls(database_url, api_key, debug_mode)

    @classmethod
    def for_testing(cls) -> "AppConfig":
        """Create configuration suitable for testing."""
        return cls(
            database_url="sqlite:///:memory:",
            api_key="test-key-12345",
            debug_mode=True
        )


# Usage is crystal clear
config = AppConfig.from_environment()
test_config = AppConfig.for_testing()
```

**Bad:**
```python
class Configuration:
    """Flexible configuration system."""

    def __init__(self):
        self._settings = {}

    def load(self, source: str | dict | Path = None, merge: bool = True) -> None:
        """Load configuration from various sources.

        Args:
            source: Config file path, dict, or source name ("env", "defaults")
            merge: Whether to merge with existing config or replace
        """
        # What happens if source is None? What format for dict?
        # What keys are valid? What types should values be?
        pass

    def get(self, key: str, default: any = None, cast: type = None) -> any:
        """Get configuration value with optional type casting."""
        # What keys exist? What does cast do with invalid types?
        pass

    def set(self, key: str, value: any, persist: bool = False) -> None:
        """Set configuration value, optionally persisting to disk."""
        # What keys are valid? Where does it persist?
        pass


# Usage is ambiguous
config = Configuration()
config.load()  # What did this load?
config.load("env", merge=False)  # String "env" or a file path?
config.set("database_url", "postgresql://...", persist=True)  # Where is this persisted?
api_key = config.get("api_key", cast=str)  # What if api_key doesn't exist?
```

**Why It Matters:** The good example makes configuration explicit and type-safe. An AI agent can see exactly what parameters are needed and what types they should be. The bad example forces the agent to guess what keys are valid, what the source parameter format should be, and what happens with various combinations of parameters. This leads to runtime errors from missing keys or type mismatches.

### Example 5: Data Validation

**Good:**
```python
class EmailValidator:
    """Validates email addresses."""

    def validate_email(self, email: str) -> None:
        """Validate email format, raising ValueError if invalid."""
        if not email:
            raise ValueError("Email cannot be empty")
        if "@" not in email:
            raise ValueError(f"Email must contain @: {email}")
        if email.count("@") > 1:
            raise ValueError(f"Email must contain exactly one @: {email}")
        local, domain = email.split("@")
        if not local or not domain:
            raise ValueError(f"Email must have non-empty local and domain parts: {email}")

    def is_valid_email(self, email: str) -> bool:
        """Check if email is valid, returning True/False."""
        try:
            self.validate_email(email)
            return True
        except ValueError:
            return False


class PasswordValidator:
    """Validates password strength."""

    def __init__(self, min_length: int = 8):
        self.min_length = min_length

    def validate_password(self, password: str) -> None:
        """Validate password strength, raising ValueError if weak."""
        if len(password) < self.min_length:
            raise ValueError(f"Password must be at least {self.min_length} characters")
        if not any(c.isupper() for c in password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in password):
            raise ValueError("Password must contain at least one digit")

    def is_valid_password(self, password: str) -> bool:
        """Check if password is valid, returning True/False."""
        try:
            self.validate_password(password)
            return True
        except ValueError:
            return False


# Usage is clear and focused
email_validator = EmailValidator()
password_validator = PasswordValidator(min_length=10)

email_validator.validate_email("user@example.com")  # Raises ValueError if invalid
if password_validator.is_valid_password("weak"):
    # Handle valid password
    pass
```

**Bad:**
```python
class Validator:
    """General-purpose validation system."""

    def validate(
        self,
        value: any,
        rules: str | list | dict,
        context: dict = None,
        raise_on_error: bool = True
    ) -> bool | dict:
        """Validate value against rules.

        Args:
            value: Value to validate
            rules: Validation rules in various formats:
                   - String: "email" | "password" | "required|email|min:8"
                   - List: ["required", "email", {"min_length": 8}]
                   - Dict: {"type": "email", "required": True, "custom": lambda v: ...}
            context: Additional context for validation
            raise_on_error: Whether to raise exception or return dict with errors

        Returns:
            True if valid (when raise_on_error=False)
            Dict with errors if invalid (when raise_on_error=False)
            None if valid (when raise_on_error=True)
            Raises exception if invalid (when raise_on_error=True)
        """
        # What rule string formats are valid?
        # What keys in dict format?
        # What's passed in context?
        # What exception type is raised?
        pass


# Usage is confusing
validator = Validator()

# Which format should I use?
validator.validate(email, "email")
validator.validate(email, ["required", "email"])
validator.validate(email, {"type": "email", "required": True})
validator.validate(email, "required|email|min:8")

# What does this return?
result = validator.validate(password, "password", raise_on_error=False)
if result:  # Wait, True means valid or True means error dict?
    pass
```

**Why It Matters:** The good example provides focused validators with clear contracts. An AI agent knows that `validate_email()` raises `ValueError` on invalid input, while `is_valid_email()` returns a boolean. The bad example forces the agent to understand a complex rule format (string? list? dict?) and remember what the return value means given different parameter combinations. This leads to bugs where the agent generates `validate(email, "email", raise_on_error=False)` but treats the return value as boolean when it's actually a dict.

## Related Principles

- **[Principle #8 - Module Boundaries as API Contracts](../process/08-module-boundaries-api-contracts.md)** - Simple interfaces form the foundation of stable module boundaries; complex interfaces create fragile contracts that break easily

- **[Principle #7 - Regenerate, Don't Edit](../process/07-regenerate-dont-edit.md)** - Simple interfaces enable confident regeneration because they're easier to implement correctly from scratch

- **[Principle #21 - Clear Component Boundaries](21-clear-component-boundaries.md)** - Simple interfaces define clean boundaries between components, making the system easier to understand and modify

- **[Principle #28 - Self-Documenting Systems](28-self-documenting-systems.md)** - Simple interfaces with clear names are self-documenting; complex interfaces require extensive documentation that AI agents may misinterpret

- **[Principle #3 - Context-Appropriate Specifications](../process/03-context-appropriate-specifications.md)** - Simple interfaces reduce the specification burden because correct usage is obvious from the interface itself

- **[Principle #16 - Parallel Development Streams](../process/16-parallel-development-streams.md)** - Simple interfaces enable parallel work because teams don't need extensive coordination to use them correctly

## Common Pitfalls

1. **Adding "Just One More" Parameter**: Each parameter multiplies the complexity of understanding and using a method. `create_user(email, password, send_welcome=True, validate=True, role="user", notify_admin=False)` has 48 possible combinations.
   - Example: Starting with `save_file(path, content)` and evolving to `save_file(path, content, overwrite=True, backup=False, compress=None, chmod=0o644)`.
   - Impact: AI agents generate calls that work in one context but fail in others because they don't understand the parameter interactions.

2. **Using Magic Values**: Accepting special string or numeric constants that trigger different behavior creates hidden complexity.
   - Example: `get_users(limit=-1)` means "all users" while `get_users(limit=0)` means "none". Why not `get_all_users()` and `get_users(limit=10)`?
   - Impact: AI agents pass wrong constants because the mapping is arbitrary and inconsistent across the codebase.

3. **Overloaded Methods**: Using the same method name for operations that do fundamentally different things based on parameter types or presence.
   - Example: `save(user)` creates new users, `save(user, id=123)` updates existing ones, `save([user1, user2])` does batch operations.
   - Impact: AI agents misuse the method because they pattern-match on name alone and miss the parameter-based behavior differences.

4. **Clever Abstractions**: Creating "elegant" abstractions that reduce code duplication but make usage patterns non-obvious.
   - Example: A `BaseProcessor` with `process()` method that different subclasses override, but each subclass needs different additional methods called in different orders.
   - Impact: AI agents generate code that calls `process()` but misses the required setup steps, leading to runtime failures.

5. **Optional Parameters with Side Effects**: Making parameters optional but having their absence trigger significant behavior changes.
   - Example: `create_user(email, password, role=None)` where `None` triggers "infer role from email domain" logic.
   - Impact: AI agents regularly pass `None` explicitly when they mean "default role", accidentally triggering the inference logic.

6. **Inconsistent Naming**: Using different verbs for similar operations across the codebase.
   - Example: `create_user()`, `add_project()`, `insert_comment()`, `make_post()` all do the same conceptual operation (create a resource).
   - Impact: AI agents guess which verb to use and get it wrong, or use them inconsistently across generated code.

7. **Boolean Trap**: Using boolean parameters where the meaning isn't clear from the call site.
   - Example: `send_email(to, subject, body, True, False)` - what do those booleans control?
   - Impact: AI agents reverse the boolean values or cargo-cult them from other call sites without understanding their meaning.

## Tools & Frameworks

### Static Analysis Tools
- **mypy**: Enforces type hints, catching interface misuse at static analysis time
- **Pylint**: Detects interface complexity through metrics like argument count and cyclomatic complexity
- **Ruff**: Fast linting with rules for interface design (too many arguments, complex signatures)

### Documentation & Interface Discovery
- **Pydantic**: Creates self-validating interfaces with clear type contracts
- **FastAPI**: Auto-generates OpenAPI docs from simple interface definitions
- **Sphinx**: Generates documentation that makes interface complexity visible

### Testing Tools
- **pytest**: Encourages small, focused test cases that expose interface complexity
- **Hypothesis**: Property-based testing reveals unexpected interface behaviors
- **coverage.py**: Shows which interface paths are actually used (dead parameters/methods)

### Design Support
- **ABC (Abstract Base Classes)**: Python's built-in tool for defining minimal interface contracts
- **Protocol classes**: Type hints that define interfaces through method signatures only
- **dataclasses**: Creates simple data-focused interfaces with minimal boilerplate

### API Development
- **GraphQL**: Encourages explicit, focused queries instead of large grab-bag endpoints
- **gRPC**: Protocol buffers enforce simple, explicit interface definitions
- **OpenAPI/Swagger**: Makes interface complexity visible through generated documentation

## Implementation Checklist

When implementing this principle, ensure:

- [ ] Each interface has fewer than 7 public methods
- [ ] Method names use clear verbs that describe exactly what happens
- [ ] No method has more than 5 parameters (3 is better)
- [ ] Boolean parameters are replaced with explicit methods or enums
- [ ] Each parameter has a single, obvious purpose with clear type hints
- [ ] Required parameters come before optional ones
- [ ] Optional parameters have sensible defaults that work in 80% of cases
- [ ] Method return types are consistent and documented
- [ ] Side effects are visible in method names (e.g., `save_and_notify`)
- [ ] Related operations are grouped in focused interfaces, not one large interface
- [ ] Interface can be mocked in 5 lines of code for testing
- [ ] New team member can understand the interface without reading implementation

## Metadata

**Category**: Technology
**Principle Number**: 25
**Related Patterns**: Interface Segregation Principle, Single Responsibility Principle, Command Pattern, Strategy Pattern, Adapter Pattern
**Prerequisites**: Understanding of object-oriented design, type systems, API design
**Difficulty**: Medium
**Impact**: High

---

**Status**: Complete
**Last Updated**: 2025-09-30
**Version**: 1.0