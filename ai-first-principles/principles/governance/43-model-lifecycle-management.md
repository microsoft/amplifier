# Principle #43 - Model Lifecycle Management

## Plain-Language Definition

Model lifecycle management treats LLM models as versioned, trackable artifacts with defined upgrade paths, performance monitoring, and fallback strategies. Like managing software dependencies, you track which models are deployed, monitor their performance, upgrade gracefully, and maintain fallback options when newer models fail.

## Why This Matters for AI-First Development

When AI agents generate and modify code using LLMs, the choice of model fundamentally affects output quality, cost, and reliability. A model that works perfectly today might be deprecated tomorrow, introduce breaking changes, or suddenly degrade in performance. Without lifecycle management, AI systems become brittle and unpredictable.

Model lifecycle management provides three critical benefits for AI-driven development:

1. **Predictable behavior across environments**: By versioning models explicitly, you ensure development, testing, and production use consistent model versions. This prevents the nightmare scenario where code that works locally fails in production because different model versions produce different outputs.

2. **Safe experimentation and upgrades**: New models offer better performance, but they also introduce risk. Lifecycle management lets you test new models in controlled environments, compare their performance against baseline models, and roll back gracefully if problems emerge. AI agents can automatically select the best model for each task based on tracked performance metrics.

3. **Cost optimization through intelligent model selection**: Different models have vastly different cost profiles. GPT-4 might cost 10x more than GPT-3.5 but only improve results by 20% for simple tasks. Lifecycle management tracks cost vs. quality trade-offs, allowing AI systems to route tasks to the most cost-effective model that meets quality requirements.

Without model lifecycle management, AI-first systems suffer from version drift, unexpected cost spikes, silent quality degradation, and catastrophic failures when models are deprecated. An AI agent that hard-codes "gpt-4" will break when that version is retired, waste money using expensive models for simple tasks, and provide no visibility into why outputs suddenly change quality.

## Implementation Approaches

### 1. **Explicit Model Versioning**

Never use model names without versions. Treat models like software dependencies:

```python
# Good: Explicit version
MODEL_VERSION = "gpt-4-0125-preview"

# Bad: Implicit version
MODEL_VERSION = "gpt-4"  # Which version? When does it change?
```

Pin specific model versions in configuration files, track them in version control, and document upgrade paths. Use semantic-style versioning when available (e.g., `gpt-4-turbo-2024-04-09` vs. `gpt-4-turbo-preview`).

**Success looks like:** You can deterministically reproduce outputs from three months ago because model versions are tracked alongside code versions.

### 2. **Performance-Based Model Selection**

Track model performance metrics and automatically route requests to the best model for each task:

```python
@dataclass
class ModelPerformance:
    model_id: str
    accuracy: float
    avg_latency_ms: float
    cost_per_1k_tokens: float
    success_rate: float

def select_model(task_type: str, quality_threshold: float) -> str:
    """Select best model based on tracked performance"""
    candidates = get_models_for_task(task_type)

    # Filter by quality threshold
    qualified = [m for m in candidates if m.accuracy >= quality_threshold]

    # Select cheapest qualified model
    return min(qualified, key=lambda m: m.cost_per_1k_tokens).model_id
```

Track performance in production, update metrics regularly, and adjust model selection based on real-world results.

**Success looks like:** Your system automatically uses cheaper models for simple tasks and more expensive models only when quality demands it.

### 3. **Graceful Model Upgrades**

When upgrading to a new model version, validate it against baseline performance before full rollout:

```python
class ModelUpgradeStrategy:
    def canary_rollout(self, new_model: str, baseline_model: str,
                      traffic_percentage: float = 0.1):
        """Gradually roll out new model while monitoring performance"""
        for request in incoming_requests():
            if random.random() < traffic_percentage:
                result = call_model(new_model, request)
                track_performance(new_model, result)
            else:
                result = call_model(baseline_model, request)

            # Compare performance
            if performance_degraded(new_model, baseline_model):
                rollback_to(baseline_model)
                alert_team("Model upgrade failed performance check")
```

Use A/B testing, canary deployments, and feature flags to control model rollouts.

**Success looks like:** You detect and rollback bad model upgrades before they affect most users.

### 4. **Multi-Model Fallback Chains**

