# Principle #39 - Metrics and Evaluation Everywhere

## Plain-Language Definition

Measure everything that matters, evaluate AI outputs systematically, and use data to improve quality over time. Metrics and evaluation everywhere means instrumenting systems to track performance, cost, quality, and user experience, then using those measurements to guide decisions and improvements.

## Why This Matters for AI-First Development

AI-first development introduces unique measurement challenges. Traditional software has predictable outputs for given inputs, but AI systems are probabilistic. The same prompt can produce different results across runs. Quality varies based on model version, temperature settings, prompt engineering, and context window usage. Without systematic evaluation, you can't tell if changes improve or degrade the system.

Metrics serve three critical roles in AI-driven development:

1. **Quality assurance**: Automated evaluation catches regressions before they reach users. When an AI agent modifies code or generates outputs, metrics verify that quality standards are maintained. This is essential because AI outputs can degrade subtly in ways that aren't immediately obvious.

2. **Cost optimization**: AI operations have real costs per token, per API call, per model. Without tracking, costs spiral. Metrics reveal expensive operations, enable budget controls, and guide optimization efforts toward high-impact areas.

3. **Continuous improvement**: Systematic evaluation creates feedback loops. A/B testing reveals which prompts work better. User satisfaction scores highlight problem areas. Performance metrics show where latency hurts UX. These insights drive iterative improvement of the AI system.

Without metrics, AI-first systems operate blindly. A model upgrade might degrade quality in ways you don't discover until users complain. Prompt changes might triple costs without improving results. Error rates might climb slowly over time as edge cases accumulate. Metrics make these problems visible immediately, enabling proactive fixes rather than reactive firefighting.

## Implementation Approaches

### 1. **Performance Metrics Collection**

Instrument all AI operations to track latency, throughput, and resource usage:

```python
@track_performance
async def generate_response(prompt: str) -> str:
    metrics.timer("ai.response.latency").start()
    metrics.counter("ai.response.requests").inc()

    response = await ai_client.generate(prompt)

    metrics.timer("ai.response.latency").stop()
    metrics.histogram("ai.response.tokens", len(response.split()))
    return response
```

Use structured logging and APM tools to capture timing, error rates, and throughput. Set up dashboards that show P50, P95, and P99 latencies. Alert when metrics degrade beyond thresholds.

**When to use**: Always. Performance metrics should be universal across all AI operations.

**Success looks like**: Real-time dashboards showing latency distributions, error rates trending down, automated alerts when SLAs are violated.

### 2. **Quality Metrics and Automated Evaluation**

Define quality metrics specific to your domain and evaluate every AI output:

```python
async def evaluate_code_generation(generated_code: str, spec: str) -> QualityScore:
    """Evaluate generated code against multiple quality dimensions"""
    scores = {
        "syntax_valid": await check_syntax(generated_code),
        "meets_spec": await verify_spec_compliance(generated_code, spec),
        "test_coverage": await calculate_coverage(generated_code),
        "security_clean": await scan_security(generated_code),
        "performance_acceptable": await benchmark_performance(generated_code),
    }

    overall = sum(scores.values()) / len(scores)

    metrics.gauge("ai.code.quality", overall)
    for dimension, score in scores.items():
        metrics.gauge(f"ai.code.{dimension}", score)

    return QualityScore(overall=overall, dimensions=scores)
```

Define quality as a multi-dimensional score. Track each dimension separately. Set minimum thresholds and reject outputs that don't meet them.

**When to use**: For all critical AI outputs that users depend on (code, documentation, analysis, recommendations).

**Success looks like**: Consistent quality scores above thresholds, early detection of quality regressions, automated rejection of poor outputs before they reach users.

### 3. **Cost Tracking and Budget Controls**

Track every API call's token usage and cost, aggregate by feature/user/operation:

```python
class CostTracker:
    def __init__(self, budget: float):
        self.budget = budget
        self.spent = 0.0

    async def track_call(self, model: str, tokens: int) -> bool:
        cost = calculate_cost(model, tokens)

        metrics.counter("ai.cost.total", cost)
        metrics.counter(f"ai.cost.{model}", cost)

        self.spent += cost
        if self.spent > self.budget:
            metrics.counter("ai.cost.budget_exceeded").inc()
            raise BudgetExceededError(f"Spent ${self.spent:.2f} of ${self.budget:.2f}")

        return True
```

