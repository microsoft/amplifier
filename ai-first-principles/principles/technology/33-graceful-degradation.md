# Principle #33 - Graceful Degradation by Design

## Plain-Language Definition

Graceful degradation means building systems that continue to provide reduced functionality when components fail, rather than crashing completely. When services are unavailable or resources are exhausted, the system falls back to simpler behavior that still serves users.

## Why This Matters for AI-First Development

AI agents building and maintaining systems face a fundamental challenge: distributed systems have many failure modes, and agents need to handle failures automatically without human intervention. A system that fails catastrophically when one component goes down forces the AI agent into emergency response mode, potentially making poor decisions under pressure.

Graceful degradation provides three critical capabilities for AI-driven development:

1. **Autonomous recovery**: AI agents can detect failures and automatically activate fallback modes without waiting for human guidance. This is essential because AI systems often operate across multiple services, APIs, and infrastructure components that can fail independently.

2. **Partial functionality over complete failure**: When an AI agent encounters a failed component, it can choose to provide reduced service rather than failing the entire operation. This matches how humans naturally handle problems - we work around obstacles rather than giving up entirely.

3. **Safe experimentation boundaries**: Graceful degradation creates clear boundaries for what happens when experiments fail. AI agents can try new approaches knowing that failures will degrade gracefully rather than cascade catastrophically.

Without graceful degradation, AI-first systems become brittle. An unavailable LLM API causes the entire application to crash. A slow database query times out and breaks unrelated features. A missing configuration file prevents startup. These cascading failures make systems unpredictable and force AI agents to be overly conservative, limiting their ability to innovate and adapt.

## Implementation Approaches

### 1. **Fallback Strategies with Priority Chains**

Implement multiple fallback options ordered by preference:

```python
async def get_completion(prompt: str) -> str:
    """Try primary LLM, fall back to secondary, finally use cached response"""
    try:
        return await primary_llm.complete(prompt)
    except APIError:
        logger.warning("Primary LLM failed, trying secondary")
        try:
            return await secondary_llm.complete(prompt)
        except APIError:
            logger.warning("Secondary LLM failed, using cached response")
            return get_cached_response(prompt)
```

Success looks like: Users receive answers even when primary services fail, with minimal latency increase.

### 2. **Partial Functionality with Feature Toggles**

Design features to work independently so failures don't cascade:

```python
class UserDashboard:
    def render(self) -> dict:
        """Build dashboard with independent sections"""
        data = {"sections": []}

        # Each section fails independently
        try:
            data["sections"].append(self.get_recent_activity())
        except ServiceError:
            data["sections"].append({"type": "activity", "status": "unavailable"})

        try:
            data["sections"].append(self.get_recommendations())
        except ServiceError:
            data["sections"].append({"type": "recommendations", "status": "unavailable"})

        return data
```

Success looks like: Dashboard loads with some sections even when others fail.

### 3. **Reduced Quality Modes**

Provide faster, simpler responses when full quality isn't available:

```python
def search_products(query: str, timeout: float = 5.0) -> list:
    """Search with quality degradation based on time available"""
    try:
        # Try comprehensive search with ML ranking
        return await search_with_ml_ranking(query, timeout=timeout)
    except TimeoutError:
        logger.info("ML ranking timed out, using simple search")
        # Fall back to keyword search without ranking
        return simple_keyword_search(query, timeout=1.0)
    except ServiceError:
        # Last resort: cached popular results
        return get_popular_products_cached()
```

Success looks like: Users get results quickly even when sophisticated processing fails.

### 4. **Cached Responses with Staleness Indicators**

Serve stale data when fresh data is unavailable:

```python
@dataclass
class CachedResult:
    data: Any
    cached_at: datetime
    max_age: timedelta

def get_user_stats(user_id: str) -> CachedResult:
    """Return fresh stats or cached with age indicator"""
    try:
        stats = calculate_user_stats(user_id, timeout=2.0)
        return CachedResult(data=stats, cached_at=now(), max_age=timedelta(0))
    except (TimeoutError, ServiceError):
        cached = get_from_cache(f"user_stats:{user_id}")
        if cached:
            age = now() - cached.timestamp
            return CachedResult(data=cached.data, cached_at=cached.timestamp, max_age=age)
        raise ValueError("No cached data available")
```

