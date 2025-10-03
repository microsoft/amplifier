# Principle #26 - Stateless by Default

## Plain-Language Definition

Design components and operations to avoid storing internal state whenever possible. Stateless components receive all the information they need to operate from inputs and external stores, making them predictable, reproducible, and easy to reason about.

## Why This Matters for AI-First Development

When AI agents build and modify systems, they must understand how components behave. Stateful components are inherently harder to reason about because their behavior depends on hidden history—past inputs, previous operations, and accumulated internal state. An AI agent looking at a stateful component can't predict its behavior without understanding its entire lifecycle and current state. This makes code generation, debugging, and refactoring dramatically more complex.

Stateless components provide three critical benefits for AI-driven development:

1. **Predictable behavior**: A stateless function always produces the same output for the same input. This makes it trivial for AI agents to understand what the code does, test its behavior, and verify correctness. When regenerating code, the AI doesn't need to worry about preserving complex state transitions.

2. **Trivial scaling and replication**: Stateless components can be replicated, restarted, or replaced without coordination. AI agents can deploy multiple instances, kill and restart containers, or regenerate components without worrying about losing critical state or synchronizing across instances.

3. **Simplified debugging and recovery**: When something goes wrong, stateless systems are easier to debug because you only need to examine the inputs, not the entire state history. Recovery is simpler too—just restart the component with the same inputs.

Without statelessness, AI systems become fragile and opaque. A crashed stateful service might lose critical data. A regenerated component might need complex migration logic to preserve state. Debugging requires understanding state transitions across time. These challenges compound in AI-first systems where components are frequently regenerated, replaced, and scaled automatically without human oversight.

## Implementation Approaches

### 1. **Pure Functions Everywhere**

Design functions that depend only on their inputs and external reads:

```python
# Stateless: behavior determined entirely by inputs
def calculate_order_total(items: list[LineItem], tax_rate: float) -> Decimal:
    subtotal = sum(item.price * item.quantity for item in items)
    tax = subtotal * tax_rate
    return subtotal + tax
```

The function has no internal state, no side effects, and produces the same result every time for the same inputs. This makes it trivial for AI to understand, test, and regenerate.

### 2. **State in External Stores**

Move all state to dedicated external systems (databases, caches, object stores):

```python
# Component is stateless; state lives in database
def get_user_preferences(user_id: str) -> UserPreferences:
    return db.query("SELECT * FROM user_preferences WHERE user_id = ?", user_id)

def update_user_preferences(user_id: str, prefs: UserPreferences):
    db.execute("UPDATE user_preferences SET ... WHERE user_id = ?", user_id)
```

The component itself holds no state. You can kill and restart it without losing anything. Multiple instances can run in parallel without coordination.

### 3. **Request-Scoped Context Only**

For operations that need temporary context, pass it explicitly through the call chain:

```python
# Pass context explicitly; don't store in component state
def process_payment(payment_data: PaymentData, user_context: UserContext) -> PaymentResult:
    validate_payment(payment_data, user_context)
    result = charge_card(payment_data)
    notify_user(result, user_context)
    return result
```

Context lives only for the duration of the request. Once the operation completes, all context is discarded. This makes the operation naturally idempotent and easy to retry.

### 4. **Stateless Microservices Pattern**

Design services that can be killed and restarted at any time:

```python
# Service has no internal state
@app.get("/api/recommendations/{user_id}")
def get_recommendations(user_id: str):
    user_profile = user_service.get_profile(user_id)  # External call
    purchase_history = order_service.get_history(user_id)  # External call
    recommendations = generate_recommendations(user_profile, purchase_history)
    return recommendations
```

The service fetches everything it needs from external sources and returns results. No state accumulates between requests. You can run 1 instance or 100, and behavior is identical.

### 5. **Immutable Data Structures**

When you must pass data around, use immutable structures:

```python
from dataclasses import dataclass

@dataclass(frozen=True)  # Immutable
class OrderSummary:
    order_id: str
    items: tuple[LineItem, ...]  # Immutable collection
    total: Decimal

def add_item(summary: OrderSummary, new_item: LineItem) -> OrderSummary:
    # Return new instance instead of modifying
    return OrderSummary(
        order_id=summary.order_id,
        items=summary.items + (new_item,),
        total=summary.total + new_item.price
    )
```

Immutability enforces statelessness. You can't accidentally mutate shared state, making behavior predictable.

### 6. **Event Sourcing for State Changes**

Store state as a sequence of immutable events rather than mutable snapshots:

