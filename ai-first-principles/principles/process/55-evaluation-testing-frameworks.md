# Principle #55 - Evaluation & Testing Frameworks

## Plain-Language Definition

Evaluation and testing frameworks systematically measure AI system quality through quantifiable metrics, automated test suites, and human validation loops. These frameworks ensure prompts, models, and agents perform consistently, safely, and effectively before deployment.

## Why This Matters for AI-First Development

AI systems introduce unique challenges that traditional software testing doesn't address. A prompt that works 90% of the time might fail catastrophically on the remaining 10%. A model that performs well in testing might degrade when deployed due to distribution shift. An agent that handles happy paths perfectly might spiral into expensive loops on edge cases.

Traditional software has deterministic behavior: the same input always produces the same output. AI systems are probabilistic: outputs vary, quality fluctuates, and failure modes are often subtle. This fundamental difference demands evaluation frameworks specifically designed for AI:

1. **Preventing silent degradation**: Without continuous evaluation, AI systems degrade invisibly as prompts drift, data distributions shift, or models update. Evaluation frameworks catch these regressions before they reach users, maintaining quality over time.

2. **Enabling confident iteration**: Teams hesitate to improve prompts or agents without knowing whether changes help or hurt. Rigorous evaluation frameworks provide the confidence to iterate rapidly, measuring improvement objectively rather than relying on anecdotal evidence.

3. **Balancing cost and quality**: AI systems often trade cost (tokens, latency, compute) for quality (accuracy, completeness, safety). Evaluation frameworks quantify these tradeoffs, enabling informed decisions about where to optimize and where premium performance justifies premium cost.

Without evaluation frameworks, AI-first development becomes guesswork. Teams deploy prompts based on a few manual tests, discover failures in production, and struggle to identify root causes. Changes that seem to help might actually hurt on unseen inputs. Costs spiral as inefficient prompts waste tokens on every request. The system becomes fragile, expensive, and unreliable—all problems that rigorous evaluation would prevent.

## Implementation Approaches

### 1. **Golden Dataset Evaluation**

Create a curated dataset of inputs with expected outputs or quality scores. Run the AI system against this dataset regularly to track performance over time:

```python
# Golden dataset with diverse test cases
golden_dataset = [
    {
        "input": "Summarize this technical article about quantum computing...",
        "expected_output": "A concise summary that captures key points without jargon",
        "quality_criteria": ["accuracy", "conciseness", "clarity"],
        "difficulty": "medium"
    },
    {
        "input": "Extract structured data from this receipt image",
        "expected_output": {"total": 42.50, "date": "2024-01-15", "items": [...]},
        "quality_criteria": ["accuracy", "completeness"],
        "difficulty": "hard"
    }
]

def evaluate_prompt_on_golden_dataset(prompt_template, model="claude-3-5-sonnet"):
    """Evaluate prompt performance against golden dataset"""
    results = []
    for test_case in golden_dataset:
        # Generate response
        response = llm_call(prompt_template.format(test_case["input"]), model)

        # Score quality
        quality_score = score_response(
            response,
            test_case["expected_output"],
            test_case["quality_criteria"]
        )

        results.append({
            "input": test_case["input"],
            "response": response,
            "score": quality_score,
            "difficulty": test_case["difficulty"]
        })

    # Aggregate metrics
    return {
        "avg_score": mean([r["score"] for r in results]),
        "score_by_difficulty": group_by(results, "difficulty"),
        "failures": [r for r in results if r["score"] < 0.7]
    }
```

**When to use**: Essential for all AI systems. Build this first before deploying any prompt or agent. Expand continuously as you discover new failure modes.

**Success looks like**: Automated tests run on every prompt change, catching regressions before deployment. Team confidently iterates because metrics show clear improvement or degradation.

### 2. **LLM-as-Judge Evaluation**

Use a strong LLM to evaluate outputs from your production system, providing scalable assessment of quality dimensions that are hard to measure programmatically:

```python
def llm_judge_evaluation(response, input_context, criteria):
    """Use LLM to judge response quality on specific criteria"""
    judge_prompt = f"""
    Evaluate the following AI response based on these criteria: {criteria}

    INPUT: {input_context}
    RESPONSE: {response}

    For each criterion, provide:
    1. Score (0-10)
    2. Brief justification
    3. Specific examples of strengths or weaknesses

    Return JSON with scores and reasoning.
    """

    evaluation = llm_call(judge_prompt, model="claude-3-5-sonnet", temperature=0)
    return parse_llm_json(evaluation)

# Example evaluation criteria
criteria = [
    "Accuracy: Does the response correctly answer the question?",
    "Completeness: Does it address all aspects of the request?",
    "Clarity: Is it easy to understand without ambiguity?",
    "Safety: Does it avoid harmful or biased content?",
    "Tone: Is the tone appropriate for the context?"
]

# Run evaluation
result = llm_judge_evaluation(
    response="The capital of France is Paris, known for the Eiffel Tower...",
    input_context="What is the capital of France?",
    criteria=criteria
)

# result = {
#     "accuracy": {"score": 10, "reasoning": "Correctly identifies Paris"},
#     "completeness": {"score": 9, "reasoning": "Answers question fully, adds context"},
#     "clarity": {"score": 10, "reasoning": "Clear and unambiguous"},
#     "safety": {"score": 10, "reasoning": "No harmful content"},
#     "tone": {"score": 8, "reasoning": "Appropriate but could be more concise"}
# }
```

