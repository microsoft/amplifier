# Principle #04 - Test-Based Verification Over Code Review

## Plain-Language Definition

Test-based verification means validating software through automated tests that verify behavior, rather than through line-by-line manual code review. Tests answer "does this work correctly?" while code review asks "is this written well?"

## Why This Matters for AI-First Development

When AI agents generate code, traditional line-by-line code review becomes impractical and often counterproductive. AI can generate thousands of lines per hour across multiple files, making manual review impossible to scale. More importantly, AI-generated code may use unfamiliar patterns or idioms that work correctly but look strange to human reviewers, leading to false positives in review.

Test-based verification fundamentally changes the human role from code inspector to requirements architect. Instead of reading every line, humans define what the code should do through tests, then verify that AI-generated code meets those requirements. This approach scales naturally with AI's speed: the same test suite that validates 100 lines also validates 10,000 lines. Tests become the contract between human intent and AI implementation.

The shift to test-based verification provides three critical advantages for AI-first development:

1. **Scalable quality assurance**: Tests validate code at machine speed, matching AI's generation pace. A comprehensive test suite can verify complex systems in seconds, regardless of how the implementation was created.

2. **Clear behavioral contracts**: Tests document what the code should do in executable form. AI agents can read tests to understand requirements and generate code that satisfies them. This creates a virtuous cycle where tests guide generation and verify results.

3. **Safe iteration**: When tests define correctness, AI agents can refactor, optimize, or completely regenerate code without fear. If tests pass, the behavior is preserved. This enables aggressive optimization and experimentation that would be risky with manual verification.

Without test-based verification, AI-first development becomes fragile. An AI agent might generate perfectly functional code that gets rejected because it looks unfamiliar. Or worse, code that looks reasonable might contain subtle bugs that slip through manual review. Tests eliminate both problems: they catch real bugs automatically and ignore stylistic differences that don't affect behavior.

## Implementation Approaches

### 1. **Behavior-Driven Test Suites**

Write tests that describe expected behavior from the user's perspective, not implementation details:

```python
def test_user_can_reset_password():
    """User receives email with reset link that works once"""
    user = create_user(email="test@example.com")

    # Request password reset
    response = client.post("/api/auth/reset-password",
                          json={"email": user.email})
    assert response.status_code == 200

    # Verify email sent with valid token
    email = get_sent_emails()[0]
    assert email.to == user.email
    reset_token = extract_token_from_email(email)

    # Reset password using token
    new_password = "new-secure-password"
    response = client.post(f"/api/auth/reset-password/{reset_token}",
                          json={"password": new_password})
    assert response.status_code == 200

    # Verify new password works
    auth_response = client.post("/api/auth/login",
                               json={"email": user.email,
                                    "password": new_password})
    assert auth_response.status_code == 200

    # Verify token can't be reused
    response = client.post(f"/api/auth/reset-password/{reset_token}",
                          json={"password": "another-password"})
    assert response.status_code == 400
```

These tests verify complete user journeys and remain valid regardless of implementation changes. AI agents can refactor the password reset logic freely as long as tests pass.

### 2. **Property-Based Testing**

Instead of testing specific examples, define properties that should always hold:

```python
from hypothesis import given, strategies as st

@given(st.text(min_size=1), st.text(min_size=1))
def test_string_concatenation_properties(s1: str, s2: str):
    """Test fundamental properties of string joining"""
    result = join_strings(s1, s2)

    # Property 1: Result contains both strings
    assert s1 in result
    assert s2 in result

    # Property 2: Order is preserved
    assert result.index(s1) < result.index(s2)

    # Property 3: Length is at least sum of inputs
    assert len(result) >= len(s1) + len(s2)

@given(st.lists(st.integers()))
def test_sort_properties(items: list[int]):
    """Sorting should have consistent properties regardless of input"""
    sorted_items = sort(items)

    # Property 1: Same length
    assert len(sorted_items) == len(items)

    # Property 2: Same elements
    assert set(sorted_items) == set(items)

    # Property 3: Ordered
    for i in range(len(sorted_items) - 1):
        assert sorted_items[i] <= sorted_items[i + 1]

    # Property 4: Idempotent
    assert sort(sorted_items) == sorted_items
```