```python
def apply_events(initial_state: dict, events: list[Event]) -> dict:
    """Stateless: same events always produce same final state"""
    state = initial_state.copy()
    for event in events:
        state = apply_event(state, event)
    return state
```

The component is stateless—it just applies a pure function to a sequence of events. State reconstruction is deterministic and reproducible.

## Good Examples vs Bad Examples

### Example 1: Request Handler

**Good:**
```python
from fastapi import FastAPI, Depends

app = FastAPI()

def get_db_session():
    """Dependency injection provides external state"""
    return create_session()

@app.get("/api/users/{user_id}")
def get_user(user_id: str, db = Depends(get_db_session)):
    """Stateless: all state comes from database"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    return user.to_dict()

# Handler has no instance variables or state
# Can be called millions of times with consistent behavior
```

**Bad:**
```python
class UserHandler:
    def __init__(self):
        self.cache = {}  # Internal state!
        self.request_count = 0  # More state!

    def get_user(self, user_id: str):
        """Stateful: behavior changes over time"""
        self.request_count += 1

        # Check internal cache
        if user_id in self.cache:
            return self.cache[user_id]

        user = db.query(User).filter(User.id == user_id).first()
        self.cache[user_id] = user  # Accumulates state
        return user

# This instance accumulates state over time
# Behavior depends on which requests came before
# Can't easily replicate or restart
```

**Why It Matters:** The stateful handler can't be scaled horizontally (each instance has different cache state), can't be safely restarted (loses cache), and has unpredictable behavior (depends on request history). The stateless version can be replicated infinitely, restarted anytime, and behaves identically in all scenarios.

### Example 2: Data Processing Pipeline

**Good:**
```python
def process_data_batch(input_path: Path, output_path: Path, config: Config):
    """Stateless: pure transformation from inputs to outputs"""
    # Read input
    data = read_csv(input_path)

    # Transform (pure functions)
    cleaned = clean_data(data, config)
    enriched = enrich_data(cleaned, config)
    aggregated = aggregate_data(enriched, config)

    # Write output
    write_csv(output_path, aggregated)

# Can run this function 1000 times in parallel on different data
# Each run is independent and produces consistent results
```

**Bad:**
```python
class DataProcessor:
    def __init__(self):
        self.processed_count = 0
        self.error_count = 0
        self.buffer = []  # Internal state

    def process_record(self, record: dict):
        """Stateful: accumulates state across calls"""
        self.buffer.append(record)

        if len(self.buffer) >= 100:
            self._flush_buffer()

        self.processed_count += 1

    def _flush_buffer(self):
        # Process buffer and update internal state
        write_to_database(self.buffer)
        self.buffer = []

# Must maintain instance across all records
# Can't parallelize easily (shared state)
# Crash loses buffered data
# Behavior depends on when flush happens
```

**Why It Matters:** The stateful processor is fragile—a crash loses buffered data, and you can't safely run multiple instances without coordination. The stateless version can be parallelized trivially, retried safely, and never loses data.

### Example 3: Configuration Loading

**Good:**
```python
from functools import lru_cache

@lru_cache(maxsize=1)
def load_config(config_path: str = "/etc/app/config.yaml") -> Config:
    """Stateless with cached result (cache is transparent)"""
    with open(config_path) as f:
        data = yaml.safe_load(f)
    return Config.from_dict(data)

def process_request(request: Request) -> Response:
    """Gets fresh config each time (via cache)"""
    config = load_config()
    return handle_request(request, config)

# Function is stateless: same path -> same config
# Cache is an optimization, not state that affects behavior
# Can call from anywhere without setup
```

**Bad:**
```python
class ConfigManager:
    def __init__(self):
        self.config = None
        self.loaded = False

    def load_config(self, path: str):
        """Stateful: must be called before use"""
        with open(path) as f:
            self.config = yaml.safe_load(f)
        self.loaded = True

    def get_config(self) -> dict:
        """Behavior depends on whether load_config was called"""
        if not self.loaded:
            raise RuntimeError("Config not loaded!")
        return self.config

# Must instantiate and initialize before use
# Order of operations matters (load before get)
# Multiple instances might have different config
# AI agent must understand initialization sequence
```

**Why It Matters:** The stateful config manager requires careful initialization and can't be used safely from multiple places without coordination. The stateless version works correctly regardless of call order or context, making it trivial for AI to understand and use.

### Example 4: Authentication Check