**When to use**: When evaluating subjective dimensions like tone, helpfulness, or creativity that are difficult to score programmatically. Essential for production systems with high quality requirements.

**Success looks like**: Scalable evaluation of thousands of outputs without manual review. Quality scores correlate highly with human judgement (validate with human evaluators on a subset).

### 3. **Regression Testing for Prompts**

Track specific known failure cases and ensure fixes don't regress. Every discovered bug becomes a permanent test case:

```python
class PromptRegressionTest:
    """Test suite for tracking prompt regression cases"""

    def __init__(self, test_db_path="regression_tests.json"):
        self.tests = load_json(test_db_path)

    def add_regression_test(self, name, input_text, issue_description, expected_behavior):
        """Add a new regression test from a discovered failure"""
        test_case = {
            "name": name,
            "input": input_text,
            "issue": issue_description,
            "expected": expected_behavior,
            "added_date": datetime.now().isoformat(),
            "status": "active"
        }
        self.tests.append(test_case)
        save_json(self.test_db_path, self.tests)

    def run_regression_tests(self, prompt_fn):
        """Run all regression tests against current prompt"""
        results = []
        for test in self.tests:
            if test["status"] != "active":
                continue

            response = prompt_fn(test["input"])
            passed = check_behavior(response, test["expected"])

            results.append({
                "name": test["name"],
                "passed": passed,
                "response": response,
                "expected": test["expected"]
            })

        return {
            "total": len(results),
            "passed": sum(r["passed"] for r in results),
            "failed": [r for r in results if not r["passed"]]
        }

# Example usage
regression_suite = PromptRegressionTest()

# Add test when bug is discovered
regression_suite.add_regression_test(
    name="special_chars_in_query",
    input_text="Search for items with & and % characters",
    issue_description="Bug #4271: Special characters caused search to crash",
    expected_behavior="Returns search results without crashing"
)

# Run tests on every prompt change
results = regression_suite.run_regression_tests(my_search_prompt)
if results["failed"]:
    print(f"FAILED: {len(results['failed'])} regression tests failed!")
    for failure in results["failed"]:
        print(f"  - {failure['name']}: {failure['issue']}")
```

**When to use**: Essential for production systems. Start collecting regression tests from day one. Every bug fix should include a regression test.

**Success looks like**: Zero tolerance for reintroducing fixed bugs. Test suite grows with every discovered issue. Team confidently refactors prompts knowing regressions will be caught.

### 4. **Property-Based Testing**

Test that certain properties always hold across randomly generated inputs, discovering edge cases humans wouldn't think to test:

```python
from hypothesis import given, strategies as st

@given(st.text(min_size=1, max_size=1000))
def test_summarization_always_shorter(input_text):
    """Property: Summaries should always be shorter than input"""
    summary = summarize_prompt(input_text)
    assert len(summary) < len(input_text), f"Summary longer than input!"

@given(st.lists(st.dictionaries(st.text(), st.integers()), min_size=1))
def test_extraction_preserves_count(input_records):
    """Property: Extraction should not lose records"""
    extracted = extract_structured_data(input_records)
    assert len(extracted) == len(input_records), "Lost records during extraction"

@given(st.text())
def test_translation_roundtrip_similarity(input_text):
    """Property: Translate to French and back should be similar"""
    french = translate_prompt(input_text, target="french")
    back_to_english = translate_prompt(french, target="english")
    similarity = semantic_similarity(input_text, back_to_english)
    assert similarity > 0.7, "Roundtrip translation lost too much meaning"

@given(st.integers(min_value=0, max_value=1000000))
def test_number_extraction_accuracy(number):
    """Property: Extracting numbers from text should be accurate"""
    text = f"The total cost is ${number:,}"
    extracted = extract_number_from_text(text)
    assert extracted == number, f"Expected {number}, got {extracted}"

# Run property-based tests
# Hypothesis will generate thousands of random inputs and verify properties hold
pytest.main([__file__, "-v"])
```

**When to use**: For AI systems with clear invariants (summaries are shorter, extractions preserve structure, classifications return valid categories). Complements example-based tests with exhaustive edge case discovery.

**Success looks like**: Property tests find edge cases humans miss. System behavior is verified across thousands of random inputs, not just cherry-picked examples.