Set budgets at multiple levels (per-user, per-feature, total). Alert when approaching limits. Provide users with cost visibility.

**When to use**: Whenever using paid AI APIs. Essential for production systems to prevent runaway costs.

**Success looks like**: Predictable monthly costs, automated budget enforcement, cost per user/feature visible in dashboards, optimization opportunities identified.

### 4. **A/B Testing for AI Improvements**

Test changes systematically before rolling them out to all users:

```python
class ABExperiment:
    def __init__(self, name: str, variants: dict[str, callable]):
        self.name = name
        self.variants = variants

    async def run(self, user_id: str, input_data: dict) -> tuple[str, any]:
        variant = assign_variant(user_id, self.variants.keys())
        metrics.counter(f"ab.{self.name}.{variant}").inc()

        start = time.time()
        result = await self.variants[variant](input_data)
        duration = time.time() - start

        metrics.histogram(f"ab.{self.name}.{variant}.latency", duration)

        return variant, result

# Usage
experiment = ABExperiment(
    name="prompt_optimization",
    variants={
        "control": lambda x: generate_with_old_prompt(x),
        "treatment": lambda x: generate_with_new_prompt(x),
    }
)

variant, result = await experiment.run(user_id, input_data)
```

Run experiments on a percentage of traffic. Collect metrics for each variant. Use statistical significance testing to determine winners.

**When to use**: Before deploying prompt changes, model upgrades, or algorithmic improvements.

**Success looks like**: Data-driven decisions about which changes to deploy, confidence in improvements, ability to roll back if metrics regress.

### 5. **User Feedback and Satisfaction Tracking**

Collect explicit and implicit feedback on AI outputs:

```python
class FeedbackCollector:
    async def collect_explicit(self, output_id: str, user_id: str, rating: int, comment: str):
        """User explicitly rates the output"""
        await db.feedback.insert({
            "output_id": output_id,
            "user_id": user_id,
            "rating": rating,
            "comment": comment,
            "timestamp": now(),
        })

        metrics.histogram("ai.user.rating", rating)

    async def collect_implicit(self, output_id: str, user_id: str, action: str):
        """Infer satisfaction from user actions"""
        signals = {
            "accepted": 1.0,      # User accepted AI suggestion
            "edited": 0.7,        # User edited before accepting
            "rejected": 0.0,      # User rejected outright
            "regenerated": 0.3,   # User asked for different output
        }

        score = signals.get(action, 0.5)
        metrics.histogram("ai.user.implicit_satisfaction", score)
```

Provide thumbs up/down buttons on AI outputs. Track whether users accept, edit, or reject suggestions. Correlate feedback with quality metrics.

**When to use**: On user-facing AI features where humans interact with AI outputs.

**Success looks like**: High acceptance rates, low rejection rates, correlation between automated quality metrics and user satisfaction.

### 6. **Error and Failure Tracking**

Monitor all failure modes and track their frequency and impact:

```python
class ErrorTracker:
    async def track_failure(self, operation: str, error: Exception, context: dict):
        """Track AI operation failures"""
        error_type = type(error).__name__

        metrics.counter(f"ai.error.{operation}.{error_type}").inc()

        await db.errors.insert({
            "operation": operation,
            "error_type": error_type,
            "error_message": str(error),
            "context": context,
            "timestamp": now(),
        })

        # Alert if error rate exceeds threshold
        error_rate = calculate_error_rate(operation)
        if error_rate > 0.05:  # 5% threshold
            alert(f"High error rate for {operation}: {error_rate:.2%}")
```

Categorize errors by type and severity. Track error rates over time. Set up automated alerts for error spikes.

**When to use**: Always. Every AI operation should have error tracking.

**Success looks like**: Low error rates, fast detection of new error patterns, automated alerts enabling quick response.

## Good Examples vs Bad Examples

### Example 1: Code Generation Quality Evaluation

