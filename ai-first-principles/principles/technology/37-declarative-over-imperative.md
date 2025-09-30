# Principle #37 - Declarative Over Imperative

## Plain-Language Definition

Declarative code describes what you want the system to do, while imperative code describes how to do it step-by-step. Declarative specifications let you state the desired end state and let the system figure out how to achieve it.

## Why This Matters for AI-First Development

When AI agents generate code, declarative specifications are dramatically easier for them to understand, validate, and implement correctly. A declarative statement like "ensure this database table exists with these columns" is unambiguous. An imperative sequence like "connect to the database, check if the table exists, if not create it, then verify the columns match, and if they don't..." requires the AI to track complex state and handle all edge cases correctly.

Declarative code naturally aligns with how AI models think. AI excels at pattern matching and generating code that matches a specification. When you declare "this is the desired state," the AI can generate implementation code that achieves that state. With imperative code, the AI must not only understand the specification but also devise the correct sequence of steps, handle all error conditions, and avoid race conditions—a much harder problem.

Three critical benefits emerge for AI-driven development:

1. **Easier code generation**: AI can map declarative specifications directly to implementation patterns without inventing control flow logic from scratch.

2. **Natural idempotency**: Declarative operations are inherently idempotent—running "ensure table exists" multiple times produces the same result. This makes AI-generated code safer and more reliable.

3. **Simpler validation**: Validating declarative code means checking "does the actual state match the declared state?" rather than tracing through imperative logic to verify correctness.

Without declarative approaches, AI-generated code becomes verbose, brittle, and full of subtle bugs. Imperative code with complex control flow is where AI agents make mistakes—forgetting edge cases, introducing race conditions, or generating overly complex solutions to simple problems.

## Implementation Approaches

### 1. **Declare Desired State, Not Steps**

Instead of writing step-by-step procedures, declare what the final state should be and let the implementation ensure it:

```python
# Declarative
def ensure_user_has_role(user_id: str, role: str):
    """User should have this role"""
    user = get_user(user_id)
    if role not in user.roles:
        user.roles.add(role)
    save_user(user)
```

This approach works well for configuration management, resource provisioning, and state synchronization. Success looks like: the system can determine current state, compare to desired state, and make only the necessary changes.

### 2. **Configuration as Code**

Express configuration declaratively rather than through imperative setup scripts:

```yaml
# Declarative configuration
database:
  host: postgres.local
  port: 5432
  pools:
    - name: main
      size: 20
      timeout: 30s
    - name: readonly
      size: 10
      timeout: 10s
```

This approach is ideal for application settings, infrastructure definitions, and deployment specifications. Success looks like: configuration files fully describe the desired state without any procedural logic.

### 3. **SQL Over Procedural Loops**

Use declarative query languages instead of imperative iteration:

```sql
-- Declarative SQL
UPDATE users
SET status = 'active'
WHERE last_login > NOW() - INTERVAL '30 days'
  AND status = 'inactive';
```

This approach excels for data transformations, bulk updates, and complex queries. Success looks like: the database engine optimizes execution while you only specify what data should look like.

### 4. **Infrastructure as Code**

Define infrastructure declaratively so AI can manage resources safely:

```terraform
# Declarative infrastructure
resource "aws_s3_bucket" "data" {
  bucket = "my-app-data"

  versioning {
    enabled = true
  }

  lifecycle_rule {
    enabled = true
    expiration {
      days = 90
    }
  }
}
```

This approach is essential for cloud resources, networking, and deployment pipelines. Success looks like: running the specification multiple times produces the same infrastructure state.

### 5. **Domain-Specific Languages (DSLs)**

Create declarative DSLs for domain-specific problems:

```python
# Declarative validation DSL
user_schema = {
    "email": Required(Email()),
    "age": Required(Integer(min=0, max=150)),
    "role": Optional(OneOf(["admin", "user", "guest"]))
}
```

This approach works well for validation, routing rules, and business logic. Success looks like: domain experts can read and modify the declarations without understanding implementation details.

### 6. **Reactive Declarations**

Declare how data flows and transforms rather than orchestrating updates:

```python
# Declarative reactive system
@computed
def total_price(items: List[Item], discount: float) -> float:
    """Total is always derived from current items and discount"""
    subtotal = sum(item.price * item.quantity for item in items)
    return subtotal * (1 - discount)
```

