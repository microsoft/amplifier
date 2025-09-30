# Principle #32 - Error Recovery Patterns Built In

## Plain-Language Definition

Error recovery patterns are pre-built mechanisms that automatically detect failures and take corrective action without human intervention. These patterns include retry with backoff, circuit breakers, fallbacks, dead letter queues, graceful degradation, and saga patterns that handle distributed transaction failures.

## Why This Matters for AI-First Development

AI agents operate asynchronously and often across distributed systems where failures are inevitable. Unlike human developers who can manually intervene when something goes wrong, AI agents need automated recovery mechanisms to handle transient failures, network issues, service outages, and resource constraints. Without built-in recovery patterns, AI systems become brittle and require constant human supervision, defeating the purpose of automation.

Error recovery is especially critical for AI-first development because:

1. **AI agents can't manually intervene**: When a human-written script fails, a developer can inspect logs, diagnose the issue, and manually correct it. AI agents executing operations need automatic recovery because they can't pause, investigate, and retry manually. They must have recovery patterns built into the code they generate and execute.

2. **Distributed systems amplify failure modes**: AI agents often orchestrate operations across multiple services, APIs, databases, and infrastructure components. Each dependency introduces failure modes—timeouts, rate limits, temporary outages, resource exhaustion. Without recovery patterns, a single transient failure can cascade and halt entire workflows.

