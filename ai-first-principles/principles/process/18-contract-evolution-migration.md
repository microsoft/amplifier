# Principle #18 - Contract Evolution with Migration Paths

## Plain-Language Definition

Contracts must evolve gracefully without breaking existing systems. When interfaces, APIs, or protocols change, provide explicit migration paths, deprecation periods, and versioning so that dependent systems can adapt at their own pace without sudden failures.

## Why This Matters for AI-First Development

When AI agents build and maintain interconnected systems, contract changes ripple through the entire ecosystem. An AI agent updating a service API might inadvertently break dozens of dependent services it doesn't even know about. Without explicit contract evolution patterns, these breaks are silent and catastrophic.

AI-first development amplifies three critical contract evolution challenges:

1. **Automated dependency management**: AI agents need to understand which contract versions are compatible with which consumers. Without explicit versioning and migration paths, agents can't safely update dependencies or regenerate components.

2. **Cross-cutting changes**: When an AI agent needs to update a contract used by multiple services, it must coordinate changes across many repositories. Clear deprecation periods and migration guides allow the agent to stage these updates safely.

3. **Long-lived parallel versions**: AI systems often run multiple versions of services simultaneously (A/B tests, gradual rollouts, experimental branches). Without versioned contracts, these parallel versions conflict and interfere with each other.

Without contract evolution patterns, AI-driven systems become brittle. An agent updating an authentication API breaks all dependent services. A generated contract change cascades into manual emergency fixes. A schema evolution requires coordinating dozens of simultaneous updates across repositories. These failures compound quickly because AI agents often work in parallel across many components simultaneously.

## Implementation Approaches

### 1. **Explicit Contract Versioning**

Version contracts in the contract definition itself, not just in deployment configuration:

```python
# API versioning in URL
@app.get("/api/v1/users/{user_id}")
@app.get("/api/v2/users/{user_id}")

# Schema versioning in protobuf
message UserV1 { ... }
message UserV2 { ... }

# Database migration versioning
-- migrations/001_create_users_table.sql
-- migrations/002_add_email_verification.sql
```

This makes version explicit and discoverable. AI agents can detect version mismatches and route to correct implementations.

### 2. **Deprecation Period with Warnings**

Support old contracts for a defined period while warning consumers:

```python
@app.get("/api/v1/users/{user_id}")
@deprecated(
    sunset_date="2026-01-01",
    migration_guide="https://docs.example.com/migrate-to-v2",
    replacement="/api/v2/users/{user_id}"
)
def get_user_v1(user_id: str):
    """Deprecated: Use v2 endpoint. This endpoint will be removed on 2026-01-01."""
    logger.warning(f"Deprecated v1 endpoint called: {request.url}")
    # Include deprecation header in response
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = "Wed, 01 Jan 2026 00:00:00 GMT"
    return user_data
```

This gives consumers time to migrate while providing clear signals about upcoming changes.

### 3. **Migration Guides as Code**

Provide executable migration examples, not just documentation:

```python
# migration_guides/v1_to_v2_users.py
"""
Migration guide: Users API v1 -> v2

Changes:
- `full_name` field split into `first_name` and `last_name`
- `created` timestamp moved from Unix epoch to ISO 8601
- `roles` field changed from string to array

Example migration:
"""

def migrate_v1_to_v2(v1_user: dict) -> dict:
    """Convert v1 user format to v2 format"""
    full_name = v1_user.get("full_name", "")
    parts = full_name.split(" ", 1)

    return {
        "first_name": parts[0] if parts else "",
        "last_name": parts[1] if len(parts) > 1 else "",
        "created": datetime.fromtimestamp(v1_user["created"]).isoformat(),
        "roles": v1_user["roles"].split(",") if v1_user.get("roles") else []
    }

# Test cases included
assert migrate_v1_to_v2({
    "full_name": "John Doe",
    "created": 1609459200,
    "roles": "admin,user"
}) == {
    "first_name": "John",
    "last_name": "Doe",
    "created": "2021-01-01T00:00:00",
    "roles": ["admin", "user"]
}
```