This approach is ideal for UI state management, derived data, and real-time updates. Success looks like: data dependencies are explicit and updates propagate automatically.

## Good Examples vs Bad Examples

### Example 1: Database Schema Management

**Good:**
```python
def ensure_schema():
    """Declarative: describe what the schema should be"""
    desired_schema = {
        "users": {
            "id": "SERIAL PRIMARY KEY",
            "email": "VARCHAR(255) UNIQUE NOT NULL",
            "created_at": "TIMESTAMP DEFAULT NOW()"
        },
        "posts": {
            "id": "SERIAL PRIMARY KEY",
            "user_id": "INTEGER REFERENCES users(id)",
            "content": "TEXT NOT NULL",
            "published_at": "TIMESTAMP"
        }
    }

    # Tool compares desired vs actual and makes only necessary changes
    apply_schema(desired_schema)
```

**Bad:**
```python
def create_tables():
    """Imperative: step-by-step table creation"""
    conn = connect_to_db()
    cursor = conn.cursor()

    # Check if users table exists
    cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='users')")
    if not cursor.fetchone()[0]:
        cursor.execute("""
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

    # Check if posts table exists
    cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='posts')")
    if not cursor.fetchone()[0]:
        cursor.execute("""
            CREATE TABLE posts (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                content TEXT NOT NULL,
                published_at TIMESTAMP
            )
        """)

    conn.commit()
    cursor.close()
    conn.close()
```

**Why It Matters:** The declarative version is 15 lines vs 30+ imperative lines, and it's dramatically easier for AI to generate correctly. The AI only needs to emit the desired schema structure, not implement the logic for checking existence, creating tables, and handling errors.

### Example 2: User Permission Management

**Good:**
```python
# Declarative permissions
PERMISSIONS = {
    "admin": [
        "users:create", "users:read", "users:update", "users:delete",
        "posts:create", "posts:read", "posts:update", "posts:delete",
        "settings:read", "settings:update"
    ],
    "editor": [
        "posts:create", "posts:read", "posts:update",
        "users:read"
    ],
    "viewer": [
        "posts:read",
        "users:read"
    ]
}

def ensure_user_permissions(user_id: str, role: str):
    """Set user permissions to match role declaration"""
    desired_permissions = PERMISSIONS[role]
    sync_user_permissions(user_id, desired_permissions)
```

**Bad:**
```python
# Imperative permissions
def setup_admin_permissions(user_id: str):
    add_permission(user_id, "users:create")
    add_permission(user_id, "users:read")
    add_permission(user_id, "users:update")
    add_permission(user_id, "users:delete")
    add_permission(user_id, "posts:create")
    add_permission(user_id, "posts:read")
    add_permission(user_id, "posts:update")
    add_permission(user_id, "posts:delete")
    add_permission(user_id, "settings:read")
    add_permission(user_id, "settings:update")

def setup_editor_permissions(user_id: str):
    add_permission(user_id, "posts:create")
    add_permission(user_id, "posts:read")
    add_permission(user_id, "posts:update")
    add_permission(user_id, "users:read")

def setup_viewer_permissions(user_id: str):
    add_permission(user_id, "posts:read")
    add_permission(user_id, "users:read")

def change_user_role(user_id: str, old_role: str, new_role: str):
    # Remove old permissions
    if old_role == "admin":
        remove_all_permissions(user_id)
    elif old_role == "editor":
        remove_permission(user_id, "posts:create")
        remove_permission(user_id, "posts:update")
    # ... complex removal logic

    # Add new permissions
    if new_role == "admin":
        setup_admin_permissions(user_id)
    elif new_role == "editor":
        setup_editor_permissions(user_id)
    # ... complex addition logic
```

**Why It Matters:** The declarative version makes it trivial to see what permissions each role has and to add new roles. The imperative version requires separate functions for setup and role changes, complex logic for determining what to add/remove, and is prone to bugs when permissions drift.

### Example 3: Infrastructure Deployment