### 5. **A/B Testing for Prompt Optimization**

Compare prompt variants in production with real traffic to measure actual impact on user outcomes:

```python
class PromptABTest:
    """Framework for A/B testing prompt variants in production"""

    def __init__(self, control_prompt, treatment_prompt, split_ratio=0.5):
        self.control = control_prompt
        self.treatment = treatment_prompt
        self.split_ratio = split_ratio
        self.results = {"control": [], "treatment": []}

    def run_variant(self, user_input, user_id):
        """Run appropriate variant based on user assignment"""
        variant = "treatment" if hash(user_id) % 100 < (self.split_ratio * 100) else "control"
        prompt = self.treatment if variant == "treatment" else self.control

        start_time = time.time()
        response = prompt(user_input)
        latency = time.time() - start_time

        self.results[variant].append({
            "user_id": user_id,
            "input": user_input,
            "response": response,
            "latency": latency,
            "timestamp": datetime.now().isoformat()
        })

        return response, variant

    def analyze_results(self, success_metric_fn):
        """Analyze A/B test results with statistical significance"""
        control_metrics = [success_metric_fn(r) for r in self.results["control"]]
        treatment_metrics = [success_metric_fn(r) for r in self.results["treatment"]]

        # Calculate means and confidence intervals
        control_mean = mean(control_metrics)
        treatment_mean = mean(treatment_metrics)

        # Statistical significance test
        p_value = ttest_ind(control_metrics, treatment_metrics).pvalue

        return {
            "control": {
                "mean": control_mean,
                "sample_size": len(control_metrics),
                "std": stdev(control_metrics)
            },
            "treatment": {
                "mean": treatment_mean,
                "sample_size": len(treatment_metrics),
                "std": stdev(treatment_metrics)
            },
            "lift": ((treatment_mean - control_mean) / control_mean) * 100,
            "p_value": p_value,
            "significant": p_value < 0.05
        }

# Example: Test two summarization prompts
ab_test = PromptABTest(
    control_prompt=summarize_v1,
    treatment_prompt=summarize_v2,
    split_ratio=0.5
)

# Run on production traffic
for user_request in production_traffic:
    response, variant = ab_test.run_variant(user_request.input, user_request.user_id)
    send_response(response)

# Analyze after 1000+ samples
results = ab_test.analyze_results(lambda r: user_satisfaction_score(r))
if results["significant"] and results["lift"] > 5:
    print(f"Treatment wins! {results['lift']:.1f}% improvement")
    deploy_treatment_prompt()
```

**When to use**: When optimizing production systems with measurable user outcomes (satisfaction, task completion, conversion). Requires sufficient traffic for statistical significance.

**Success looks like**: Data-driven decisions about prompt changes. Clear evidence of improvement before full rollout. No surprises or regressions in production.

### 6. **Human-in-the-Loop Validation**

Incorporate human review at strategic checkpoints, focusing human effort on high-value, high-risk, or ambiguous cases:

```python
class HumanValidationLoop:
    """Framework for strategic human validation of AI outputs"""

    def __init__(self, confidence_threshold=0.8):
        self.confidence_threshold = confidence_threshold
        self.validation_queue = []
        self.human_feedback = []

    def needs_human_validation(self, response, confidence_score):
        """Determine if response needs human review"""
        # Send to humans if:
        # 1. Low confidence
        # 2. High-stakes decision
        # 3. Random sampling for calibration
        return (
            confidence_score < self.confidence_threshold or
            is_high_stakes(response) or
            random.random() < 0.05  # 5% random sampling
        )

    def add_to_validation_queue(self, response, context):
        """Queue response for human validation"""
        self.validation_queue.append({
            "response": response,
            "context": context,
            "queued_at": datetime.now(),
            "priority": calculate_priority(response, context)
        })

    def collect_human_feedback(self, response_id, feedback):
        """Collect and store human feedback"""
        self.human_feedback.append({
            "response_id": response_id,
            "feedback": feedback,
            "timestamp": datetime.now()
        })

        # Use feedback to improve system
        self.update_golden_dataset(feedback)
        self.retrain_confidence_model(feedback)

    def get_validation_metrics(self):
        """Analyze human validation patterns"""
        return {
            "queue_size": len(self.validation_queue),
            "avg_review_time": calculate_avg_review_time(),
            "agreement_rate": calculate_human_llm_agreement(),
            "feedback_incorporated": len(self.human_feedback)
        }

# Example usage
validator = HumanValidationLoop(confidence_threshold=0.8)

def process_request_with_validation(user_input):
    """Process request with optional human validation"""
    response, confidence = ai_system(user_input)

    if validator.needs_human_validation(response, confidence):
        # Add to validation queue
        validator.add_to_validation_queue(response, user_input)

        # For high-stakes, block on human review
        if is_high_stakes(response):
            human_approval = wait_for_human_review(response)
            if not human_approval:
                response = generate_safer_fallback(user_input)

    return response
```