3. **Idempotency enables safe recovery**: Recovery patterns depend on idempotent operations (Principle #31). You can't safely retry operations that aren't idempotent. AI agents need to know which operations can be retried safely and which require compensation logic or saga patterns. This is why error recovery and idempotency are inseparable principles.

Without recovery patterns, AI-generated code becomes fragile. A temporary network glitch fails an entire deployment. A rate-limited API call stops a data pipeline. A database deadlock crashes an application. These failures compound in AI-driven systems where operations happen automatically at scale without human oversight.

## Implementation Approaches

### 1. **Retry with Exponential Backoff**

Automatically retry failed operations with increasing delays between attempts:

```python
async def retry_with_backoff(operation, max_retries=3, base_delay=1.0):
    for attempt in range(max_retries):
        try:
            return await operation()
        except TransientError as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)  # 1s, 2s, 4s
            await asyncio.sleep(delay)
```

**When to use**: For transient failures like network timeouts, temporary service unavailability, or rate limiting. Essential for any operation that depends on external services.

**Success looks like**: Operations succeed after temporary failures without cascading to dependent systems. Logs show successful retries with appropriate delays.

### 2. **Circuit Breaker Pattern**

Stop calling a failing service after repeated failures, giving it time to recover:

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open

    async def call(self, operation):
        if self.state == "open":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "half-open"  # Try one request
            else:
                raise CircuitBreakerOpen("Service is unavailable")

        try:
            result = await operation()
            if self.state == "half-open":
                self.state = "closed"  # Service recovered
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
            raise
```

**When to use**: When calling external services that may become overloaded or fail completely. Prevents overwhelming a struggling service with retries.

**Success looks like**: System continues operating with degraded functionality instead of cascading failures. Failed service gets time to recover without additional load.

### 3. **Fallback Strategies**

Provide alternative behavior when primary operations fail:

```python
async def get_user_data(user_id: str):
    try:
        # Try primary database
        return await primary_db.get_user(user_id)
    except DatabaseError:
        try:
            # Fall back to cache
            return await cache.get_user(user_id)
        except CacheError:
            # Fall back to default data
            return {"id": user_id, "name": "Unknown", "status": "degraded"}
```

**When to use**: For read operations where stale or default data is better than complete failure. Essential for user-facing features that need high availability.

**Success looks like**: Users experience degraded functionality (stale data, limited features) instead of complete failure. System maintains basic operation during outages.

### 4. **Dead Letter Queue (DLQ)**

Capture failed operations for later processing or investigation:

```python
async def process_message_with_dlq(message):
    try:
        await process_message(message)
    except Exception as e:
        # After max retries, send to DLQ
        await dlq.publish({
            "original_message": message,
            "error": str(e),
            "timestamp": time.time(),
            "retry_count": message.retry_count
        })
        # Don't let failure block the queue
        logger.error(f"Message sent to DLQ: {e}")
```

**When to use**: For message queues, event processing, and batch jobs where some items may fail but shouldn't block others. Essential for preserving data that can't be processed immediately.

**Success looks like**: Failed messages are preserved for investigation or reprocessing. System continues processing other messages. Operations team can review and handle failures systematically.

### 5. **Graceful Degradation**

Continue operating with reduced functionality when components fail:

```python
async def generate_product_recommendations(user_id: str):
    try:
        # Try ML-based recommendations
        return await ml_service.get_recommendations(user_id)
    except MLServiceError:
        try:
            # Fall back to collaborative filtering
            return await collaborative_filter(user_id)
        except CollaborativeFilterError:
            # Fall back to popular items
            return await get_popular_items()
```

**When to use**: For features where partial functionality is valuable. Prioritize core operations over advanced features during failures.

**Success looks like**: System provides basic functionality even when advanced features are unavailable. Users don't experience complete outages.

### 6. **Saga Pattern for Distributed Transactions**

Coordinate multi-step operations with compensation logic for rollback:

```python
class OrderSaga:
    async def execute(self, order_data):
        completed_steps = []
        try:
            # Step 1: Reserve inventory
            reservation = await inventory_service.reserve(order_data.items)
            completed_steps.append(("inventory", reservation))

            # Step 2: Charge payment
            payment = await payment_service.charge(order_data.payment_info)
            completed_steps.append(("payment", payment))

            # Step 3: Create shipment
            shipment = await shipping_service.create(order_data.address)
            completed_steps.append(("shipment", shipment))

            return {"status": "success", "order_id": shipment.order_id}

        except Exception as e:
            # Compensation: Undo completed steps in reverse order
            for step_name, step_data in reversed(completed_steps):
                try:
                    if step_name == "shipment":
                        await shipping_service.cancel(step_data.shipment_id)
                    elif step_name == "payment":
                        await payment_service.refund(step_data.payment_id)
                    elif step_name == "inventory":
                        await inventory_service.release(step_data.reservation_id)
                except Exception as comp_error:
                    logger.error(f"Compensation failed for {step_name}: {comp_error}")
            raise OrderFailed(f"Order failed: {e}")
```

**When to use**: For complex workflows spanning multiple services where all-or-nothing semantics are required. Essential for financial transactions, order processing, and resource provisioning.

**Success looks like**: Multi-step operations either complete fully or are rolled back cleanly. No partial state remains after failures.

## Good Examples vs Bad Examples

### Example 1: API Call with Retry

**Good:**
```python
import asyncio
import logging
from typing import TypeVar, Callable

T = TypeVar('T')

async def api_call_with_retry(
    operation: Callable[[], T],
    max_retries: int = 3,
    base_delay: float = 1.0
) -> T:
    """Idempotent API call with exponential backoff"""
    last_exception = None

    for attempt in range(max_retries):
        try:
            return await operation()
        except (TimeoutError, ConnectionError) as e:
            last_exception = e
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)  # 1s, 2s, 4s
                logging.warning(f"Retry {attempt + 1}/{max_retries} after {delay}s: {e}")
                await asyncio.sleep(delay)
            else:
                logging.error(f"All {max_retries} retries exhausted")

    raise last_exception

# Usage
async def get_user_data(user_id: str):
    return await api_call_with_retry(
        lambda: api_client.get(f"/users/{user_id}")
    )
```

**Bad:**
```python
async def get_user_data(user_id: str):
    """No retry logic - fails on any transient error"""
    return await api_client.get(f"/users/{user_id}")
    # Any network glitch, timeout, or temporary service issue fails permanently