**Good:**
```python
def verify_token(token: str, secret_key: str) -> User | None:
    """Stateless: pure function from token to user"""
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        user_id = payload.get("user_id")
        return get_user_from_db(user_id)
    except jwt.InvalidTokenError:
        return None

@app.get("/api/protected")
def protected_endpoint(user = Depends(verify_token)):
    """Stateless: authentication happens per request"""
    return {"message": f"Hello {user.name}"}

# Each request is independently authenticated
# No session state to manage
# Works identically across all instances
```

**Bad:**
```python
class SessionManager:
    def __init__(self):
        self.active_sessions = {}  # session_id -> user
        self.session_timeouts = {}  # session_id -> expiry

    def login(self, username: str, password: str) -> str:
        """Creates stateful session"""
        if verify_password(username, password):
            session_id = generate_session_id()
            self.active_sessions[session_id] = get_user(username)
            self.session_timeouts[session_id] = time.time() + 3600
            return session_id
        raise AuthError("Invalid credentials")

    def verify_session(self, session_id: str) -> User:
        """Behavior depends on internal session state"""
        if session_id not in self.active_sessions:
            raise AuthError("Invalid session")
        if time.time() > self.session_timeouts[session_id]:
            del self.active_sessions[session_id]
            raise AuthError("Session expired")
        return self.active_sessions[session_id]

# Must maintain session state across requests
# Can't scale horizontally without session replication
# Restart loses all sessions
# Memory grows unbounded without cleanup
```

**Why It Matters:** The stateful session manager requires sticky sessions (requests from the same user must hit the same instance) or complex state replication. The stateless version works identically across all instances and can scale infinitely. AI agents can understand and regenerate the stateless version without worrying about session migration or state synchronization.

### Example 5: Task Queue Worker

**Good:**
```python
def process_task(task: Task, context: WorkerContext) -> TaskResult:
    """Stateless worker: each task is independent"""
    # Fetch everything needed for this task
    user = context.user_service.get(task.user_id)
    config = context.config_service.get_current()

    # Process task
    result = execute_task_logic(task, user, config)

    # Store result
    context.result_store.save(result)

    return result

# Can run 1 worker or 1000 workers
# Each processes tasks independently
# Workers can die and restart without losing work
# Task queue handles state (what's pending vs complete)
```

**Bad:**
```python
class TaskWorker:
    def __init__(self):
        self.processed_tasks = set()  # Track what we've done
        self.current_task = None
        self.task_count = 0
        self.in_progress = False

    def process_next_task(self, task: Task):
        """Stateful: tracks processing state internally"""
        if self.in_progress:
            raise RuntimeError("Already processing a task")

        if task.id in self.processed_tasks:
            return  # Skip duplicates

        self.current_task = task
        self.in_progress = True

        try:
            result = execute_task_logic(task)
            self.processed_tasks.add(task.id)
            self.task_count += 1
        finally:
            self.in_progress = False
            self.current_task = None

# Must maintain worker instance across tasks
# Can't run multiple workers without coordination
# Crash loses tracking of processed tasks
# State grows unbounded (processed_tasks)
```

**Why It Matters:** The stateful worker can't be replicated (each instance tracks different processed tasks), can't be safely restarted (loses task tracking), and has memory leaks (processed_tasks grows forever). The stateless version trivially scales to thousands of workers, each independently processing tasks.

## Related Principles