**When to use**: For high-stakes applications (medical, legal, financial), when building initial training data, or when calibrating automated evaluation systems.

**Success looks like**: Human reviewers focus on genuinely ambiguous or high-risk cases, not routine outputs. Feedback loop improves automated systems over time, reducing human review burden.

## Good Examples vs Bad Examples

### Example 1: Comprehensive Evaluation Suite

**Good:**
```python
# evaluation_suite.py - Comprehensive multi-metric evaluation
class SummarizationEvaluator:
    """Comprehensive evaluation for summarization system"""

    def __init__(self, golden_dataset, regression_tests):
        self.golden_dataset = golden_dataset
        self.regression_tests = regression_tests

    def evaluate_comprehensive(self, summarize_fn):
        """Run all evaluation metrics"""
        results = {
            "accuracy": self.eval_accuracy(summarize_fn),
            "token_efficiency": self.eval_token_usage(summarize_fn),
            "latency": self.eval_latency(summarize_fn),
            "quality": self.eval_llm_judge_quality(summarize_fn),
            "regressions": self.eval_regressions(summarize_fn),
            "edge_cases": self.eval_property_tests(summarize_fn)
        }

        # Aggregate score with weights
        overall_score = (
            0.40 * results["accuracy"] +
            0.20 * results["quality"] +
            0.15 * results["token_efficiency"] +
            0.15 * results["latency"] +
            0.10 * results["regressions"]
        )

        return {
            "overall_score": overall_score,
            "breakdown": results,
            "recommendation": self.generate_recommendation(results)
        }

    def eval_accuracy(self, summarize_fn):
        """Evaluate against golden dataset"""
        correct = 0
        for test_case in self.golden_dataset:
            summary = summarize_fn(test_case["input"])
            if semantic_similarity(summary, test_case["expected"]) > 0.85:
                correct += 1
        return correct / len(self.golden_dataset)

    def eval_llm_judge_quality(self, summarize_fn):
        """Use LLM-as-judge for quality assessment"""
        scores = []
        for test_case in self.golden_dataset[:50]:  # Sample
            summary = summarize_fn(test_case["input"])
            quality_score = llm_judge_evaluation(
                response=summary,
                input_context=test_case["input"],
                criteria=["accuracy", "conciseness", "clarity"]
            )
            scores.append(mean(quality_score.values()))
        return mean(scores)

# Run comprehensive evaluation before deploying
evaluator = SummarizationEvaluator(golden_dataset, regression_tests)
results = evaluator.evaluate_comprehensive(new_summarize_prompt)

if results["overall_score"] > 0.85 and results["regressions"] == 1.0:
    print("✓ All checks passed - safe to deploy")
    deploy_to_production(new_summarize_prompt)
else:
    print(f"✗ Score too low: {results['overall_score']:.2f}")
    print(f"Issues: {results['recommendation']}")
```

**Bad:**
```python
# bad_evaluation.py - Minimal, unreliable evaluation
def test_summarization():
    """Basic test with cherry-picked example"""
    summary = summarize("This is a test article about AI...")
    assert len(summary) > 0  # Just checks it didn't crash
    print("Test passed!")

# No golden dataset
# No regression tests
# No edge case testing
# No quality metrics
# No performance measurement
# Manual inspection only
```

**Why It Matters:** Comprehensive evaluation catches issues before production. The good example measures multiple dimensions (accuracy, quality, efficiency, regressions) with weighted scores. The bad example only checks that code runs without crashing, missing quality issues, regressions, and edge cases that will surface in production.

### Example 2: Regression Test Discipline

**Good:**
```python
# regression_tracking.py - Systematic regression prevention
class RegressionTestSuite:
    """Track and prevent regressions from returning"""

    def add_bug_as_test(self, bug_id, description, input_case, failure_mode, fix_verification):
        """Convert every bug into a permanent test"""
        test = {
            "bug_id": bug_id,
            "description": description,
            "input": input_case,
            "failure_mode": failure_mode,
            "verification": fix_verification,
            "added": datetime.now().isoformat()
        }
        self.tests.append(test)
        save_json("regression_tests.json", self.tests)

    def run_all_regression_tests(self, system_fn):
        """Verify all historical bugs remain fixed"""
        failures = []
        for test in self.tests:
            try:
                result = system_fn(test["input"])
                if not test["verification"](result):
                    failures.append({
                        "bug_id": test["bug_id"],
                        "description": test["description"],
                        "result": result
                    })
            except Exception as e:
                failures.append({
                    "bug_id": test["bug_id"],
                    "description": test["description"],
                    "error": str(e)
                })

        return {
            "total_tests": len(self.tests),
            "passed": len(self.tests) - len(failures),
            "failures": failures
        }

# Example: Bug discovered in production
suite = RegressionTestSuite()

suite.add_bug_as_test(
    bug_id="BUG-4271",
    description="Special characters (&, %) in search query caused crash",
    input_case="Search for items with & and % characters",
    failure_mode="ValueError: invalid syntax",
    fix_verification=lambda result: result is not None and len(result) >= 0
)

# Every deployment runs all regression tests
regression_results = suite.run_all_regression_tests(search_system)
if regression_results["failures"]:
    print(f"DEPLOYMENT BLOCKED: {len(regression_results['failures'])} regressions")
    for failure in regression_results["failures"]:
        print(f"  {failure['bug_id']}: {failure['description']}")
    sys.exit(1)
```

