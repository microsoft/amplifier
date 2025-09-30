# Principle #34 - Feature Flags as Deployment Strategy

## Plain-Language Definition

Feature flags (also called feature toggles) let you deploy code to production but control when features become active. They act as runtime switches that enable or disable functionality without redeploying code, allowing safe rollouts, quick rollbacks, and controlled experimentation.

## Why This Matters for AI-First Development

When AI agents generate and deploy code, the traditional "deploy equals release" model becomes a significant risk. An AI agent might generate perfectly valid code that causes unexpected production issues due to edge cases, performance characteristics, or integration problems that weren't visible in testing. Feature flags decouple deployment from activation, giving you a safety mechanism between AI-generated code and user impact.

Feature flags provide three critical capabilities for AI-driven development:

1. **Safe AI-generated deployments**: AI agents can confidently deploy new code with features disabled by default. You can then gradually enable features, monitor behavior, and quickly disable them if problems emerge. This transforms risky "all-or-nothing" deployments into controlled, reversible experiments.

2. **Rapid incident response**: When AI-generated code causes production issues, toggling a flag is faster than rolling back a deployment or regenerating code. Instead of waiting for CI/CD pipelines or reverting commits, you flip a switch and immediately restore service. This is crucial when AI agents might introduce subtle bugs that only manifest under production load.

3. **Progressive validation**: AI agents can deploy multiple variations of features simultaneously, controlled by flags. You can expose new AI-generated implementations to 5% of users, compare metrics against the existing version, and automatically roll back if key indicators degrade. This enables data-driven decisions about which AI-generated solutions to keep.

Without feature flags, every AI-generated code change requires either complete confidence (unrealistic) or complex deployment orchestration with manual rollback procedures. A single bad AI-generated change can require emergency reverts, causing downtime and disrupting other work. Feature flags transform this binary choice into a spectrum of controlled risk, where AI agents can deploy continuously while maintaining production stability.

## Implementation Approaches

### 1. **Simple Boolean Toggles**

The most basic approach: a boolean flag that enables or disables a feature:

```python
def process_payment(amount: float) -> PaymentResult:
    if feature_flags.is_enabled("new_payment_processor"):
        return new_payment_processor.charge(amount)
    else:
        return legacy_payment_processor.charge(amount)
```

**When to use**: For simple on/off feature switches, initial feature flag implementations, or binary A/B tests. Best for features with clear boundaries and minimal integration points.

**Success looks like**: Features can be toggled without code deployment, rollback happens instantly via configuration change, and the flag is temporary (removed once feature is stable).

### 2. **Percentage-Based Gradual Rollout**

Expose features to an increasing percentage of users:

```python
def get_recommendations(user_id: str) -> List[Product]:
    rollout_pct = feature_flags.get_rollout_percentage("ai_recommendations")
    if should_enable_for_user(user_id, rollout_pct):
        return ai_recommendation_engine.get_products(user_id)
    else:
        return legacy_recommendation_engine.get_products(user_id)
```

**When to use**: For gradual feature rollouts, validating performance under increasing load, or reducing blast radius of potential issues. Ideal for features with performance implications or user-facing behavior changes.

**Success looks like**: Start at 1%, monitor metrics, increase to 5%, 10%, 25%, 50%, 100% over days or weeks. Automatic rollback if error rates spike or key metrics degrade.

### 3. **User Segment Targeting**

Enable features for specific user groups based on attributes:

```python
def show_experimental_ui(user: User) -> bool:
    return feature_flags.is_enabled_for_user(
        "experimental_ui",
        user,
        targeting_rules={
            "beta_tester": True,
            "account_type": ["premium", "enterprise"],
            "region": ["us-west", "us-east"]
        }
    )
```

**When to use**: For beta testing, internal dogfooding, customer-specific features, or region-specific rollouts. Perfect for gathering feedback from specific audiences before wider release.

**Success looks like**: Internal teams use features first, then beta users, then specific customer segments, with metrics tracked separately for each group.

### 4. **Kill Switches for Risk Mitigation**