**Good:**
```terraform
# Declarative infrastructure
resource "aws_instance" "web_server" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"

  tags = {
    Name        = "web-server"
    Environment = "production"
  }

  vpc_security_group_ids = [aws_security_group.web.id]

  depends_on = [aws_security_group.web]
}

resource "aws_security_group" "web" {
  name        = "web-server-sg"
  description = "Security group for web server"

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

**Bad:**
```python
# Imperative infrastructure
def deploy_web_server():
    ec2 = boto3.client('ec2')

    # Check if security group exists
    try:
        sg_response = ec2.describe_security_groups(
            GroupNames=['web-server-sg']
        )
        sg_id = sg_response['SecurityGroups'][0]['GroupId']
    except:
        # Create security group
        sg_response = ec2.create_security_group(
            GroupName='web-server-sg',
            Description='Security group for web server'
        )
        sg_id = sg_response['GroupId']

        # Add ingress rules
        ec2.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 80,
                    'ToPort': 80,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 443,
                    'ToPort': 443,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                }
            ]
        )

    # Check if instance exists
    instances = ec2.describe_instances(
        Filters=[
            {'Name': 'tag:Name', 'Values': ['web-server']},
            {'Name': 'instance-state-name', 'Values': ['running']}
        ]
    )

    if not instances['Reservations']:
        # Create instance
        ec2.run_instances(
            ImageId='ami-0c55b159cbfafe1f0',
            InstanceType='t2.micro',
            SecurityGroupIds=[sg_id],
            MinCount=1,
            MaxCount=1,
            TagSpecifications=[{
                'ResourceType': 'instance',
                'Tags': [
                    {'Key': 'Name', 'Value': 'web-server'},
                    {'Key': 'Environment', 'Value': 'production'}
                ]
            }]
        )
```

**Why It Matters:** The declarative Terraform version is clear, concise, and automatically handles dependencies, idempotency, and state tracking. The imperative Python version is verbose, error-prone, and doesn't handle updates well (what if you need to change instance type?).

### Example 4: Data Validation

**Good:**
```python
# Declarative validation with schema
from pydantic import BaseModel, EmailStr, conint, validator

class UserInput(BaseModel):
    email: EmailStr
    age: conint(ge=0, le=150)
    username: str
    role: str

    @validator('username')
    def username_alphanumeric(cls, v):
        assert v.isalnum(), 'must be alphanumeric'
        return v

    @validator('role')
    def valid_role(cls, v):
        assert v in ['admin', 'user', 'guest'], 'invalid role'
        return v

# Usage is simple
try:
    user = UserInput(
        email="test@example.com",
        age=25,
        username="john123",
        role="user"
    )
except ValidationError as e:
    print(e.errors())
```

**Bad:**
```python
# Imperative validation with manual checks
def validate_user_input(data: dict) -> tuple[bool, list[str]]:
    errors = []

    # Check email
    if 'email' not in data:
        errors.append("email is required")
    else:
        email = data['email']
        if '@' not in email:
            errors.append("invalid email format")
        if not email.split('@')[0]:
            errors.append("email must have local part")
        if not email.split('@')[1]:
            errors.append("email must have domain")
        # ... more email validation

    # Check age
    if 'age' not in data:
        errors.append("age is required")
    else:
        try:
            age = int(data['age'])
            if age < 0:
                errors.append("age must be non-negative")
            if age > 150:
                errors.append("age must be 150 or less")
        except ValueError:
            errors.append("age must be an integer")

    # Check username
    if 'username' not in data:
        errors.append("username is required")
    else:
        username = data['username']
        if not username.isalnum():
            errors.append("username must be alphanumeric")

    # Check role
    if 'role' not in data:
        errors.append("role is required")
    else:
        role = data['role']
        if role not in ['admin', 'user', 'guest']:
            errors.append("invalid role")

    return len(errors) == 0, errors
```

**Why It Matters:** The declarative Pydantic version is type-safe, automatically generates documentation, provides clear error messages, and is much easier for AI to generate. The imperative version is verbose, repetitive, and easy to get wrong.

### Example 5: UI State Management

**Good:**
```python
# Declarative reactive UI state
from dataclasses import dataclass
from typing import List

@dataclass
class ShoppingCart:
    items: List[tuple[str, float, int]]  # (name, price, quantity)
    discount: float = 0.0

    @property
    def subtotal(self) -> float:
        """Subtotal is declared as computation from items"""
        return sum(price * quantity for name, price, quantity in self.items)

    @property
    def discount_amount(self) -> float:
        """Discount amount is declared as computation from subtotal"""
        return self.subtotal * self.discount

    @property
    def total(self) -> float:
        """Total is declared as computation from subtotal and discount"""
        return self.subtotal - self.discount_amount

    @property
    def item_count(self) -> int:
        """Item count is declared as sum of quantities"""
        return sum(quantity for name, price, quantity in self.items)