- **[Principle #31 - Idempotency by Design](31-idempotency-by-design.md)** - Stateless operations are naturally more idempotent because they don't accumulate state across calls. Without internal state, running an operation twice produces the same result as running it once.

- **[Principle #27 - Disposable Components Everywhere](27-disposable-components.md)** - Stateless components are inherently disposable. You can kill and restart them at any time without losing data or breaking functionality, making them perfect for fault-tolerant systems.

- **[Principle #24 - Long-Running Agent Processes](24-configuration-as-immutable-artifacts.md)** - Stateless components read configuration from immutable artifacts rather than accumulating configuration state over time, ensuring consistent behavior across restarts.

- **[Principle #32 - Error Recovery Patterns Built In](32-error-recovery-patterns.md)** - Stateless components simplify error recovery—just restart the component. No need to restore complex internal state or handle partially-updated state.

- **[Principle #33 - Graceful Degradation by Design](33-observable-operations-by-default.md)** - Stateless operations are easier to observe because their behavior depends only on observable inputs, not hidden internal state.

- **[Principle #7 - Regenerate, Don't Edit](../process/07-regenerate-dont-edit.md)** - Stateless components can be safely regenerated because there's no complex internal state to preserve. AI agents can regenerate the entire component without worrying about state migration.

## Common Pitfalls

1. **Hidden State in Closures**: Functions that capture mutable state from enclosing scopes become stateful without obvious indication.
   - Example: `counter = 0; def increment(): nonlocal counter; counter += 1` looks stateless but isn't.
   - Impact: Unpredictable behavior, race conditions, inability to parallelize.

2. **Class Instance Variables as State**: Using `self.variable` to store state across method calls makes the entire instance stateful.
   - Example: `self.cache = {}` in `__init__` means every method call potentially depends on previous calls.
   - Impact: Can't replicate instances, difficult to test, behavior depends on call order.

3. **Global Variables**: Mutable global state is shared across all operations, creating hidden dependencies.
   - Example: `PROCESSED_IDS = set(); def process(id): if id in PROCESSED_IDS: return; PROCESSED_IDS.add(id)`
   - Impact: Thread-unsafe, can't parallelize, impossible to test in isolation.

4. **File System as State**: Treating the file system as component state (beyond explicit caching) creates hidden dependencies.
   - Example: Writing temp files in `__init__` and reading them in methods without explicit path management.
   - Impact: Race conditions, cleanup problems, hard to understand component lifecycle.

5. **Singleton Pattern**: Singletons enforce a single stateful instance, making the entire class stateful by design.
   - Example: `class ConfigManager: _instance = None; @classmethod def get_instance()`
   - Impact: Hidden global state, testing difficulties, can't have multiple configurations.

6. **Generators with Side Effects**: Generators that modify external state during iteration become stateful.
   - Example: `def process_items(): for item in items: self.count += 1; yield process(item)`
   - Impact: Partial consumption leaves state incomplete, can't restart iteration safely.

7. **Database Connection Pooling Done Wrong**: Maintaining connection state in components rather than using external pooling.
   - Example: `self.connection = create_connection()` in component makes component stateful.
   - Impact: Can't safely restart component, connections leak on crash, hard to scale.

## Tools & Frameworks

### Functional Programming Libraries
- **toolz**: Functional programming utilities for Python (composition, immutable operations)
- **pyrsistent**: Immutable data structures (PVector, PMap, PSet) for enforcing statelessness
- **returns**: Railway-oriented programming with immutable Result types

### Web Frameworks Encouraging Statelessness
- **FastAPI**: Dependency injection system encourages stateless request handlers
- **Flask**: Minimal framework that naturally supports stateless endpoints
- **Starlette**: ASGI framework with stateless middleware and routing

### State Management (External)
- **Redis**: External in-memory state store, keeping components themselves stateless
- **Memcached**: Distributed caching layer for externalized state
- **DynamoDB**: Serverless database for stateless compute functions

### Serverless Platforms (Inherently Stateless)
- **AWS Lambda**: Functions are stateless by design, state must be external
- **Google Cloud Functions**: No instance state preserved between invocations
- **Azure Functions**: Ephemeral compute with no guaranteed state persistence

### Testing Tools
- **pytest fixtures**: Create fresh test state for each test, enforcing statelessness
- **Hypothesis**: Property-based testing verifies stateless behavior
- **freezegun**: Time mocking ensures tests don't depend on hidden time state

## Implementation Checklist

When implementing this principle, ensure:

- [ ] Functions depend only on their explicit parameters, not hidden state
- [ ] Class instance variables store configuration or dependencies, not mutable state
- [ ] All mutable state lives in external stores (database, cache, file system)
- [ ] Components can be killed and restarted without data loss
- [ ] Multiple instances of a component can run simultaneously without coordination
- [ ] Request handlers don't accumulate state across requests
- [ ] Configuration is loaded from external sources, not accumulated over time
- [ ] Data structures are immutable where possible (frozen dataclasses, tuples)
- [ ] Tests can run in any order without setup dependencies
- [ ] No global mutable variables are used for component state
- [ ] Generators and iterators don't modify external state during iteration
- [ ] Documentation explicitly notes any necessary state and where it lives

## Metadata

**Category**: Technology
**Principle Number**: 26
**Related Patterns**: Pure Functions, Dependency Injection, Immutable Objects, Stateless Services, Event Sourcing
**Prerequisites**: Understanding of state vs configuration, external storage systems, functional programming basics
**Difficulty**: Medium
**Impact**: High

---

**Status**: Complete
**Last Updated**: 2025-09-30
**Version**: 1.0