Flags that default to ON but can be quickly disabled if problems emerge:

```python
def expensive_analytics_job():
    if not feature_flags.is_enabled("disable_analytics_job"):
        # This flag defaults to False (meaning job runs)
        # But can be set to True to disable the job quickly
        run_analytics_pipeline()
        update_dashboards()
```

**When to use**: For resource-intensive operations, external service integrations, or any feature that could cause cascading failures. Essential for new AI-generated code that might have unexpected resource consumption.

**Success looks like**: Features run normally but can be instantly disabled during incidents without deployment. Clear documentation of which flags are kill switches vs feature toggles.

### 5. **Configuration-Driven Feature Variations**

Flags that control behavior parameters, not just on/off:

```python
def query_with_timeout(query: str):
    timeout_config = feature_flags.get_config("database_query_timeout")
    timeout_ms = timeout_config.get("timeout_ms", default=5000)
    max_retries = timeout_config.get("max_retries", default=3)

    return execute_query(query, timeout=timeout_ms, retries=max_retries)
```

**When to use**: For tuning performance parameters, adjusting resource limits, or experimenting with different configurations. Useful when AI-generated code needs runtime parameter optimization.

**Success looks like**: Parameters can be adjusted in production without deployment, A/B tests can compare different configuration values, and optimal settings emerge through experimentation.

### 6. **Dependency-Based Feature Prerequisites**

Flags that require other features to be enabled first:

```python
def load_user_dashboard(user: User):
    if feature_flags.is_enabled("new_dashboard"):
        # New dashboard requires new API to be enabled
        if not feature_flags.is_enabled("new_api_v2"):
            raise RuntimeError("new_dashboard requires new_api_v2 to be enabled")
        return render_new_dashboard(user)
    else:
        return render_old_dashboard(user)
```

**When to use**: For complex features with multiple components, staged rollouts of interconnected systems, or when testing integration between AI-generated components.

**Success looks like**: Feature dependencies are explicit and enforced at runtime, deployment order doesn't matter because flags control activation order, and partial feature states are impossible.

## Good Examples vs Bad Examples

### Example 1: Database Migration Cutover

**Good:**
```python
class UserRepository:
    def get_user(self, user_id: str) -> User:
        """Feature flag controls which database to query"""
        if feature_flags.is_enabled("postgres_migration"):
            user = postgres_db.get_user(user_id)
            if user is None:
                # Fallback to old database if not found (during migration)
                user = mysql_db.get_user(user_id)
            return user
        else:
            return mysql_db.get_user(user_id)

    def save_user(self, user: User):
        """Always write to both databases during migration"""
        mysql_db.save_user(user)
        if feature_flags.is_enabled("postgres_migration"):
            postgres_db.save_user(user)
```

**Bad:**
```python
class UserRepository:
    def __init__(self):
        # Database chosen at startup - can't switch without restart
        if os.getenv("USE_POSTGRES") == "true":
            self.db = postgres_db
        else:
            self.db = mysql_db

    def get_user(self, user_id: str) -> User:
        return self.db.get_user(user_id)
        # No fallback, no runtime switching, requires restart to change
```

**Why It Matters:** Database migrations are high-risk operations. The good example allows instant rollback to the old database if issues emerge, supports gradual cutover with dual-write patterns, and enables testing the new database with production traffic before full commitment. The bad example locks you into a choice at startup, requiring downtime to switch back if problems occur.

### Example 2: A/B Testing New Algorithm

**Good:**
```python
def get_search_results(query: str, user_id: str) -> List[Result]:
    """A/B test controlled by feature flag with metrics"""
    variant = feature_flags.get_variant("search_algorithm", user_id)

    start_time = time.time()

    if variant == "new_ml_ranker":
        results = ml_search_ranker.search(query)
        metrics.record("search.new_algorithm", time.time() - start_time)
    else:
        results = classic_search_ranker.search(query)
        metrics.record("search.classic_algorithm", time.time() - start_time)

    # Track which variant was used for result quality analysis
    metrics.record("search.variant", variant, tags={"user_id": user_id})

    return results
```