Success looks like: Users see data with clear staleness indicators rather than errors.

### 5. **Circuit Breakers with Automatic Degradation**

Detect failing services and automatically switch to degraded mode:

```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5):
        self.failure_count = 0
        self.state = "closed"  # closed, open, half-open
        self.threshold = failure_threshold

    def call(self, func: callable, fallback: callable):
        if self.state == "open":
            logger.info("Circuit open, using fallback")
            return fallback()

        try:
            result = func()
            self.failure_count = 0  # Reset on success
            return result
        except Exception as e:
            self.failure_count += 1
            if self.failure_count >= self.threshold:
                self.state = "open"
                logger.warning(f"Circuit opened after {self.failure_count} failures")
            return fallback()
```

Success looks like: Failing services are automatically bypassed until they recover.

### 6. **Progressive Enhancement Architecture**

Build core functionality first, add enhancements that can fail independently:

```python
class DocumentProcessor:
    def process(self, doc: Document) -> ProcessedDocument:
        """Core processing always succeeds, enhancements degrade gracefully"""
        # Core: always works
        result = ProcessedDocument(
            text=doc.content,
            word_count=len(doc.content.split())
        )

        # Enhancement 1: AI summarization (can fail)
        try:
            result.summary = self.ai_summarize(doc.content)
        except ServiceError:
            logger.info("AI summarization unavailable, skipping")
            result.summary = None

        # Enhancement 2: Entity extraction (can fail)
        try:
            result.entities = self.extract_entities(doc.content)
        except ServiceError:
            logger.info("Entity extraction unavailable, skipping")
            result.entities = []

        return result
```

Success looks like: Core functionality always works, advanced features add value when available.

## Good Examples vs Bad Examples

### Example 1: LLM API Failure Handling

**Good:**
```python
class LLMClient:
    def __init__(self):
        self.circuit_breaker = CircuitBreaker(failure_threshold=3)
        self.cache = ResponseCache(max_age=timedelta(hours=1))

    async def generate(self, prompt: str) -> LLMResponse:
        """Degrade gracefully through multiple fallback levels"""
        # Try cached response first for identical prompts
        cached = self.cache.get(prompt)
        if cached and cached.age < timedelta(minutes=5):
            return LLMResponse(text=cached.text, source="cache-fresh")

        # Try primary LLM with circuit breaker
        def primary():
            return self.primary_api.generate(prompt, timeout=5.0)

        def fallback_to_secondary():
            try:
                return self.secondary_api.generate(prompt, timeout=3.0)
            except APIError:
                # Last resort: use stale cache if available
                if cached:
                    return LLMResponse(text=cached.text, source="cache-stale")
                raise ServiceUnavailable("No LLM service available")

        try:
            result = self.circuit_breaker.call(primary, fallback_to_secondary)
            self.cache.set(prompt, result.text)
            return result
        except Exception as e:
            logger.error(f"All LLM services failed: {e}")
            raise
```

**Bad:**
```python
class LLMClient:
    async def generate(self, prompt: str) -> str:
        """No fallback, complete failure when API is down"""
        response = await self.api.generate(prompt, timeout=30.0)
        return response.text
        # If API fails or times out, entire application breaks
```

**Why It Matters:** LLM APIs are external dependencies with unpredictable availability. The good example continues serving users through multiple fallback layers, while the bad example creates a single point of failure that brings down the entire system.

### Example 2: Database Query Degradation

**Good:**
```python
class ProductSearch:
    def search(self, query: str, max_time: float = 3.0) -> SearchResults:
        """Degrade from complex to simple queries based on time available"""
        start_time = time.time()

        try:
            # Try comprehensive search with ML ranking
            results = self.db.execute(
                """
                SELECT p.*, similarity_score(p.description, %s) as score
                FROM products p
                WHERE search_vector @@ to_tsquery(%s)
                ORDER BY score DESC, p.popularity DESC
                LIMIT 50
                """,
                (query, query),
                timeout=max_time - 0.5  # Reserve time for fallback
            )
            return SearchResults(items=results, quality="high")
        except TimeoutError:
            elapsed = time.time() - start_time
            remaining = max_time - elapsed

            if remaining > 0.5:
                # Fall back to simple keyword search
                logger.info("Complex search timed out, using simple search")
                results = self.db.execute(
                    """
                    SELECT * FROM products
                    WHERE name ILIKE %s OR description ILIKE %s
                    ORDER BY popularity DESC
                    LIMIT 20
                    """,
                    (f"%{query}%", f"%{query}%"),
                    timeout=remaining
                )
                return SearchResults(items=results, quality="medium")
            else:
                # Last resort: cached popular items
                logger.info("Insufficient time for DB query, using cache")
                return SearchResults(items=self.get_popular_cached(), quality="low")
```