AI agents can execute these migration guides to understand and perform the transformation.

### 4. **Backward Compatibility Layers**

Implement adapters that translate old contracts to new ones:

```python
class UserServiceV2:
    """New implementation with v2 contract"""
    def get_user(self, user_id: str) -> UserV2:
        # Native v2 implementation
        pass

class UserServiceV1Adapter:
    """Adapter that provides v1 contract using v2 implementation"""
    def __init__(self, v2_service: UserServiceV2):
        self.v2_service = v2_service

    def get_user(self, user_id: str) -> UserV1:
        """V1 endpoint that delegates to v2 and transforms response"""
        v2_user = self.v2_service.get_user(user_id)
        # Transform v2 response to v1 format
        return UserV1(
            full_name=f"{v2_user.first_name} {v2_user.last_name}",
            created=int(v2_user.created.timestamp()),
            roles=",".join(v2_user.roles)
        )
```

This allows old consumers to continue working while you migrate them incrementally.

### 5. **Contract Testing with Version Compatibility Matrix**

Test that new contract versions remain compatible with old consumers:

```python
# tests/contract_compatibility_test.py
import pytest

@pytest.mark.parametrize("client_version,server_version", [
    ("v1", "v1"),  # Same version - must work
    ("v1", "v2"),  # Old client, new server - must work (backward compatible)
    ("v2", "v1"),  # New client, old server - expected to fail
    ("v2", "v2"),  # Same version - must work
])
def test_client_server_compatibility(client_version, server_version):
    client = get_client(client_version)
    server = get_server(server_version)

    response = client.get_user("user123")

    if client_version == "v1" and server_version == "v2":
        # Backward compatibility required
        assert response.full_name == "John Doe"
        assert isinstance(response.created, int)
    elif client_version == "v2" and server_version == "v1":
        # Forward compatibility not guaranteed
        with pytest.raises(IncompatibleVersionError):
            response
```

This ensures backward compatibility is maintained across versions.

### 6. **Staged Rollout with Canary Testing**

Deploy new contract versions gradually with rollback capability:

```python
@app.get("/api/users/{user_id}")
def get_user(user_id: str, version: str = Header(default="v1")):
    """Route to correct version based on client header"""

    # Canary: 5% of traffic to v2, 95% to v1
    if version == "v2" or (version == "v1" and random.random() < 0.05):
        return get_user_v2(user_id)
    else:
        return get_user_v1(user_id)
```

This allows testing new contracts in production with minimal blast radius.

## Good Examples vs Bad Examples

### Example 1: API Field Rename

**Good:**
```python
# Version 1 (original)
class UserResponseV1(BaseModel):
    user_id: str
    email: str
    signup_date: str

# Version 2 (renamed field with backward compatibility)
class UserResponseV2(BaseModel):
    user_id: str
    email: str
    created_at: str  # Renamed from signup_date
    signup_date: str | None = None  # Deprecated but still present

    @classmethod
    def from_user(cls, user: User):
        created_at = user.created_at
        return cls(
            user_id=user.id,
            email=user.email,
            created_at=created_at,
            signup_date=created_at  # Populate deprecated field during transition
        )

@app.get("/api/v2/users/{user_id}")
def get_user_v2(user_id: str) -> UserResponseV2:
    """
    Returns user data with new field names.

    DEPRECATED: `signup_date` field is deprecated, use `created_at` instead.
    The `signup_date` field will be removed in v3 (sunset: 2026-06-01).
    """
    user = db.get_user(user_id)
    return UserResponseV2.from_user(user)
```