**Bad:**
```python
# bad_regression.py - No regression prevention
def fix_bug_4271():
    """Fixed bug where special characters crashed search"""
    # Fixed the code...
    # But no test added to prevent recurrence
    pass

# Later, during refactoring...
def refactor_search_system():
    """Refactor search for better performance"""
    # Accidentally reintroduces bug #4271
    # No test catches it
    # Bug returns to production
    pass
```

**Why It Matters:** Without regression tests, fixed bugs return during refactoring. The good example creates a permanent test for every bug, preventing recurrence. The bad example fixes bugs in code but doesn't prevent them from coming back, wasting time repeatedly fixing the same issues.

### Example 3: Property-Based Edge Case Discovery

**Good:**
```python
# property_tests.py - Systematic edge case discovery
from hypothesis import given, strategies as st

class TranslationPropertyTests:
    """Property-based tests discover edge cases automatically"""

    @given(st.text(min_size=1, max_size=500))
    def test_translation_preserves_meaning(self, text):
        """Property: Translating and back should preserve meaning"""
        french = translate(text, target="french")
        back = translate(french, target="english")
        similarity = semantic_similarity(text, back)
        assert similarity > 0.7, f"Lost meaning: {text} -> {back}"

    @given(st.lists(st.text(min_size=1), min_size=1, max_size=10))
    def test_batch_translation_equals_individual(self, texts):
        """Property: Batch translation should match individual"""
        batch_results = translate_batch(texts, target="french")
        individual_results = [translate(t, target="french") for t in texts]
        assert batch_results == individual_results

    @given(st.text(alphabet=st.characters(blacklist_categories=['Cs', 'Cc'])))
    def test_translation_handles_unicode(self, unicode_text):
        """Property: Should handle any Unicode without crashing"""
        try:
            result = translate(unicode_text, target="french")
            assert result is not None
        except Exception as e:
            pytest.fail(f"Crashed on Unicode input: {e}")

    @given(st.integers(min_value=0, max_value=1000))
    def test_translation_cost_linear(self, num_chars):
        """Property: Cost should scale linearly with length"""
        text = "a" * num_chars
        tokens = count_tokens(translate(text, target="french"))
        # Cost should be approximately linear (within 2x factor)
        assert tokens < num_chars * 2

# Run property tests - Hypothesis generates thousands of inputs
pytest.main(["-v", "property_tests.py"])

# Example output:
# test_translation_preserves_meaning - Falsifying example: text='!@#$%^&*()'
# test_batch_translation_equals_individual - Passed 1000 examples
# test_translation_handles_unicode - Falsifying example: unicode_text='👨‍👩‍👧‍👦'
# test_translation_cost_linear - Passed 1000 examples
```

**Bad:**
```python
# bad_property_tests.py - Only tests cherry-picked examples
def test_translation():
    """Test a single example"""
    result = translate("Hello world", target="french")
    assert result == "Bonjour le monde"

def test_translation_batch():
    """Test one batch example"""
    results = translate_batch(["Hello", "Goodbye"], target="french")
    assert len(results) == 2

# Missing edge cases:
# - Special characters
# - Unicode/emoji
# - Empty strings
# - Very long text
# - Numbers and punctuation
# - Mixed languages
```

**Why It Matters:** Property-based tests explore thousands of edge cases automatically, discovering failures humans wouldn't think to test. The good example found that special characters and emoji crashed the system—inputs that manual testing missed. The bad example only tests happy paths with cherry-picked inputs.

### Example 4: LLM-as-Judge with Calibration

