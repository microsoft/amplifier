# Principle #16 - Docs Define, Not Describe

## Plain-Language Definition

Documentation should prescribe what the system must do (definition) rather than describe what it currently does (description). Definitive docs serve as specifications that AI generates code from, while descriptive docs merely document existing implementations.

## Why This Matters for AI-First Development

Traditional documentation is descriptive—it explains what code does after that code is written. A developer builds a feature, then documents how it works. This creates a problematic dependency: documentation trails implementation, often becoming outdated as code evolves. When AI agents need to understand or modify code, descriptive docs are unreliable guides because they may not reflect current reality.

AI-first development inverts this relationship. Definitive documentation becomes the authoritative specification from which AI generates code. Instead of "The `create_user` function validates email format and hashes passwords," definitive docs state "The `create_user` function MUST validate email format using RFC 5322 rules and MUST hash passwords using bcrypt with cost factor 12." This shifts docs from passive observation to active contract.

Three critical benefits emerge from definitive documentation:

**Reliable generation source**: When AI generates or regenerates code, definitive docs provide unambiguous specifications. The AI doesn't guess at requirements or infer intent from existing code—it implements exactly what the documentation mandates. This produces predictable, consistent implementations.

**Single source of truth**: With definitive docs, there's no ambiguity about what's correct. If code doesn't match the documentation, the code is wrong, not the docs. This clarity is essential for AI systems where multiple agents might work on different modules—everyone works from the same authoritative specification.

**Documentation as validation**: Definitive docs enable automated validation. You can verify that implementations satisfy their specifications by checking against the documented contracts, requirements, and constraints. This turns documentation from passive reference material into active quality gates.

Without definitive documentation, AI-first systems suffer from specification drift. AI agents regenerate code based on incomplete or ambiguous descriptions, each iteration potentially diverging from intended behavior. Requirements become implicit and scattered across the codebase rather than explicit and centralized. The system's actual behavior becomes the de facto specification, making it impossible to verify correctness or intentionally change behavior.

## Implementation Approaches

### 1. **Specs as Source of Truth**

Write specifications that define system behavior before any code exists. Use prescriptive language that states requirements, not observations:

- **MUST/SHALL**: Required behavior (e.g., "The API MUST return 401 for invalid tokens")
- **SHOULD**: Recommended behavior with flexibility (e.g., "Responses SHOULD complete within 200ms")
- **MAY**: Optional behavior (e.g., "The cache MAY be disabled for debugging")
- **MUST NOT**: Forbidden behavior (e.g., "Passwords MUST NOT be logged")

**When to use**: For all public APIs, core business logic, security-critical components, and integration points.

**Success looks like**: AI can read the spec and generate correct implementations without seeing any existing code or asking clarifying questions.

### 2. **API-First with OpenAPI Definitions**

Define APIs using OpenAPI specifications that prescribe request/response formats, validation rules, and behavior contracts:

```yaml
# This defines what the API must do, not what it currently does
paths:
  /users:
    post:
      summary: Create a new user account
      description: |
        Creates a new user account. Email MUST be unique across all users.
        Password MUST be hashed using bcrypt before storage.
        MUST return 201 with Location header on success.
        MUST return 409 if email already exists.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [email, password]
              properties:
                email:
                  type: string
                  format: email
                  description: MUST be valid RFC 5322 email address
                password:
                  type: string
                  minLength: 8
                  description: MUST be at least 8 characters
      responses:
        '201':
          description: User created successfully
          headers:
            Location:
              description: URL of created user resource
              required: true
              schema:
                type: string
        '409':
          description: Email already exists
```

**When to use**: For all REST APIs, especially those consumed by external clients or multiple internal services.

**Success looks like**: Generated server code implements exactly the documented behavior, and client code can be generated from the same specification.

### 3. **Executable Documentation with Docstrings**

Write function and class docstrings that define contracts, not just describe current behavior:

```python
def create_user(email: str, password: str) -> User:
    """Create a new user account with validation and security.

    Behavior Contract:
    - MUST validate email format according to RFC 5322
    - MUST reject email if already exists (raise UserExistsError)
    - MUST hash password using bcrypt with cost factor 12
    - MUST NOT store plaintext password
    - MUST set created_at to current UTC timestamp
    - MUST return User object with generated UUID

    Args:
        email: User's email address. MUST be valid format.
        password: Plaintext password. MUST be at least 8 characters.

    Returns:
        User: Newly created user object with id, email, created_at populated.

    Raises:
        ValueError: If email format is invalid or password too short.
        UserExistsError: If email already exists in database.

    Example:
        >>> user = create_user("alice@example.com", "secure_pass123")
        >>> assert user.id is not None
        >>> assert user.email == "alice@example.com"
    """
    # Implementation follows the documented contract
```

**When to use**: For all public functions, especially those that form module boundaries or are used by AI for regeneration.

**Success looks like**: An AI agent can regenerate the function body solely from the docstring, producing code that satisfies all documented requirements.

### 4. **Contract-First Database Schemas**

Define database schemas prescriptively with explicit constraints, not just descriptively listing current columns:

```python
"""User table schema definition.

This schema defines the required structure and constraints for user storage.

Requirements:
- id MUST be UUID primary key
- email MUST be unique across all users
- email MUST NOT be null
- password_hash MUST be bcrypt hash, never plaintext
- created_at MUST default to current timestamp
- updated_at MUST auto-update on any modification

Constraints:
- Email uniqueness MUST be enforced at database level
- Deletion MUST be soft delete (deleted_at timestamp) to preserve audit trail
"""

from sqlalchemy import Column, String, DateTime, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
import uuid

class User(Base):
    __tablename__ = "users"

    # MUST use UUID for globally unique identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # MUST enforce uniqueness at database level, not just application level
    email = Column(String(255), unique=True, nullable=False, index=True)

    # MUST store bcrypt hash, never plaintext
    password_hash = Column(String(60), nullable=False)

    # MUST track creation time for audit purposes
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    # MUST track modification time for audit purposes
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    # MUST support soft delete for data retention compliance
    deleted_at = Column(DateTime(timezone=True), nullable=True)
```

**When to use**: For all database schemas, especially those involving data integrity, audit requirements, or regulatory compliance.

**Success looks like**: Migration generation tools can create correct database structure from schema definitions, and AI can regenerate model code that satisfies all constraints.

### 5. **Test Cases as Behavioral Specifications**

Write tests that define required behavior before implementation exists:

```python
"""Test specification for user authentication system.

These tests define the required behavior of the authentication system.
Any implementation MUST pass all these tests.
"""

class TestAuthenticationRequirements:
    def test_successful_login_must_return_valid_token(self):
        """Requirement: Valid credentials MUST produce a valid JWT token."""
        user = create_test_user("user@test.com", "password123")
        token = authenticate("user@test.com", "password123")

        # MUST return non-empty token
        assert token is not None
        assert len(token) > 0

        # MUST be valid JWT format
        decoded = jwt.decode(token, verify=False)
        assert "user_id" in decoded
        assert decoded["user_id"] == str(user.id)

    def test_invalid_password_must_raise_authentication_error(self):
        """Requirement: Invalid password MUST reject authentication."""
        create_test_user("user@test.com", "password123")

        # MUST raise AuthenticationError, not return None or empty string
        with pytest.raises(AuthenticationError) as exc_info:
            authenticate("user@test.com", "wrong_password")

        # Error message MUST NOT reveal whether user exists
        assert "email" not in str(exc_info.value).lower()

    def test_token_must_expire_after_configured_duration(self):
        """Requirement: Tokens MUST expire after TOKEN_LIFETIME_SECONDS."""
        token = authenticate("user@test.com", "password123")

        # Token MUST be valid immediately after generation
        assert verify_token(token) is not None

        # Token MUST be invalid after expiration
        time.sleep(TOKEN_LIFETIME_SECONDS + 1)
        with pytest.raises(TokenExpiredError):
            verify_token(token)

    def test_password_reset_must_invalidate_existing_tokens(self):
        """Requirement: Password change MUST invalidate all existing tokens."""
        token_before = authenticate("user@test.com", "old_password")
        assert verify_token(token_before) is not None

        # Change password
        change_password("user@test.com", "old_password", "new_password")

        # Old token MUST be invalid
        with pytest.raises(TokenInvalidError):
            verify_token(token_before)

        # New authentication MUST work with new password
        token_after = authenticate("user@test.com", "new_password")
        assert verify_token(token_after) is not None
```