**Bad:**
```python
# Version 1 (original)
class UserResponse(BaseModel):
    user_id: str
    email: str
    signup_date: str

# Version 2 (immediate breaking change)
class UserResponse(BaseModel):
    user_id: str
    email: str
    created_at: str  # Renamed from signup_date - old clients break!

@app.get("/api/users/{user_id}")  # Same endpoint, breaking change
def get_user(user_id: str) -> UserResponse:
    user = db.get_user(user_id)
    return UserResponse(
        user_id=user.id,
        email=user.email,
        created_at=user.created_at
    )
    # All existing clients looking for signup_date fail immediately
```

**Why It Matters:** Field renames are common contract changes. Without versioning and transition periods, every rename breaks every consumer. By supporting both field names during a transition period, you allow consumers to migrate at their own pace. AI agents can detect the deprecated field and schedule a migration task instead of causing immediate failures.

### Example 2: Database Schema Evolution

**Good:**
```sql
-- Migration 001: Original schema
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email TEXT NOT NULL,
    full_name TEXT NOT NULL
);

-- Migration 002: Add new fields without removing old ones
ALTER TABLE users ADD COLUMN first_name TEXT;
ALTER TABLE users ADD COLUMN last_name TEXT;

-- Migration 003: Backfill new fields from old field
UPDATE users
SET
    first_name = SPLIT_PART(full_name, ' ', 1),
    last_name = SUBSTRING(full_name FROM POSITION(' ' IN full_name) + 1)
WHERE first_name IS NULL;

-- Migration 004: Make new fields non-null after backfill
ALTER TABLE users ALTER COLUMN first_name SET NOT NULL;
ALTER TABLE users ALTER COLUMN last_name SET NOT NULL;

-- Migration 005: Mark old field as deprecated (keep for transition period)
COMMENT ON COLUMN users.full_name IS
    'DEPRECATED: Use first_name and last_name instead. Will be removed 2026-06-01.';

-- Migration 006: (scheduled for 2026-06-01) Remove deprecated field
-- ALTER TABLE users DROP COLUMN full_name;
```

**Bad:**
```sql
-- Migration 001: Original schema
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email TEXT NOT NULL,
    full_name TEXT NOT NULL
);

-- Migration 002: Breaking change - remove old field immediately
ALTER TABLE users DROP COLUMN full_name;
ALTER TABLE users ADD COLUMN first_name TEXT NOT NULL;
ALTER TABLE users ADD COLUMN last_name TEXT NOT NULL;
-- All queries using full_name break immediately!
-- No migration path for dependent applications!
```

**Why It Matters:** Database schemas are contracts between your application and the database. Breaking changes cause application crashes. By adding new columns before removing old ones, you create a migration window where both old and new application code can run. AI agents can detect the schema version and generate compatible queries for either schema version.

### Example 3: Protocol Buffer Evolution

**Good:**
```protobuf
// Version 1
message UserProfile {
  string user_id = 1;
  string email = 2;
  repeated string roles = 3;  // List of role names
}

// Version 2 - Add new field without removing old one
message UserProfile {
  string user_id = 1;
  string email = 2;
  repeated string roles = 3 [deprecated = true];  // Deprecated but still present
  repeated Role role_objects = 4;  // New structured roles

  message Role {
    string name = 1;
    repeated string permissions = 2;
    int64 granted_at = 3;
  }
}

// Backward compatibility code
def convert_to_v2(v1_profile: UserProfile) -> UserProfile:
    """Convert v1 format to v2, preserving v1 fields for compatibility"""
    v2_profile = UserProfile(
        user_id=v1_profile.user_id,
        email=v1_profile.email,
        roles=v1_profile.roles,  # Keep old format
        role_objects=[
            Role(name=role, permissions=[], granted_at=0)
            for role in v1_profile.roles
        ]  # Add new format
    )
    return v2_profile
```