**Bad:**
```python
def get_search_results(query: str, user_id: str) -> List[Result]:
    """A/B test based on user ID - no control or visibility"""
    # Users with even IDs get new algorithm
    if int(user_id) % 2 == 0:
        return ml_search_ranker.search(query)
    else:
        return classic_search_ranker.search(query)
    # No way to change the split, no metrics tracking, permanently splits users
```

**Why It Matters:** A/B testing requires control over assignment and metrics collection. The good example uses a feature flag system that can adjust the test (change percentages, disable the test, target specific users) without code changes, and tracks which variant users saw for analysis. The bad example hard-codes the assignment logic, making it impossible to adjust the test or roll back without deploying code.

### Example 3: External Service Integration

**Good:**
```python
def send_notification(user_id: str, message: str):
    """Feature flag with kill switch for external service"""
    if not feature_flags.is_enabled("notifications_enabled", default=True):
        # Kill switch: can disable all notifications instantly
        logger.info(f"Notifications disabled via feature flag")
        return

    provider = feature_flags.get_config("notification_provider").get("name", "email")

    try:
        if provider == "push":
            push_service.send(user_id, message)
        elif provider == "sms":
            sms_service.send(user_id, message)
        else:
            email_service.send(user_id, message)
    except Exception as e:
        logger.error(f"Notification failed: {e}")
        # Feature flag allows switching providers without code change
        metrics.record("notification.failure", tags={"provider": provider})
```

**Bad:**
```python
def send_notification(user_id: str, message: str):
    """Hard-coded to single provider"""
    push_service.send(user_id, message)
    # No way to disable if push service has outage
    # No way to switch to email fallback
    # No way to test SMS provider in production
```

**Why It Matters:** External services fail. The good example provides a kill switch to disable notifications during outages, allows switching between providers to route around problems, and enables testing new providers with a subset of traffic. The bad example locks you into a single provider with no escape hatch when things go wrong.

### Example 4: Resource-Intensive Feature

**Good:**
```python
async def generate_report(report_id: str) -> Report:
    """Resource-intensive operation with throttling via feature flags"""
    config = feature_flags.get_config("report_generation")

    if not config.get("enabled", True):
        raise ServiceUnavailableError("Report generation temporarily disabled")

    max_concurrent = config.get("max_concurrent", 10)
    timeout_seconds = config.get("timeout_seconds", 300)

    async with resource_limiter.acquire(max_concurrent):
        try:
            async with async_timeout.timeout(timeout_seconds):
                return await expensive_report_generation(report_id)
        except asyncio.TimeoutError:
            metrics.record("report.timeout")
            raise
```

**Bad:**
```python
async def generate_report(report_id: str) -> Report:
    """No control over resource usage"""
    return await expensive_report_generation(report_id)
    # Can't disable if it's overloading the system
    # Can't reduce concurrency during high load
    # Can't adjust timeouts based on system conditions
```

**Why It Matters:** Resource-intensive operations can overwhelm systems under load. The good example uses feature flags to control resource limits, allowing instant adjustment during incidents (reduce concurrency, decrease timeouts, or disable entirely). The bad example provides no runtime control, requiring code changes to adjust resource usage during an outage.

### Example 5: Progressive Feature Rollout

**Good:**
```python
class RecommendationService:
    def get_recommendations(self, user_id: str) -> List[Product]:
        """Progressive rollout with automatic metrics comparison"""
        rollout = feature_flags.get_rollout("ai_recommendations", user_id)

        if rollout.is_enabled:
            variant = "ai_engine"
            with metrics.timer("recommendations.ai_engine"):
                results = self.ai_recommendation_engine.recommend(user_id)
        else:
            variant = "rule_based"
            with metrics.timer("recommendations.rule_based"):
                results = self.rule_based_engine.recommend(user_id)

        # Track metrics for both variants
        metrics.record("recommendations.count", len(results), tags={"variant": variant})
        metrics.record("recommendations.served", tags={
            "variant": variant,
            "rollout_pct": rollout.percentage
        })

        return results
```