Configure fallback models for when primary models fail or are unavailable:

```python
MODEL_CHAIN = [
    {"id": "gpt-4-0125-preview", "max_cost": 0.10},
    {"id": "gpt-3.5-turbo-0125", "max_cost": 0.02},
    {"id": "claude-3-opus-20240229", "max_cost": 0.15},
]

async def call_with_fallback(prompt: str) -> str:
    """Try models in order until one succeeds"""
    for model_config in MODEL_CHAIN:
        try:
            result = await call_model(model_config["id"], prompt)
            if cost_acceptable(result.cost, model_config["max_cost"]):
                return result.text
        except ModelUnavailableError:
            logger.warning(f"Model {model_config['id']} unavailable, trying next")
            continue

    raise AllModelsFailed("All models in chain failed")
```

**Success looks like:** Your system stays operational even when primary models are down or degraded.

### 5. **Model Performance Tracking Dashboard**

Maintain real-time visibility into model performance across all dimensions:

- **Quality metrics**: Task success rate, user satisfaction, output correctness
- **Cost metrics**: Tokens consumed, dollar cost per task, cost trends over time
- **Performance metrics**: Latency, timeout rate, error rate
- **Usage metrics**: Requests per model, task distribution, peak usage times

Store this data in time-series databases and create dashboards that show trends, anomalies, and comparisons between models.

**Success looks like:** You spot performance degradation within hours and can correlate quality drops with specific model versions.

### 6. **Model Deprecation Planning**

Model providers deprecate models regularly. Plan for this:

```python
@dataclass
class ModelDeprecation:
    model_id: str
    deprecation_date: datetime
    replacement_model: str
    breaking_changes: list[str]

def check_deprecated_models():
    """Alert when using deprecated models"""
    for model in get_active_models():
        deprecation = get_deprecation_info(model)
        if deprecation:
            days_until = (deprecation.deprecation_date - now()).days
            if days_until < 30:
                alert_team(f"Model {model} deprecated in {days_until} days")
                test_replacement(deprecation.replacement_model)
```

Monitor model provider announcements, test replacements proactively, and migrate before forced deprecation.

**Success looks like:** You're never caught off-guard by a model being retired.

## Good Examples vs Bad Examples

### Example 1: Model Configuration

**Good:**
```python
from dataclasses import dataclass
from typing import Literal

@dataclass
class ModelConfig:
    model_id: str  # Explicit version
    provider: Literal["openai", "anthropic", "google"]
    max_tokens: int
    temperature: float
    deprecated_on: datetime | None
    replacement_model: str | None

# Versioned configuration
MODELS = {
    "primary": ModelConfig(
        model_id="gpt-4-0125-preview",
        provider="openai",
        max_tokens=4096,
        temperature=0.7,
        deprecated_on=None,
        replacement_model=None,
    ),
    "fast": ModelConfig(
        model_id="gpt-3.5-turbo-0125",
        provider="openai",
        max_tokens=2048,
        temperature=0.5,
        deprecated_on=None,
        replacement_model=None,
    ),
}

def get_model(tier: str) -> ModelConfig:
    """Get versioned model configuration"""
    config = MODELS[tier]

    # Check deprecation
    if config.deprecated_on and now() > config.deprecated_on:
        logger.warning(f"Model {config.model_id} is deprecated")
        if config.replacement_model:
            return get_model_by_id(config.replacement_model)

    return config
```

**Bad:**
```python
# Hard-coded model names without versions
def generate_text(prompt: str):
    response = openai.ChatCompletion.create(
        model="gpt-4",  # Which version? When does it change?
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content

# No configuration management
# No deprecation tracking
# No fallback strategy
# No version control
```

**Why It Matters:** The bad example will break unpredictably when OpenAI updates what "gpt-4" points to, offers no way to test new models safely, and provides no visibility into which model version produced which outputs.

### Example 2: Performance Tracking