**Good:**
```python
# llm_judge_calibrated.py - Calibrated LLM-as-judge evaluation
class CalibratedLLMJudge:
    """LLM-as-judge with human calibration for reliability"""

    def __init__(self):
        self.human_agreements = []
        self.calibration_bias = 0.0

    def judge_quality(self, response, input_context, criteria):
        """Judge response quality with calibrated LLM"""
        judge_prompt = f"""
        Evaluate this AI response on: {criteria}

        INPUT: {input_context}
        RESPONSE: {response}

        For each criterion, provide:
        1. Score (0-10)
        2. Specific evidence from response
        3. What would make it better

        Be critical and specific. A score of 7-8 is good, 9-10 is exceptional.
        Return JSON: {{"criterion": {{"score": X, "evidence": "...", "improvement": "..."}}}}
        """

        raw_scores = llm_call(judge_prompt, model="claude-3-5-sonnet", temperature=0)
        scores = parse_llm_json(raw_scores)

        # Apply calibration bias if available
        if self.calibration_bias:
            for criterion in scores:
                scores[criterion]["score"] += self.calibration_bias
                scores[criterion]["score"] = max(0, min(10, scores[criterion]["score"]))

        return scores

    def calibrate_with_human_judgments(self, test_cases, human_scores):
        """Calibrate LLM judge against human judgments"""
        llm_scores = []
        for test_case in test_cases:
            scores = self.judge_quality(
                test_case["response"],
                test_case["input"],
                test_case["criteria"]
            )
            avg_score = mean([s["score"] for s in scores.values()])
            llm_scores.append(avg_score)

        # Calculate systematic bias
        differences = [h - l for h, l in zip(human_scores, llm_scores)]
        self.calibration_bias = mean(differences)

        # Calculate agreement rate
        agreement = sum(1 for h, l in zip(human_scores, llm_scores)
                       if abs(h - l) <= 1) / len(human_scores)

        return {
            "calibration_bias": self.calibration_bias,
            "agreement_rate": agreement,
            "correlation": correlation(human_scores, llm_scores)
        }

# Example usage
judge = CalibratedLLMJudge()

# Calibrate with 100 human-labeled examples
calibration_results = judge.calibrate_with_human_judgments(
    human_labeled_test_cases,
    human_scores
)

print(f"Agreement with humans: {calibration_results['agreement_rate']:.1%}")
print(f"Calibration bias: {calibration_results['calibration_bias']:.2f}")

# Now use calibrated judge at scale
for response in production_outputs:
    quality_scores = judge.judge_quality(response, input_ctx, criteria)
```

**Bad:**
```python
# bad_llm_judge.py - Uncalibrated LLM-as-judge
def llm_judge(response):
    """Use LLM to judge quality"""
    prompt = f"Rate this response 1-10: {response}"
    score = llm_call(prompt)
    return int(score)

# No calibration against human judgments
# No verification that LLM scores correlate with quality
# No criteria specified
# No evidence or reasoning provided
# No systematic bias correction
```

**Why It Matters:** Uncalibrated LLM judges may systematically over-score or under-score, or their judgments may not correlate with actual quality. The good example calibrates against human judgments, corrects systematic bias, and requires evidence for scores. The bad example blindly trusts LLM scores without validation.

### Example 5: A/B Testing with Statistical Rigor

**Good:**
```python
# ab_testing_rigorous.py - Statistically rigorous A/B testing
class StatisticalABTest:
    """A/B test with proper statistical analysis"""

    def __init__(self, control, treatment, min_sample_size=1000):
        self.control = control
        self.treatment = treatment
        self.min_sample_size = min_sample_size
        self.results = {"control": [], "treatment": []}

    def run_test(self, user_input, user_id):
        """Run appropriate variant"""
        variant = "treatment" if hash(user_id) % 2 == 0 else "control"
        prompt = self.treatment if variant == "treatment" else self.control

        response = prompt(user_input)
        self.results[variant].append({
            "user_id": user_id,
            "response": response,
            "timestamp": datetime.now()
        })

        return response

    def analyze_with_stats(self, metric_fn):
        """Statistical analysis with confidence intervals"""
        control_metrics = [metric_fn(r) for r in self.results["control"]]
        treatment_metrics = [metric_fn(r) for r in self.results["treatment"]]

        # Check minimum sample size
        if len(control_metrics) < self.min_sample_size:
            return {"status": "insufficient_data", "needed": self.min_sample_size}

        # Calculate statistics
        control_mean = mean(control_metrics)
        treatment_mean = mean(treatment_metrics)

        # Statistical significance test
        t_stat, p_value = ttest_ind(control_metrics, treatment_metrics)

        # Effect size (Cohen's d)
        pooled_std = sqrt(
            (stdev(control_metrics)**2 + stdev(treatment_metrics)**2) / 2
        )
        cohens_d = (treatment_mean - control_mean) / pooled_std

        # Confidence interval for lift
        lift = ((treatment_mean - control_mean) / control_mean) * 100
        se_lift = sqrt(
            (stdev(control_metrics)**2 / len(control_metrics)) +
            (stdev(treatment_metrics)**2 / len(treatment_metrics))
        ) / control_mean * 100

        ci_lower = lift - 1.96 * se_lift
        ci_upper = lift + 1.96 * se_lift

        return {
            "status": "complete",
            "control_mean": control_mean,
            "treatment_mean": treatment_mean,
            "lift_pct": lift,
            "confidence_interval_95": (ci_lower, ci_upper),
            "p_value": p_value,
            "significant": p_value < 0.05,
            "effect_size": cohens_d,
            "recommendation": self.generate_recommendation(p_value, lift, cohens_d)
        }

    def generate_recommendation(self, p_value, lift, effect_size):
        """Generate deployment recommendation"""
        if p_value >= 0.05:
            return "No significant difference - keep control"
        elif lift > 0 and effect_size > 0.2:
            return f"Deploy treatment - significant improvement ({lift:.1f}%)"
        elif lift < 0 and abs(effect_size) > 0.2:
            return f"Keep control - treatment significantly worse ({lift:.1f}%)"
        else:
            return "Difference too small to matter - keep control"

# Example usage
ab_test = StatisticalABTest(
    control=summarize_v1,
    treatment=summarize_v2,
    min_sample_size=1000
)

# Collect data from production
for request in production_stream:
    ab_test.run_test(request.input, request.user_id)

    # Check if we can analyze yet
    if len(ab_test.results["control"]) % 100 == 0:
        analysis = ab_test.analyze_with_stats(user_satisfaction_score)
        if analysis["status"] == "complete":
            print(f"Results: {analysis['recommendation']}")
            if analysis["significant"] and analysis["lift_pct"] > 5:
                deploy_treatment()
            break
```

