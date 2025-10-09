# Principle #08 - Contract-First Everything

## Plain-Language Definition

Define contracts (APIs, interfaces, schemas, protocols) before implementing code. Contracts are the stable connection points between modules—like LEGO studs and sockets—that remain unchanged even when internal implementations are regenerated or replaced.

## Why This Matters for AI-First Development

In traditional development, contracts often emerge organically as code is written. A function signature evolves through refactoring, an API endpoint gets shaped by implementation constraints, a database schema grows feature by feature. This works when humans coordinate closely, but creates chaos in AI-first systems where multiple agents work in parallel or modules are frequently regenerated.

Contract-first development inverts this: you design the connections before building the components. This is critical for AI systems because it enables three key capabilities:

**Parallel Development**: When contracts are defined first, different AI agents can implement different modules simultaneously without stepping on each other. One agent builds the frontend consuming an API while another implements the backend—both working from the same API contract. Without contracts, one agent must wait for the other to finish, then adapt to whatever interface emerged.

**Safe Regeneration**: Contracts are the stable anchors that enable module regeneration (Principle #07). When you regenerate a module's implementation, the contract guarantees it will still connect correctly to its dependents. Without explicit contracts, regeneration risks breaking everything that depends on the module.

**Predictable Integration**: AI agents can reason about system behavior by examining contracts without understanding implementations. A well-defined contract makes integration mechanical—ensuring the signatures match and handling specified errors—rather than requiring deep understanding of implementation details.

The "bricks and studs" metaphor captures this perfectly: LEGO bricks work because the studs and sockets are standardized. You can freely swap bricks (regenerate implementations) as long as the connection points (contracts) remain compatible. The same brick can be red or blue (different implementations) but the studs remain identical (stable contract).

For AI-driven systems, contracts also serve as reliable context. An AI agent can load a contract specification and generate correct implementations without needing to understand the entire system. This focused context dramatically improves generation quality and reduces token usage compared to working with full implementations.

## Implementation Approaches

### 1. **API-First Design with OpenAPI/Swagger**

Define REST APIs as OpenAPI specifications before implementing endpoints. Generate server stubs and client SDKs from the contract.

```yaml
# contracts/user_api.yaml - Define first
openapi: 3.0.0
paths:
  /users:
    post:
      summary: Create new user
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateUserRequest'
      responses:
        '201':
          description: User created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
```

Tools like OpenAPI Generator can produce type-safe clients and server stubs from this contract, ensuring implementation matches specification.

### 2. **Interface-Driven Development with Protocols**

Define interfaces as abstract contracts before concrete implementations. Use dependency injection to work against interfaces.

```python
# contracts/user_service.py - Define contract first
from typing import Protocol

class UserService(Protocol):
    """Contract for user management operations"""

    def create_user(self, email: str, password: str) -> User:
        """Create a new user account"""
        ...

    def get_user(self, user_id: str) -> User | None:
        """Retrieve user by ID"""
        ...

# Multiple implementations can satisfy this contract
# implementations/postgres_user_service.py
# implementations/mongo_user_service.py
# implementations/mock_user_service.py
```

### 3. **Schema-First Database Design**

Design database schemas explicitly before implementation. Use migrations to evolve schemas with clear versioning.

```python
# contracts/schemas/user_schema.py
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import DeclarativeBase

class User(DeclarativeBase):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)

# Generate migrations from schema changes
# alembic revision --autogenerate -m "add users table"
```

### 4. **GraphQL Schema Definition**

Define GraphQL schemas as the contract between frontend and backend. Generate type-safe resolvers and client queries.

```graphql
# contracts/schema.graphql
type User {
  id: ID!
  email: String!
  createdAt: DateTime!
}

type Query {
  user(id: ID!): User
  users(limit: Int = 10): [User!]!
}

type Mutation {
  createUser(email: String!, password: String!): User!
}
```

### 5. **Message Schema Contracts**

Define message formats for event-driven systems before implementing producers or consumers.

```python
# contracts/events/user_events.py
from dataclasses import dataclass
from datetime import datetime

@dataclass
class UserCreatedEvent:
    """Published when a new user is created"""
    user_id: str
    email: str
    created_at: datetime
    version: str = "1.0"

# Multiple services can consume this event contract
```

### 6. **Contract Testing**

Write tests that verify implementations satisfy contracts without testing implementation details.

```python
# contracts/tests/test_user_service_contract.py
def test_user_service_contract(user_service: UserService):
    """Test any UserService implementation against the contract"""
    # Contract: create_user returns User with email
    user = user_service.create_user("test@example.com", "password")
    assert user.email == "test@example.com"

    # Contract: get_user returns the same user
    retrieved = user_service.get_user(user.id)
    assert retrieved.id == user.id
```

## Good Examples vs Bad Examples

### Example 1: REST API Development

**Good:**
```yaml
# 1. Define contract first (contracts/order_api.yaml)
paths:
  /orders:
    post:
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [items, shipping_address]
              properties:
                items:
                  type: array
                  items:
                    $ref: '#/components/schemas/OrderItem'
                shipping_address:
                  $ref: '#/components/schemas/Address'

# 2. Generate server stubs
# openapi-generator generate -i contracts/order_api.yaml

# 3. Implement handlers that satisfy contract
@app.post("/orders")
def create_order(request: CreateOrderRequest) -> Order:
    # Implementation can be regenerated as long as it matches contract
    pass
```

**Bad:**
```python
# Write implementation first, let contract emerge
@app.post("/orders")
def create_order(request):  # What fields? What types?
    items = request.json.get("items")  # Optional or required?
    address = request.json.get("address")  # What structure?
    # Contract is implicit in implementation
```

**Why It Matters:** Contract-first enables parallel development (frontend team works from contract while backend implements) and ensures type safety. Implementation-first requires constant coordination and lacks guarantees.

### Example 2: Service Layer Interfaces

**Good:**
```python
# 1. Define contract (contracts/payment_service.py)
from typing import Protocol, Decimal

class PaymentService(Protocol):
    def charge(self, amount: Decimal, card_token: str) -> PaymentResult:
        """Charge a payment card. Raises PaymentError on failure."""
        ...

    def refund(self, payment_id: str, amount: Decimal) -> RefundResult:
        """Refund a payment. Idempotent."""
        ...

# 2. Implement against contract
class StripePaymentService:
    def charge(self, amount: Decimal, card_token: str) -> PaymentResult:
        # Implementation can be swapped without changing dependents
        pass
```

**Bad:**
```python
# Implementation first, interface emerges
class PaymentProcessor:
    def process_payment(self, amt, card):  # Different naming
        # What does it return? What errors?
        pass

    def do_refund(self, payment_ref, amt=None):  # Different signature
        # Is amount optional? What's the default?
        pass
```

**Why It Matters:** Explicit contracts enable swapping implementations (mock for testing, different provider for production) and make behavior predictable. Implicit contracts require reading implementation to understand behavior.

### Example 3: Database Schema Evolution

**Good:**
```python
# 1. Define schema contract
class Order(Base):
    __tablename__ = "orders"
    id = Column(UUID, primary_key=True)
    status = Column(Enum("pending", "paid", "shipped"), nullable=False)
    total = Column(Numeric(10, 2), nullable=False)

# 2. Generate migration from schema change
# alembic revision --autogenerate -m "add orders table"

# 3. Migration clearly shows contract evolution
def upgrade():
    op.create_table(
        'orders',
        sa.Column('id', UUID(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'paid', 'shipped'), nullable=False),
        sa.Column('total', sa.Numeric(10, 2), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
```

**Bad:**
```sql
-- Write SQL first, backfill schema later (or never)
CREATE TABLE orders (
    id VARCHAR(36) PRIMARY KEY,  -- Should be UUID but used VARCHAR
    status VARCHAR(20),  -- Should be enum but used VARCHAR
    total DECIMAL  -- Missing precision specification
);

-- Schema definition doesn't match actual database
```

**Why It Matters:** Schema-first ensures code matches database reality and provides clear evolution history. SQL-first creates drift between declared schema and actual database structure.

### Example 4: Message Queue Events

**Good:**
```python
# 1. Define event contract
@dataclass
class OrderPlacedEvent:
    """Published when customer places an order"""
    order_id: str
    customer_id: str
    total_amount: Decimal
    timestamp: datetime
    version: str = "1.0"

# 2. Producer publishes contract
def place_order(order: Order):
    event = OrderPlacedEvent(
        order_id=order.id,
        customer_id=order.customer_id,
        total_amount=order.total,
        timestamp=datetime.utcnow()
    )
    publish("orders.placed", event)

# 3. Consumers depend on contract
def handle_order_placed(event: OrderPlacedEvent):
    # Type-safe consumption of known structure
    send_confirmation_email(event.customer_id, event.order_id)
```

**Bad:**
```python
# No contract, just publish dictionaries
def place_order(order):
    publish("orders", {
        "id": order.id,
        "cust": order.customer_id,  # Inconsistent naming
        "total": float(order.total),  # Type conversion in producer
        # Missing timestamp
    })

# Consumer guesses at structure
def handle_order(msg):
    order_id = msg.get("id") or msg.get("order_id")  # Which one?
    customer_id = msg.get("cust") or msg.get("customer_id")
    # Fragile and error-prone
```

**Why It Matters:** Event contracts enable confident consumption and schema evolution. Without contracts, producers and consumers drift, causing runtime errors and data inconsistencies.

### Example 5: Module Boundaries

**Good:**
```python
# contracts/auth_module.py - Public interface
class AuthModule(Protocol):
    def authenticate(self, credentials: Credentials) -> User:
        """Returns User if credentials valid, raises AuthError otherwise"""
        ...

    def check_permission(self, user: User, resource: str) -> bool:
        """Returns True if user can access resource"""
        ...

# Implementation can use any internal structure
# implementations/auth/
#   ├── jwt_handler.py
#   ├── permission_checker.py
#   └── user_validator.py
# As long as it satisfies the public contract
```

**Bad:**
```python
# No contract, internal functions become de facto API
# auth.py
def _validate_jwt(token):  # Internal but used externally
    pass

def _check_db_permissions(user_id, resource):  # Internal but used externally
    pass

# Other modules import and use "private" functions
from auth import _validate_jwt, _check_db_permissions
```

**Why It Matters:** Explicit contracts define public vs private clearly. Without contracts, internal functions become implicit API, preventing refactoring and creating tight coupling.

## Related Principles

- **[Principle #07 - Regenerate, Don't Edit](07-regenerate-dont-edit.md)** - Contracts enable safe regeneration by preserving stable connection points while implementations change

- **[Principle #18 - Contract Evolution with Migration Paths](18-contract-evolution-migration.md)** - Defines how to evolve contracts over time without breaking existing dependents

- **[Principle #25 - Simple Interfaces by Design](../technology/25-simple-interfaces-design.md)** - Contracts should be simple and focused to maximize stability and usability

- **[Principle #22 - Separation of Concerns Through Layered Virtualization](../technology/22-layered-virtualization.md)** - Contracts define boundaries between layers

- **[Principle #09 - Tests as Quality Gate](09-tests-as-quality-gate.md)** - Contract tests verify implementations satisfy their contracts

- **[Principle #16 - Docs Define, Not Describe](16-docs-define-not-describe.md)** - Contract documentation is prescriptive (defines behavior) not descriptive (describes implementation)

## Common Pitfalls

1. **Defining Contracts After Implementation**: Writing OpenAPI specs or interface definitions by reverse-engineering existing code loses the benefits of contract-first design.
   - Example: Implementing a user API, then generating OpenAPI from code annotations.
   - Impact: Contract reflects implementation limitations rather than ideal interface design.

2. **Vague or Incomplete Contracts**: Contracts that don't specify error conditions, validation rules, or edge case behavior.
   - Example: API contract says "creates user" but doesn't specify what happens if email already exists.
   - Impact: Implementations handle edge cases differently, creating inconsistent behavior.

3. **Mixing Contract and Implementation**: Putting implementation details in contract definitions or failing to separate public contracts from internal code.
   - Example: Contract includes database-specific types or internal helper functions.
   - Impact: Contract changes whenever implementation details change, defeating the purpose.

4. **Over-Specified Contracts**: Including implementation details in contracts that should only specify behavior.
   - Example: Contract specifies "must use PostgreSQL" or "must use bcrypt with 12 rounds."
   - Impact: Limits implementation flexibility and couples contract to specific technologies.

5. **Forgetting Backwards Compatibility**: Changing contracts without versioning or migration paths.
   - Example: Renaming a required field in an API contract without deprecation period.
   - Impact: All consumers break instantly with no migration path.

6. **No Contract Validation**: Implementations drift from contracts because nothing enforces compliance.
   - Example: Contract says email is required but implementation allows null.
   - Impact: Contract becomes untrustworthy, defeats the purpose of having contracts.

7. **Single-Use Contracts**: Defining contracts that are only used by one implementation, adding overhead without benefit.
   - Example: Creating an interface for a service that will only ever have one implementation.
   - Impact: Unnecessary abstraction without the benefits of contract-first design.

## Tools & Frameworks

### API Specification Tools
- **OpenAPI/Swagger**: REST API contract definition and code generation
- **GraphQL Schema**: Type-safe API contracts with code generation
- **gRPC/Protocol Buffers**: Efficient binary API contracts
- **AsyncAPI**: Event-driven API contract specification

### Contract Testing
- **Pact**: Consumer-driven contract testing framework
- **Spring Cloud Contract**: Contract testing for microservices
- **Postman**: API contract testing and validation
- **Dredd**: API contract validation against OpenAPI specs

### Code Generation from Contracts
- **OpenAPI Generator**: Generate clients/servers from OpenAPI
- **GraphQL Code Generator**: Generate types from GraphQL schemas
- **Protocol Buffers Compiler**: Generate code from proto files
- **SQLAlchemy**: Generate migrations from model schemas

### Type Systems
- **TypeScript**: Structural typing for interface contracts
- **Python typing/Protocol**: Nominal and structural typing
- **Rust traits**: Strong compile-time contract enforcement
- **Go interfaces**: Implicit interface satisfaction

### Schema Validation
- **JSON Schema**: Validate data against contracts
- **Pydantic**: Python data validation using type hints
- **Zod**: TypeScript schema validation
- **Joi**: JavaScript schema validation

## Implementation Checklist

When implementing this principle, ensure:

- [ ] All module boundaries have explicit contract definitions
- [ ] Contracts are defined before implementations
- [ ] Contracts are versioned separately from implementations
- [ ] Contract changes follow a defined evolution process
- [ ] Generated code (stubs, types) is derived from contracts
- [ ] Contract tests verify implementations satisfy contracts
- [ ] Public contracts are separated from internal implementation
- [ ] Contracts specify error conditions and edge cases
- [ ] Breaking changes to contracts go through deprecation
- [ ] Contract documentation is prescriptive, not descriptive
- [ ] All teams understand which files are contracts vs implementations
- [ ] Contracts are the source of truth for integration

## Metadata

**Category**: Process
**Principle Number**: 08
**Related Patterns**: Interface Segregation, Dependency Inversion, API Gateway, Adapter Pattern
**Prerequisites**: Understanding of interfaces, APIs, and module boundaries
**Difficulty**: Medium
**Impact**: High

---

**Status**: Complete
**Last Updated**: 2025-09-30
**Version**: 1.0