```

**Why It Matters:** External API calls fail regularly due to network issues, timeouts, and temporary service problems. Without retry logic, AI agents can't handle these transient failures and require human intervention for issues that would resolve themselves in seconds.

### Example 2: Database Operation with Circuit Breaker

**Good:**
```python
class DatabaseCircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failures = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure = None
        self.state = "closed"

    async def execute_query(self, query_func):
        if self.state == "open":
            if time.time() - self.last_failure > self.recovery_timeout:
                logging.info("Circuit breaker entering half-open state")
                self.state = "half-open"
            else:
                raise CircuitBreakerError("Database circuit breaker is open")

        try:
            result = await query_func()
            if self.state == "half-open":
                logging.info("Circuit breaker closing - database recovered")
                self.state = "closed"
                self.failures = 0
            return result
        except DatabaseError as e:
            self.failures += 1
            self.last_failure = time.time()
            if self.failures >= self.failure_threshold:
                logging.error(f"Circuit breaker opening after {self.failures} failures")
                self.state = "open"
            raise

# Usage
db_breaker = DatabaseCircuitBreaker()

async def get_orders():
    return await db_breaker.execute_query(
        lambda: db.query("SELECT * FROM orders")
    )
```

**Bad:**
```python
async def get_orders():
    """No circuit breaker - keeps hammering failing database"""
    return await db.query("SELECT * FROM orders")
    # If database is struggling, this keeps sending queries
    # Prevents database from recovering, causes cascade failures
```

**Why It Matters:** When a database or service is overloaded or failing, continuing to send requests makes the problem worse. Circuit breakers give failing services time to recover and prevent cascade failures across the system.

### Example 3: Message Processing with Dead Letter Queue

**Good:**
```python
import json
from dataclasses import dataclass
from datetime import datetime

@dataclass
class FailedMessage:
    original_message: dict
    error: str
    timestamp: float
    retry_count: int
    queue_name: str

class MessageProcessor:
    def __init__(self, max_retries=3):
        self.max_retries = max_retries

    async def process_with_dlq(self, message: dict, queue_name: str):
        retry_count = message.get("retry_count", 0)

        try:
            # Attempt to process message
            await self._process_message(message)
            logging.info(f"Message processed successfully: {message.get('id')}")

        except Exception as e:
            retry_count += 1

            if retry_count <= self.max_retries:
                # Retry with backoff
                message["retry_count"] = retry_count
                delay = 2 ** (retry_count - 1)  # 1s, 2s, 4s
                logging.warning(f"Retry {retry_count}/{self.max_retries} in {delay}s: {e}")
                await asyncio.sleep(delay)
                await self.process_with_dlq(message, queue_name)
            else:
                # Send to DLQ after exhausting retries
                failed = FailedMessage(
                    original_message=message,
                    error=str(e),
                    timestamp=time.time(),
                    retry_count=retry_count,
                    queue_name=queue_name
                )
                await self._send_to_dlq(failed)
                logging.error(f"Message sent to DLQ after {retry_count} retries")

    async def _send_to_dlq(self, failed_message: FailedMessage):
        """Persist failed messages for later investigation"""
        await dlq_storage.write(json.dumps(failed_message.__dict__))

    async def _process_message(self, message: dict):
        # Actual message processing logic
        pass
```

**Bad:**
```python
async def process_message(message: dict):
    """No DLQ - failed messages are lost or block the queue"""
    try:
        await _process_message(message)
    except Exception as e:
        logging.error(f"Message processing failed: {e}")
        # Failed message is lost forever
        # Or worse, if we raise, it blocks all subsequent messages
```

**Why It Matters:** In message-driven architectures, some messages will fail to process due to data issues, bugs, or service failures. Without a DLQ, these messages either block the queue or are lost forever, causing data loss and pipeline stalls.

### Example 4: Multi-Service Operation with Saga Pattern

**Good:**
```python
from typing import List, Tuple, Callable
from enum import Enum

class SagaStep:
    def __init__(self, name: str, action: Callable, compensation: Callable):
        self.name = name
        self.action = action
        self.compensation = compensation