**Bad:**
```python
class ProductSearch:
    def search(self, query: str) -> SearchResults:
        """Single complex query with no timeout or fallback"""
        results = self.db.execute(
            """
            SELECT p.*,
                   similarity_score(p.description, %s) as score,
                   get_user_preferences(p.id) as personalization
            FROM products p
            LEFT JOIN reviews r ON r.product_id = p.id
            WHERE search_vector @@ to_tsquery(%s)
            GROUP BY p.id
            ORDER BY score DESC, AVG(r.rating) DESC
            LIMIT 50
            """,
            (query, query)
        )
        return results
        # If query is slow or times out, user waits indefinitely or sees error
```

**Why It Matters:** Database queries can be unpredictably slow due to load, query complexity, or data volume. The good example provides results within a time budget by degrading query sophistication, while the bad example risks timeouts and poor user experience.

### Example 3: Multi-Service Dashboard

**Good:**
```python
class Dashboard:
    def get_data(self, user_id: str) -> DashboardData:
        """Each service fails independently without breaking dashboard"""
        data = DashboardData(user_id=user_id, sections={})

        # Analytics service (not critical)
        try:
            data.sections["analytics"] = self.analytics_service.get_stats(
                user_id, timeout=2.0
            )
        except (TimeoutError, ServiceError) as e:
            logger.warning(f"Analytics unavailable: {e}")
            data.sections["analytics"] = {"status": "unavailable", "error": "temporary"}

        # Recommendations service (not critical)
        try:
            data.sections["recommendations"] = self.ml_service.get_recommendations(
                user_id, timeout=3.0
            )
        except (TimeoutError, ServiceError) as e:
            logger.warning(f"Recommendations unavailable: {e}")
            # Use simple rule-based recommendations as fallback
            data.sections["recommendations"] = self.get_popular_items()

        # Activity feed (critical - must succeed)
        try:
            data.sections["activity"] = self.activity_service.get_recent(
                user_id, timeout=5.0
            )
        except Exception as e:
            # Even critical section has fallback
            logger.error(f"Activity service failed: {e}")
            data.sections["activity"] = self.get_cached_activity(user_id)

        return data
```

**Bad:**
```python
class Dashboard:
    def get_data(self, user_id: str) -> DashboardData:
        """All services must succeed or entire dashboard fails"""
        analytics = self.analytics_service.get_stats(user_id)
        recommendations = self.ml_service.get_recommendations(user_id)
        activity = self.activity_service.get_recent(user_id)

        return DashboardData(
            user_id=user_id,
            analytics=analytics,
            recommendations=recommendations,
            activity=activity
        )
        # If any service fails, entire dashboard fails
```

**Why It Matters:** Dashboards aggregate data from multiple services, each with independent failure modes. The good example isolates failures and provides partial dashboards, while the bad example creates cascading failures where one slow service breaks everything.

### Example 4: Image Processing Pipeline

**Good:**
```python
class ImageProcessor:
    def process(self, image: Image) -> ProcessedImage:
        """Core processing always succeeds, enhancements degrade gracefully"""
        result = ProcessedImage(original=image)

        # Core: Basic processing (always works)
        result.resized = self.resize(image, target_size=(800, 600))
        result.format = "JPEG"

        # Enhancement 1: Face detection (can fail)
        try:
            result.faces = self.face_detector.detect(image, timeout=2.0)
        except (TimeoutError, ServiceError) as e:
            logger.info(f"Face detection unavailable: {e}")
            result.faces = None

        # Enhancement 2: Object recognition (can fail)
        try:
            result.objects = self.object_recognizer.recognize(image, timeout=3.0)
        except (TimeoutError, ServiceError) as e:
            logger.info(f"Object recognition unavailable: {e}")
            result.objects = None

        # Enhancement 3: OCR text extraction (can fail)
        try:
            result.text = self.ocr_service.extract_text(image, timeout=2.0)
        except (TimeoutError, ServiceError) as e:
            logger.info(f"OCR unavailable: {e}")
            result.text = None

        return result
```