**Good:**
```python
class CodeEvaluator:
    async def evaluate(self, generated_code: str, spec: str) -> EvalResult:
        """Multi-dimensional quality evaluation"""
        # Syntax check
        syntax_score = await self._check_syntax(generated_code)

        # Static analysis
        lint_score = await self._run_linter(generated_code)

        # Security scan
        security_score = await self._scan_vulnerabilities(generated_code)

        # Test execution
        test_score = await self._run_tests(generated_code)

        # Spec compliance (using another AI)
        compliance_score = await self._verify_spec(generated_code, spec)

        overall = (syntax_score + lint_score + security_score +
                   test_score + compliance_score) / 5

        # Record all metrics
        metrics.gauge("ai.code.syntax", syntax_score)
        metrics.gauge("ai.code.lint", lint_score)
        metrics.gauge("ai.code.security", security_score)
        metrics.gauge("ai.code.tests", test_score)
        metrics.gauge("ai.code.compliance", compliance_score)
        metrics.gauge("ai.code.overall", overall)

        return EvalResult(
            overall=overall,
            dimensions={
                "syntax": syntax_score,
                "lint": lint_score,
                "security": security_score,
                "tests": test_score,
                "compliance": compliance_score,
            },
            passed=overall >= 0.8  # Minimum quality threshold
        )
```

**Bad:**
```python
async def evaluate(generated_code: str) -> bool:
    """Binary pass/fail with no metrics"""
    try:
        compile(generated_code)
        return True  # If it compiles, it's good enough
    except SyntaxError:
        return False
    # No metrics recorded, no multi-dimensional evaluation,
    # no way to detect quality degradation over time
```

**Why It Matters:** Multi-dimensional evaluation reveals which aspects of quality are strong or weak. Binary pass/fail hides problems. The good example tracks metrics over time, enabling trend analysis and early detection of regressions. The bad example provides no insight into why code fails or how to improve.

### Example 2: Cost Tracking with Budget Controls

**Good:**
```python
class AIClient:
    def __init__(self, budget_manager: BudgetManager):
        self.budget_manager = budget_manager
        self.client = OpenAI()

    async def generate(self, prompt: str, user_id: str, model: str = "gpt-4") -> str:
        # Pre-check budget
        estimated_tokens = estimate_tokens(prompt)
        estimated_cost = calculate_cost(model, estimated_tokens)

        if not self.budget_manager.check_budget(user_id, estimated_cost):
            metrics.counter("ai.budget.blocked").inc()
            raise BudgetExceededError(f"User {user_id} exceeds budget")

        # Track the call
        start = time.time()
        response = await self.client.generate(prompt, model=model)
        duration = time.time() - start

        actual_cost = calculate_cost(model, response.usage.total_tokens)

        # Record metrics
        metrics.counter("ai.cost.total", actual_cost)
        metrics.counter(f"ai.cost.user.{user_id}", actual_cost)
        metrics.counter(f"ai.cost.model.{model}", actual_cost)
        metrics.histogram("ai.tokens.prompt", response.usage.prompt_tokens)
        metrics.histogram("ai.tokens.completion", response.usage.completion_tokens)
        metrics.timer("ai.latency", duration)

        # Update budget
        self.budget_manager.record_spend(user_id, actual_cost)

        return response.text
```

**Bad:**
```python
async def generate(prompt: str) -> str:
    response = await openai.generate(prompt)
    return response.text
    # No cost tracking, no budget controls, no visibility into spending
```

**Why It Matters:** Without cost tracking, AI costs can spiral out of control. The good example provides complete visibility into spending by user and model, enforces budget limits, and alerts when costs are high. The bad example has no safeguards—users could accidentally spend thousands of dollars before anyone notices.

### Example 3: A/B Testing Prompt Changes

