# Principle #07 - Regenerate, Don't Edit

## Plain-Language Definition

When modifying code, regenerate entire modules from their specifications rather than editing code line by line. Treat code as the output of specifications, not as the primary artifact to maintain.

## Why This Matters for AI-First Development

AI agents are fundamentally generators, not editors. When you ask an LLM to modify code, it's actually regenerating that code internally based on your instructions—the "edit" is an illusion. By embracing regeneration explicitly, we align our workflow with how AI actually works, leading to more reliable and maintainable systems.

Traditional development treats code as precious, making small surgical edits to avoid breaking things. This creates accumulating complexity as changes layer on top of changes, with the codebase drifting from its original design. Code reviews focus on ensuring each edit is correct, but the overall coherence degrades over time.

In AI-first development, regeneration inverts this model. The specification is precious, and code is disposable. When requirements change, you update the spec and regenerate the module. This ensures the code always reflects its current specification exactly, with no drift or accumulated cruft. The module is born fresh each time, incorporating all current requirements without legacy compromises.

This approach unlocks unique AI capabilities: parallel exploration (generate multiple variants simultaneously), fearless refactoring (regenerate with new patterns), and automatic consistency (all modules follow current standards). It also makes human review more effective—instead of verifying that a 50-line diff correctly implements a change, you verify that the specification captures requirements correctly, then trust the generation process.

The key insight is that code quality comes from specification quality, not from careful editing. A well-specified module that's regenerated will be more consistent and maintainable than a hand-edited module that's drifted from its original design. This requires a shift in mindset: invest in specifications and contracts, not in preserving specific code implementations.

## Implementation Approaches

### 1. **Module-Level Regeneration**

Regenerate complete modules (files or logical units) rather than editing portions. Define clear module boundaries that can be regenerated independently.

```python
# Instead of editing functions within auth.py, regenerate the entire module
# from auth_spec.md when authentication requirements change
```

Set boundaries at natural interfaces—don't split a cohesive implementation just to make regeneration easier, but don't make modules so large that regeneration becomes unwieldy.

### 2. **Contract Preservation During Regeneration**

Maintain stable external contracts (APIs, interfaces, schemas) even as internal implementation is regenerated. Document contracts explicitly so regeneration can preserve them.

```python
# contracts/auth_service.py - Never regenerate this
class AuthService(Protocol):
    def authenticate(self, credentials: Credentials) -> User: ...
    def authorize(self, user: User, resource: str) -> bool: ...

# implementations/auth_service.py - Regenerate freely as long as it satisfies the contract
```

### 3. **Specification-Driven Development**

Write specifications before code. Update specifications when requirements change. Regenerate code from specifications. Treat specs as the source of truth.

```markdown
<!-- user_management_spec.md -->
# User Management Module

## Public API
- `create_user(email, password) -> User`
- `get_user(user_id) -> User | None`
- `update_user(user_id, changes) -> User`

## Validation Rules
- Email must be valid format
- Password minimum 8 characters
- Email must be unique

## Storage
- PostgreSQL users table
- Passwords hashed with bcrypt
```

### 4. **Test-Driven Regeneration**

Write tests that verify behavior and contracts. Regenerate implementations that pass those tests. Tests serve as both verification and specification.

```python
# tests/test_user_service.py - Keep tests stable
def test_create_user_validates_email():
    with pytest.raises(ValidationError):
        create_user("invalid-email", "password123")

# src/user_service.py - Regenerate to pass tests
```

### 5. **Blueprint-Based Generation**

Use templates, schemas, or blueprints that define the structure of generated code. Update blueprints to change all instances, then regenerate.

```yaml
# api_blueprint.yaml
endpoints:
  - path: /users
    method: POST
    handler: create_user
    validation: user_schema
  - path: /users/{id}
    method: GET
    handler: get_user
```

### 6. **Incremental Regeneration**

Don't regenerate everything at once. Regenerate one module, verify it works, commit. Regenerate the next module. This localizes risk and simplifies debugging.

## Good Examples vs Bad Examples

### Example 1: Adding User Roles

**Good:**
```python
# Update specification
"""
user_spec.md:
- Users have a 'role' field (admin, user, guest)
- Roles determine permission levels
- Default role is 'user'
"""

# Regenerate user_service.py from updated spec
# Result: Clean implementation with roles integrated throughout
class User:
    def __init__(self, email: str, role: str = "user"):
        self.email = email
        self.role = role

    def has_permission(self, permission: str) -> bool:
        return permission in ROLE_PERMISSIONS[self.role]
```