**Bad:**
```protobuf
// Version 1
message UserProfile {
  string user_id = 1;
  string email = 2;
  repeated string roles = 3;
}

// Version 2 - Breaking change to field type
message UserProfile {
  string user_id = 1;
  string email = 2;
  repeated Role roles = 3;  // Changed from string to Role - breaks v1 consumers!

  message Role {
    string name = 1;
    repeated string permissions = 2;
  }
}
// All v1 clients fail to deserialize this message
```

**Why It Matters:** Protocol buffers enable efficient cross-service communication, but field type changes break binary compatibility. Adding new fields with new tags preserves backward compatibility. Old clients ignore new fields, new clients can handle both. AI agents generating protobuf definitions need to understand these compatibility rules to avoid breaking distributed systems.

### Example 4: REST API Versioning Strategy

**Good:**
```python
from enum import Enum
from datetime import datetime, timedelta

class ApiVersion(str, Enum):
    V1 = "v1"
    V2 = "v2"

# Version registry with sunset dates
VERSION_INFO = {
    ApiVersion.V1: {
        "sunset_date": datetime(2026, 6, 1),
        "migration_guide": "/docs/migrate-v1-to-v2",
        "status": "deprecated"
    },
    ApiVersion.V2: {
        "sunset_date": None,
        "migration_guide": None,
        "status": "current"
    }
}

def add_version_headers(version: ApiVersion, response: Response):
    """Add standard versioning headers to all responses"""
    info = VERSION_INFO[version]
    response.headers["API-Version"] = version

    if info["status"] == "deprecated":
        response.headers["Deprecation"] = "true"
        response.headers["Sunset"] = info["sunset_date"].strftime("%a, %d %b %Y %H:%M:%S GMT")
        response.headers["Link"] = f'<{info["migration_guide"]}>; rel="deprecation"'

@app.get("/api/{version}/users/{user_id}")
async def get_user(version: ApiVersion, user_id: str):
    """Versioned endpoint with automatic deprecation warnings"""

    # Check if version is sunset
    if version in VERSION_INFO:
        info = VERSION_INFO[version]
        if info["sunset_date"] and datetime.now() > info["sunset_date"]:
            raise HTTPException(
                status_code=410,  # Gone
                detail=f"API version {version} is no longer supported. "
                       f"Please migrate to a newer version: {info['migration_guide']}"
            )

    # Route to appropriate implementation
    if version == ApiVersion.V1:
        response = get_user_v1(user_id)
    else:
        response = get_user_v2(user_id)

    add_version_headers(version, response)
    return response
```

**Bad:**
```python
@app.get("/api/users/{user_id}")
async def get_user(user_id: str, use_new_format: bool = False):
    """
    Get user by ID

    Args:
        use_new_format: If true, returns new response format (EXPERIMENTAL)
    """
    user = db.get_user(user_id)

    if use_new_format:
        # New format - experimental, might change
        return {
            "id": user.id,
            "profile": {"email": user.email, "name": user.name},
            "meta": {"created": user.created_at}
        }
    else:
        # Old format - stable
        return {
            "user_id": user.id,
            "email": user.email,
            "name": user.name,
            "created": user.created_at
        }

    # No version numbers, no sunset dates, no migration path
    # Clients don't know when new format becomes default
    # No warning when old format is removed
```

**Why It Matters:** Versioning through URL paths (not query parameters) makes version explicit and discoverable. Sunset dates and deprecation headers give consumers advance warning. Migration guides provide actionable next steps. Without these signals, consumers can't plan migrations. AI agents need this structured information to schedule updates and coordinate changes across dependent services.

### Example 5: Event Schema Evolution