**Good:**
```python
class PromptExperiment:
    def __init__(self):
        self.prompts = {
            "control": "Generate code for: {spec}",
            "treatment_concise": "Generate minimal code for: {spec}",
            "treatment_detailed": "Generate well-documented code for: {spec}",
        }
        self.results = defaultdict(list)

    async def run(self, spec: str, user_id: str) -> str:
        # Assign user to variant
        variant = self._assign_variant(user_id)
        prompt = self.prompts[variant].format(spec=spec)

        # Generate with timing
        start = time.time()
        code = await ai_client.generate(prompt)
        latency = time.time() - start

        # Evaluate quality
        quality = await evaluate_code(code, spec)

        # Record experiment metrics
        metrics.counter(f"experiment.prompt.{variant}.requests").inc()
        metrics.histogram(f"experiment.prompt.{variant}.latency", latency)
        metrics.histogram(f"experiment.prompt.{variant}.quality", quality.overall)
        metrics.histogram(f"experiment.prompt.{variant}.tokens", len(code.split()))

        # Store for statistical analysis
        self.results[variant].append({
            "quality": quality.overall,
            "latency": latency,
            "user_id": user_id,
            "timestamp": now(),
        })

        return code

    def analyze(self) -> dict:
        """Statistical analysis of experiment results"""
        return {
            variant: {
                "mean_quality": np.mean([r["quality"] for r in results]),
                "mean_latency": np.mean([r["latency"] for r in results]),
                "sample_size": len(results),
                "p_value": t_test(self.results["control"], results),
            }
            for variant, results in self.results.items()
        }
```

**Bad:**
```python
# Try new prompt for everyone
async def generate_code(spec: str) -> str:
    prompt = "Generate well-documented code for: {spec}"  # Changed from old prompt
    return await ai_client.generate(prompt)
    # No comparison, no metrics, no way to know if new prompt is better
```

**Why It Matters:** A/B testing lets you compare approaches scientifically. The good example runs variants in parallel, collects metrics, and determines which prompt produces better quality, faster, or more efficiently. The bad example changes the prompt for everyone immediately—if quality degrades, you won't know until users complain, and you won't have baseline data to compare against.

### Example 4: User Feedback Collection

**Good:**
```python
class FeedbackSystem:
    async def track_ai_output(self, output_id: str, code: str, user_id: str):
        """Track AI output and user interactions"""
        await db.outputs.insert({
            "output_id": output_id,
            "code": code,
            "user_id": user_id,
            "timestamp": now(),
        })

    async def record_explicit_feedback(self, output_id: str, rating: int, comment: str):
        """User explicitly rates the output (1-5 stars)"""
        await db.feedback.insert({
            "output_id": output_id,
            "rating": rating,
            "comment": comment,
            "feedback_type": "explicit",
            "timestamp": now(),
        })

        metrics.histogram("ai.user.rating", rating)

    async def record_implicit_feedback(self, output_id: str, action: str):
        """Infer satisfaction from user actions"""
        satisfaction_scores = {
            "accepted_as_is": 1.0,
            "edited_slightly": 0.8,
            "edited_heavily": 0.5,
            "rejected": 0.0,
            "regenerated": 0.3,
        }

        score = satisfaction_scores.get(action, 0.5)

        await db.feedback.insert({
            "output_id": output_id,
            "action": action,
            "implied_satisfaction": score,
            "feedback_type": "implicit",
            "timestamp": now(),
        })

        metrics.histogram("ai.user.implicit_satisfaction", score)

    async def analyze_feedback(self) -> dict:
        """Correlate feedback with quality metrics"""
        outputs = await db.query("""
            SELECT o.output_id, o.quality_score,
                   COALESCE(f.rating, i.implied_satisfaction) as satisfaction
            FROM outputs o
            LEFT JOIN feedback f ON o.output_id = f.output_id AND f.feedback_type = 'explicit'
            LEFT JOIN feedback i ON o.output_id = i.output_id AND i.feedback_type = 'implicit'
        """)

        correlation = calculate_correlation(
            [o.quality_score for o in outputs],
            [o.satisfaction for o in outputs]
        )

        return {
            "satisfaction_avg": np.mean([o.satisfaction for o in outputs]),
            "quality_satisfaction_correlation": correlation,
        }
```

**Bad:**
```python
async def generate_code(spec: str) -> str:
    code = await ai_client.generate(f"Generate code for: {spec}")
    return code
    # No feedback collection, no way to know if users are satisfied
```

**Why It Matters:** User feedback is the ultimate quality metric. The good example collects both explicit ratings and implicit signals (accept, edit, reject), correlates them with automated quality metrics, and identifies gaps. The bad example generates code with no feedback loop—you never learn what users actually need or how to improve.

### Example 5: Error Tracking and Alerting