Property-based tests explore edge cases automatically and verify behavior across infinite inputs, making them ideal for validating AI-generated code.

### 3. **Contract Testing**

Define explicit contracts between components and verify both sides independently:

```python
# Define the contract
class PaymentServiceContract:
    """Contract that payment service must satisfy"""

    @abstractmethod
    def charge(self, amount: Decimal, customer_id: str,
               idempotency_key: str) -> ChargeResult:
        """
        Charge customer the specified amount.

        Contract:
        - Must be idempotent (same idempotency_key returns same result)
        - Must validate amount > 0
        - Must return ChargeResult with charge_id and status
        - Must raise PaymentError for failures
        """
        pass

# Test the contract implementation
class TestStripePaymentService:
    def test_satisfies_payment_contract(self):
        service = StripePaymentService(api_key=TEST_API_KEY)

        # Idempotency requirement
        key = str(uuid.uuid4())
        result1 = service.charge(Decimal("10.00"), "cust_123", key)
        result2 = service.charge(Decimal("10.00"), "cust_123", key)
        assert result1.charge_id == result2.charge_id

        # Validation requirement
        with pytest.raises(ValueError):
            service.charge(Decimal("0"), "cust_123", str(uuid.uuid4()))

        # Return type requirement
        result = service.charge(Decimal("10.00"), "cust_123",
                               str(uuid.uuid4()))
        assert isinstance(result, ChargeResult)
        assert result.charge_id is not None
        assert result.status in ["succeeded", "failed"]

# Test the consumer side
class TestOrderService:
    def test_handles_payment_contract_correctly(self):
        # Use mock that satisfies contract
        mock_payment = MockPaymentService()
        order_service = OrderService(payment=mock_payment)

        # Verify order service uses idempotency correctly
        order = order_service.place_order(items=[...])
        assert mock_payment.last_call.idempotency_key is not None

        # Verify order service handles failures
        mock_payment.set_next_result(error=PaymentError("Declined"))
        with pytest.raises(OrderFailedError):
            order_service.place_order(items=[...])
```

Contract tests ensure components can be developed and tested independently while maintaining integration guarantees.

### 4. **Coverage-Guided Test Generation**

Use coverage tools to identify untested code paths and generate tests systematically:

```python
# Run coverage analysis
# $ pytest --cov=myapp --cov-report=term-missing

# Coverage report shows:
# myapp/auth.py        85%   Lines 45-52, 89-91 missing

# Generate tests for uncovered paths
def test_password_reset_with_expired_token():
    """Cover lines 45-52: expired token handling"""
    user = create_user()
    token = generate_reset_token(user, expires_in=-3600)  # Expired

    response = client.post(f"/api/auth/reset-password/{token}",
                          json={"password": "new-password"})
    assert response.status_code == 400
    assert "expired" in response.json()["error"].lower()

def test_password_reset_with_invalid_token_format():
    """Cover lines 89-91: malformed token handling"""
    response = client.post("/api/auth/reset-password/not-a-valid-token",
                          json={"password": "new-password"})
    assert response.status_code == 400
    assert "invalid" in response.json()["error"].lower()

# Set coverage thresholds in pytest.ini
# [tool:pytest]
# addopts = --cov=myapp --cov-fail-under=90
```

Coverage-guided testing ensures systematic validation of all code paths, catching edge cases that manual review might miss.

### 5. **Mutation Testing**

Verify that tests actually detect bugs by introducing artificial mutations:

```python
# Original code
def calculate_discount(price: Decimal, coupon_code: str) -> Decimal:
    if coupon_code == "SAVE10":
        return price * Decimal("0.9")
    elif coupon_code == "SAVE20":
        return price * Decimal("0.8")
    else:
        return price

# Mutation testing tool changes code and runs tests:
# Mutation 1: Change 0.9 to 0.8
# Mutation 2: Change 0.8 to 0.9
# Mutation 3: Change "SAVE10" to "SAVE20"
# Mutation 4: Change else return to return Decimal("0")

# Tests must kill these mutations
def test_save10_coupon_applies_10_percent():
    result = calculate_discount(Decimal("100"), "SAVE10")
    assert result == Decimal("90")  # Kills mutation 1

def test_save20_coupon_applies_20_percent():
    result = calculate_discount(Decimal("100"), "SAVE20")
    assert result == Decimal("80")  # Kills mutation 2

def test_invalid_coupon_returns_full_price():
    result = calculate_discount(Decimal("100"), "INVALID")
    assert result == Decimal("100")  # Kills mutation 4

# Run mutation testing
# $ mutmut run
# $ mutmut results
# 4/4 mutations killed - 100% mutation score
```

Mutation testing verifies that your tests would catch real bugs, not just exercise code.

### 6. **Automated Test Generation from Specifications**

Define behavior in structured format and generate tests automatically:

```python
# Specification in YAML or code
api_spec = {
    "endpoint": "/api/users",
    "method": "POST",
    "request_schema": {
        "email": {"type": "string", "format": "email", "required": True},
        "name": {"type": "string", "min_length": 1, "required": True},
        "age": {"type": "integer", "minimum": 18, "required": False}
    },
    "responses": {
        "200": {"schema": "User", "description": "User created"},
        "400": {"schema": "Error", "description": "Invalid input"},
        "409": {"schema": "Error", "description": "Email already exists"}
    },
    "behaviors": [
        "Creates user with valid data",
        "Rejects missing required fields",
        "Rejects invalid email format",
        "Rejects duplicate email",
        "Rejects age under 18"
    ]
}

# Generate tests from specification
def generate_tests_from_spec(spec):
    tests = []

    # Valid case test
    tests.append(f"""
def test_{spec['endpoint'].replace('/', '_')}_creates_user():
    response = client.{spec['method'].lower()}(
        '{spec['endpoint']}',
        json={{"email": "test@example.com", "name": "Test User", "age": 25}}
    )
    assert response.status_code == 200
    assert response.json()['email'] == "test@example.com"
    """)

    # Required field tests
    for field, schema in spec['request_schema'].items():
        if schema.get('required'):
            tests.append(f"""
def test_{spec['endpoint'].replace('/', '_')}_rejects_missing_{field}():
    data = {{"email": "test@example.com", "name": "Test User"}}
    del data['{field}']
    response = client.{spec['method'].lower()}('{spec['endpoint']}', json=data)
    assert response.status_code == 400
    assert '{field}' in response.json()['error'].lower()
            """)

    return tests
```

Specification-driven test generation ensures comprehensive coverage and maintains alignment between documentation and tests.

## Good Examples vs Bad Examples

### Example 1: API Endpoint Validation

**Good:**
```python
def test_create_order_complete_workflow():
    """Test behavior: customer can place order and receive confirmation"""
    # Setup
    customer = create_customer(email="test@example.com")
    product = create_product(name="Widget", price=29.99)

    # Action: Place order
    response = client.post("/api/orders", json={
        "customer_id": customer.id,
        "items": [{"product_id": product.id, "quantity": 2}]
    })

    # Verify behavior
    assert response.status_code == 201
    order = response.json()
    assert order["total"] == 59.98
    assert order["status"] == "pending"

    # Verify side effects
    emails = get_sent_emails(to=customer.email)
    assert len(emails) == 1
    assert order["id"] in emails[0].body

    # Verify persistence
    stored_order = Order.get(order["id"])
    assert stored_order.customer_id == customer.id
    assert len(stored_order.items) == 1
```