**Bad:**
```python
class RecommendationService:
    def __init__(self):
        # Rollout percentage set at deployment time
        self.rollout_pct = int(os.getenv("AI_ROLLOUT_PCT", "0"))

    def get_recommendations(self, user_id: str) -> List[Product]:
        """Can't adjust rollout without redeploying"""
        user_hash = hash(user_id) % 100
        if user_hash < self.rollout_pct:
            return self.ai_recommendation_engine.recommend(user_id)
        else:
            return self.rule_based_engine.recommend(user_id)
        # No metrics tracking, can't change rollout percentage dynamically
```

**Why It Matters:** Progressive rollouts require the ability to adjust percentages quickly based on metrics. The good example uses a feature flag system that can increase or decrease rollout percentages instantly, track metrics per variant, and roll back if problems emerge. The bad example requires redeployment to change the rollout percentage, making it impossible to react quickly to issues.

## Related Principles

- **[Principle #33 - Graceful Degradation by Design](33-blue-green-canary-deployments.md)** - Feature flags enable canary deployments by controlling which users see new features, complementing infrastructure-level traffic routing with application-level control

- **[Principle #13 - Parallel Exploration by Default](../process/13-incremental-complexity-escape-hatches.md)** - Feature flags are escape hatches that allow instant rollback without code changes, essential for managing complexity in AI-generated systems

- **[Principle #18 - Contract Evolution with Migration Paths](../process/18-clear-component-contracts.md)** - Feature flags must respect component contracts; toggling a flag shouldn't violate interface guarantees or break dependent systems

- **[Principle #7 - Regenerate, Don't Edit](../process/07-regenerate-dont-edit.md)** - Feature flags allow AI agents to regenerate features without risk because new code can be deployed disabled and gradually enabled

- **[Principle #39 - Metrics and Evaluation Everywhere](39-observable-system-behavior.md)** - Feature flags must be observable; you need metrics showing which flags are enabled, for whom, and what impact they have on system behavior

- **[Principle #41 - Adaptive Sandboxing with Explicit Approvals](41-audit-trails-ai-actions.md)** - Feature flag changes should be logged with who changed them, when, and why, creating an audit trail of feature activation decisions

## Common Pitfalls

1. **Flag Sprawl and Technical Debt**: Accumulating hundreds of feature flags without cleaning up old ones creates maintenance burden and code complexity.
   - Example: 200 feature flags in production, 150 of them always enabled and never referenced in decision-making.
   - Impact: Code becomes unreadable with nested flag checks, testing requires evaluating 2^200 combinations, and developers fear removing flags that might still be needed.

2. **Long-Lived Flags Instead of Temporary Toggles**: Using feature flags as permanent configuration instead of temporary deployment tools.
   - Example: A flag added in 2023 that's still in the code in 2025, always enabled, but never removed.
   - Impact: Code carries the weight of multiple implementation paths forever, new developers don't know which code path is "real," and technical debt accumulates.

3. **Testing Only One Flag State**: Tests that only validate behavior with flags enabled or disabled, not both states.
   - Example: All tests run with `new_feature=true`, old code path never tested, breaks when flag is disabled.
   - Impact: Rollback via flag doesn't work because old code path is broken, defeats the purpose of having the flag as a safety mechanism.

4. **Flag Checks Deep in Business Logic**: Scattering flag checks throughout the codebase instead of at clear boundaries.
   - Example: `if feature_flags.is_enabled("new_algo")` appears in 47 different files across 200 lines of code.
   - Impact: Impossible to understand feature scope, can't cleanly remove flag, behavior changes unpredictably, and code becomes unmaintainable.

5. **No Default Values for Flags**: Feature flags that fail-closed without sensible defaults when the flag service is unavailable.
   - Example: Flag service down, all flag checks return `False`, entire application broken because features are disabled.
   - Impact: Feature flag system becomes a single point of failure, outages in flag service cause application outages.

6. **Inconsistent Flag State Across Services**: Microservices with different feature flag states, breaking distributed features.
   - Example: Frontend enables `new_checkout`, backend disables `new_checkout_api`, requests fail with cryptic errors.
   - Impact: Feature rollout requires coordinating flag changes across services, rollback is complicated, and inconsistent states cause user-visible bugs.

7. **Overusing Flags for Configuration**: Using feature flags for application configuration that should be in environment variables or config files.
   - Example: Database connection strings, API keys, and timeouts all controlled by feature flags.
   - Impact: Configuration management becomes complex, flag service must be available for basic operations, and sensitive configuration data lives in flag system instead of secrets management.

## Tools & Frameworks

### Managed Feature Flag Services
- **LaunchDarkly**: Enterprise feature flag platform with real-time updates, targeting rules, A/B testing, and extensive SDK support across languages
- **Split.io**: Feature flag service with built-in experimentation, impact analysis, and automated rollback based on metrics
- **Optimizely**: Feature flagging combined with experimentation platform, strong analytics and personalization capabilities
- **ConfigCat**: Simple, cost-effective feature flag service with team collaboration features and SDK support

### Open Source Solutions
- **Unleash**: Self-hosted feature flag system with admin UI, client SDKs, and gradual rollout support
- **Flagsmith**: Open-source feature flag and remote config service with multi-environment support and user segmentation
- **GrowthBook**: Open-source feature flagging with built-in experimentation and statistical analysis
- **Flipper**: Ruby gem for feature flagging with multiple storage backends (Redis, database, memory)

### Language-Specific Libraries
- **Python: flagsmith-python, unleash-client-python**: Official SDK clients for popular flag services
- **JavaScript: launchdarkly-js-client-sdk, @growthbook/growthbook**: Client-side feature flag evaluation
- **Go: go-feature-flag, go-unleash**: Native Go clients with minimal dependencies
- **Java: ff4j, togglz**: Java-native feature flag frameworks with Spring integration

### Infrastructure Integration
- **Kubernetes: ConfigMaps and Secrets**: Built-in Kubernetes primitives for configuration management
- **AWS AppConfig**: AWS service for feature flags, configuration, and operational flags with safe deployment
- **Azure App Configuration**: Microsoft's configuration service with feature flag management
- **HashiCorp Consul**: Service mesh with key-value store suitable for feature flags

### Testing and Validation
- **pytest-split**: Python library for testing all combinations of feature flag states
- **cypress-ld-control**: Cypress integration for testing features behind LaunchDarkly flags
- **test containers**: Spin up feature flag services in tests for integration testing

## Implementation Checklist

When implementing this principle, ensure:

- [ ] Feature flags have clear owners and expiration dates (plan removal from the start)
- [ ] Flags default to safe values (usually disabled) when flag service is unavailable
- [ ] Both enabled and disabled code paths are tested in CI/CD pipeline
- [ ] Flag checks happen at clear architectural boundaries, not scattered throughout code
- [ ] Metrics track flag state, user exposure, and impact on key business indicators
- [ ] Flag changes are logged with audit trail (who, what, when, why)
- [ ] Documentation explains each flag's purpose, safe values, and rollback procedure
- [ ] Stale flags (>90 days unchanged) are reviewed for removal quarterly
- [ ] Feature flags integrate with observability tools for correlation with incidents
- [ ] Gradual rollout flags start at 1% and increase slowly with validation between steps
- [ ] Kill switches for critical features are tested regularly (chaos engineering)
- [ ] Flag configuration is stored in version control with review process for changes

## Metadata

**Category**: Technology
**Principle Number**: 34
**Related Patterns**: Blue-Green Deployment, Canary Release, A/B Testing, Circuit Breaker, Strangler Fig Pattern
**Prerequisites**: Centralized configuration system, metrics and monitoring, deployment automation
**Difficulty**: Medium
**Impact**: High

---

**Status**: Complete
**Last Updated**: 2025-09-30
**Version**: 1.0