**Good:**
```python
from dataclasses import dataclass, asdict
import json
from datetime import datetime

@dataclass
class ModelPerformanceRecord:
    timestamp: datetime
    model_id: str
    task_type: str
    latency_ms: float
    input_tokens: int
    output_tokens: int
    cost_usd: float
    success: bool
    error_type: str | None

class ModelPerformanceTracker:
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, record: ModelPerformanceRecord):
        """Append performance record"""
        with open(self.storage_path, 'a') as f:
            f.write(json.dumps(asdict(record), default=str) + '\n')

    def get_metrics(self, model_id: str, hours: int = 24) -> dict:
        """Calculate metrics for a model"""
        cutoff = now() - timedelta(hours=hours)
        records = [r for r in self._read_records()
                  if r.model_id == model_id and r.timestamp > cutoff]

        if not records:
            return {}

        return {
            "total_requests": len(records),
            "success_rate": sum(r.success for r in records) / len(records),
            "avg_latency_ms": sum(r.latency_ms for r in records) / len(records),
            "total_cost_usd": sum(r.cost_usd for r in records),
            "cost_per_request": sum(r.cost_usd for r in records) / len(records),
        }

# Usage
tracker = ModelPerformanceTracker(Path("data/model_performance.jsonl"))

async def call_model_tracked(model_id: str, prompt: str) -> str:
    start = time.time()
    try:
        response = await call_model(model_id, prompt)
        tracker.record(ModelPerformanceRecord(
            timestamp=now(),
            model_id=model_id,
            task_type="text_generation",
            latency_ms=(time.time() - start) * 1000,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            cost_usd=calculate_cost(response.usage),
            success=True,
            error_type=None,
        ))
        return response.text
    except Exception as e:
        tracker.record(ModelPerformanceRecord(
            timestamp=now(),
            model_id=model_id,
            task_type="text_generation",
            latency_ms=(time.time() - start) * 1000,
            input_tokens=0,
            output_tokens=0,
            cost_usd=0.0,
            success=False,
            error_type=type(e).__name__,
        ))
        raise
```

**Bad:**
```python
# No performance tracking
def call_model(prompt: str):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content

# Can't answer:
# - How much are we spending per model?
# - Which model is fastest for this task?
# - Is model performance degrading?
# - Which model has the best success rate?
```

**Why It Matters:** Without performance tracking, you can't make data-driven decisions about model selection, can't detect performance degradation, and have no visibility into costs. The good example provides actionable metrics for every dimension of model performance.

### Example 3: Model Selection Strategy

**Good:**
```python
from enum import Enum
from dataclasses import dataclass

class TaskComplexity(Enum):
    SIMPLE = "simple"      # Basic classification, extraction
    MODERATE = "moderate"  # Summarization, simple reasoning
    COMPLEX = "complex"    # Multi-step reasoning, code generation

@dataclass
class ModelCapabilities:
    model_id: str
    max_complexity: TaskComplexity
    cost_per_1k_tokens: float
    avg_latency_ms: float

class IntelligentModelSelector:
    def __init__(self):
        self.models = [
            ModelCapabilities(
                model_id="gpt-3.5-turbo-0125",
                max_complexity=TaskComplexity.MODERATE,
                cost_per_1k_tokens=0.0015,
                avg_latency_ms=500,
            ),
            ModelCapabilities(
                model_id="gpt-4-0125-preview",
                max_complexity=TaskComplexity.COMPLEX,
                cost_per_1k_tokens=0.03,
                avg_latency_ms=2000,
            ),
            ModelCapabilities(
                model_id="gpt-4-turbo-2024-04-09",
                max_complexity=TaskComplexity.COMPLEX,
                cost_per_1k_tokens=0.01,
                avg_latency_ms=1200,
            ),
        ]

    def select_model(self, complexity: TaskComplexity,
                    max_cost: float | None = None,
                    max_latency: float | None = None) -> str:
        """Select optimal model for task requirements"""
        # Filter by capability
        capable = [m for m in self.models
                  if m.max_complexity.value >= complexity.value]

        # Filter by cost constraint
        if max_cost:
            capable = [m for m in capable
                      if m.cost_per_1k_tokens <= max_cost]

        # Filter by latency constraint
        if max_latency:
            capable = [m for m in capable
                      if m.avg_latency_ms <= max_latency]

        if not capable:
            raise NoModelMeetsRequirements()

        # Select cheapest capable model
        return min(capable, key=lambda m: m.cost_per_1k_tokens).model_id

# Usage
selector = IntelligentModelSelector()

# Simple task: uses cheapest model
model = selector.select_model(TaskComplexity.SIMPLE)
# Returns: "gpt-3.5-turbo-0125" (cheapest)

# Complex task with latency constraint: uses optimal model
model = selector.select_model(TaskComplexity.COMPLEX, max_latency=1500)
# Returns: "gpt-4-turbo-2024-04-09" (complex capable + under latency limit)
```