**Bad:**
```python
def test_create_order_implementation():
    """Test implementation details instead of behavior"""
    # Tests internal implementation that may change
    order_service = OrderService()

    # Checking private method
    assert hasattr(order_service, '_calculate_subtotal')

    # Checking internal data structures
    assert isinstance(order_service._pending_orders, dict)

    # Checking implementation-specific behavior
    with patch('order_service.validate_inventory') as mock:
        order_service.create_order(...)
        assert mock.called_with(...)  # Tests mock interaction, not behavior

    # Checking variable names
    order = order_service.create_order(...)
    assert hasattr(order, 'confirmation_email_sent')  # Internal flag
```

**Why It Matters:** The good example tests observable behavior that matters to users: can they place orders and receive confirmation? It remains valid even if the implementation completely changes. The bad example tests implementation details that might change without affecting behavior, causing tests to break unnecessarily when code is refactored or regenerated by AI.

### Example 2: Error Handling Validation

**Good:**
```python
def test_payment_failures_handled_gracefully():
    """Test that payment failures don't corrupt order state"""
    customer = create_customer()
    product = create_product(price=100.00)

    # Simulate payment service failure
    with mock_payment_service(will_fail=True):
        response = client.post("/api/orders", json={
            "customer_id": customer.id,
            "items": [{"product_id": product.id, "quantity": 1}]
        })

        # Verify appropriate error response
        assert response.status_code == 400
        assert "payment" in response.json()["error"].lower()

    # Verify no side effects from failed order
    assert Order.count(customer_id=customer.id) == 0
    assert get_sent_emails(to=customer.email) == []
    assert product.inventory_count == product.original_inventory

    # Verify customer can retry successfully
    with mock_payment_service(will_fail=False):
        response = client.post("/api/orders", json={
            "customer_id": customer.id,
            "items": [{"product_id": product.id, "quantity": 1}]
        })
        assert response.status_code == 201
```

**Bad:**
```python
def test_payment_exception_caught():
    """Tests that exceptions are caught, not that behavior is correct"""
    order_service = OrderService()

    # Only tests that exception doesn't propagate
    with pytest.raises(Exception):
        order_service._process_payment(amount=-10)  # Invalid input

    # Doesn't verify state remains consistent
    # Doesn't verify error messages
    # Doesn't verify recovery behavior
```

**Why It Matters:** The good example verifies complete error behavior: appropriate error response, no data corruption, and ability to recover. This ensures AI-generated error handling code actually protects system integrity. The bad example only checks that exceptions don't crash the system, missing critical behavioral requirements around state consistency and user experience.

### Example 3: Integration Testing

**Good:**
```python
def test_user_registration_and_first_login_flow():
    """Test complete user journey from registration to first login"""
    # Register new user
    email = f"test-{uuid.uuid4()}@example.com"
    password = "secure-password-123"

    register_response = client.post("/api/auth/register", json={
        "email": email,
        "password": password,
        "name": "Test User"
    })
    assert register_response.status_code == 201

    # Verify welcome email sent
    emails = get_sent_emails(to=email)
    assert len(emails) == 1
    assert "welcome" in emails[0].subject.lower()

    # Verify can log in immediately
    login_response = client.post("/api/auth/login", json={
        "email": email,
        "password": password
    })
    assert login_response.status_code == 200
    token = login_response.json()["token"]

    # Verify token works for authenticated endpoint
    profile_response = client.get("/api/users/me",
                                  headers={"Authorization": f"Bearer {token}"})
    assert profile_response.status_code == 200
    assert profile_response.json()["email"] == email

    # Verify wrong password fails
    wrong_login = client.post("/api/auth/login", json={
        "email": email,
        "password": "wrong-password"
    })
    assert wrong_login.status_code == 401
```

**Bad:**
```python
def test_user_components_individually():
    """Tests components in isolation without integration"""
    # Test 1: User model saves
    user = User(email="test@example.com")
    user.save()
    assert User.get(user.id) is not None

    # Test 2: Password hashing works
    hashed = hash_password("password")
    assert verify_password("password", hashed)

    # Test 3: Token generation works
    token = generate_token(user_id="123")
    assert decode_token(token)["user_id"] == "123"

    # Test 4: Email sending works
    send_email(to="test@example.com", subject="Test", body="Test")
    assert get_sent_emails()[0].to == "test@example.com"

    # These pass but don't verify they work together!
```