# Usage - all derived values update automatically
cart = ShoppingCart(items=[("Book", 20.0, 2), ("Pen", 1.5, 3)])
print(f"Total: ${cart.total:.2f}")  # Automatically computed

cart.discount = 0.1  # Change discount
print(f"Total: ${cart.total:.2f}")  # Total updates automatically
```

**Bad:**
```python
# Imperative UI state management
class ShoppingCart:
    def __init__(self):
        self.items: List[tuple[str, float, int]] = []
        self.discount: float = 0.0
        self.subtotal: float = 0.0
        self.discount_amount: float = 0.0
        self.total: float = 0.0
        self.item_count: int = 0

    def add_item(self, name: str, price: float, quantity: int):
        self.items.append((name, price, quantity))
        # Must manually update all derived values
        self._recalculate()

    def set_discount(self, discount: float):
        self.discount = discount
        # Must manually update all derived values
        self._recalculate()

    def remove_item(self, index: int):
        del self.items[index]
        # Must manually update all derived values
        self._recalculate()

    def update_quantity(self, index: int, quantity: int):
        name, price, _ = self.items[index]
        self.items[index] = (name, price, quantity)
        # Must manually update all derived values
        self._recalculate()

    def _recalculate(self):
        # Manually recalculate subtotal
        self.subtotal = 0.0
        for name, price, quantity in self.items:
            self.subtotal += price * quantity

        # Manually recalculate discount amount
        self.discount_amount = self.subtotal * self.discount

        # Manually recalculate total
        self.total = self.subtotal - self.discount_amount

        # Manually recalculate item count
        self.item_count = 0
        for name, price, quantity in self.items:
            self.item_count += quantity

# Usage - must remember to call recalculate or use specific methods
cart = ShoppingCart()
cart.add_item("Book", 20.0, 2)
cart.add_item("Pen", 1.5, 3)
print(f"Total: ${cart.total:.2f}")