**Bad:**
```python
# Edit existing User class to add roles
class User:
    def __init__(self, email: str):
        self.email = email
        self.role = "user"  # Added role but forgot to update other methods

    # Original method doesn't check roles
    def can_access_admin(self) -> bool:
        return True  # BUG: Should check role
```

**Why It Matters:** Regeneration ensures all methods are updated consistently to handle roles. Editing leaves old methods unchanged, creating bugs and inconsistency.

### Example 2: Changing API Response Format

**Good:**
```python
# Update API contract specification
"""
api_spec.md:
Response format changed from:
  {"data": {...}}
to:
  {"data": {...}, "meta": {"version": "v2"}}
"""

# Regenerate all endpoint handlers from spec
@app.get("/users/{id}")
def get_user(id: str):
    user = fetch_user(id)
    return {
        "data": user.to_dict(),
        "meta": {"version": "v2"}
    }
# All endpoints consistently return new format
```

**Bad:**
```python
# Edit each endpoint individually
@app.get("/users/{id}")
def get_user(id: str):
    user = fetch_user(id)
    return {
        "data": user.to_dict(),
        "meta": {"version": "v2"}  # Updated
    }

@app.get("/posts/{id}")
def get_post(id: str):
    post = fetch_post(id)
    return {"data": post.to_dict()}  # FORGOT to update this one!
```

**Why It Matters:** When changing cross-cutting concerns, regeneration ensures consistency. Editing is error-prone and leaves some endpoints using the old format.

### Example 3: Refactoring Database Access

**Good:**
```python
# Update data_access_spec.md to use new ORM patterns
"""
Migration: SQLAlchemy raw queries → ORM models
- All queries should use ORM methods
- Use session management context
- Apply consistent error handling
"""

# Regenerate data_access.py following new patterns
class UserRepository:
    def get_by_email(self, email: str) -> User | None:
        with get_session() as session:
            return session.query(User).filter_by(email=email).first()
# All methods follow new ORM pattern consistently
```

**Bad:**
```python
# Edit some methods to use ORM, leave others with raw SQL
class UserRepository:
    def get_by_email(self, email: str) -> User | None:
        # Updated to ORM
        with get_session() as session:
            return session.query(User).filter_by(email=email).first()

    def get_by_id(self, id: str) -> User | None:
        # Still using raw SQL - forgot to update
        cursor.execute("SELECT * FROM users WHERE id = ?", (id,))
        return cursor.fetchone()
```

**Why It Matters:** Partial refactoring creates inconsistent patterns in the codebase. Regeneration ensures all methods follow current standards.

### Example 4: Configuration File Updates

**Good:**
```yaml
# config_template.yaml - Source of truth
database:
  host: ${DB_HOST}
  port: ${DB_PORT}
  name: ${DB_NAME}
  pool_size: 10
  timeout: 30

# Regenerate actual config from template
# Result: All config files have same structure
```

**Bad:**
```yaml
# Manually edit config.yaml
database:
  host: localhost
  port: 5432
  name: mydb
  pool_size: 10
  # Forgot to add timeout when it was added to other configs
```

**Why It Matters:** Configuration drift is a common source of bugs. Regenerating from templates ensures all environments have consistent configuration structure.

### Example 5: Component Library Updates

**Good:**
```jsx
// Update component_spec.md with new design system
// Regenerate all Button components from spec
export const Button = ({ variant = "primary", children }) => (
  <button className={`btn btn-${variant} rounded-lg shadow-sm`}>
    {children}
  </button>
)
// All buttons immediately follow new design system
```

**Bad:**
```jsx
// Edit some button components manually
export const PrimaryButton = ({ children }) => (
  <button className="btn btn-primary rounded-lg shadow-sm">
    {children}  {/* Updated */}
  </button>
)

export const SecondaryButton = ({ children }) => (
  <button className="btn btn-secondary">
    {children}  {/* Forgot to update - still using old styles */}
  </button>
)
```

**Why It Matters:** Design system changes need to apply consistently across all components. Regeneration ensures instant, uniform application.

## Related Principles