**Why It Matters:** The good example tests end-to-end integration: registration creates a user that can immediately log in and access protected endpoints. This catches integration bugs that unit tests miss, such as token format mismatches between generation and validation. When AI regenerates authentication code, this test verifies the entire flow still works correctly.

### Example 4: Data Validation Testing

**Good:**
```python
from hypothesis import given, strategies as st

@given(
    email=st.one_of(
        st.text(),  # Random strings
        st.just("not-an-email"),
        st.just("missing@domain"),
        st.just("@nodomain.com"),
        st.just("spaces in@email.com"),
    ),
    age=st.integers()
)
def test_user_validation_rejects_invalid_data(email: str, age: int):
    """Property: invalid data should always be rejected"""
    # Assume invalid if email doesn't match pattern or age is negative
    is_valid_email = "@" in email and "." in email.split("@")[1]
    is_valid_age = age >= 18

    response = client.post("/api/users", json={
        "email": email,
        "age": age,
        "name": "Test User"
    })

    if is_valid_email and is_valid_age:
        assert response.status_code in [200, 201]
    else:
        assert response.status_code == 400
        error = response.json()["error"].lower()
        if not is_valid_email:
            assert "email" in error
        if not is_valid_age:
            assert "age" in error

def test_user_validation_specific_cases():
    """Test specific edge cases we care about"""
    test_cases = [
        ("valid@example.com", 18, 201),
        ("no-at-sign.com", 25, 400),
        ("valid@example.com", 17, 400),
        ("valid@example.com", -1, 400),
        ("", 25, 400),
        ("valid@example.com", None, 400),
    ]

    for email, age, expected_status in test_cases:
        response = client.post("/api/users", json={
            "email": email,
            "age": age,
            "name": "Test"
        })
        assert response.status_code == expected_status, \
            f"Failed for email={email}, age={age}"
```

**Bad:**
```python
def test_user_validation_happy_path_only():
    """Only tests that valid input works"""
    response = client.post("/api/users", json={
        "email": "valid@example.com",
        "age": 25,
        "name": "Test User"
    })
    assert response.status_code == 201

    # Doesn't test:
    # - Invalid email formats
    # - Edge cases (age=0, age=17, age=18)
    # - Missing fields
    # - Boundary conditions
    # - SQL injection attempts
    # - XSS attempts
```

**Why It Matters:** The good example systematically tests both valid and invalid inputs using property-based testing and specific edge cases. This ensures AI-generated validation code handles all scenarios correctly. The bad example only verifies the happy path, missing the majority of cases where validation is actually needed.

### Example 5: Performance and Resource Testing

**Good:**
```python
def test_bulk_operations_perform_efficiently():
    """Test that bulk operations scale appropriately"""
    # Create test data
    users = [create_user(email=f"user{i}@example.com")
             for i in range(100)]

    # Measure bulk operation performance
    start = time.time()
    response = client.post("/api/users/bulk-update", json={
        "user_ids": [u.id for u in users],
        "update": {"status": "active"}
    })
    duration = time.time() - start

    # Verify correctness
    assert response.status_code == 200
    assert response.json()["updated_count"] == 100

    # Verify performance (should be near-constant time, not O(n²))
    assert duration < 2.0, f"Bulk update took {duration}s, expected <2s"

    # Verify database efficiency (should use bulk query, not N queries)
    with assert_max_queries(5):  # Setup + bulk select + bulk update + commit + verify
        client.post("/api/users/bulk-update", json={
            "user_ids": [u.id for u in users[:50]],
            "update": {"status": "inactive"}
        })

def test_resource_cleanup_prevents_leaks():
    """Test that operations don't leak resources"""
    initial_connections = get_active_db_connections()
    initial_memory = get_memory_usage()

    # Perform many operations
    for i in range(100):
        response = client.get(f"/api/users/{i}")
        assert response.status_code in [200, 404]

    # Force garbage collection
    import gc
    gc.collect()

    # Verify no resource leaks
    final_connections = get_active_db_connections()
    final_memory = get_memory_usage()

    assert final_connections <= initial_connections + 2, \
        "Database connections leaked"
    assert final_memory < initial_memory * 1.5, \
        f"Memory leaked: {initial_memory} -> {final_memory}"
```