**Good:**
```python
class AIOperationMonitor:
    def __init__(self):
        self.error_counts = defaultdict(int)
        self.total_counts = defaultdict(int)

    async def execute_with_monitoring(
        self,
        operation: str,
        func: callable,
        *args,
        **kwargs
    ) -> any:
        """Execute AI operation with comprehensive monitoring"""
        self.total_counts[operation] += 1
        metrics.counter(f"ai.{operation}.requests").inc()

        start = time.time()

        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start

            # Success metrics
            metrics.counter(f"ai.{operation}.success").inc()
            metrics.timer(f"ai.{operation}.latency", duration)

            return result

        except RateLimitError as e:
            # Track specific error types
            self.error_counts[f"{operation}.rate_limit"] += 1
            metrics.counter(f"ai.{operation}.error.rate_limit").inc()

            await self._alert_if_threshold_exceeded(
                operation,
                "rate_limit",
                threshold=0.1
            )
            raise

        except InvalidRequestError as e:
            self.error_counts[f"{operation}.invalid_request"] += 1
            metrics.counter(f"ai.{operation}.error.invalid_request").inc()

            # Log full context for debugging
            logger.error(
                f"Invalid request in {operation}",
                extra={
                    "error": str(e),
                    "args": args,
                    "kwargs": kwargs,
                }
            )
            raise

        except Exception as e:
            # Catch-all for unexpected errors
            self.error_counts[f"{operation}.unknown"] += 1
            metrics.counter(f"ai.{operation}.error.unknown").inc()

            logger.exception(f"Unexpected error in {operation}")
            raise

        finally:
            # Always record total duration (success or failure)
            duration = time.time() - start
            metrics.timer(f"ai.{operation}.duration", duration)

    async def _alert_if_threshold_exceeded(
        self,
        operation: str,
        error_type: str,
        threshold: float
    ):
        """Alert if error rate exceeds threshold"""
        error_count = self.error_counts[f"{operation}.{error_type}"]
        total_count = self.total_counts[operation]
        error_rate = error_count / max(total_count, 1)

        if error_rate > threshold:
            await send_alert(
                f"High {error_type} rate for {operation}: "
                f"{error_rate:.1%} ({error_count}/{total_count})"
            )
```

**Bad:**
```python
async def generate_code(spec: str) -> str:
    try:
        return await ai_client.generate(f"Generate code for: {spec}")
    except Exception as e:
        logger.error(f"Error: {e}")
        raise
    # Catches errors but doesn't track rates, types, or alert on spikes
```

**Why It Matters:** Errors happen in AI systems (rate limits, invalid inputs, model failures). The good example tracks error rates by type, alerts when rates spike, and provides rich context for debugging. The bad example just logs errors without tracking patterns—you won't notice if errors suddenly jump from 1% to 20% until users complain.

## Related Principles