- **[Principle #08 - Contract-First Everything](08-contract-first-everything.md)** - Contracts define what must be preserved during regeneration; specifications drive what to regenerate

- **[Principle #31 - Idempotency by Design](../technology/31-idempotency-by-design.md)** - Idempotency makes regeneration safe; running generation twice produces the same result

- **[Principle #27 - Disposable Components Everywhere](../technology/27-disposable-components.md)** - Components designed to be disposable can be freely regenerated without fear

- **[Principle #10 - Git as Safety Net](10-git-as-safety-net.md)** - Git enables fearless regeneration; you can always roll back if regeneration goes wrong

- **[Principle #09 - Tests as Quality Gate](09-tests-as-quality-gate.md)** - Tests verify that regenerated code meets requirements; failing tests indicate spec/code mismatch

- **[Principle #25 - Simple Interfaces by Design](../technology/25-simple-interfaces-design.md)** - Stable, simple interfaces enable regeneration of implementations without breaking dependents

## Common Pitfalls

1. **Regenerating Without Clear Contracts**: Attempting to regenerate modules that have implicit rather than explicit contracts leads to breaking changes in dependents.
   - Example: Regenerating an API handler without documenting which routes and response formats must be preserved.
   - Impact: Dependent services break because the contract changed unknowingly.

2. **Manual Customizations in Generated Code**: Adding hand-edits to generated code that get lost when regenerated.
   - Example: Adding a special-case check in generated code, then regenerating and losing that check.
   - Impact: Bug reappears, work is lost, customization needs to be re-added repeatedly.

3. **Regenerating Too Large a Scope**: Trying to regenerate an entire large application at once rather than incrementally by module.
   - Example: "Regenerate the whole backend to use the new framework."
   - Impact: Massive changes are hard to verify, debugging becomes nearly impossible, high risk of introducing bugs.

4. **Not Testing After Regeneration**: Assuming regenerated code works without verification.
   - Example: Regenerating a module, committing without running tests.
   - Impact: Silent breakage that only surfaces in production.

5. **Specification-Code Drift**: Updating code without updating specifications, or vice versa.
   - Example: Spec says password is 8+ characters, but generated code requires 10+ characters.
   - Impact: Spec becomes untrustworthy, regeneration produces incorrect code.

6. **Treating Code as Precious**: Psychological attachment to existing code prevents regeneration even when it would be beneficial.
   - Example: "This authentication code was carefully written—let's just edit it instead of regenerating."
   - Impact: Technical debt accumulates, code drifts from current patterns and standards.

7. **Forgetting to Preserve State**: Regenerating stateful components without preserving necessary state or data migrations.
   - Example: Regenerating a database model without creating migration for existing data.
   - Impact: Data loss or corruption, production outages.

## Tools & Frameworks

### Code Generators
- **Yeoman**: General-purpose code generator with template system
- **Plop**: Micro-generator framework for creating custom generators
- **Cookiecutter**: Template-based project and file generation
- **Hygen**: Fast code generator with template inheritance

### Schema-Driven Generation
- **OpenAPI Generator**: Generate clients, servers from OpenAPI specs
- **GraphQL Code Generator**: Generate types, resolvers from GraphQL schemas
- **Prisma**: Generate database client from schema
- **SQLAlchemy with Alembic**: Generate migrations from model changes

### Template Engines
- **Jinja2**: Python template engine for code generation
- **Mustache/Handlebars**: Logic-less templates for consistent generation
- **EJS**: Embedded JavaScript templates
- **Liquid**: Safe template language with filters

### Infrastructure as Code
- **Terraform**: Declarative infrastructure regeneration
- **Pulumi**: Programmatic infrastructure generation
- **AWS CDK**: Generate CloudFormation from code
- **Ansible**: Idempotent configuration management

### AI-Specific Tools
- **Claude Code SDK**: Programmatic LLM-driven code generation
- **GitHub Copilot**: AI-assisted code generation from comments
- **Cursor**: Editor with regeneration-first workflow
- **Aider**: AI pair programmer for spec-driven generation

## Implementation Checklist

When implementing this principle, ensure:

- [ ] Module boundaries are clearly defined and documented
- [ ] External contracts are explicitly specified and version-controlled
- [ ] Specifications exist for all modules that will be regenerated
- [ ] Tests verify behavior and contracts, not implementation details
- [ ] Regeneration process is automated and repeatable
- [ ] Generated code is marked as such (comments, file headers)
- [ ] Manual customizations are moved to specifications, not code
- [ ] Git history shows regeneration as atomic commits
- [ ] Team understands that code is disposable, specs are precious
- [ ] Regeneration is tested in isolation before integration
- [ ] Rollback plan exists if regeneration causes issues
- [ ] Documentation explains how to regenerate each module

## Metadata

**Category**: Process
**Principle Number**: 07
**Related Patterns**: Template Method, Strategy Pattern, Factory Pattern, Builder Pattern
**Prerequisites**: Version control, contract definitions, test coverage
**Difficulty**: Medium
**Impact**: High

---

**Status**: Complete
**Last Updated**: 2025-09-30
**Version**: 1.0