**Good:**
```python
from typing import Literal
from pydantic import BaseModel, Field

class UserCreatedEventV1(BaseModel):
    """Original event schema"""
    event_type: Literal["user.created"] = "user.created"
    schema_version: int = 1
    user_id: str
    email: str
    created_at: str

class UserCreatedEventV2(BaseModel):
    """Evolved event schema with additional context"""
    event_type: Literal["user.created"] = "user.created"
    schema_version: int = 2
    user_id: str
    email: str
    created_at: str
    source: str = Field(description="Registration source: web, mobile, api")
    utm_params: dict = Field(default_factory=dict)

    @classmethod
    def from_v1(cls, v1_event: UserCreatedEventV1):
        """Migration helper: upgrade v1 event to v2"""
        return cls(
            user_id=v1_event.user_id,
            email=v1_event.email,
            created_at=v1_event.created_at,
            source="unknown",  # Default for migrated events
            utm_params={}
        )

class EventConsumer:
    """Event consumer that handles multiple schema versions"""

    def handle_user_created(self, event: dict):
        """Handle user.created event, supporting multiple versions"""
        schema_version = event.get("schema_version", 1)

        if schema_version == 1:
            event_obj = UserCreatedEventV1(**event)
            # Process v1 event with limited data
            self.process_basic_signup(event_obj)

        elif schema_version == 2:
            event_obj = UserCreatedEventV2(**event)
            # Process v2 event with additional context
            self.process_signup_with_attribution(event_obj)

        else:
            # Forward compatibility: log and skip unknown versions
            logger.warning(f"Unknown schema version {schema_version} for user.created event")
            return
```

**Bad:**
```python
class UserCreatedEvent(BaseModel):
    """Event schema - no versioning"""
    event_type: str = "user.created"
    user_id: str
    email: str
    created_at: str
    # Added later without versioning - breaks old consumers!
    source: str
    utm_params: dict

def handle_user_created(event: dict):
    """Event handler - assumes current schema"""
    event_obj = UserCreatedEvent(**event)
    process_signup(event_obj)
    # Fails when receiving old events that don't have source/utm_params
    # Fails when future events add new required fields
```

**Why It Matters:** Event-driven systems often have many consumers running different versions. Without schema versioning, you can't evolve event formats safely. Old consumers crash on new fields, new consumers crash on old events. Including schema_version in every event allows consumers to handle multiple formats gracefully. AI agents generating event consumers can detect supported versions and route to appropriate handlers.

## Related Principles