**Bad:**
```python
def test_bulk_operations_work():
    """Only tests functionality, not performance or resource usage"""
    users = [create_user(email=f"user{i}@example.com") for i in range(10)]

    response = client.post("/api/users/bulk-update", json={
        "user_ids": [u.id for u in users],
        "update": {"status": "active"}
    })

    assert response.status_code == 200

    # Doesn't verify:
    # - Performance characteristics
    # - Resource usage
    # - Scalability
    # - Database query efficiency
    # - Memory leaks
```

**Why It Matters:** The good example verifies not just correctness but also performance characteristics and resource usage. When AI regenerates code, these tests ensure the new implementation doesn't introduce performance regressions or resource leaks. The bad example would pass even if the AI generated an O(n²) algorithm or leaked database connections.

## Related Principles

- **[Principle #09 - Living Documentation Through Tests](09-living-documentation-tests.md)** - Tests serve as executable documentation that stays current with code. Test-based verification ensures documentation accuracy by making tests the primary specification.

- **[Principle #02 - Specifications as Contracts](02-specifications-as-contracts.md)** - Tests are executable contracts that verify specifications are met. Test-based verification operationalizes specifications through automated validation.

- **[Principle #11 - Continuous Validation with Fast Feedback](../process/11-continuous-validation-fast-feedback.md)** - Test-based verification enables continuous validation by providing fast, automated feedback on every change.

- **[Principle #07 - Regenerate, Don't Edit](../process/07-regenerate-dont-edit.md)** - Tests enable safe regeneration by verifying behavior is preserved regardless of implementation changes.

- **[Principle #17 - Prompt Versioning and Testing](17-ai-agents-as-first-class-developers.md)** - Test-based verification treats AI agents as developers whose output is validated the same way: through automated tests, not manual review.

- **[Principle #39 - Metrics and Evaluation Everywhere](../governance/39-ruthless-automation.md)** - Test-based verification automates the repetitive task of validating code correctness, replacing manual review with systematic verification.

## Common Pitfalls

1. **Testing Implementation Instead of Behavior**: Tests that verify internal implementation details break when code is refactored or regenerated, even though behavior remains correct.
   - Example: `assert user_service._hash_function == 'bcrypt'` instead of testing that passwords are validated correctly.
   - Impact: Tests become brittle, requiring updates whenever implementation changes. AI regeneration breaks tests unnecessarily.

2. **Insufficient Test Coverage**: Tests that only cover happy paths miss edge cases, error conditions, and boundary scenarios that AI-generated code might handle incorrectly.
   - Example: Testing only valid inputs, not validation, error handling, or edge cases like empty strings, null values, or boundary conditions.
   - Impact: AI-generated code with subtle bugs passes tests, degrading system reliability over time.

3. **No Performance or Resource Tests**: Tests that only verify functional correctness miss performance regressions, resource leaks, and scalability issues.
   - Example: Testing that bulk operations work but not measuring time complexity or resource usage.
   - Impact: AI-generated code might use inefficient algorithms (O(n²) instead of O(n)) or leak resources, causing production failures.

4. **Flaky Tests**: Tests that fail intermittently due to timing issues, race conditions, or external dependencies undermine confidence in test-based verification.
   - Example: Tests that depend on exact timing (`sleep(0.5)`), external APIs, or shared state between tests.
   - Impact: Developers and AI agents ignore test failures, missing real bugs. Regeneration hesitation due to unreliable feedback.

5. **Over-Mocking**: Tests that mock too many dependencies test the mocks rather than real behavior, missing integration issues.
   - Example: Mocking every database call, API request, and file operation, leaving nothing real to test.
   - Impact: Tests pass but real system fails due to integration bugs. AI-generated code might violate contracts that mocks don't enforce.

6. **Missing Property-Based Tests**: Tests that only check specific examples miss entire classes of bugs that property-based testing would catch.
   - Example: Testing `sort([3, 1, 2])` but not testing properties like idempotency (`sort(sort(x)) == sort(x)`).
   - Impact: AI-generated code works for tested examples but fails on edge cases discovered later in production.

7. **No Test Maintenance Strategy**: Tests that accumulate without review become slow, redundant, or obsolete, reducing their value.
   - Example: 1000 slow integration tests that take 30 minutes to run, with 20% redundant and 10% testing deprecated features.
   - Impact: Slow feedback loops discourage running tests. Developers and AI agents skip tests or ignore failures, undermining verification.

## Tools & Frameworks

### Test Frameworks
- **pytest**: Python testing with fixtures, parametrization, and extensive plugin ecosystem. Excellent for behavior-driven tests.
- **Jest**: JavaScript testing with built-in mocking, coverage, and snapshot testing. Fast feedback for frontend code.
- **JUnit 5**: Java testing with parameterized tests, nested test classes, and extension model.
- **RSpec**: Ruby testing with behavior-driven development syntax and rich matchers.

### Property-Based Testing
- **Hypothesis**: Python library for property-based testing that generates test cases automatically.
- **fast-check**: JavaScript property-based testing with shrinking and replay capabilities.
- **QuickCheck**: Original Haskell property-based testing library, ported to many languages.

### Coverage Tools
- **Coverage.py**: Python code coverage measurement with branch coverage and HTML reports.
- **Istanbul/nyc**: JavaScript coverage tools with statement, branch, and function coverage.
- **JaCoCo**: Java code coverage library with integration for major build tools.

### Mutation Testing
- **mutmut**: Python mutation testing that verifies tests actually detect bugs.
- **Stryker**: JavaScript mutation testing framework with multiple language support.
- **PITest**: Java mutation testing with incremental analysis and IDE integration.

### Contract Testing
- **Pact**: Consumer-driven contract testing for microservices with language-agnostic DSL.
- **Spring Cloud Contract**: JVM contract testing with stub generation and verification.
- **Schemathesis**: Property-based testing for OpenAPI/GraphQL APIs.

### Performance Testing
- **pytest-benchmark**: Python benchmarking plugin for pytest with statistical analysis.
- **Locust**: Python load testing tool with distributed testing capabilities.
- **k6**: JavaScript load testing with scripting and cloud execution.

### Test Automation
- **GitHub Actions**: CI/CD with test automation, matrix testing, and artifact management.
- **pytest-xdist**: Parallel test execution for pytest with load balancing.
- **Testcontainers**: Real dependency testing with Docker containers for databases, message queues, etc.

## Implementation Checklist

When implementing this principle, ensure:

- [ ] All user-facing behavior has corresponding automated tests
- [ ] Tests verify observable behavior, not implementation details
- [ ] Test suite includes edge cases, error conditions, and boundary scenarios
- [ ] Property-based tests verify critical algorithms and data structures
- [ ] Integration tests validate end-to-end workflows across components
- [ ] Performance tests measure time complexity and resource usage
- [ ] Contract tests verify APIs and component interfaces
- [ ] Test coverage is measured and meets project thresholds (typically 80%+ for critical code)
- [ ] Mutation testing verifies tests actually detect bugs
- [ ] Tests run automatically on every commit via CI/CD
- [ ] Test execution time is optimized (full suite <10 minutes, smoke tests <2 minutes)
- [ ] Test failures provide clear, actionable error messages

## Metadata

**Category**: People
**Principle Number**: 04
**Related Patterns**: Behavior-Driven Development, Test-Driven Development, Property-Based Testing, Contract Testing, Continuous Integration
**Prerequisites**: Automated test infrastructure, CI/CD pipeline, test framework knowledge
**Difficulty**: Medium
**Impact**: High

---

**Status**: Complete
**Last Updated**: 2025-09-30
**Version**: 1.0