**When to use**: For all critical functionality, especially security, data integrity, and business logic components.

**Success looks like**: Tests define complete behavioral contracts that any implementation must satisfy, enabling AI to regenerate implementations with confidence.

### 6. **ADRs (Architecture Decision Records) as Definitive Constraints**

Document architectural decisions as binding constraints, not just historical records:

```markdown
# ADR-015: User Authentication Token Format

## Status
Accepted

## Context
User authentication requires secure, stateless token format for API access.

## Decision
We MUST use JWT (JSON Web Tokens) for user authentication with the following requirements:

### Token Structure Requirements
- Tokens MUST be signed using RS256 (RSA with SHA-256)
- Tokens MUST include claims: user_id, email, issued_at, expires_at
- Tokens MUST NOT include sensitive data (password, SSN, etc.)
- Tokens MUST expire after 24 hours (86400 seconds)

### Security Requirements
- Private keys MUST be stored in secure key management system
- Public keys MUST be rotated every 90 days
- Token signature MUST be verified on every API request
- Expired tokens MUST be rejected with 401 status

### Implementation Requirements
- MUST use PyJWT library version 2.x or higher
- MUST validate token signature before extracting claims
- MUST check expiration before accepting any token
- MUST log all token validation failures for security monitoring

## Consequences
Any implementation of authentication MUST satisfy these requirements.
Any deviation requires updating this ADR and related implementations.

## Compliance Verification
See tests/test_auth_requirements.py for executable verification of these requirements.
```

**When to use**: For architectural decisions that constrain implementations, especially security, scalability, and integration architecture.

**Success looks like**: AI agents reference ADRs when generating code, ensuring all implementations comply with architectural constraints.

## Good Examples vs Bad Examples

### Example 1: API Endpoint Documentation

**Good (Definitive):**
```yaml
# API Specification - Source of Truth
paths:
  /api/orders/{order_id}:
    get:
      summary: Retrieve order details
      description: |
        Retrieves complete order information by ID.

        Requirements:
        - MUST return 200 with order details if order exists and user has permission
        - MUST return 404 if order does not exist
        - MUST return 403 if user does not own the order
        - MUST include all line items with current pricing
        - Response time SHOULD be under 200ms for 95th percentile

      parameters:
        - name: order_id
          in: path
          required: true
          description: UUID of the order to retrieve
          schema:
            type: string
            format: uuid

      responses:
        '200':
          description: Order found and returned
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Order'
        '403':
          description: User does not have permission to view this order
        '404':
          description: Order not found
```

**Bad (Descriptive):**
```yaml
# API Documentation - Describes Current Behavior
paths:
  /api/orders/{order_id}:
    get:
      summary: Get order
      description: |
        This endpoint gets an order by ID. It returns the order information
        if the order exists. Sometimes it might return 403 if there's a
        permission issue.

      parameters:
        - name: order_id
          in: path
          description: The order ID

      responses:
        '200':
          description: Returns the order
        '404':
          description: When order doesn't exist
```

**Why It Matters:** The definitive version prescribes exact behavior including all edge cases (permissions, not found) and performance requirements. AI can generate implementations that precisely match these requirements. The descriptive version vaguely describes current behavior without stating requirements, leading AI to generate code that might handle errors differently or miss edge cases.

### Example 2: Function Documentation