**Bad:**
```python
# bad_ab_test.py - No statistical rigor
def ab_test_bad(control, treatment):
    """Test with insufficient samples and no stats"""
    # Run on 10 users (way too few!)
    control_scores = [control(f"test_{i}") for i in range(5)]
    treatment_scores = [treatment(f"test_{i}") for i in range(5)]

    # Simple average, no confidence interval, no significance test
    if mean(treatment_scores) > mean(control_scores):
        print("Treatment wins - deploying!")
        deploy(treatment)

    # Issues:
    # - Sample size too small (5 users)
    # - No statistical significance test
    # - No confidence intervals
    # - No effect size measurement
    # - No consideration of practical significance
```

**Why It Matters:** A/B tests without statistical rigor lead to false conclusions and wrong decisions. The good example requires sufficient sample size, tests significance, calculates confidence intervals, and measures effect size. The bad example draws conclusions from tiny samples without statistical validation, likely deploying changes that don't actually improve outcomes.

## Related Principles

- **[Principle #09 - Tests as Quality Gate](09-tests-as-quality-gate.md)** - Evaluation frameworks extend test-as-quality-gate thinking to AI systems, where behavioral validation requires probabilistic evaluation beyond deterministic tests.

- **[Principle #11 - Continuous Validation with Fast Feedback](11-continuous-validation-fast-feedback.md)** - Evaluation frameworks enable continuous validation by automating quality checks, providing fast feedback on prompt changes and model updates.

- **[Principle #04 - Explicit Human-AI Boundaries](../people/04-explicit-human-ai-boundaries.md)** - Human-in-the-loop validation defines clear boundaries where human judgment complements automated evaluation, focusing human effort where it adds most value.

- **[Principle #17 - Observable Behavior Over Implementation](17-observable-behavior-over-implementation.md)** - Evaluation frameworks focus on measuring observable outputs (quality, accuracy, cost) rather than internal model mechanics, aligning with behavior-first thinking.

- **[Principle #31 - Idempotency by Design](../technology/31-idempotency-by-design.md)** - Evaluation frameworks must produce consistent results when run repeatedly, requiring idempotent test execution and deterministic scoring where possible.

## Common Pitfalls

1. **Testing Only Happy Paths**: Evaluating with cherry-picked examples that show the system at its best, missing edge cases and failure modes that appear in production.
   - Example: Testing translation only with simple English sentences, not Unicode, special characters, or mixed languages.
   - Impact: System appears to work well in testing but fails frequently in production on inputs developers didn't anticipate.

2. **Insufficient Sample Sizes**: Drawing conclusions from too few test cases, leading to false confidence in system performance.
   - Example: Testing prompt with 10 examples, declaring it works, then discovering 30% failure rate in production with thousands of inputs.
   - Impact: Production deployment of prompts that perform much worse than testing suggested, requiring emergency rollbacks.

3. **No Regression Test Discipline**: Fixing bugs without adding tests to prevent their return, allowing same bugs to reappear during refactoring.
   - Example: Bug #4271 fixed in code, but no test added. Three months later, refactoring reintroduces the exact same bug.
   - Impact: Wasted time repeatedly fixing the same issues. Loss of confidence in system stability.

4. **Evaluation-Production Mismatch**: Testing on data that doesn't represent production distribution, leading to misleading quality metrics.
   - Example: Testing medical diagnosis system on textbook cases, but production sees messy, ambiguous real-world reports.
   - Impact: System that scores 95% in testing but only 60% in production because test data was too clean.

5. **No Cost/Latency Tracking**: Optimizing only for quality without measuring cost and latency, resulting in expensive or slow systems.
   - Example: Improving prompt accuracy from 90% to 92% by adding examples that triple token usage and double latency.
   - Impact: Production system becomes too expensive or slow, negating quality improvements. Need to roll back changes.

6. **Uncalibrated LLM-as-Judge**: Using LLM judgments without validating that they correlate with actual quality or human assessments.
   - Example: LLM judge consistently rates all outputs 8-9/10, providing no signal about actual quality differences.
   - Impact: False confidence in output quality. Unable to distinguish good from bad outputs. Evaluation becomes meaningless.

7. **Manual Evaluation at Scale**: Relying on human review for all outputs instead of automating evaluation where possible.
   - Example: Human reviewing every single response before deployment, creating bottleneck that prevents rapid iteration.
   - Impact: Slow iteration cycles. Human burnout. Inability to scale. Team can't experiment rapidly or deploy improvements quickly.

## Tools & Frameworks

### Evaluation Platforms
- **[OpenAI Evals](https://github.com/openai/evals)**: Framework for evaluating LLMs with built-in eval templates, metrics, and reporting. Supports custom evals and integration with CI/CD.
- **[PromptFoo](https://www.promptfoo.dev/)**: Testing framework specifically for prompts with A/B testing, regression tracking, and quality metrics. CLI and web interface.
- **[Weights & Biases Prompts](https://docs.wandb.ai/guides/prompts)**: Experiment tracking for prompt engineering with versioning, comparison, and visualization.
- **[LangSmith](https://www.langchain.com/langsmith)**: Debugging and testing platform for LLM applications with tracing, evaluation, and monitoring.

### LLM-as-Judge Tools
- **[RAGAS](https://docs.ragas.io/)**: Evaluation framework for RAG systems with metrics for faithfulness, relevance, and context quality.
- **[DeepEval](https://docs.confident-ai.com/)**: Open-source evaluation framework with LLM-based metrics for hallucination, toxicity, and quality.
- **[Patronus AI](https://www.patronus.ai/)**: Enterprise evaluation platform with pre-built judges for common quality dimensions.

### Property-Based Testing
- **[Hypothesis](https://hypothesis.readthedocs.io/)**: Python property-based testing library that generates edge cases automatically. Excellent for testing LLM invariants.
- **[Schemathesis](https://schemathesis.readthedocs.io/)**: API testing tool that generates test cases from OpenAPI specs. Useful for testing LLM API wrappers.

### Statistical Analysis
- **[SciPy](https://scipy.org/)**: Python library for statistical tests (t-tests, ANOVA, correlation). Essential for rigorous A/B testing.
- **[Statsmodels](https://www.statsmodels.org/)**: Statistical modeling and hypothesis testing. Use for power analysis and effect size calculations.
- **[Bayesian A/B Testing](https://github.com/facebookarchive/planout)**: Framework for Bayesian A/B testing with faster decision-making than frequentist methods.

### Monitoring & Observability
- **[Langfuse](https://langfuse.com/)**: Open-source observability for LLM applications with tracing, metrics, and user feedback collection.
- **[Helicone](https://www.helicone.ai/)**: LLM observability platform with cost tracking, latency monitoring, and quality metrics.
- **[Phoenix](https://docs.arize.com/phoenix)**: Open-source ML observability with support for LLM tracing and evaluation.

## Implementation Checklist

When implementing this principle, ensure:

- [ ] Golden dataset exists with diverse, representative test cases covering common inputs and edge cases
- [ ] Evaluation runs automatically on every prompt change, blocking deployment if quality degresses
- [ ] Multiple metrics tracked (accuracy, quality, cost, latency, user satisfaction) with defined thresholds
- [ ] Regression test suite captures every discovered bug, preventing recurrence
- [ ] Property-based tests verify system invariants across randomly generated inputs
- [ ] LLM-as-judge evaluation is calibrated against human judgments for reliability
- [ ] Statistical rigor applied to A/B tests with minimum sample sizes and significance testing
- [ ] Human-in-the-loop validation focuses on high-stakes, low-confidence, or ambiguous cases
- [ ] Evaluation-production parity ensured by testing on data matching production distribution
- [ ] Cost and latency tracked alongside quality to enable informed optimization tradeoffs
- [ ] Continuous monitoring detects quality degradation in production with alerting
- [ ] Evaluation results visible to entire team with clear pass/fail criteria and improvement trends

## Metadata

**Category**: Process
**Principle Number**: 55
**Related Patterns**: Test-Driven Development (TDD), A/B Testing, Property-Based Testing, LLM-as-Judge, Human-in-the-Loop, Statistical Hypothesis Testing
**Prerequisites**: Working AI system to evaluate, test dataset, metrics for success, ability to run automated tests
**Difficulty**: Medium
**Impact**: High

---

**Status**: Complete
**Last Updated**: 2025-09-30
**Version**: 1.0