**Bad:**
```python
# Always uses most expensive model
def generate_response(prompt: str):
    return openai.ChatCompletion.create(
        model="gpt-4",  # Uses expensive model even for simple tasks
        messages=[{"role": "user", "content": prompt}],
    )

# Cost implications:
# Simple classification: GPT-4 costs 20x more than GPT-3.5
# Extracting dates: GPT-4 costs 20x more with no quality benefit
# Summarizing short text: GPT-4 costs 20x more with minimal benefit
```

**Why It Matters:** The bad example wastes money using expensive models for tasks that cheaper models handle perfectly. At scale, this difference is enormous: a system handling 1M simple tasks per day wastes $30,000 per day ($10M/year) by not optimizing model selection.

### Example 4: Graceful Model Upgrades

**Good:**
```python
from dataclasses import dataclass
from typing import Callable

@dataclass
class ModelRolloutConfig:
    new_model_id: str
    baseline_model_id: str
    rollout_percentage: float  # 0.0 to 1.0
    min_requests_before_decision: int
    success_rate_threshold: float

class GradualModelRollout:
    def __init__(self, config: ModelRolloutConfig,
                 tracker: ModelPerformanceTracker):
        self.config = config
        self.tracker = tracker
        self.rollout_active = True

    async def call_with_gradual_rollout(self, prompt: str) -> str:
        """Route to new or baseline model based on rollout percentage"""
        if not self.rollout_active:
            model = self.config.baseline_model_id
        elif random.random() < self.config.rollout_percentage:
            model = self.config.new_model_id
        else:
            model = self.config.baseline_model_id

        result = await call_model_tracked(model, prompt)

        # Check if we should roll back
        if self._should_rollback():
            self.rollout_active = False
            logger.error(f"Rolling back from {self.config.new_model_id} to "
                        f"{self.config.baseline_model_id}")

        return result

    def _should_rollback(self) -> bool:
        """Check if new model is underperforming"""
        new_metrics = self.tracker.get_metrics(
            self.config.new_model_id, hours=1
        )
        baseline_metrics = self.tracker.get_metrics(
            self.config.baseline_model_id, hours=1
        )

        # Need minimum requests to make decision
        if new_metrics.get("total_requests", 0) < self.config.min_requests_before_decision:
            return False

        # Check success rate
        new_success = new_metrics.get("success_rate", 0)
        baseline_success = baseline_metrics.get("success_rate", 1)

        return new_success < (baseline_success * self.config.success_rate_threshold)

# Usage: Safe rollout of new model
rollout = GradualModelRollout(
    config=ModelRolloutConfig(
        new_model_id="gpt-4-turbo-2024-04-09",
        baseline_model_id="gpt-4-0125-preview",
        rollout_percentage=0.1,  # Start with 10% traffic
        min_requests_before_decision=100,
        success_rate_threshold=0.95,  # Rollback if <95% of baseline
    ),
    tracker=tracker,
)

response = await rollout.call_with_gradual_rollout(prompt)
```

**Bad:**
```python
# Switch all traffic immediately without validation
def upgrade_model():
    global CURRENT_MODEL
    CURRENT_MODEL = "gpt-4-turbo-2024-04-09"  # Hope it works!

# No gradual rollout
# No performance comparison
# No automatic rollback
# If new model is worse, ALL users affected immediately
```

**Why It Matters:** The bad example causes full outages when new models have issues. The good example catches problems when they affect only 10% of traffic and automatically rolls back before most users are impacted.

### Example 5: Model Deprecation Handling