**Good (Definitive):**
```python
def process_payment(order_id: str, payment_method: str, amount: Decimal) -> PaymentResult:
    """Process payment for an order.

    Behavior Contract:
    - MUST validate order exists and is in 'pending' state
    - MUST validate amount matches order total exactly
    - MUST be idempotent - processing same order_id twice returns same result
    - MUST NOT charge payment method more than once per order_id
    - MUST atomically update order status to 'paid' on success
    - MUST NOT update order status if payment fails
    - MUST complete within 10 seconds or raise TimeoutError

    Args:
        order_id: UUID of the order. MUST exist and be in 'pending' state.
        payment_method: Payment method identifier. MUST be valid and active.
        amount: Payment amount. MUST match order total exactly.

    Returns:
        PaymentResult containing:
        - success: True if payment processed, False otherwise
        - transaction_id: Payment gateway transaction ID (present if success=True)
        - error_code: Error code if success=False
        - timestamp: When payment was processed

    Raises:
        OrderNotFoundError: If order_id does not exist
        OrderStateError: If order is not in 'pending' state
        PaymentMethodError: If payment_method is invalid or inactive
        AmountMismatchError: If amount doesn't match order total
        TimeoutError: If payment processing exceeds 10 seconds

    Idempotency:
        Calling with same order_id multiple times MUST return same result
        without charging payment method multiple times.
    """
```

**Bad (Descriptive):**
```python
def process_payment(order_id: str, payment_method: str, amount: Decimal) -> PaymentResult:
    """Processes a payment for an order.

    This function takes an order ID and payment method, then processes
    the payment. It returns a PaymentResult with the outcome.

    Args:
        order_id: The order ID
        payment_method: The payment method to use
        amount: How much to charge

    Returns:
        PaymentResult object with payment details
    """
```

**Why It Matters:** The definitive version specifies exact preconditions, postconditions, error cases, idempotency guarantees, and performance requirements. AI can generate implementations that handle all these cases correctly. The descriptive version just paraphrases the function signature without adding useful information, forcing AI to guess at error handling and edge cases.

### Example 3: Database Schema Documentation

**Good (Definitive):**
```python
"""Order table schema specification.

This table stores customer orders with the following requirements:

Data Integrity Requirements:
- id MUST be UUID primary key for global uniqueness
- customer_id MUST reference valid user (foreign key)
- status MUST be one of: pending, paid, shipped, delivered, cancelled
- total_amount MUST be positive decimal with 2 decimal places
- created_at MUST default to current timestamp
- updated_at MUST auto-update on any modification

Business Logic Requirements:
- Orders MUST NOT be deleted, only marked as cancelled
- Status transitions MUST follow: pending -> paid -> shipped -> delivered
- Status MUST NOT transition from delivered or cancelled to any other state
- total_amount MUST be recalculated and validated against line items

Audit Requirements:
- All status changes MUST be logged in order_status_history table
- created_at and updated_at MUST be preserved for compliance
- Soft delete via cancelled status MUST preserve all data
"""

from sqlalchemy import Column, String, Numeric, DateTime, Enum, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # Status MUST be constrained to valid values at database level
    status = Column(
        Enum("pending", "paid", "shipped", "delivered", "cancelled", name="order_status"),
        nullable=False,
        default="pending",
        index=True
    )

    # Amount MUST be positive and exactly 2 decimal places
    total_amount = Column(
        Numeric(10, 2),
        CheckConstraint("total_amount > 0", name="positive_amount"),
        nullable=False
    )

    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
```

**Bad (Descriptive):**
```python
"""Order table.

Stores information about customer orders.
"""

class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID, primary_key=True)
    customer_id = Column(UUID)
    status = Column(String)  # Order status
    total_amount = Column(Numeric)  # Total order amount
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
```

**Why It Matters:** The definitive version specifies exact constraints, business rules, and data integrity requirements that must be enforced. AI can generate migrations, validation logic, and application code that respects all these constraints. The descriptive version just lists fields without constraints, leading AI to generate code that might allow invalid data or violate business rules.

### Example 4: Error Handling Documentation