**Bad:**
```python
class ImageProcessor:
    def process(self, image: Image) -> ProcessedImage:
        """All processing steps must succeed"""
        # All operations are treated as equally critical
        resized = self.resize(image, target_size=(800, 600))
        faces = self.face_detector.detect(image)
        objects = self.object_recognizer.recognize(image)
        text = self.ocr_service.extract_text(image)

        return ProcessedImage(
            original=image,
            resized=resized,
            faces=faces,
            objects=objects,
            text=text
        )
        # If any ML service is down, processing completely fails
```

**Why It Matters:** Image processing often involves multiple ML services with varying reliability. The good example distinguishes core functionality from enhancements and degrades gracefully, while the bad example fails completely if any enhancement service is unavailable.

### Example 5: Configuration Loading

**Good:**
```python
class ConfigLoader:
    def __init__(self):
        self.defaults = {
            "max_retries": 3,
            "timeout": 5.0,
            "log_level": "INFO",
            "feature_flags": {}
        }

    def load(self, config_path: Path) -> Config:
        """Always returns valid config, even if file is missing or corrupt"""
        config = self.defaults.copy()

        # Try to load from file
        try:
            if config_path.exists():
                user_config = yaml.safe_load(config_path.read_text())
                config.update(user_config)
                logger.info(f"Loaded config from {config_path}")
            else:
                logger.warning(f"Config file not found: {config_path}, using defaults")
        except yaml.YAMLError as e:
            logger.error(f"Invalid config file: {e}, using defaults")
        except Exception as e:
            logger.error(f"Error loading config: {e}, using defaults")

        # Validate and sanitize loaded values
        config["max_retries"] = max(1, int(config.get("max_retries", 3)))
        config["timeout"] = max(0.1, float(config.get("timeout", 5.0)))
        config["log_level"] = config.get("log_level", "INFO").upper()

        return Config(**config)
```

**Bad:**
```python
class ConfigLoader:
    def load(self, config_path: Path) -> Config:
        """Crashes if config file is missing or invalid"""
        config = yaml.safe_load(config_path.read_text())
        return Config(**config)
        # Application won't start if config file has any issues
```

**Why It Matters:** Configuration files are a common source of deployment failures. The good example ensures the application always starts with sensible defaults even when config files are missing or corrupt, while the bad example prevents startup entirely.

## Related Principles

