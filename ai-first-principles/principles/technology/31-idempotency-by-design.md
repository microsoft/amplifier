# Principle #31 - Idempotency by Design

## Plain-Language Definition

An operation is idempotent when running it multiple times produces the same result as running it once. Idempotency by design means building systems where operations can be safely retried without causing unintended side effects or accumulating errors.

## Why This Matters for AI-First Development

When AI agents build and modify systems, they need reliable recovery mechanisms. An AI agent might be interrupted mid-operation, lose network connectivity, or need to retry failed operations. Without idempotency, these retries can cause data corruption, duplicate resources, or cascading failures.

Idempotency provides three critical benefits for AI-driven development:

1. **Reliability through retries**: AI agents can confidently retry operations without fear of creating duplicate state or corrupting data. This is essential because AI-driven systems often operate asynchronously across distributed components.

2. **Predictable system behavior**: When operations are idempotent, the system state becomes more predictable. AI agents can reason about what will happen when they execute operations, making it easier to generate correct code and recovery logic.

3. **Safe experimentation**: Idempotent operations allow AI agents to explore different approaches safely. If an agent tries an operation and wants to roll back, idempotency ensures the rollback itself won't cause new problems.

Without idempotency, AI systems become fragile. A network hiccup during deployment might create duplicate database records. A failed API call might leave resources in an inconsistent state. An interrupted file write might corrupt configuration. These failures compound quickly in AI-first systems where many operations happen automatically without human oversight.

## Implementation Approaches

### 1. **Natural Idempotency Through HTTP Verbs**

Use HTTP methods according to their semantic guarantees:
- **GET**: Always idempotent (read-only)
- **PUT**: Idempotent (full resource replacement)
- **DELETE**: Idempotent (deleting already-deleted resource succeeds)
- **POST**: Generally NOT idempotent (creates new resources)
- **PATCH**: Can be made idempotent with careful design

When designing APIs, prefer PUT over POST for operations that should be idempotent.

### 2. **Idempotency Keys**

For operations that aren't naturally idempotent (like POST requests that create resources), use idempotency keys:

```python
def create_payment(amount: float, idempotency_key: str) -> Payment:
    # Check if we've already processed this idempotency key
    existing = get_payment_by_idempotency_key(idempotency_key)
    if existing:
        return existing  # Return the same result as before

    # Process the payment
    payment = process_new_payment(amount)
    save_idempotency_key(idempotency_key, payment)
    return payment
```

The client generates a unique key for each logical operation. If the operation is retried with the same key, the server returns the original result instead of creating a duplicate.

### 3. **Check-Then-Act Patterns**

Before performing an action, check if it's already been done:

```python
def ensure_database_exists(db_name: str):
    if not database_exists(db_name):
        create_database(db_name)
    # If it already exists, do nothing
```

This pattern works well for resource provisioning, configuration updates, and infrastructure setup.

### 4. **Immutable State with Versioning**

Instead of modifying state in place, create new versions:

```python
def update_config(config_id: str, changes: dict) -> Config:
    # Never modify existing config
    current = get_config(config_id)
    new_version = create_new_version(current, changes)
    return new_version
```

This makes all operations naturally idempotent because you're always creating new state rather than mutating existing state.

### 5. **Transaction-Based Idempotency**

Use database transactions with unique constraints to enforce idempotency:

```python
def record_event(event_id: str, event_data: dict):
    try:
        with transaction():
            # Unique constraint on event_id ensures no duplicates
            db.events.insert({"id": event_id, "data": event_data})
    except UniqueConstraintError:
        # Event already recorded, operation is idempotent
        pass
```

The database enforces idempotency through its constraints, preventing duplicate operations even if multiple requests arrive.

## Good Examples vs Bad Examples

### Example 1: File Deployment

**Good:**
```python
def deploy_config_file(content: str, target_path: Path):
    """Idempotent: writing the same content multiple times is safe"""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(content)
    # No matter how many times we run this, the file contains the same content
```

**Bad:**
```python
def deploy_config_file(content: str, target_path: Path):
    """NOT idempotent: appends instead of replacing"""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with open(target_path, 'a') as f:  # 'a' = append mode
        f.write(content)
    # Running twice appends content twice, corrupting the file
```

**Why It Matters:** File operations are common in deployment and configuration. Append mode seems convenient but breaks idempotency. AI agents deploying configurations need to know that running deployment twice won't corrupt files.