**Good (Definitive):**
```python
"""Error handling specification for user service.

All user service functions MUST follow these error handling requirements:

Validation Errors:
- MUST raise ValueError with descriptive message for invalid input
- Error message MUST specify which field failed validation
- Error message MUST NOT include sensitive data (passwords, tokens)

Not Found Errors:
- MUST raise UserNotFoundError when user does not exist
- MUST NOT reveal whether email exists in system (security)
- MUST log user ID/email of not-found requests for security monitoring

Permission Errors:
- MUST raise PermissionError when user lacks required permission
- MUST specify which permission is required
- MUST log all permission failures for audit trail

Database Errors:
- MUST catch and wrap database exceptions in UserServiceError
- MUST include transaction ID in error for debugging
- MUST NOT expose SQL queries or database schema in error messages

All Errors:
- MUST inherit from appropriate base exception class
- MUST be documented in function docstring
- MUST include context (user_id, operation) for debugging
"""

class UserServiceError(Exception):
    """Base exception for all user service errors.

    All user service exceptions MUST inherit from this class.
    """
    def __init__(self, message: str, context: dict = None):
        super().__init__(message)
        self.context = context or {}
        self.timestamp = datetime.utcnow()

class UserNotFoundError(UserServiceError):
    """Raised when requested user does not exist.

    Security requirement: Message MUST NOT reveal if email exists.
    """
    pass

class PermissionError(UserServiceError):
    """Raised when user lacks required permission.

    Audit requirement: All instances MUST be logged.
    """
    def __init__(self, message: str, required_permission: str, user_id: str):
        super().__init__(
            message,
            context={
                "required_permission": required_permission,
                "user_id": user_id
            }
        )
```

**Bad (Descriptive):**
```python
"""Error classes for user service.

These exceptions can be raised by user service functions.
"""

class UserServiceError(Exception):
    """Something went wrong in the user service"""
    pass

class UserNotFoundError(UserServiceError):
    """User wasn't found"""
    pass

class PermissionError(UserServiceError):
    """User doesn't have permission"""
    pass
```

**Why It Matters:** The definitive version specifies exactly what errors must be raised under what conditions, what information they must contain, and what security/audit requirements apply. AI can generate error handling code that correctly implements these requirements. The descriptive version just names exceptions without specifying when to use them or what they should contain.

### Example 5: Configuration Documentation

**Good (Definitive):**
```python
"""Application configuration specification.

Configuration MUST be loaded from environment variables with the following requirements:

Required Configuration:
- DATABASE_URL: MUST be valid PostgreSQL connection string
- SECRET_KEY: MUST be at least 32 characters for security
- API_KEY: MUST be valid API key from external service

Optional Configuration:
- DEBUG: MAY be "true" or "false", defaults to "false"
- LOG_LEVEL: MAY be DEBUG, INFO, WARNING, ERROR, defaults to INFO
- MAX_CONNECTIONS: MAY be 1-100, defaults to 10

Validation Requirements:
- MUST validate all required settings at startup
- MUST fail fast if required settings are missing or invalid
- MUST NOT proceed with default values for required settings
- MUST log all configuration values except secrets

Security Requirements:
- MUST NOT log SECRET_KEY or API_KEY values
- MUST mask secrets in error messages
- MUST load secrets from secure storage in production
"""

import os
from dataclasses import dataclass

@dataclass
class AppConfig:
    """Application configuration with validation.

    All instances MUST pass validation before use.
    """
    database_url: str
    secret_key: str
    api_key: str
    debug: bool = False
    log_level: str = "INFO"
    max_connections: int = 10

    def __post_init__(self):
        """Validate configuration on initialization.

        MUST raise ValueError with clear message if validation fails.
        """
        # MUST validate database URL format
        if not self.database_url.startswith("postgresql://"):
            raise ValueError("DATABASE_URL must be valid PostgreSQL connection string")

        # MUST validate secret key length for security
        if len(self.secret_key) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters for security")

        # MUST validate API key is non-empty
        if not self.api_key or self.api_key.strip() == "":
            raise ValueError("API_KEY must be non-empty")

        # MUST validate log level
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR"}
        if self.log_level not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")

        # MUST validate connection pool size
        if not 1 <= self.max_connections <= 100:
            raise ValueError("MAX_CONNECTIONS must be between 1 and 100")

    @classmethod
    def from_environment(cls) -> "AppConfig":
        """Load configuration from environment variables.

        MUST validate all required variables are present.
        MUST apply defaults for optional variables.
        MUST fail fast with clear error if required variable is missing.

        Raises:
            ValueError: If required environment variable is missing or invalid
        """
        # MUST require these variables
        required_vars = ["DATABASE_URL", "SECRET_KEY", "API_KEY"]
        missing = [var for var in required_vars if var not in os.environ]
        if missing:
            raise ValueError(f"Required environment variables missing: {', '.join(missing)}")

        return cls(
            database_url=os.environ["DATABASE_URL"],
            secret_key=os.environ["SECRET_KEY"],
            api_key=os.environ["API_KEY"],
            debug=os.environ.get("DEBUG", "false").lower() == "true",
            log_level=os.environ.get("LOG_LEVEL", "INFO").upper(),
            max_connections=int(os.environ.get("MAX_CONNECTIONS", "10")),
        )
```