class SagaOrchestrator:
    def __init__(self, steps: List[SagaStep]):
        self.steps = steps

    async def execute(self, context: dict) -> dict:
        """Execute saga with automatic compensation on failure"""
        completed: List[Tuple[str, dict]] = []

        try:
            # Execute each step
            for step in self.steps:
                logging.info(f"Executing saga step: {step.name}")
                result = await step.action(context)
                completed.append((step.name, result))
                context[f"{step.name}_result"] = result

            logging.info(f"Saga completed successfully with {len(completed)} steps")
            return {"status": "success", "context": context}

        except Exception as e:
            logging.error(f"Saga failed at step {len(completed)}, compensating...")

            # Compensate in reverse order
            for step_name, result in reversed(completed):
                try:
                    # Find the step to get its compensation function
                    step = next(s for s in self.steps if s.name == step_name)
                    logging.info(f"Compensating: {step_name}")
                    await step.compensation(result)
                except Exception as comp_error:
                    logging.critical(f"Compensation failed for {step_name}: {comp_error}")
                    # Log but continue trying to compensate other steps

            raise SagaFailure(f"Saga failed: {e}") from e

# Usage example
async def book_travel(user_id: str, trip_details: dict):
    saga = SagaOrchestrator([
        SagaStep(
            name="reserve_flight",
            action=lambda ctx: flight_service.reserve(ctx["flight_id"]),
            compensation=lambda result: flight_service.cancel(result["reservation_id"])
        ),
        SagaStep(
            name="reserve_hotel",
            action=lambda ctx: hotel_service.reserve(ctx["hotel_id"]),
            compensation=lambda result: hotel_service.cancel(result["reservation_id"])
        ),
        SagaStep(
            name="charge_payment",
            action=lambda ctx: payment_service.charge(ctx["payment_info"]),
            compensation=lambda result: payment_service.refund(result["transaction_id"])
        ),
    ])

    context = {
        "user_id": user_id,
        "flight_id": trip_details["flight_id"],
        "hotel_id": trip_details["hotel_id"],
        "payment_info": trip_details["payment_info"]
    }

    return await saga.execute(context)
```

**Bad:**
```python
async def book_travel(user_id: str, trip_details: dict):
    """No saga pattern - leaves partial bookings on failure"""
    # Reserve flight
    flight = await flight_service.reserve(trip_details["flight_id"])

    # Reserve hotel
    hotel = await hotel_service.reserve(trip_details["hotel_id"])

    # Charge payment - if this fails, flight and hotel remain reserved!
    payment = await payment_service.charge(trip_details["payment_info"])

    return {"flight": flight, "hotel": hotel, "payment": payment}
    # No compensation logic - failed bookings leave resources reserved
```

**Why It Matters:** Distributed transactions across multiple services can fail at any step. Without saga patterns and compensation logic, failures leave the system in inconsistent states—reserved resources that are never released, charges without corresponding services, or incomplete workflows that require manual cleanup.

### Example 5: Service Call with Graceful Degradation

**Good:**
```python
from enum import Enum

class ServiceQuality(Enum):
    FULL = "full"
    DEGRADED = "degraded"
    MINIMAL = "minimal"

async def get_product_page(product_id: str) -> dict:
    """Load product page with graceful degradation"""
    quality = ServiceQuality.FULL
    response = {"product_id": product_id, "quality": quality}

    # Core data (required)
    try:
        response["product"] = await product_service.get(product_id)
    except Exception as e:
        logging.error(f"Failed to load product: {e}")
        raise  # Can't degrade below core data

    # Recommendations (enhanced feature)
    try:
        response["recommendations"] = await ml_service.get_recommendations(product_id)
    except Exception as e:
        logging.warning(f"ML recommendations failed: {e}")
        quality = ServiceQuality.DEGRADED
        try:
            # Fall back to simpler recommendations
            response["recommendations"] = await get_popular_products()
        except Exception as e2:
            logging.warning(f"Popular products failed: {e2}")
            response["recommendations"] = []

    # Reviews (nice-to-have)
    try:
        response["reviews"] = await review_service.get_reviews(product_id)
    except Exception as e:
        logging.warning(f"Reviews service failed: {e}")
        quality = ServiceQuality.DEGRADED
        response["reviews"] = {"error": "Reviews temporarily unavailable"}

    # Inventory (important but can be stale)
    try:
        response["inventory"] = await inventory_service.get_stock(product_id)
    except Exception as e:
        logging.warning(f"Live inventory failed, using cache: {e}")
        quality = ServiceQuality.DEGRADED
        try:
            response["inventory"] = await cache.get_inventory(product_id)
            response["inventory"]["cached"] = True
        except Exception as e2:
            response["inventory"] = {"available": "unknown"}

    response["quality"] = quality.value
    return response