### Example 2: Database Initialization

**Good:**
```python
def initialize_user_table():
    """Idempotent: checks if table exists before creating"""
    if not table_exists('users'):
        execute_sql("""
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
```

**Bad:**
```python
def initialize_user_table():
    """NOT idempotent: fails if table already exists"""
    execute_sql("""
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    # Raises error if table already exists
```

**Why It Matters:** Database initialization is often part of application startup or deployment. If initialization isn't idempotent, restarting the application after a partial failure can crash the system.

### Example 3: API Resource Creation

**Good:**
```python
@app.post("/api/projects")
def create_project(name: str, idempotency_key: str = Header(...)):
    """Idempotent: uses idempotency key to prevent duplicates"""
    # Check if we've seen this idempotency key before
    existing = get_project_by_idempotency_key(idempotency_key)
    if existing:
        return existing  # Return the same project

    project = Project.create(name=name)
    save_idempotency_key(idempotency_key, project.id)
    return project
```

**Bad:**
```python
@app.post("/api/projects")
def create_project(name: str):
    """NOT idempotent: creates duplicate projects on retry"""
    project = Project.create(name=name)
    return project
    # Retrying this request creates multiple projects with the same name
```

**Why It Matters:** Network failures are common. Without idempotency keys, a client that retries after a timeout might create duplicate resources, leading to data inconsistency and user confusion.

### Example 4: User Role Assignment

**Good:**
```python
def assign_role(user_id: str, role: str):
    """Idempotent: assigning the same role multiple times is safe"""
    user = get_user(user_id)
    if role not in user.roles:
        user.roles.append(role)
        save_user(user)
    # If role already exists, do nothing
```

**Bad:**
```python
def assign_role(user_id: str, role: str):
    """NOT idempotent: duplicates roles"""
    user = get_user(user_id)
    user.roles.append(role)  # No check for existing role
    save_user(user)
    # Running twice gives user.roles = ['admin', 'admin']
```

**Why It Matters:** Authorization logic often runs multiple times (on retry, during sync, after recovery). Duplicate roles can break permission checks and cause security vulnerabilities.

### Example 5: Event Processing

**Good:**
```python
def process_payment_event(event_id: str, payment_data: dict):
    """Idempotent: uses database unique constraint"""
    try:
        with transaction():
            # event_id has unique constraint
            db.processed_events.insert({
                "event_id": event_id,
                "processed_at": now()
            })
            charge_customer(payment_data)
            send_confirmation_email(payment_data)
    except UniqueConstraintError:
        # Event already processed, skip it
        logger.info(f"Event {event_id} already processed")
```

**Bad:**
```python
def process_payment_event(event_id: str, payment_data: dict):
    """NOT idempotent: charges customer multiple times"""
    charge_customer(payment_data)
    send_confirmation_email(payment_data)
    db.processed_events.insert({"event_id": event_id})
    # If this runs twice, customer is charged twice
```

**Why It Matters:** Event-driven systems often deliver events multiple times (at-least-once delivery). Without idempotency, duplicate events cause financial errors, duplicate notifications, and data inconsistency.

## Related Principles