- **[Principle #08 - Contracts as Explicit Specifications](08-contracts-explicit-specifications.md)** - Foundational principle that contracts must be explicit; this principle extends it to handle evolution over time

- **[Principle #31 - Idempotency by Design](../technology/31-idempotency-by-design.md)** - Idempotent migration operations allow safe retries and rollbacks during contract transitions

- **[Principle #34 - Contract Testing First](../technology/34-contract-testing-first.md)** - Contract tests must evolve with contracts to verify backward compatibility during transitions

- **[Principle #15 - Automated Verification Gates](15-automated-verification-gates.md)** - Verification gates should check contract compatibility before allowing breaking changes to deploy

- **[Principle #40 - Testing in Production Safely](../governance/40-testing-in-production-safely.md)** - New contract versions can be tested in production using canary releases and feature flags

- **[Principle #36 - Self-Documenting Systems](../technology/36-self-documenting-systems.md)** - Contracts should include their version, deprecation status, and migration guides in their documentation

## Common Pitfalls

1. **Breaking Changes Without Version Bump**: Making breaking changes to "current" version instead of creating a new version.
   - Example: Changing field type from string to integer in existing v1 API without creating v2.
   - Impact: All consumers break immediately with no warning or migration path. Emergency rollback required.

2. **No Sunset Dates**: Deprecating old versions without specifying when they'll be removed.
   - Example: Marking v1 as "deprecated" but never communicating when it will stop working.
   - Impact: Consumers don't prioritize migration, leading to emergency migrations when v1 is finally removed.

3. **Migration Guides as Prose Only**: Providing migration instructions as documentation without executable examples.
   - Example: "The full_name field has been split into first_name and last_name. Please update your code accordingly."
   - Impact: AI agents can't parse prose instructions. Human developers waste time interpreting ambiguous guidance.

4. **Testing Only Current Version**: Only testing the latest contract version, ignoring backward compatibility.
   - Example: Integration tests only use v2 API, never verifying v1 still works.
   - Impact: Backward compatibility breaks silently. Old consumers fail in production.

5. **Versioning Infrastructure But Not Contracts**: Using service version numbers (v1.2.3) instead of contract versions (v1, v2).
   - Example: Deploy service version 1.2.3 with breaking API changes but no API version bump.
   - Impact: Semantic versioning of deployments doesn't communicate contract compatibility. Consumers can't determine compatibility.

6. **Removing Old Version Before Sunset Date**: Deleting deprecated version implementations before the announced sunset date.
   - Example: Announcing v1 sunset for June 2026, but removing v1 code in March 2026.
   - Impact: Consumers who planned migrations based on sunset date experience unexpected failures. Trust in deprecation schedules eroded.

7. **No Version Detection in Adapters**: Backward compatibility layers that don't detect consumer version.
   - Example: Always returning v2 format even to v1 clients, relying on "best effort" parsing.
   - Impact: Subtle data loss or corruption as v1 clients misinterpret v2 responses. Hard to debug mismatches.

## Tools & Frameworks

### API Versioning
- **FastAPI**: URL path versioning with automated OpenAPI docs per version
- **Django REST Framework**: Versioning classes for Accept header, URL, and query param versioning
- **API Blueprint**: Contract-first API design with version tracking
- **Swagger/OpenAPI**: Version metadata in API specs with schema evolution support

### Schema Evolution
- **Protobuf**: Field numbering and deprecation markers for backward compatibility
- **Avro**: Schema evolution rules with reader/writer schema compatibility
- **JSON Schema**: Schema versioning with $schema identifier
- **GraphQL**: Field deprecation with @deprecated directive

### Database Migrations
- **Alembic**: Python database migrations with up/down migration paths
- **Flyway**: Version-based database migrations with checksums
- **Liquibase**: Database schema evolution with rollback support
- **Atlas**: Modern database schema migration with safety checks

### Contract Testing
- **Pact**: Consumer-driven contract testing with version compatibility matrix
- **Spring Cloud Contract**: Contract testing for microservices
- **Postman Contract Testing**: API contract validation across versions
- **Prism**: Mock servers that validate against OpenAPI contracts

### Deprecation Management
- **deprecation**: Python library for marking deprecated code with sunset dates
- **OpenAPI Specification**: Sunset and Deprecation HTTP headers
- **GraphQL**: @deprecated directive with reason and replacement fields
- **Stripe API Versioning**: Excellent example of date-based API versioning

## Implementation Checklist

When implementing this principle, ensure:

- [ ] All contracts include explicit version numbers (in URL, header, or schema)
- [ ] Breaking changes always create a new version rather than modifying existing version
- [ ] Deprecated versions include sunset date in responses/documentation
- [ ] Migration guides exist as executable code, not just prose documentation
- [ ] Contract tests verify backward compatibility between versions
- [ ] Old versions continue to work for entire deprecation period (typically 6-12 months)
- [ ] Adapters translate between contract versions where needed
- [ ] Version compatibility matrix is documented and tested
- [ ] Monitoring tracks usage of deprecated versions to plan sunset
- [ ] Sunset dates are communicated at least 6 months in advance
- [ ] New versions are deployed with canary/gradual rollout before forcing migration
- [ ] Version information is included in error messages and logs for debugging

## Metadata

**Category**: Process
**Principle Number**: 18
**Related Patterns**: Adapter Pattern, Strategy Pattern, Facade Pattern, Semantic Versioning, Blue-Green Deployment
**Prerequisites**: Explicit contract specifications (Principle #08), contract testing capability, version control system
**Difficulty**: High
**Impact**: High

---

**Status**: Complete
**Last Updated**: 2025-09-30
**Version**: 1.0