```

**Bad:**
```python
async def get_product_page(product_id: str) -> dict:
    """No graceful degradation - fails completely if any service is down"""
    # All-or-nothing approach
    product = await product_service.get(product_id)
    recommendations = await ml_service.get_recommendations(product_id)
    reviews = await review_service.get_reviews(product_id)
    inventory = await inventory_service.get_stock(product_id)

    return {
        "product": product,
        "recommendations": recommendations,
        "reviews": reviews,
        "inventory": inventory
    }
    # If ANY service fails, entire page fails to load
```

**Why It Matters:** User-facing features often depend on multiple services. Without graceful degradation, a single service failure causes complete outages. With degradation, users get core functionality even when enhanced features are unavailable, providing better user experience and system resilience.

## Related Principles

- **[Principle #31 - Idempotency by Design](31-idempotency-by-design.md)** - Foundation for error recovery; operations must be idempotent to be safely retried. Without idempotency, retry patterns can cause duplicate actions, corrupted state, and cascading failures.

- **[Principle #33 - Observable Operations](33-observable-operations.md)** - Error recovery requires visibility into what went wrong. Observability enables detecting failures, understanding their causes, and validating that recovery mechanisms worked correctly.

- **[Principle #11 - Continuous Validation with Fast Feedback](../process/11-continuous-validation-fast-feedback.md)** - Fast feedback loops detect failures quickly, enabling rapid recovery. Without fast feedback, recovery patterns trigger too late or on the wrong failures.

- **[Principle #30 - Defense in Depth](30-defense-in-depth.md)** - Error recovery is one layer of defense. Combine it with input validation, resource limits, and security controls to create resilient systems that survive multiple failure modes.

- **[Principle #23 - Protected Self-Healing Kernel](23-protected-self-healing-kernel.md)** - Self-healing systems depend on error recovery patterns to automatically correct failures without human intervention. Recovery patterns are the mechanisms that enable self-healing.

- **[Principle #27 - Disposable Components Everywhere](27-disposable-components.md)** - Disposable components enable simple recovery: destroy failed components and recreate them. Error recovery patterns make this safe by handling state migration and ensuring idempotency.

## Common Pitfalls

1. **Retrying Non-Idempotent Operations**: Retrying operations that aren't idempotent causes duplicate actions, corrupted state, and financial errors.
   - Example: Retrying `charge_credit_card()` without idempotency key charges the customer multiple times.
   - Impact: Duplicate charges, duplicate database records, inconsistent state across systems, customer complaints.

2. **No Maximum Retry Limit**: Retrying indefinitely without a maximum attempt limit causes infinite loops and resource exhaustion.
   - Example: `while True: try: operation() except: continue` never gives up.
   - Impact: Memory leaks, CPU exhaustion, log spam, cascade failures to dependent systems.

3. **Retrying Without Backoff**: Immediate retries without delays overwhelm failing services and prevent recovery.
   - Example: `for i in range(100): try: api_call()` sends 100 requests instantly.
   - Impact: Rate limiting, service overload, IP bans, extended outages as service can't recover.

4. **Ignoring Error Types**: Retrying all errors including permanent failures wastes resources and delays failure detection.
   - Example: Retrying 404 Not Found or 400 Bad Request errors that will never succeed.
   - Impact: Wasted compute, delayed error reporting, false hope in monitoring, resource exhaustion.

5. **No Compensation Logic for Distributed Transactions**: Multi-step operations without compensation leave partial state on failure.
   - Example: Creating user account, sending welcome email, but failing to create billing record leaves incomplete user.
   - Impact: Inconsistent state, orphaned resources, manual cleanup required, data integrity issues.

6. **Circuit Breaker Without Half-Open State**: Circuit breakers that stay open forever never recover when service becomes healthy again.
   - Example: Circuit opens after failures but never attempts to close, permanently disabling functionality.
   - Impact: Extended outages beyond actual service downtime, manual intervention required to restore service.

7. **Dead Letter Queue Without Monitoring**: Failed messages go to DLQ but are never reviewed or reprocessed.
   - Example: DLQ accumulates thousands of failed messages that nobody monitors or handles.
   - Impact: Silent data loss, incomplete workflows, bugs go unnoticed, wasted storage, compliance violations.

## Tools & Frameworks

### Retry Libraries
- **Tenacity (Python)**: Flexible retry library with exponential backoff, custom conditions, async support
- **retry (Python)**: Simple decorator-based retries with configurable backoff strategies
- **Polly (.NET)**: Resilience and transient-fault-handling library with retry, circuit breaker, fallback
- **resilience4j (Java)**: Circuit breaker, retry, rate limiter, bulkhead for Java applications

### Circuit Breaker Implementations
- **Hystrix (Netflix)**: Latency and fault tolerance library with circuit breaker, fallback, metrics
- **resilience4j Circuit Breaker**: Lightweight circuit breaker for Java with configurable thresholds
- **PyBreaker (Python)**: Circuit breaker pattern implementation with state persistence
- **Opossum (Node.js)**: Circuit breaker with event emitter for monitoring state changes

### Message Queue & DLQ Support
- **AWS SQS**: Native dead letter queue support with configurable max receives
- **RabbitMQ**: DLQ support through dead letter exchanges and message TTL
- **Apache Kafka**: Error topics and custom DLQ implementations with retry topics
- **Azure Service Bus**: Built-in DLQ with automatic message forwarding on failure
- **Google Cloud Pub/Sub**: DLQ support with dead letter topics and subscription configuration

### Distributed Transaction & Saga Orchestration
- **Temporal**: Workflow orchestration with built-in compensation and retry logic
- **Netflix Conductor**: Workflow orchestration engine with saga pattern support
- **Camunda**: BPMN-based workflow and saga orchestration platform
- **Eventuate Tram Saga**: Framework for implementing saga pattern in microservices

### Monitoring & Observability
- **Prometheus**: Metrics collection for tracking retry attempts, circuit breaker states, failure rates
- **Grafana**: Visualization for error recovery patterns, DLQ depth, circuit breaker transitions
- **Datadog**: APM with automatic error tracking, retry detection, and failure correlation
- **Sentry**: Error tracking with context preservation for debugging failed recovery attempts

### Testing Tools
- **Chaos Monkey**: Randomly terminates instances to test recovery mechanisms
- **Toxiproxy**: Network failure simulation to test retry and timeout behavior
- **WireMock**: HTTP mock server for testing API retry and error handling
- **pytest-timeout**: Timeout enforcement for testing long-running recovery scenarios

## Implementation Checklist

When implementing this principle, ensure:

- [ ] All external service calls have retry logic with exponential backoff
- [ ] Maximum retry limits prevent infinite loops and resource exhaustion
- [ ] Circuit breakers protect failing services from overload
- [ ] Transient errors (timeouts, connection failures) are distinguished from permanent errors
- [ ] Idempotency guarantees make retry operations safe (reference Principle #31)
- [ ] Dead letter queues capture messages that fail after max retries
- [ ] Graceful degradation provides core functionality when enhanced features fail
- [ ] Saga patterns with compensation logic handle distributed transaction failures
- [ ] Circuit breakers include half-open state to test service recovery
- [ ] Fallback strategies provide alternative behavior for critical read paths
- [ ] DLQ monitoring and alerting notify operations team of accumulating failures
- [ ] Error recovery patterns are tested with chaos engineering and fault injection

## Metadata

**Category**: Technology
**Principle Number**: 32
**Related Patterns**: Retry Logic, Circuit Breaker, Saga Pattern, Dead Letter Queue, Graceful Degradation, Fallback Strategy, Bulkhead Pattern, Timeout Pattern
**Prerequisites**: Idempotency by design (Principle #31), understanding of distributed systems failures, async programming knowledge
**Difficulty**: High
**Impact**: High

---

**Status**: Complete
**Last Updated**: 2025-09-30
**Version**: 1.0