**Good:**
```python
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class ModelLifecycle:
    model_id: str
    status: Literal["active", "deprecated", "retired"]
    deprecated_date: datetime | None
    retirement_date: datetime | None
    replacement_model_id: str | None

class ModelLifecycleManager:
    def __init__(self):
        self.models = {
            "gpt-3.5-turbo-0613": ModelLifecycle(
                model_id="gpt-3.5-turbo-0613",
                status="deprecated",
                deprecated_date=datetime(2024, 1, 1),
                retirement_date=datetime(2024, 6, 1),
                replacement_model_id="gpt-3.5-turbo-0125",
            ),
            "gpt-3.5-turbo-0125": ModelLifecycle(
                model_id="gpt-3.5-turbo-0125",
                status="active",
                deprecated_date=None,
                retirement_date=None,
                replacement_model_id=None,
            ),
        }

    def check_model_status(self, model_id: str) -> tuple[bool, str]:
        """Check if model is usable, return status message"""
        lifecycle = self.models.get(model_id)
        if not lifecycle:
            return False, f"Unknown model: {model_id}"

        if lifecycle.status == "retired":
            return False, f"Model {model_id} is retired, use {lifecycle.replacement_model_id}"

        if lifecycle.status == "deprecated":
            days_until_retirement = (lifecycle.retirement_date - now()).days
            if days_until_retirement < 30:
                logger.warning(
                    f"Model {model_id} will be retired in {days_until_retirement} days. "
                    f"Migrate to {lifecycle.replacement_model_id}"
                )
            return True, f"Model deprecated, migrate to {lifecycle.replacement_model_id}"

        return True, "Model active"

    def get_active_model(self, requested_model: str) -> str:
        """Get active model, substituting deprecated models"""
        is_usable, message = self.check_model_status(requested_model)

        if not is_usable:
            lifecycle = self.models[requested_model]
            if lifecycle.replacement_model_id:
                logger.info(f"Substituting {lifecycle.replacement_model_id} for {requested_model}")
                return lifecycle.replacement_model_id
            else:
                raise ModelRetiredError(message)

        return requested_model

# Usage
lifecycle_manager = ModelLifecycleManager()

def call_model_with_lifecycle(model_id: str, prompt: str) -> str:
    """Call model with automatic handling of deprecated models"""
    active_model = lifecycle_manager.get_active_model(model_id)
    return call_model(active_model, prompt)
```

**Bad:**
```python
# Hard-coded model with no deprecation awareness
def generate_text(prompt: str):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",  # This model was retired!
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content

# System breaks completely when model is retired
# No warning before retirement
# No automatic migration to replacement
# No visibility into which models are at risk
```

**Why It Matters:** Model providers regularly deprecate and retire models. The bad example will experience complete system failure when the model is retired. The good example automatically migrates to replacement models and warns you weeks in advance.

## Related Principles