- **[Principle #30 - Observability Baked In](30-observable-by-default.md)** - Metrics require observability infrastructure; this principle provides the foundation for measurement

- **[Principle #19 - Cost and Token Budgeting](../process/19-version-everything-visibility.md)** - Versioning enables tracking how metrics change across versions; you can correlate quality/cost with specific model or prompt versions

- **[Principle #13 - Parallel Exploration by Default](../process/13-context-as-structured-input.md)** - Structured context makes evaluation easier; you can measure how well outputs match structured specs

- **[Principle #17 - Prompt Versioning and Testing](../technology/17-async-first-parallel-always.md)** - Parallel execution of evaluations speeds up feedback loops; you can evaluate multiple outputs simultaneously

- **[Principle #11 - Continuous Validation with Fast Feedback](../process/11-continuous-validation-fast-feedback.md)** - Metrics enable continuous validation; fast feedback loops require fast measurement

- **[Principle #09 - Regeneration with Compare-and-Verify](../process/09-regeneration-compare-verify.md)** - Metrics power the "verify" step; you compare metrics before and after regeneration to validate improvements

## Common Pitfalls

1. **Vanity Metrics Over Actionable Metrics**: Tracking metrics that look good but don't drive decisions.
   - Example: Tracking "total AI requests" without tracking quality, cost, or satisfaction per request.
   - Impact: Dashboard looks impressive but provides no actionable insights. You can't identify problems or improvements.

2. **No Baseline Measurements**: Making changes without establishing baseline metrics first.
   - Example: Switching to a new model without measuring current quality and latency.
   - Impact: Can't determine if the change improved or degraded the system. No way to justify rolling back.

3. **Metrics Without Alerts**: Collecting metrics but not alerting when they degrade.
   - Example: Tracking error rates in dashboard but no alert when errors spike to 20%.
   - Impact: Problems go unnoticed until users complain. Reactive firefighting instead of proactive fixes.

4. **Ignoring Cost Metrics**: Optimizing for quality without considering cost trade-offs.
   - Example: Using GPT-4 for every operation when GPT-3.5 would suffice for 80% of cases.
   - Impact: Unnecessarily high costs. Budget exhausted quickly. Difficult to justify AI investment to leadership.

5. **Binary Quality Evaluation**: Treating quality as pass/fail instead of multi-dimensional.
   - Example: Code quality = "Does it compile?" instead of syntax + security + tests + performance + spec compliance.
   - Impact: Masks quality problems. Code might compile but have security vulnerabilities or performance issues.

6. **No User Feedback Loop**: Relying solely on automated metrics without collecting user feedback.
   - Example: Automated quality score is high but users constantly reject or heavily edit the outputs.
   - Impact: Mismatch between measured quality and actual usefulness. Building toward the wrong optimization target.

7. **Drowning in Metrics**: Tracking too many metrics without prioritizing what matters.
   - Example: 100+ metrics tracked but no one looks at them because it's overwhelming.
   - Impact: Important signals lost in noise. Inability to identify critical issues quickly. Alert fatigue.

## Tools & Frameworks

### Metrics Collection
- **Prometheus**: Time-series database for metrics, integrates with Grafana for visualization
- **StatsD**: Simple metrics aggregation, good for high-volume counters and timers
- **Datadog**: Full-featured APM with built-in AI cost tracking and alerting

### Quality Evaluation
- **LangSmith**: Evaluation framework for LLM outputs with dataset comparison
- **Weights & Biases**: Experiment tracking and model evaluation for ML systems
- **Ragas**: Evaluation framework specifically for RAG (Retrieval-Augmented Generation) systems

### A/B Testing
- **Eppo**: Experimentation platform with statistical analysis built-in
- **GrowthBook**: Open-source feature flagging and A/B testing framework
- **Optimizely**: Enterprise A/B testing with AI-specific features

### Cost Tracking
- **Helicone**: LLM observability platform with detailed cost tracking per user/operation
- **LangFuse**: Open-source LLM observability with cost attribution
- **LLMOps platforms**: OpenAI dashboard, Anthropic console, Azure OpenAI analytics

### Alerting
- **PagerDuty**: Incident management with alert routing and escalation
- **Opsgenie**: Alert management with on-call scheduling
- **Slack/Discord webhooks**: Simple alerting for smaller teams

### Visualization
- **Grafana**: Dashboard creation for metrics visualization
- **Kibana**: Log and metrics visualization, part of ELK stack
- **Tableau**: Advanced analytics and business intelligence dashboards

## Implementation Checklist

When implementing this principle, ensure:

- [ ] All AI operations emit timing metrics (latency, throughput)
- [ ] Cost tracking is enabled for every API call with per-user and per-operation granularity
- [ ] Quality evaluation runs automatically on AI outputs with multi-dimensional scoring
- [ ] Error rates are tracked by operation and error type
- [ ] Automated alerts trigger when metrics degrade beyond thresholds
- [ ] A/B testing framework is available for comparing prompt or model changes
- [ ] User feedback collection is integrated into user-facing AI features
- [ ] Dashboards visualize key metrics with appropriate time windows and aggregations
- [ ] Budget controls prevent runaway costs at user and system levels
- [ ] Baseline metrics are established before making any significant changes
- [ ] Metrics retention policy ensures historical data is available for trend analysis
- [ ] Regular reviews of metrics inform prioritization of improvements

## Metadata

**Category**: Governance
**Principle Number**: 39
**Related Patterns**: Observability, Continuous Integration, A/B Testing, Feedback Loops, Quality Assurance
**Prerequisites**: Logging infrastructure, metrics collection system, basic statistical knowledge
**Difficulty**: Medium
**Impact**: High

---

**Status**: Complete
**Last Updated**: 2025-09-30
**Version**: 1.0