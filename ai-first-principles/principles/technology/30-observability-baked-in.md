# Principle #30 - Observability Baked In

## Plain-Language Definition

Observability means building systems that explain their own behavior through logs, metrics, and traces. Baking in observability means designing instrumentation from the start, not adding it as an afterthought when things go wrong.

## Why This Matters for AI-First Development

When AI agents build and modify systems, observability becomes critical for understanding what's happening. Unlike human developers who can add print statements and debuggers interactively, AI agents need comprehensive observability built into the system to diagnose issues, validate behavior, and make informed decisions about changes.

AI-driven systems compound the observability challenge in three ways:

1. **Black-box behavior**: AI agents generate code that humans may not fully review. Without built-in observability, it's impossible to know what the generated code is actually doing in production. Logs, metrics, and traces provide a window into AI-generated behavior.

2. **Emergent complexity**: AI systems often have emergent properties that weren't explicitly programmed. Observability helps detect when these emergent behaviors are beneficial versus problematic. Without it, you're flying blind.

3. **Continuous evolution**: AI agents continuously modify systems. Observability provides the feedback loop needed to validate that changes improved (or didn't break) the system. It enables AI agents to self-correct by observing the impact of their changes.

Without baked-in observability, AI-first development becomes a game of whack-a-mole. You discover problems through user reports rather than system telemetry. Debugging requires adding instrumentation after the fact, which is slower and less effective. AI agents can't learn from production behavior because the data simply isn't captured.

## Implementation Approaches

### 1. **Structured Logging with Context**

Every log statement should be machine-parseable and include contextual information:

```python
import structlog

logger = structlog.get_logger()

def process_user_request(user_id: str, request_type: str):
    logger.info(
        "processing_request",
        user_id=user_id,
        request_type=request_type,
        timestamp=time.time()
    )
```

Structured logs can be queried, filtered, and analyzed programmatically. Include correlation IDs, user context, operation type, and timing information in every log line.

### 2. **Metrics for System Health**

Expose quantitative metrics that track system health and business outcomes:

```python
from prometheus_client import Counter, Histogram

request_count = Counter('requests_total', 'Total requests', ['endpoint', 'status'])
request_duration = Histogram('request_duration_seconds', 'Request duration', ['endpoint'])

@request_duration.time()
def handle_request(endpoint: str):
    result = process_request(endpoint)
    request_count.labels(endpoint=endpoint, status='success').inc()
    return result
```

Track request rates, error rates, latency percentiles, resource utilization, and business metrics. Metrics provide aggregate views that logs can't efficiently offer.

### 3. **Distributed Tracing**

For systems with multiple services, use distributed tracing to follow requests across boundaries:

```python
from opentelemetry import trace
from opentelemetry.instrumentation.requests import RequestsInstrumentor

tracer = trace.get_tracer(__name__)

def call_downstream_service(user_id: str):
    with tracer.start_as_current_span("downstream_call") as span:
        span.set_attribute("user_id", user_id)
        response = requests.get(f"http://service/api/{user_id}")
        span.set_attribute("status_code", response.status_code)
        return response
```

Tracing shows how requests flow through services, where time is spent, and which service caused failures.

### 4. **Correlation IDs Throughout**

Generate a unique correlation ID at system entry and propagate it through all operations:

```python
import uuid
from contextvars import ContextVar

correlation_id: ContextVar[str] = ContextVar('correlation_id')

def handle_api_request(request):
    # Generate or extract correlation ID
    corr_id = request.headers.get('X-Correlation-ID', str(uuid.uuid4()))
    correlation_id.set(corr_id)

    logger.info("request_received", correlation_id=corr_id)
    result = process_request()
    logger.info("request_completed", correlation_id=corr_id)
    return result
```

Correlation IDs let you trace a single request across all logs, metrics, and traces, making debugging dramatically easier.

### 5. **Health Checks and Readiness Probes**

Expose endpoints that report system health:

```python
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "version": "1.2.3",
        "uptime_seconds": get_uptime(),
        "dependencies": {
            "database": check_database_connection(),
            "cache": check_cache_connection(),
            "external_api": check_external_api()
        }
    }
```

Health checks enable automated monitoring and alerting. They provide instant visibility into system state.

### 6. **Dashboard-First Development**

Build dashboards before writing code. Decide what you want to observe, then instrument the code to provide that visibility:

1. Design dashboard showing key metrics (request rate, error rate, latency, business KPIs)
2. Implement metrics collection to populate the dashboard
3. Write the actual business logic
4. Validate dashboard reflects expected behavior

This ensures observability is built in, not bolted on.

## Good Examples vs Bad Examples

### Example 1: API Request Handling

**Good:**
```python
import structlog
from opentelemetry import trace
from prometheus_client import Counter, Histogram

logger = structlog.get_logger()
tracer = trace.get_tracer(__name__)

request_counter = Counter('api_requests_total', 'Total API requests', ['endpoint', 'status'])
request_duration = Histogram('api_request_duration_seconds', 'API request duration', ['endpoint'])

@app.post("/api/users")
def create_user(user_data: dict, correlation_id: str = Header(None)):
    # Set correlation ID
    if not correlation_id:
        correlation_id = str(uuid.uuid4())

    # Start trace
    with tracer.start_as_current_span("create_user") as span:
        span.set_attribute("correlation_id", correlation_id)

        # Log structured data
        logger.info(
            "user_creation_started",
            correlation_id=correlation_id,
            email=user_data.get('email'),
            timestamp=time.time()
        )

        # Time the operation
        with request_duration.labels(endpoint='create_user').time():
            try:
                user = User.create(**user_data)
                request_counter.labels(endpoint='create_user', status='success').inc()

                logger.info(
                    "user_creation_completed",
                    correlation_id=correlation_id,
                    user_id=user.id,
                    duration_ms=(time.time() - start) * 1000
                )

                return {"user_id": user.id}

            except Exception as e:
                request_counter.labels(endpoint='create_user', status='error').inc()
                span.set_attribute("error", True)
                span.set_attribute("error_message", str(e))

                logger.error(
                    "user_creation_failed",
                    correlation_id=correlation_id,
                    error=str(e),
                    error_type=type(e).__name__
                )
                raise
```

**Bad:**
```python
@app.post("/api/users")
def create_user(user_data: dict):
    # No logging, no metrics, no tracing
    user = User.create(**user_data)
    return {"user_id": user.id}
    # When this fails in production, you have no idea why
```

**Why It Matters:** The good example provides complete visibility: structured logs show what happened and when, metrics track aggregate behavior, traces show request flow, and correlation IDs tie everything together. When something goes wrong, you have all the data needed to diagnose and fix it. The bad example provides nothing—when it fails, you're guessing.

### Example 2: Database Query Performance

**Good:**
```python
import structlog
from prometheus_client import Histogram

logger = structlog.get_logger()
query_duration = Histogram(
    'database_query_duration_seconds',
    'Database query duration',
    ['query_type', 'table']
)

def get_user_by_email(email: str) -> User:
    with query_duration.labels(query_type='select', table='users').time():
        logger.debug(
            "database_query_started",
            query_type="select",
            table="users",
            filter="email",
            correlation_id=get_correlation_id()
        )

        start = time.time()
        user = db.users.find_one({"email": email})
        duration_ms = (time.time() - start) * 1000

        logger.debug(
            "database_query_completed",
            query_type="select",
            table="users",
            found=user is not None,
            duration_ms=duration_ms,
            correlation_id=get_correlation_id()
        )

        if duration_ms > 100:  # Log slow queries
            logger.warning(
                "slow_database_query",
                query_type="select",
                table="users",
                duration_ms=duration_ms,
                threshold_ms=100
            )

        return user
```

**Bad:**
```python
def get_user_by_email(email: str) -> User:
    user = db.users.find_one({"email": email})
    return user
    # No visibility into query performance or failures
```

**Why It Matters:** Database queries are often the performance bottleneck. The good example tracks query duration, logs slow queries, and provides data to optimize performance. The bad example hides performance problems until users complain. You can't optimize what you can't measure.

### Example 3: Background Job Processing

**Good:**
```python
import structlog
from prometheus_client import Counter, Gauge, Histogram

logger = structlog.get_logger()

job_counter = Counter('background_jobs_total', 'Total background jobs', ['job_type', 'status'])
job_duration = Histogram('background_job_duration_seconds', 'Job duration', ['job_type'])
job_queue_size = Gauge('background_job_queue_size', 'Jobs waiting in queue', ['job_type'])

def process_email_job(job_id: str, recipient: str, template: str):
    correlation_id = str(uuid.uuid4())

    logger.info(
        "background_job_started",
        job_id=job_id,
        job_type="send_email",
        correlation_id=correlation_id,
        recipient=recipient,
        template=template
    )

    with job_duration.labels(job_type='send_email').time():
        try:
            send_email(recipient, template)

            job_counter.labels(job_type='send_email', status='success').inc()

            logger.info(
                "background_job_completed",
                job_id=job_id,
                job_type="send_email",
                correlation_id=correlation_id,
                recipient=recipient
            )

        except Exception as e:
            job_counter.labels(job_type='send_email', status='failed').inc()

            logger.error(
                "background_job_failed",
                job_id=job_id,
                job_type="send_email",
                correlation_id=correlation_id,
                error=str(e),
                error_type=type(e).__name__,
                recipient=recipient
            )
            raise

        finally:
            # Update queue size metric
            remaining_jobs = get_queue_size('send_email')
            job_queue_size.labels(job_type='send_email').set(remaining_jobs)
```

**Bad:**
```python
def process_email_job(job_id: str, recipient: str, template: str):
    send_email(recipient, template)
    # No visibility into job success, duration, or queue health
```

**Why It Matters:** Background jobs often fail silently. The good example provides visibility into job execution, duration, success/failure rates, and queue depth. This enables monitoring and alerting. The bad example hides failures—users don't get emails, and you don't know why.

### Example 4: External API Integration

**Good:**
```python
import structlog
from prometheus_client import Counter, Histogram
from opentelemetry import trace

logger = structlog.get_logger()
tracer = trace.get_tracer(__name__)

api_call_counter = Counter(
    'external_api_calls_total',
    'External API calls',
    ['service', 'endpoint', 'status_code']
)
api_call_duration = Histogram(
    'external_api_call_duration_seconds',
    'External API call duration',
    ['service', 'endpoint']
)

def call_payment_api(amount: float, currency: str) -> dict:
    service = "payment_gateway"
    endpoint = "charge"
    correlation_id = get_correlation_id()

    with tracer.start_as_current_span("external_api_call") as span:
        span.set_attribute("service", service)
        span.set_attribute("endpoint", endpoint)
        span.set_attribute("correlation_id", correlation_id)

        logger.info(
            "external_api_call_started",
            service=service,
            endpoint=endpoint,
            correlation_id=correlation_id,
            amount=amount,
            currency=currency
        )

        with api_call_duration.labels(service=service, endpoint=endpoint).time():
            try:
                response = requests.post(
                    "https://api.payment.com/charge",
                    json={"amount": amount, "currency": currency},
                    headers={"X-Correlation-ID": correlation_id},
                    timeout=5.0
                )

                api_call_counter.labels(
                    service=service,
                    endpoint=endpoint,
                    status_code=response.status_code
                ).inc()

                span.set_attribute("status_code", response.status_code)

                logger.info(
                    "external_api_call_completed",
                    service=service,
                    endpoint=endpoint,
                    correlation_id=correlation_id,
                    status_code=response.status_code,
                    response_time_ms=response.elapsed.total_seconds() * 1000
                )

                return response.json()

            except requests.Timeout as e:
                api_call_counter.labels(
                    service=service,
                    endpoint=endpoint,
                    status_code='timeout'
                ).inc()

                span.set_attribute("error", True)
                span.set_attribute("error_type", "timeout")

                logger.error(
                    "external_api_call_timeout",
                    service=service,
                    endpoint=endpoint,
                    correlation_id=correlation_id,
                    timeout_seconds=5.0
                )
                raise

            except Exception as e:
                api_call_counter.labels(
                    service=service,
                    endpoint=endpoint,
                    status_code='error'
                ).inc()

                span.set_attribute("error", True)
                span.set_attribute("error_message", str(e))

                logger.error(
                    "external_api_call_failed",
                    service=service,
                    endpoint=endpoint,
                    correlation_id=correlation_id,
                    error=str(e),
                    error_type=type(e).__name__
                )
                raise
```

**Bad:**
```python
def call_payment_api(amount: float, currency: str) -> dict:
    response = requests.post(
        "https://api.payment.com/charge",
        json={"amount": amount, "currency": currency}
    )
    return response.json()
    # No visibility into API latency, failures, or status codes
```

**Why It Matters:** External APIs fail frequently and unpredictably. The good example tracks success rates, response times, status codes, and errors. This enables alerting when the external API degrades. The bad example leaves you blind to external dependencies—you discover API problems only when customers complain.

### Example 5: System Startup and Health

**Good:**
```python
import structlog
from prometheus_client import Info, Gauge

logger = structlog.get_logger()

app_info = Info('application', 'Application information')
app_health = Gauge('application_healthy', 'Application health status')

def initialize_application():
    start_time = time.time()

    # Record application metadata
    app_info.info({
        'version': '1.2.3',
        'environment': 'production',
        'build_date': '2025-09-30',
        'commit_sha': 'abc123'
    })

    logger.info(
        "application_startup_started",
        version='1.2.3',
        environment='production'
    )

    # Initialize components with observability
    components = {
        'database': initialize_database,
        'cache': initialize_cache,
        'message_queue': initialize_queue
    }

    for component_name, init_func in components.items():
        logger.info(f"{component_name}_initialization_started")

        try:
            init_func()
            logger.info(
                f"{component_name}_initialization_completed",
                component=component_name
            )
        except Exception as e:
            app_health.set(0)  # Mark unhealthy
            logger.error(
                f"{component_name}_initialization_failed",
                component=component_name,
                error=str(e),
                error_type=type(e).__name__
            )
            raise

    startup_duration = time.time() - start_time
    app_health.set(1)  # Mark healthy

    logger.info(
        "application_startup_completed",
        startup_duration_seconds=startup_duration,
        components_initialized=len(components)
    )

@app.get("/health")
def health_check():
    checks = {
        "database": check_database_connection(),
        "cache": check_cache_connection(),
        "queue": check_queue_connection()
    }

    all_healthy = all(checks.values())
    status = "healthy" if all_healthy else "degraded"

    logger.debug(
        "health_check_performed",
        status=status,
        checks=checks
    )

    return {
        "status": status,
        "checks": checks,
        "version": "1.2.3",
        "uptime_seconds": time.time() - startup_time
    }
```

**Bad:**
```python
def initialize_application():
    initialize_database()
    initialize_cache()
    initialize_queue()
    # No logging of startup sequence or component initialization

@app.get("/health")
def health_check():
    return {"status": "ok"}
    # No actual health checking of dependencies
```

**Why It Matters:** Application startup often fails in production due to missing dependencies or configuration issues. The good example logs each initialization step, records application metadata, and provides real health checks. This enables rapid diagnosis of startup failures and dependency issues. The bad example provides no visibility—when startup fails, you're debugging blind.

## Related Principles

- **[Principle #11 - Continuous Validation with Fast Feedback](../process/11-continuous-validation-fast-feedback.md)** - Observability provides the feedback data that enables continuous validation; you can't validate what you can't observe

- **[Principle #39 - Progressive Enhancement](39-progressive-enhancement.md)** - Observability enables progressive enhancement by providing data on what's actually being used and where improvements are needed

- **[Principle #32 - Error Recovery Patterns Built In](32-error-recovery-patterns.md)** - Error recovery depends on observability to detect failures, understand their context, and validate recovery success

- **[Principle #23 - Protected Self-Healing Kernel](23-protected-self-healing-kernel.md)** - Self-healing systems require observability to detect issues, trigger healing actions, and verify healing worked

- **[Principle #12 - Specification-Driven Iteration](../process/12-specification-driven-iteration.md)** - Observability data informs specification refinement by showing actual system behavior versus intended behavior

- **[Principle #19 - Context-Aware Communication](../people/19-context-aware-communication.md)** - Observability provides the context needed for effective communication about system behavior and issues

## Common Pitfalls

1. **Adding Observability After Problems Occur**: Waiting to add logging/metrics until something breaks means you don't have data about the failure. Observability must be built in from the start.
   - Example: Service crashes in production but has no logs, making root cause analysis impossible.
   - Impact: Extended outages, inability to diagnose issues, repeated failures of the same problem.

2. **Logging Sensitive Data**: Including passwords, tokens, credit card numbers, or PII in logs creates security vulnerabilities and compliance violations.
   - Example: `logger.info(f"User logged in: {username}, password: {password}")`
   - Impact: Data breaches, compliance violations (GDPR, PCI-DSS), security incidents.

3. **Too Much Logging**: Logging every single operation creates noise that makes it impossible to find useful information. It also impacts performance.
   - Example: Logging every database query in a high-traffic system generates millions of log lines per minute.
   - Impact: Logs become unusable, storage costs explode, log ingestion rate limits hit, performance degradation.

4. **Unstructured Logs**: Human-readable log messages are hard to query and analyze. Use structured logging with machine-parseable fields.
   - Example: `print(f"User {user_id} failed to login at {timestamp}")` instead of structured logging.
   - Impact: Can't efficiently search, filter, or analyze logs; manual log review is slow and error-prone.

5. **Missing Correlation IDs**: Without correlation IDs, you can't trace a single request across multiple services or components.
   - Example: Logs from different services reference the same user but no way to correlate them to a single request.
   - Impact: Impossible to debug distributed systems, can't understand request flow across services.

6. **Metrics Without Dimensions**: Recording aggregate metrics without dimensions (labels) makes them less useful for debugging.
   - Example: Total request count without breaking down by endpoint, status code, or user type.
   - Impact: Can see that errors are happening but not where or for whom; can't identify specific problem areas.

7. **Ignoring Cardinality**: Using high-cardinality values (like user IDs) as metric labels causes metrics explosion and system overload.
   - Example: `request_count.labels(user_id=user_id).inc()` creates a metric per user.
   - Impact: Metrics storage explodes, query performance degrades, monitoring system becomes unusable.

## Tools & Frameworks

### Structured Logging
- **structlog (Python)**: Best-in-class structured logging with rich context and processors for formatting
- **Zap (Go)**: High-performance structured logging with zero allocations
- **winston (Node.js)**: Feature-rich logging library with multiple transports and formats
- **Loguru (Python)**: Simpler structured logging alternative with great defaults

### Metrics and Monitoring
- **Prometheus**: Industry-standard metrics collection and alerting with pull-based model
- **Grafana**: Visualization and dashboarding for metrics from multiple sources
- **StatsD**: Push-based metrics aggregation for simple use cases
- **DataDog**: Commercial all-in-one observability platform with metrics, logs, and traces

### Distributed Tracing
- **OpenTelemetry**: Vendor-neutral standard for traces, metrics, and logs across languages
- **Jaeger**: Open-source distributed tracing platform from Uber
- **Zipkin**: Distributed tracing system from Twitter with simple setup
- **Tempo**: Grafana's distributed tracing backend with low cost

### Log Aggregation
- **Elasticsearch + Kibana (ELK)**: Full-featured log aggregation, search, and visualization
- **Loki**: Grafana's log aggregation designed to be cost-effective and simple
- **Splunk**: Enterprise log management with advanced analytics
- **CloudWatch Logs**: AWS-native log aggregation for cloud workloads

### Application Performance Monitoring (APM)
- **New Relic**: Full-stack APM with code-level visibility and AI-powered insights
- **Datadog APM**: Distributed tracing integrated with infrastructure monitoring
- **Elastic APM**: Application performance monitoring built on Elasticsearch
- **Sentry**: Error tracking and performance monitoring focused on developer experience

### Testing Observability
- **pytest + caplog**: Test logging output in Python tests
- **pprof**: Go profiling tool for CPU and memory analysis
- **py-spy**: Python sampling profiler to understand production performance
- **OpenTelemetry test instrumentation**: Verify tracing in integration tests

## Implementation Checklist

When implementing this principle, ensure:

- [ ] All API endpoints emit structured logs with correlation IDs
- [ ] Key metrics (request rate, error rate, latency) are tracked for all endpoints
- [ ] Database queries are instrumented with duration metrics
- [ ] External API calls include timeout tracking and error rate metrics
- [ ] Background jobs log start, completion, failure, and duration
- [ ] Health check endpoints verify all critical dependencies
- [ ] Correlation IDs propagate across all service boundaries
- [ ] Sensitive data (passwords, tokens, PII) is never logged
- [ ] Log levels are appropriate (DEBUG for verbose, INFO for key events, ERROR for failures)
- [ ] Dashboards exist for all critical system metrics before code is deployed
- [ ] Alerts are configured for error rates, latency, and health check failures
- [ ] Distributed traces connect all services involved in a request

## Metadata

**Category**: Technology
**Principle Number**: 30
**Related Patterns**: Circuit Breaker, Health Check Pattern, Correlation ID Pattern, Structured Logging, Metrics-Driven Development
**Prerequisites**: Understanding of logging frameworks, metrics systems, distributed tracing concepts
**Difficulty**: Medium
**Impact**: High

---

**Status**: Complete
**Last Updated**: 2025-09-30
**Version**: 1.0