cart.set_discount(0.1)
print(f"Total: ${cart.total:.2f}")
```

**Why It Matters:** The declarative version automatically maintains consistency—there's no way to forget to update derived values. The imperative version requires remembering to call `_recalculate()` after every change, leading to bugs where state becomes inconsistent.

## Related Principles

- **[Principle #31 - Idempotency by Design](31-idempotency-by-design.md)** - Declarative operations are naturally idempotent because they describe desired state rather than change sequences. Running a declarative specification multiple times produces the same result.

- **[Principle #8 - Context-First Architecture](../process/08-context-first-architecture.md)** - Declarative specifications are the most efficient form of context for AI agents. Instead of explaining step-by-step procedures, you declare "this is what the system should look like" and let the AI implement it.

- **[Principle #16 - Generation Over Accumulation](../process/16-generation-over-accumulation.md)** - Declarative specifications enable clean regeneration. Rather than accumulating patches to imperative code, you update the declaration and regenerate the implementation.

- **[Principle #21 - Simple Over Perfect](21-simple-over-perfect.md)** - Declarative code is inherently simpler because it eliminates complex control flow. The implementation handles the "how" while you focus on the "what."

- **[Principle #25 - Fail-Fast with Clear Errors](25-fail-fast-clear-errors.md)** - Declarative specifications make validation straightforward: compare actual state to desired state. Mismatches are immediately obvious and easy to report.

- **[Principle #28 - Composable Building Blocks](28-composable-building-blocks.md)** - Declarative components compose naturally because they describe interfaces and contracts rather than implementation details. You can nest declarative specifications to build complex systems.

## Common Pitfalls

1. **Hidden Imperative Code in Declarative Wrappers**: Creating a declarative-looking API that's just a thin wrapper around imperative code doesn't provide real benefits.
   - Example: `config.set("database.host", "localhost"); config.set("database.port", 5432)` looks declarative but still requires step-by-step calls.
   - Impact: Loses the benefits of declarative thinking, still requires managing order and state.

2. **Mixing Declarative and Imperative Styles**: Using both approaches in the same system creates confusion about when each applies.
   - Example: Using Terraform for infrastructure but manual bash scripts for configuration, or SQL queries mixed with procedural loops.
   - Impact: Inconsistent mental models, difficult to predict behavior, hard for AI to understand the codebase.

3. **Over-Abstracting the Declaration**: Creating such abstract declarative DSLs that they become harder to understand than imperative code.
   - Example: A configuration language so generic it requires understanding meta-programming concepts to use.
   - Impact: Defeats the simplicity benefit, makes code generation harder, creates learning barriers.

4. **Not Validating Declarative Specifications**: Accepting any declaration without validating that it's achievable or consistent.
   - Example: Allowing impossible infrastructure configurations that fail at deployment time.
   - Impact: Late failure detection, unclear error messages, difficult debugging.

5. **Ignoring Performance Trade-offs**: Assuming declarative is always faster because the system optimizes execution.
   - Example: Using ORM queries for operations where raw SQL would be 10x faster.
   - Impact: Performance problems that require reverting to imperative code, inconsistent optimization strategies.

6. **No Escape Hatch for Edge Cases**: Building purely declarative systems without any way to handle special cases imperatively.
   - Example: Configuration systems that can't handle one-off migrations or special initialization logic.
   - Impact: Forces workarounds in declarations, or requires abandoning the declarative approach entirely.

7. **Forgetting State Transitions**: Declaring end state without considering how to safely transition from current state.
   - Example: Database schema changes that would lose data during migration.
   - Impact: Dangerous deployments, data loss, need for manual intervention during updates.

## Tools & Frameworks

### Infrastructure as Code
- **Terraform**: Declarative infrastructure provisioning with state management and dependency resolution
- **Ansible**: Declarative configuration management with idempotent operations
- **Kubernetes**: Declarative container orchestration where you specify desired state and the system maintains it
- **CloudFormation**: AWS-native declarative infrastructure with rollback support

### Data and Queries
- **SQL**: The original declarative query language, letting databases optimize execution
- **GraphQL**: Declarative data fetching where clients specify exactly what data they need
- **LINQ**: Language-integrated queries that compile to optimized database operations
- **Pandas**: Declarative data transformations with query optimization

### Configuration Management
- **JSON Schema**: Declarative validation for JSON data structures
- **YAML**: Human-readable configuration format for declarative specifications
- **Pydantic**: Declarative data validation and settings management for Python
- **Zod**: TypeScript-first schema validation with static type inference

### UI and State Management
- **React (with hooks)**: Declarative UI where you describe what should render based on state
- **SwiftUI**: Declarative UI framework for iOS with automatic state synchronization
- **SQL**: Declarative reactive state management with derived values
- **Vue Composition API**: Declarative reactive data flow

### Build and Deployment
- **Make**: Declarative build system where you specify dependencies and targets
- **Bazel**: Declarative build system with automatic dependency management
- **Docker Compose**: Declarative multi-container application definitions
- **GitHub Actions**: Declarative CI/CD workflows

### Validation and Types
- **TypeScript**: Declarative type system that catches errors at compile time
- **OpenAPI**: Declarative API specification that generates documentation and validation
- **Protocol Buffers**: Declarative schema for structured data with code generation
- **JSON Schema**: Declarative validation rules for JSON data

## Implementation Checklist

When implementing this principle, ensure:

- [ ] Configuration is expressed as data structures, not procedural code
- [ ] Infrastructure specifications describe desired end state, not deployment steps
- [ ] Database operations use SQL or ORMs rather than procedural iteration
- [ ] Validation rules are declared as schemas, not implemented as imperative checks
- [ ] State transitions are expressed as transformations from one state to another
- [ ] Dependencies between components are explicitly declared, not implicitly ordered
- [ ] Error messages compare actual state to desired state
- [ ] Operations are naturally idempotent because they enforce declared state
- [ ] AI agents can generate implementations from declarative specifications
- [ ] Documentation shows declarations first, implementation details second
- [ ] Testing validates that actual state matches declared state
- [ ] Code reviews check for imperative patterns that could be declarative

## Metadata

**Category**: Technology
**Principle Number**: 37
**Related Patterns**: Infrastructure as Code, Configuration as Code, Domain-Specific Languages, Reactive Programming, Declarative APIs
**Prerequisites**: Understanding of state management, configuration systems, and the difference between describing goals vs. steps
**Difficulty**: Medium
**Impact**: High

---

**Status**: Complete
**Last Updated**: 2025-09-30
**Version**: 1.0