**Bad (Descriptive):**
```python
"""Configuration settings.

Loads configuration from environment variables.
"""

class AppConfig:
    def __init__(self):
        self.database_url = os.environ.get("DATABASE_URL")
        self.secret_key = os.environ.get("SECRET_KEY")
        self.api_key = os.environ.get("API_KEY")
        self.debug = os.environ.get("DEBUG", "false") == "true"
        self.log_level = os.environ.get("LOG_LEVEL", "INFO")
```

**Why It Matters:** The definitive version specifies exactly which settings are required vs optional, what validation must be performed, what error handling is needed, and what security requirements apply. AI can generate configuration loading code that properly validates, fails fast, and handles errors correctly. The descriptive version just loads variables without validation, leading to runtime failures or security issues.

## Related Principles

- **[Principle #08 - Contract-First Everything](08-contract-first-everything.md)** - Contracts are definitive documentation of interfaces. Docs define contracts, contracts define what to build, code implements contracts.

- **[Principle #07 - Regenerate, Don't Edit](07-regenerate-dont-edit.md)** - Definitive docs enable regeneration by providing clear specifications. AI regenerates from docs, not from reading existing code.

- **[Principle #25 - Simple Interfaces by Design](../technology/25-simple-interfaces-design.md)** - Simple interfaces are easier to document definitively. Complex interfaces require verbose prescriptive documentation.

- **[Principle #09 - Tests as Quality Gate](09-tests-as-quality-gate.md)** - Tests are executable definitive documentation. They prescribe required behavior that code must satisfy.

- **[Principle #17 - Prompt Versioning and Testing](17-test-intent-not-implementation.md)** - Tests document intent (what must happen) not implementation (how it happens), making them definitive rather than descriptive.

- **[Principle #03 - Embrace Regeneration](../mindset/03-embrace-regeneration.md)** - Regeneration requires definitive docs as stable specifications. Without them, each regeneration drifts from original intent.

## Common Pitfalls

1. **Writing Docs After Code**: Writing documentation by looking at existing code and describing what it does creates descriptive docs, not definitive specs.
   - Example: Reading through `auth.py` and documenting "The authenticate function checks the password hash and returns a token."
   - Impact: Documentation reflects current implementation bugs and all, not requirements. AI regenerating from these docs perpetuates existing issues.

2. **Using Passive Voice**: Passive voice creates descriptive documentation that observes rather than prescribes.
   - Example: "Invalid credentials result in an error being raised" vs "MUST raise AuthenticationError for invalid credentials."
   - Impact: Ambiguous whether this is required behavior or just current observation. AI might implement differently.

3. **Omitting Error Cases**: Documenting only happy paths without specifying required error handling.
   - Example: "Returns user object when email exists" without stating what must happen when email doesn't exist.
   - Impact: AI generates code that handles errors inconsistently or not at all.

4. **Vague Requirements**: Using imprecise language that allows multiple interpretations.
   - Example: "Password should be secure" instead of "Password MUST be at least 12 characters with uppercase, lowercase, digit, and special character."
   - Impact: AI makes arbitrary security decisions that might not meet actual security requirements.

5. **Missing Performance Requirements**: Not specifying performance constraints that implementations must satisfy.
   - Example: Documenting API endpoint without stating "MUST respond within 200ms for 95th percentile."
   - Impact: AI generates functionally correct but unacceptably slow implementations.

6. **Coupling Docs to Implementation**: Including implementation details in documentation that should only specify behavior.
   - Example: "Uses bcrypt with cost factor 12" in API docs instead of schema/implementation docs.
   - Impact: Prevents AI from choosing better implementations. Docs become descriptive of current tech choices.

7. **No Versioning of Requirements**: Updating definitive docs without versioning, making it unclear which code should satisfy which requirements.
   - Example: Changing "MUST respond within 500ms" to "MUST respond within 200ms" without version marker.
   - Impact: Existing code that satisfied old requirements now appears non-compliant with current docs.

## Tools & Frameworks

### API Specification Tools
- **OpenAPI/Swagger**: Definitive API specifications with request/response contracts, validation rules, and error codes. AI generates server/client code from specs.
- **GraphQL Schema Definition Language**: Prescriptive schema definitions with type constraints and validation rules.
- **gRPC Protocol Buffers**: Strongly-typed interface definitions that prescribe exact message formats and service contracts.
- **AsyncAPI**: Definitive specifications for event-driven APIs with message formats and behavioral contracts.

### Documentation Generation
- **Sphinx**: Python documentation generator that can validate docstring contracts and generate comprehensive API docs.
- **JSDoc**: JavaScript documentation with type annotations that prescribe function contracts.
- **rustdoc**: Rust documentation that integrates with type system to provide definitive API documentation.
- **Swagger UI**: Interactive API documentation generated from OpenAPI specs, ensuring docs match implementation.

### Contract Validation
- **Pact**: Consumer-driven contract testing that validates implementations satisfy documented contracts.
- **JSON Schema**: Formal schema definitions that prescribe exact data structure requirements.
- **Pydantic**: Python data validation using type hints to enforce documented contracts at runtime.
- **Ajv**: JSON Schema validator for JavaScript that ensures data matches definitive schemas.

### Specification Languages
- **RFC 2119 (MUST/SHOULD/MAY)**: Standard keywords for requirement levels in definitive documentation.
- **Gherkin (Given/When/Then)**: Behavior-driven specification language that defines required behavior.
- **Alloy**: Formal specification language for modeling system behavior and constraints.
- **TLA+**: Formal specification language for concurrent and distributed systems.

### Documentation Linting
- **Vale**: Prose linter that can enforce use of RFC 2119 keywords and definitive language patterns.
- **alex**: Linter that identifies non-prescriptive language patterns in documentation.
- **write-good**: Linter that catches passive voice and vague language in documentation.

## Implementation Checklist

When implementing this principle, ensure:

- [ ] All API documentation uses prescriptive language (MUST/SHOULD/MAY) not descriptive
- [ ] Function docstrings specify complete behavior contracts including error cases
- [ ] Database schemas document all constraints, business rules, and data integrity requirements
- [ ] Error handling is fully specified with exact conditions for each exception type
- [ ] Performance requirements are quantified with specific metrics and thresholds
- [ ] Security requirements are explicitly stated with MUST NOT restrictions
- [ ] Edge cases and error paths are documented with same detail as happy paths
- [ ] Documentation can serve as sole input for AI code generation without ambiguity
- [ ] Tests validate that implementations satisfy documented requirements
- [ ] Documentation is versioned and updated before code changes, not after
- [ ] ADRs document binding architectural constraints as definitive requirements
- [ ] All public interfaces have definitive documentation before any implementation exists

## Metadata

**Category**: Process
**Principle Number**: 16
**Related Patterns**: Design by Contract, API-First Design, Specification by Example, Behavior-Driven Development, Contract-Driven Development
**Prerequisites**: Understanding of API design, contract specification, RFC 2119 requirement levels
**Difficulty**: Medium
**Impact**: High

---

**Status**: Complete
**Last Updated**: 2025-09-30
**Version**: 1.0