- **[Principle #32 - Error Recovery Patterns Built In](32-error-recovery-patterns.md)** - Graceful degradation is a specific form of error recovery that maintains partial functionality rather than failing completely

- **[Principle #34 - Observable System Behavior](34-observable-system-behavior.md)** - Degraded mode needs to be observable so operators and AI agents can detect and respond to reduced functionality

- **[Principle #26 - Stateless by Default](26-stateless-by-default.md)** - Stateless components degrade more gracefully because they don't accumulate corrupted state during partial failures

- **[Principle #27 - Disposable Components Everywhere](27-disposable-components.md)** - Disposable components enable graceful degradation by allowing quick replacement of failed components with fresh instances

- **[Principle #24 - Test in Production Safely](24-test-in-production-safely.md)** - Graceful degradation provides safety boundaries for production testing by ensuring experiments fail gracefully

- **[Principle #11 - Continuous Validation with Fast Feedback](../process/11-continuous-validation-fast-feedback.md)** - Fast feedback loops help detect when systems enter degraded mode so recovery can begin quickly

## Common Pitfalls

1. **Degrading Silently Without Alerting**: Systems that degrade gracefully but don't notify operators or log degradation events create invisible problems.
   - Example: Falling back to cached data without logging cache age or that fresh data failed.
   - Impact: Operators unaware of ongoing issues, degraded mode becomes permanent, stale data serves users indefinitely.

2. **Cascading Degradation Without Boundaries**: Degradation in one component triggers degradation in dependent components, creating cascading failures.
   - Example: Slow database causes API timeouts, which cause circuit breakers to open, which cause all clients to fail.
   - Impact: Single slow component brings down entire system despite degradation strategies.

3. **Fallbacks That Are Worse Than Failure**: Some fallback strategies create worse outcomes than explicit failure.
   - Example: Returning random recommendations when ML service fails creates confusing user experience.
   - Impact: Users lose trust in system quality, prefer explicit "unavailable" message over poor fallback.

4. **No Testing of Degraded Modes**: Fallback code paths that are never tested often don't work when actually needed.
   - Example: Circuit breaker fallback that crashes because it accesses uninitialized cache.
   - Impact: Degraded mode is discovered to be broken during actual outage, making situation worse.

5. **Degradation That Never Recovers**: Systems that enter degraded mode but don't automatically recover when underlying issues are fixed.
   - Example: Circuit breaker opens and never checks if service has recovered.
   - Impact: System remains in degraded mode indefinitely even after issues resolve.

6. **Inconsistent Degradation Strategies**: Different parts of system handle failures differently, creating unpredictable behavior.
   - Example: Some endpoints cache responses, others fail immediately, others retry infinitely.
   - Impact: Users and operators can't predict system behavior, AI agents struggle to reason about failure modes.

7. **Degraded Mode Without Quality Indicators**: Users receive degraded responses without knowing they're degraded.
   - Example: Serving stale cached data without indicating cache age or freshness.
   - Impact: Users make decisions based on stale data thinking it's current, loss of trust when staleness discovered.

## Tools & Frameworks

### Circuit Breakers & Resilience
- **Resilience4j**: Comprehensive fault tolerance library with circuit breakers, rate limiters, retries, and bulkheads
- **Polly (.NET)**: Resilience and transient-fault-handling library with fallback policies
- **PyBreaker**: Python circuit breaker implementation with multiple state transition strategies
- **Hystrix**: Netflix's latency and fault tolerance library (archived but influential pattern)

### Service Mesh & Infrastructure
- **Istio**: Service mesh with automatic circuit breaking, retries, and timeout management
- **Linkerd**: Lightweight service mesh with built-in failure handling and load balancing
- **Envoy**: Proxy with advanced circuit breaking and outlier detection
- **Consul**: Service discovery with health checking and traffic management

### Caching & Fallback Data
- **Redis**: High-performance cache for storing fallback data and responses
- **Varnish**: HTTP cache for serving stale content when origin is unavailable
- **Memcached**: Distributed memory caching for quick fallback responses
- **CDN (CloudFlare/Fastly)**: Edge caching that continues serving when origin fails

### Monitoring & Detection
- **Prometheus**: Metrics collection to track degraded mode indicators
- **Grafana**: Visualization of service health and degradation events
- **Datadog**: APM and monitoring with automatic anomaly detection
- **New Relic**: Application performance monitoring with service health tracking

### Feature Flags & Progressive Rollout
- **LaunchDarkly**: Feature flag management for enabling/disabling degraded modes
- **Split.io**: Feature flags with automatic rollback on errors
- **Unleash**: Open-source feature toggle system
- **Flipper**: Ruby feature flag library with percentage-based rollouts

## Implementation Checklist

When implementing this principle, ensure:

- [ ] All critical paths have at least one fallback strategy defined
- [ ] Fallback quality is explicitly labeled (cached, stale, reduced, unavailable)
- [ ] Degraded modes are logged with severity and context
- [ ] Circuit breakers automatically open after threshold failures
- [ ] Circuit breakers automatically test for recovery (half-open state)
- [ ] Timeouts are set at every external service boundary
- [ ] Cached fallback data includes age/staleness indicators
- [ ] Progressive enhancement separates core from optional features
- [ ] Degraded modes are tested regularly in staging/production
- [ ] Monitoring alerts trigger when systems enter degraded mode
- [ ] Recovery procedures are automated when possible
- [ ] Documentation clearly describes degradation behavior and fallback quality

## Metadata

**Category**: Technology
**Principle Number**: 33
**Related Patterns**: Circuit Breaker, Bulkhead, Retry with Backoff, Cache-Aside, Fallback, Progressive Enhancement
**Prerequisites**: Error handling patterns, caching strategy, observability infrastructure, understanding of failure modes
**Difficulty**: Medium
**Impact**: High

---

**Status**: Complete
**Last Updated**: 2025-09-30
**Version**: 1.0