- **[Principle #18 - Observable Everything](18-observable-everything.md)** - Model performance tracking requires comprehensive observability of model calls, costs, latencies, and outcomes. You can't manage what you can't measure.

- **[Principle #19 - AI Performance Testing](19-ai-performance-testing.md)** - Model upgrades need performance validation before rollout. Testing frameworks must compare new models against baseline models across multiple dimensions.

- **[Principle #39 - Cost Transparency](39-cost-transparency.md)** - Model lifecycle management must track costs per model to enable cost-optimized model selection. Without cost visibility, you can't make intelligent model routing decisions.

- **[Principle #34 - Contract-Based AI Integration](../technology/34-contract-based-ai-integration.md)** - Model substitution requires stable contracts between application code and model interfaces. Contract testing validates that replacement models honor expected behaviors.

- **[Principle #33 - Graceful Degradation](../technology/33-graceful-degradation.md)** - Fallback chains and multi-model strategies implement graceful degradation when primary models fail or are unavailable.

- **[Principle #17 - Fast Feedback Loops](17-fast-feedback-loops.md)** - Model performance tracking provides fast feedback on quality degradation, allowing rapid response to issues before they affect many users.

## Common Pitfalls

1. **Using Unversioned Model Names**: Referring to models as "gpt-4" or "claude-3" without explicit versions causes unpredictable behavior when providers update what these aliases point to.
   - Example: Code using "gpt-4" suddenly behaves differently when OpenAI updates the alias to point to a new model version.
   - Impact: Silent behavior changes, inability to reproduce outputs, failed regression tests, production incidents.

2. **No Cost Tracking Per Model**: Running LLM operations without tracking cost per model prevents cost optimization and leads to budget overruns.
   - Example: Accidentally routing all traffic to GPT-4 instead of GPT-3.5 for simple tasks, increasing costs by 20x.
   - Impact: Unexpected $50K/month bills, emergency budget requests, forced service degradation.

3. **Immediate Full Rollout of New Models**: Switching 100% of traffic to a new model version without gradual rollout risks catastrophic failure.
   - Example: New model version has higher error rate but you only discover this after all users are affected.
   - Impact: Complete service outage, degraded user experience, emergency rollback, customer churn.

4. **No Performance Baseline**: Upgrading models without establishing baseline performance metrics makes it impossible to detect degradation.
   - Example: New model is 30% slower but you don't notice because you weren't tracking latency.
   - Impact: Gradual performance degradation, user complaints, inability to diagnose issues.

5. **Single Model Dependency**: Relying on a single model with no fallback creates single point of failure.
   - Example: Primary model provider has outage and your entire system stops working.
   - Impact: Complete service unavailability, revenue loss, SLA violations.

6. **Ignoring Model Deprecation Warnings**: Not monitoring model lifecycle announcements leads to sudden breakage when models are retired.
   - Example: Model is deprecated, you ignore warnings, then it's retired and your system fails completely.
   - Impact: Emergency incident response, rushed migration under pressure, potential data loss.

7. **No Model Selection Strategy**: Always using the most expensive model wastes money on tasks that cheaper models handle well.
   - Example: Using GPT-4 for simple yes/no classification when GPT-3.5 would work fine.
   - Impact: 10-20x higher costs than necessary, budget exhaustion, service cuts.

## Tools & Frameworks

### Model Management Platforms
- **LangSmith**: Comprehensive LLM observability with model performance tracking, cost analysis, and trace debugging
- **Weights & Biases**: Experiment tracking for model comparison, A/B testing results, and performance metrics
- **MLflow**: Model registry, versioning, and lifecycle management with deployment tracking

### Observability Tools
- **OpenTelemetry**: Distributed tracing for LLM calls with custom spans for model invocations
- **Datadog LLM Observability**: Real-time monitoring of LLM costs, latencies, and error rates
- **Prometheus + Grafana**: Time-series metrics for model performance with custom dashboards

### Cost Management
- **OpenAI Usage Dashboard**: Built-in cost tracking per model and API key
- **Anthropic Console**: Cost monitoring and usage analytics for Claude models
- **CloudZero**: Multi-provider LLM cost allocation and optimization

### Testing Frameworks
- **LangChain Evaluation**: Framework for comparing model outputs against golden datasets
- **Promptfoo**: Model comparison and regression testing for prompt changes
- **pytest with custom fixtures**: Test harnesses for validating model upgrades

### Deployment Tools
- **LaunchDarkly**: Feature flags for gradual model rollouts and A/B testing
- **Split.io**: Experimentation platform for model selection strategies
- **Optimizely**: A/B testing for model performance comparison

## Implementation Checklist

When implementing this principle, ensure:

- [ ] All model references use explicit version identifiers (e.g., "gpt-4-0125-preview" not "gpt-4")
- [ ] Model configuration is centralized and version-controlled
- [ ] Performance metrics (latency, cost, success rate) are tracked for every model call
- [ ] Cost per model is calculated and monitored against budgets
- [ ] Model selection logic considers task complexity, cost constraints, and quality requirements
- [ ] Fallback chains are configured with at least 2-3 model alternatives
- [ ] New model rollouts use gradual traffic shifting (10% -> 50% -> 100%)
- [ ] Performance baselines exist for all models before upgrades
- [ ] Automated rollback triggers are defined based on success rate thresholds
- [ ] Model deprecation dates are tracked and monitored
- [ ] Replacement models are tested before original models are retired
- [ ] Documentation explains which model to use for which task types

## Metadata

**Category**: Governance
**Principle Number**: 43
**Related Patterns**: Circuit Breaker, Fallback Pattern, Canary Deployment, Blue-Green Deployment, Feature Flags, A/B Testing
**Prerequisites**: Observability infrastructure, cost tracking, model provider API access, performance testing framework
**Difficulty**: High
**Impact**: High

---

**Status**: Complete
**Last Updated**: 2025-09-30
**Version**: 1.0