- **[Principle #7 - Regenerate, Don't Edit](../process/07-regenerate-dont-edit.md)** - Idempotency enables safe regeneration because operations can be re-run without side effects

- **[Principle #26 - Stateless by Default](26-stateless-by-default.md)** - Stateless operations are naturally more idempotent because they don't accumulate state

- **[Principle #32 - Error Recovery Patterns Built In](32-error-recovery-patterns.md)** - Idempotency is foundational to error recovery; you can't safely retry operations that aren't idempotent

- **[Principle #27 - Disposable Components Everywhere](27-disposable-components.md)** - Idempotent operations make components safely disposable; you can restart them without worrying about partial state

- **[Principle #10 - Git as Safety Net](../process/10-git-as-safety-net.md)** - Git operations (commit, push, pull) are largely idempotent, making rollback safe

- **[Principle #11 - Continuous Validation with Fast Feedback](../process/11-continuous-validation-fast-feedback.md)** - Validation can run repeatedly without side effects when operations are idempotent

- **[Principle #23 - Protected Self-Healing Kernel](23-protected-self-healing-kernel.md)** - Self-healing requires idempotent recovery operations to avoid making problems worse

## Common Pitfalls

1. **Forgetting About Partial Failures**: Operations that modify multiple resources can fail partway through. Without transactional guarantees or careful ordering, retries can leave the system in an inconsistent state.
   - Example: Creating a user record but failing to send the welcome email. Retry creates duplicate user.
   - Impact: Data corruption, duplicate resources, inconsistent state across systems.

2. **Using Append Operations Without Deduplication**: Appending to lists, logs, or files without checking for duplicates breaks idempotency.
   - Example: `log_file.append(event)` instead of checking if event is already logged.
   - Impact: Duplicate log entries, incorrect metrics, unbounded growth of lists.

3. **Generating Random IDs on Each Call**: Using `uuid.uuid4()` or `random()` inside an operation makes it non-idempotent because each call produces different results.
   - Example: `user_id = uuid.uuid4(); create_user(user_id, email)` creates different users on retry.
   - Impact: Duplicate resources with different IDs, inability to deduplicate.

4. **Side Effects in Idempotent Operations**: Sending emails, notifications, or external API calls inside otherwise idempotent operations breaks idempotency.
   - Example: `update_user(user_id, data); send_email(user_id)` sends duplicate emails on retry.
   - Impact: Spam, rate limiting, external service costs, user annoyance.

5. **Mutable Default Arguments**: Python's mutable default arguments are evaluated once and shared across calls, breaking idempotency.
   - Example: `def add_item(item, items=[]):` accumulates items across calls.
   - Impact: Unexpected state accumulation, hard-to-debug behavior.

6. **Time-Based Operations**: Using `now()` or `timestamp()` inside operations makes them non-idempotent because the result changes over time.
   - Example: `record.created_at = now()` produces different timestamps on retry.
   - Impact: Inconsistent data, inability to verify idempotency in tests.

7. **Missing Idempotency Key Validation**: Accepting idempotency keys but not validating their format or expiration allows clients to accidentally reuse keys.
   - Example: Accepting empty string as idempotency key.
   - Impact: Unintentional duplicate operations, lack of deduplication.

## Tools & Frameworks

### HTTP Frameworks with Idempotency Support
- **Django REST Framework**: Built-in support for proper HTTP verb semantics
- **FastAPI**: Supports idempotency keys through dependencies and middleware
- **Flask-RESTful**: Provides decorators for enforcing idempotent endpoints

### Database Tools
- **PostgreSQL**: UPSERT (INSERT ... ON CONFLICT) for idempotent inserts
- **MongoDB**: `update_one` with `upsert=True` for idempotent updates
- **Redis**: `SET NX` and `SET XX` for idempotent key operations

### Cloud Infrastructure
- **Terraform**: Declarative infrastructure with built-in idempotency
- **Ansible**: Idempotent by design for configuration management
- **CloudFormation**: AWS infrastructure-as-code with idempotent updates

### Message Queues
- **Kafka**: Exactly-once semantics with idempotent producers
- **RabbitMQ**: Message deduplication through message IDs
- **AWS SQS**: Supports message deduplication for FIFO queues

### Testing Tools
- **pytest**: Fixtures with idempotent setup/teardown
- **Hypothesis**: Property-based testing to verify idempotency
- **Docker**: Container operations are idempotent by design

## Implementation Checklist

When implementing this principle, ensure:

- [ ] All HTTP PUT and DELETE endpoints are truly idempotent
- [ ] POST endpoints that create resources use idempotency keys
- [ ] Database operations use unique constraints to prevent duplicates
- [ ] File operations overwrite rather than append (unless append is intentional)
- [ ] Resource creation checks for existence before creating
- [ ] Retry logic assumes operations may have partially succeeded
- [ ] Side effects (emails, notifications) are tracked to prevent duplicates
- [ ] Generated IDs are deterministic or stored with idempotency keys
- [ ] Time-sensitive operations document their idempotency boundaries
- [ ] Tests verify that operations can be safely retried
- [ ] Error handling preserves idempotency guarantees
- [ ] Documentation explicitly states whether operations are idempotent

## Metadata

**Category**: Technology
**Principle Number**: 31
**Related Patterns**: Retry Logic, Circuit Breaker, Saga Pattern, Event Sourcing, CQRS
**Prerequisites**: Understanding of HTTP semantics, database transactions, error handling
**Difficulty**: Medium
**Impact**: High

---

**Status**: Complete
**Last Updated**: 2025-09-30
**Version**: 1.0