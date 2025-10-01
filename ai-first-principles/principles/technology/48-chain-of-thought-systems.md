# Principle #48 - Chain-of-Thought Systems

## Plain-Language Definition

Chain-of-thought (CoT) systems guide AI models to break down complex reasoning into explicit, sequential steps before reaching a conclusion. Instead of jumping directly to an answer, the model articulates its thinking process, making reasoning transparent and improving accuracy on multi-step problems.

## Why This Matters for AI-First Development

When AI agents tackle complex problems, they benefit from explicit reasoning scaffolds just as humans do. Without structured thinking, models often miss critical steps, make logical leaps, or produce confident but incorrect answers. Chain-of-thought systems address this by creating space for deliberate reasoning.

AI agents building and maintaining code face particularly challenging reasoning demands. They must trace execution paths, evaluate multiple approaches, verify logical consistency, and predict edge cases—all while maintaining coherent context across potentially hundreds of steps. CoT systems provide the structured reasoning framework that makes this possible.

Chain-of-thought systems deliver three critical benefits for AI-first development:

1. **Improved accuracy on complex tasks**: Research consistently shows CoT prompting improves performance on mathematical reasoning, logical inference, and multi-step problem-solving by 16-54% depending on task complexity. Models using cognitive tools with CoT outperformed base models by 16.6% on mathematical benchmarks, with even advanced models like GPT-4 showing substantial gains.

2. **Transparent reasoning for debugging**: When AI agents make mistakes, explicit reasoning traces make failures diagnosable. Instead of opaque wrong answers, you can see exactly where reasoning broke down—whether it was a faulty assumption, missed constraint, or logical error. This transparency is essential when agents operate autonomously.

3. **Reliable multi-step execution**: Complex workflows require maintaining context and consistency across many steps. CoT systems provide the scaffolding for agents to track their progress, verify intermediate results, and backtrack when needed. This is especially valuable in tool use chains, policy-heavy environments, and sequential decision-making.

Without chain-of-thought systems, AI agents become unreliable black boxes. They might solve simple problems quickly but fail catastrophically on anything requiring multi-step reasoning. In production systems where agents operate with minimal human oversight, this brittleness is unacceptable.

## Implementation Approaches

### 1. **Zero-Shot Chain-of-Thought**

The simplest CoT approach: add "Let's think step by step" to your prompt.

When to use: Quick improvement on any reasoning task without examples. Works surprisingly well despite its simplicity. Best for problems where the reasoning structure is relatively standard.

Success looks like: The model naturally breaks down the problem, shows its work, and reaches correct conclusions more often than with direct prompting.

```python
def solve_with_zero_shot_cot(problem: str, model) -> str:
    """Apply zero-shot CoT by adding a thinking prompt."""
    prompt = f"""
    {problem}

    Let's think step by step:
    """
    return model.generate(prompt)

# Example usage
problem = "If a train leaves Station A at 2pm traveling at 60mph, and another leaves Station B at 3pm traveling at 80mph toward Station A, and the stations are 200 miles apart, when do they meet?"
answer = solve_with_zero_shot_cot(problem, model)
```

### 2. **Few-Shot Chain-of-Thought with Examples**

Provide 2-3 examples of complete reasoning chains before the actual problem.

When to use: When you need more control over the reasoning structure or when zero-shot CoT doesn't capture domain-specific reasoning patterns. Essential for specialized domains or complex reasoning steps.

Success looks like: The model follows the example pattern, producing similarly structured reasoning that's appropriate for your domain.

```python
def solve_with_few_shot_cot(problem: str, examples: list[dict], model) -> str:
    """Apply few-shot CoT with reasoning examples."""
    prompt_parts = ["Here are examples of how to solve similar problems:\n"]

    for i, example in enumerate(examples, 1):
        prompt_parts.append(f"\nExample {i}:")
        prompt_parts.append(f"Problem: {example['problem']}")
        prompt_parts.append(f"Reasoning: {example['reasoning']}")
        prompt_parts.append(f"Answer: {example['answer']}\n")

    prompt_parts.append(f"\nNow solve this problem using the same reasoning approach:")
    prompt_parts.append(f"Problem: {problem}")
    prompt_parts.append("Reasoning:")

    return model.generate("\n".join(prompt_parts))

# Example usage
examples = [
    {
        "problem": "What is 15% of 80?",
        "reasoning": "Step 1: Convert percentage to decimal: 15% = 0.15\nStep 2: Multiply: 0.15 × 80 = 12",
        "answer": "12"
    },
    {
        "problem": "What is 25% of 60?",
        "reasoning": "Step 1: Convert percentage to decimal: 25% = 0.25\nStep 2: Multiply: 0.25 × 60 = 15",
        "answer": "15"
    }
]
answer = solve_with_few_shot_cot("What is 18% of 150?", examples, model)
```

### 3. **Tree-of-Thought (Exploring Multiple Paths)**

Generate and evaluate multiple reasoning paths, exploring different approaches simultaneously.

When to use: Complex problems with multiple valid solution approaches, strategic planning, or when you need to find the best solution among several possibilities. Essential for tasks requiring lookahead and backtracking.

Success looks like: The system explores promising paths, prunes unlikely ones, and converges on the best solution even when the optimal path isn't obvious initially.

```python
def solve_with_tree_of_thought(
    problem: str,
    num_candidates: int = 5,
    depth: int = 3,
    model
) -> str:
    """
    Implement Tree-of-Thought reasoning with branching exploration.
    """
    def generate_thoughts(state: str, step: int) -> list[str]:
        """Generate candidate next thoughts for current state."""
        prompt = f"""
        Current problem state: {state}
        Step {step} of {depth}

        Generate {num_candidates} different possible next steps or approaches.
        Each should be a distinct way to proceed.
        Format as numbered list.
        """
        response = model.generate(prompt)
        return [t.strip() for t in response.split('\n') if t.strip()]

    def evaluate_thought(thought: str, goal: str) -> str:
        """Evaluate if this thought is promising (sure/maybe/impossible)."""
        prompt = f"""
        Goal: {goal}
        Current thought: {thought}

        Evaluate if this approach can lead to the goal.
        Respond with only: "sure", "maybe", or "impossible"
        """
        return model.generate(prompt).strip().lower()

    # Initialize with problem
    current_thoughts = [(problem, 1.0)]  # (state, score)

    for step in range(depth):
        next_thoughts = []

        for state, score in current_thoughts:
            # Generate candidate next thoughts
            candidates = generate_thoughts(state, step + 1)

            # Evaluate each candidate
            for candidate in candidates[:num_candidates]:
                evaluation = evaluate_thought(candidate, problem)

                # Score based on evaluation
                if evaluation == "sure":
                    new_score = score * 1.0
                elif evaluation == "maybe":
                    new_score = score * 0.7
                else:  # impossible
                    continue  # Prune this branch

                next_thoughts.append((f"{state}\n{candidate}", new_score))

        # Keep best candidates for next iteration
        current_thoughts = sorted(next_thoughts, key=lambda x: x[1], reverse=True)[:num_candidates]

    # Return the best path
    return current_thoughts[0][0] if current_thoughts else "No solution found"
```

### 4. **Self-Consistency via Multiple Sampling**

Generate multiple independent reasoning chains and select the most common answer.

When to use: When accuracy is critical and you can afford extra inference cost. Particularly effective for problems with discrete answers where multiple reasoning paths should converge to the same solution.

Success looks like: Different reasoning chains reach the same answer through different approaches, increasing confidence. Disagreement highlights areas of genuine uncertainty.

```python
def solve_with_self_consistency(
    problem: str,
    num_samples: int = 5,
    model
) -> tuple[str, float]:
    """
    Generate multiple reasoning chains and select most common answer.
    Returns (answer, confidence) where confidence is agreement ratio.
    """
    reasoning_chains = []
    answers = []

    # Generate multiple independent chains
    for _ in range(num_samples):
        prompt = f"""
        {problem}

        Let's think step by step to solve this:
        """
        chain = model.generate(prompt, temperature=0.7)
        reasoning_chains.append(chain)

        # Extract final answer from chain
        answer = extract_final_answer(chain)
        answers.append(answer)

    # Find most common answer
    from collections import Counter
    answer_counts = Counter(answers)
    best_answer, count = answer_counts.most_common(1)[0]
    confidence = count / num_samples

    return best_answer, confidence

def extract_final_answer(chain: str) -> str:
    """Extract the final answer from a reasoning chain."""
    # Look for common answer indicators
    lines = chain.split('\n')
    for line in reversed(lines):
        if any(indicator in line.lower() for indicator in ['answer:', 'therefore', 'thus', 'final answer']):
            return line.strip()
    return lines[-1].strip()
```

### 5. **The "Think" Tool for Agentic Systems**

Provide a dedicated tool that agents can call to process information between actions.

When to use: Agentic tool use scenarios, especially policy-heavy environments, sequential decision-making, or when analyzing tool outputs before taking further actions. Not needed for simple single-step tool calls.

Success looks like: Agents pause to reason at appropriate moments, analyze tool results before acting, verify policy compliance, and make more consistent decisions across trials.

```python
def create_think_tool() -> dict:
    """
    Create a 'think' tool for Claude or other agentic systems.
    This tool creates space for reasoning between tool calls.
    """
    return {
        "name": "think",
        "description": """Use this tool when you need to pause and reason about complex situations.

        Use it to:
        - Analyze tool results before deciding next steps
        - List applicable rules and policies
        - Verify you have all required information
        - Plan multi-step approaches
        - Check if actions comply with constraints

        The tool doesn't change anything - it just creates space for structured thinking.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "thought": {
                    "type": "string",
                    "description": "Your reasoning, analysis, or planning notes."
                }
            },
            "required": ["thought"]
        }
    }

# Example system prompt when using the think tool
SYSTEM_PROMPT_WITH_THINK = """
Before taking any action after receiving tool results, use the think tool to:

1. List specific rules that apply to this situation
2. Verify all required information is collected
3. Check that planned actions comply with policies
4. Review tool results for correctness

Example pattern:
- User wants to cancel reservation ABC123
- Use think tool: "Need to verify: user ID, reservation details, cancellation rules.
  Cancellation rules to check: within 24h of booking? If not, check ticket class.
  Plan: collect missing info, verify rules apply, get confirmation before canceling."
- Then proceed with actions
"""

def handle_think_call(thought: str) -> dict:
    """Handle when the agent calls the think tool."""
    # Log the thought (could save to structured logs)
    print(f"[THINKING] {thought}")

    # Return simple acknowledgment
    return {
        "result": "Thought recorded. Proceed with next action.",
        "thought_logged": True
    }
```

### 6. **Sequential Chaining with Validation**

Chain multiple reasoning steps where each step's output feeds into the next, with validation at each stage.

When to use: Complex workflows that must be broken into distinct phases (understand → plan → execute → verify). Particularly valuable when mistakes are costly and you want to catch errors early.

Success looks like: Each stage produces reliable output that serves as solid foundation for the next stage. Errors are caught at validation points before cascading forward.

```python
class SequentialCoTChain:
    """
    Chain multiple CoT steps with validation between stages.
    """
    def __init__(self, model):
        self.model = model
        self.history = []

    def understand_problem(self, problem: str) -> dict:
        """First stage: Break down the problem."""
        prompt = f"""
        Analyze this problem carefully:

        {problem}

        Provide:
        1. What is being asked?
        2. What information is given?
        3. What information is missing?
        4. What constraints apply?
        5. What approach seems most appropriate?
        """
        understanding = self.model.generate(prompt)
        self.history.append({"stage": "understand", "output": understanding})
        return {"understanding": understanding}

    def plan_solution(self, understanding: dict) -> dict:
        """Second stage: Create solution plan."""
        prompt = f"""
        Based on this problem understanding:

        {understanding['understanding']}

        Create a detailed step-by-step plan to solve it.
        Number each step clearly.
        For each step, specify:
        - What will be done
        - What this accomplishes
        - What the expected outcome is
        """
        plan = self.model.generate(prompt)
        self.history.append({"stage": "plan", "output": plan})
        return {"plan": plan}

    def execute_solution(self, plan: dict, original_problem: str) -> dict:
        """Third stage: Execute the plan."""
        prompt = f"""
        Original problem: {original_problem}

        Solution plan:
        {plan['plan']}

        Now execute this plan step by step.
        Show all work for each step.
        State the final answer clearly.
        """
        solution = self.model.generate(prompt)
        self.history.append({"stage": "execute", "output": solution})
        return {"solution": solution}

    def verify_solution(self, solution: dict, original_problem: str) -> dict:
        """Final stage: Verify the solution."""
        prompt = f"""
        Original problem: {original_problem}

        Proposed solution:
        {solution['solution']}

        Verify this solution:
        1. Does it answer the original question?
        2. Are all calculations correct?
        3. Are all constraints satisfied?
        4. Are there any logical errors?

        If errors found, explain them clearly.
        If correct, confirm with explanation.
        """
        verification = self.model.generate(prompt)
        self.history.append({"stage": "verify", "output": verification})
        return {"verification": verification}

    def solve(self, problem: str) -> dict:
        """Run the complete chain."""
        understanding = self.understand_problem(problem)
        plan = self.plan_solution(understanding)
        solution = self.execute_solution(plan, problem)
        verification = self.verify_solution(solution, problem)

        return {
            "understanding": understanding,
            "plan": plan,
            "solution": solution,
            "verification": verification,
            "history": self.history
        }
```

## Good Examples vs Bad Examples

### Example 1: Mathematical Problem Solving

**Good:**
```python
def solve_math_with_cot(problem: str) -> str:
    """Solve math problem with explicit reasoning steps."""
    prompt = f"""
    Problem: {problem}

    Let's solve this step by step:

    Step 1: Identify what we know and what we need to find
    Step 2: Determine the appropriate method or formula
    Step 3: Show all calculations with work
    Step 4: Verify the answer makes sense

    Solution:
    """
    return model.generate(prompt)

# The model produces:
# "Step 1: We know the train leaves at 2pm at 60mph and stations are 200 miles apart...
#  Step 2: Use distance = rate × time formula for both trains...
#  Step 3: Let t = time for first train. Distance = 60t and 80(t-1)..."
```

**Bad:**
```python
def solve_math_direct(problem: str) -> str:
    """Solve math problem with direct prompting."""
    prompt = f"Solve this problem: {problem}\n\nAnswer:"
    return model.generate(prompt)

# The model might produce:
# "They meet at 4:20pm"
# Without showing any work or reasoning, making it impossible to:
# - Verify the answer
# - Understand where errors occurred if wrong
# - Trust the answer without independent verification
```

**Why It Matters:** Chain-of-thought makes reasoning transparent and verifiable. Direct answers hide the logic, making errors impossible to diagnose. When AI agents make decisions autonomously, opaque reasoning is unacceptable—you need to see the thinking to trust the output.

### Example 2: Code Debugging

**Good:**
```python
def debug_with_cot(code: str, error: str) -> str:
    """Debug code with structured reasoning."""
    prompt = f"""
    Code with error:
    {code}

    Error message:
    {error}

    Let's debug this systematically:

    1. Understand the error:
       - What is the error type?
       - What is the error message telling us?
       - On which line does it occur?

    2. Analyze the code:
       - What is this code trying to do?
       - What are the inputs and expected outputs?
       - What assumptions does it make?

    3. Identify the root cause:
       - Why does this error occur?
       - What condition triggers it?
       - Are there edge cases being missed?

    4. Propose a fix:
       - What changes would resolve this?
       - Are there any side effects to consider?
       - How can we prevent similar errors?

    Debug analysis:
    """
    return model.generate(prompt)
```

**Bad:**
```python
def debug_direct(code: str, error: str) -> str:
    """Debug code with direct prompting."""
    prompt = f"This code has an error:\n{code}\n\nError: {error}\n\nFix it:"
    return model.generate(prompt)

# Produces:
# "Change line 5 to: if x is not None:"
#
# But doesn't explain:
# - Why this fixes it
# - What caused the error
# - Whether there are other related issues
# - If this change has side effects
```

**Why It Matters:** Without structured reasoning, the AI might suggest superficial fixes that don't address root causes. CoT debugging finds underlying issues, considers edge cases, and produces robust solutions rather than quick patches.

### Example 3: Policy-Compliant Decision Making

**Good:**
```python
def make_policy_decision_with_cot(request: str, policies: dict) -> str:
    """Make decision with policy verification using think tool."""
    tools = [create_think_tool(), {"name": "approve_request", ...}, {"name": "deny_request", ...}]

    system_prompt = """
    Before approving or denying any request, use the think tool to:

    1. List all policies that apply to this request
    2. Check if request satisfies each policy requirement
    3. Identify any missing information needed
    4. Determine if request should be approved or denied
    5. Prepare clear explanation for the decision

    Only after thinking through these points should you call approve or deny.
    """

    messages = [
        {"role": "user", "content": request}
    ]

    # Agent will call think tool, then make decision
    return agent.run(messages, tools, system_prompt)

# Agent produces:
# 1. Calls think tool: "User wants to cancel reservation.
#    Policies to check: 1) 24hr cancellation rule, 2) Ticket class restrictions...
#    Request satisfies: Made within 24hr, economy class, no segments flown...
#    Decision: Approve with full refund per policy 3.2"
# 2. Calls approve_request with proper parameters
```

**Bad:**
```python
def make_policy_decision_direct(request: str, policies: dict) -> str:
    """Make decision without structured thinking."""
    prompt = f"""
    Request: {request}
    Policies: {json.dumps(policies)}

    Should this be approved? Answer yes or no and explain why.
    """
    return model.generate(prompt)

# Produces:
# "Yes, this should be approved because the customer asked nicely."
#
# Misses:
# - Policy verification
# - Required information checks
# - Compliance documentation
# - Consistent decision-making process
```

**Why It Matters:** Policy-heavy environments require systematic verification. Without the think tool creating explicit reasoning space, agents make inconsistent decisions and miss requirements. Benchmarks show 54% improvement in policy compliance with structured thinking versus direct responses.

### Example 4: Multi-Step API Workflow

**Good:**
```python
def execute_workflow_with_cot(goal: str, available_tools: list) -> str:
    """Execute multi-step workflow with thinking between actions."""
    system_prompt = """
    For complex workflows:

    1. Use think tool to plan entire workflow before starting
    2. After each tool call, use think tool to verify results
    3. Use think tool to check if goal is achieved before finishing

    Example workflow thinking:
    "Goal: Create user account with payment method.
     Plan:
     1. Create user (need: email, name)
     2. Verify user creation succeeded
     3. Add payment method (need: user_id from step 1, card details)
     4. Verify payment method attached
     5. Confirm complete account setup"
    """

    messages = [{"role": "user", "content": goal}]
    tools = [create_think_tool()] + available_tools

    return agent.run(messages, tools, system_prompt)

# Agent produces:
# 1. think: "Planning workflow... need to create user first, then add payment..."
# 2. create_user(email="...", name="...")
# 3. think: "User created successfully with ID 12345. Now add payment method..."
# 4. add_payment_method(user_id=12345, card="...")
# 5. think: "Payment method added. Verify account is complete..."
# 6. get_user_details(user_id=12345)
# 7. think: "Confirmed: account has user profile and payment method. Goal achieved."
```

**Bad:**
```python
def execute_workflow_direct(goal: str, available_tools: list) -> str:
    """Execute workflow without explicit thinking."""
    prompt = f"Achieve this goal using available tools: {goal}"

    # Agent might produce:
    # 1. create_user(email="...", name="...")
    # 2. add_payment_method(card="...")  # WRONG: doesn't use user_id from step 1
    # 3. Returns "Done" without verification
    #
    # Result: Broken workflow, payment method not attached to user
```

**Why It Matters:** Multi-step workflows require maintaining context and verifying results between steps. Without structured thinking space, agents lose track of dependencies, skip verification, and produce broken workflows. The think tool provides the cognitive buffer needed for complex orchestration.

### Example 5: Self-Consistency for Critical Decisions

**Good:**
```python
def make_critical_decision(scenario: str) -> dict:
    """Use self-consistency for important decisions."""
    # Generate 5 independent reasoning chains
    chains = []
    for i in range(5):
        prompt = f"""
        Scenario: {scenario}

        Analyze this carefully and recommend an action.
        Think through:
        1. What are the key factors?
        2. What are the risks of each option?
        3. What is the best course of action?

        Reasoning chain {i+1}:
        """
        chain = model.generate(prompt, temperature=0.8)
        chains.append(chain)

        # Extract decision
        decision = extract_decision(chain)

    # Find consensus
    from collections import Counter
    decision_counts = Counter([extract_decision(c) for c in chains])
    consensus_decision, count = decision_counts.most_common(1)[0]
    confidence = count / 5

    return {
        "decision": consensus_decision,
        "confidence": confidence,
        "chains": chains,
        "analysis": f"{count}/5 chains recommended this action"
    }
```

**Bad:**
```python
def make_critical_decision_single(scenario: str) -> str:
    """Make critical decision with single inference."""
    prompt = f"Analyze this scenario and recommend an action: {scenario}"
    return model.generate(prompt)

# Single inference means:
# - No verification of reasoning
# - No confidence estimate
# - Can't detect uncertainty
# - Higher error rate on complex decisions
```

**Why It Matters:** For critical decisions, single-pass inference is unreliable. Self-consistency through multiple reasoning chains provides confidence estimates and catches errors. When 5 independent chains agree, you can trust the answer. When they disagree, you know the problem needs human review.

## Related Principles

- **[Principle #45 - Prompt Patterns](45-prompt-patterns.md)** - CoT systems are advanced prompt patterns that enable structured reasoning. Prompt patterns provide the foundation; CoT adds systematic reasoning scaffolds.

- **[Principle #47 - Context Engineering](47-context-engineering.md)** - CoT reasoning consumes significant context. Effective context engineering determines how many reasoning steps fit in the model's context window and how to structure chains efficiently.

- **[Principle #49 - Tool Use Patterns](49-tool-use-patterns.md)** - The "think" tool exemplifies how CoT integrates with agentic tool use. CoT helps agents reason about when to use tools, how to interpret tool results, and how to chain tool calls effectively.

- **[Principle #52 - Multi-Agent Systems](52-multi-agent-systems.md)** - Multi-agent systems benefit from CoT when agents need to reason about their roles, coordinate actions, or explain their decisions to other agents. Tree-of-thought enables exploring multiple agent strategies simultaneously.

- **[Principle #26 - Stateless by Default](26-stateless-by-default.md)** - CoT reasoning chains should be stateless—each step can be understood independently. This enables caching, parallel exploration (as in ToT), and easier debugging of reasoning failures.

- **[Principle #32 - Error Recovery Patterns Built In](32-error-recovery-patterns.md)** - CoT enhances error recovery because explicit reasoning makes failures diagnosable. When errors occur, you can identify which reasoning step failed and why, enabling targeted correction.

## Common Pitfalls

1. **Overusing CoT on Simple Tasks**: Applying CoT to trivial problems wastes tokens and adds latency without improving accuracy.
   - Example: Using "let's think step by step" for "What is 2+2?" adds 20-50 tokens for zero benefit.
   - Impact: Increased costs, slower responses, cluttered outputs. Can reduce user experience by adding unnecessary verbosity.
   - Solution: Use direct prompting for simple tasks. Reserve CoT for problems requiring multi-step reasoning, policy verification, or complex analysis.

2. **Not Providing Reasoning Structure**: Zero-shot "think step by step" works but isn't optimal for complex domains.
   - Example: Asking the model to debug code without specifying what aspects to analyze (error type, root cause, edge cases, etc.).
   - Impact: Shallow or incomplete reasoning. Model might skip critical steps or focus on irrelevant details.
   - Solution: Use few-shot examples or explicit reasoning templates for domain-specific tasks. Show the model what good reasoning looks like in your context.

3. **Ignoring Cost-Benefit Trade-offs**: CoT dramatically increases token usage—reasoning chains can be 3-10x longer than direct answers.
   - Example: Using self-consistency with 5 samples on every query increases costs 5x and latency significantly.
   - Impact: Unsustainable costs at scale. $100/day API budget becomes $500/day without proportional value gain.
   - Solution: Measure task accuracy with and without CoT. Use CoT only where error reduction justifies cost increase. Consider caching reasoning chains for common problems.

4. **Missing Verification Steps**: Generating reasoning chains without validating them allows errors to propagate.
   - Example: Model produces multi-step solution but never verifies intermediate results or final answer correctness.
   - Impact: Confidently wrong answers that look superficially correct due to detailed reasoning. Harder to spot errors in long reasoning chains.
   - Solution: Add explicit verification steps. For critical tasks, use self-consistency to catch errors through disagreement between chains.

5. **Treating All CoT Steps Equally**: Not all reasoning steps require the same depth or contribute equally to final accuracy.
   - Example: Spending 100 tokens on "Step 1: Understand the problem" when it's trivial, then rushing through complex calculation steps.
   - Impact: Wasted tokens on obvious steps, insufficient reasoning on hard steps. Suboptimal token allocation.
   - Solution: Use adaptive CoT depth. Allocate more reasoning budget to complex steps, less to obvious ones. Learn which steps matter most for your domain.

6. **No Structured Storage of Reasoning Chains**: Treating reasoning chains as ephemeral text instead of structured data for analysis.
   - Example: Logging raw text outputs without parsing steps, decisions, or confidence levels.
   - Impact: Can't analyze failure patterns, measure reasoning quality, or improve prompts based on data. No visibility into what reasoning works best.
   - Solution: Parse and structure reasoning chains. Track which steps succeed/fail, measure agreement in self-consistency, identify common error patterns.

7. **Forgetting Temperature Settings**: Using inappropriate temperature for CoT sampling.
   - Example: Using temperature=0.0 for self-consistency, which produces identical chains instead of diverse reasoning paths.
   - Impact: Self-consistency provides no benefit if all chains are identical. Tree-of-thought fails to explore diverse strategies.
   - Solution: Use temperature=0.0 for deterministic reasoning when you want reproducibility. Use temperature=0.7-0.9 for self-consistency and ToT to ensure diverse exploration.

## Tools & Frameworks

### Chain-of-Thought Libraries
- **LangChain**: Built-in CoT chains with sequential execution, custom reasoning templates, and result parsing. Provides `SequentialChain` for step-by-step workflows.
- **Guidance**: Constrained generation for CoT with step-by-step templates, validation at each stage, and type-safe reasoning structures.
- **DSPy**: Programmatic CoT with automatic optimization of reasoning steps, learned few-shot examples, and performance tuning.

### Tree-of-Thought Implementations
- **tree-of-thought-llm**: Original ToT research implementation with BFS/DFS search, thought evaluation, and backtracking. Includes Game of 24 and creative writing tasks.
- **PanelGPT**: Multi-agent panel discussions as ToT variant, where different "experts" explore different reasoning paths before reaching consensus.

### Agentic Tool Use
- **Anthropic Claude with Think Tool**: Native "think" tool in Claude API for structured reasoning between tool calls. Improves policy compliance by 54% in complex domains.
- **LangChain Agents with ReAct**: Combines reasoning and acting in loops, with explicit thought steps between actions.
- **AutoGPT**: Autonomous agent framework using CoT for goal decomposition, step planning, and execution verification.

### Validation and Evaluation
- **τ-Bench**: Benchmark for tool use with policy compliance, includes "think" tool evaluation in customer service scenarios.
- **SWE-Bench**: Software engineering benchmark where "think" tool improves debugging performance by 1.6%.
- **Hypothesis**: Property-based testing framework for verifying CoT consistency across multiple runs.

### Cognitive Tools Frameworks
- **Context-Engineering Toolkit**: Collection of cognitive tools (understand_question, verify_logic, backtracking) composable for custom CoT workflows.
- **Prompt Programs**: Libraries of reusable reasoning functions with explicit parameters, enabling modular CoT construction.

## Implementation Checklist

When implementing chain-of-thought systems, ensure:

- [ ] Task complexity justifies CoT overhead (multi-step reasoning, policy verification, or complex analysis required)
- [ ] Appropriate CoT variant selected (zero-shot, few-shot, ToT, self-consistency, or think tool based on use case)
- [ ] Reasoning structure explicit in prompts (steps numbered, verification included, output format specified)
- [ ] Few-shot examples match problem domain (show domain-specific reasoning patterns, not generic examples)
- [ ] Verification steps included where critical (check intermediate results, validate final answers, ensure constraint compliance)
- [ ] Temperature set appropriately (0.0 for reproducibility, 0.7-0.9 for exploration and self-consistency)
- [ ] Token costs measured and acceptable (compare CoT vs direct prompting costs, ensure improvement justifies expense)
- [ ] Reasoning chains structured and logged (parse steps, track success rates, identify failure patterns for continuous improvement)
- [ ] Think tool included for agentic workflows (available between tool calls, prompted with domain examples, monitored for appropriate use)
- [ ] Self-consistency used for critical decisions (multiple chains sampled, consensus measured, confidence thresholds set)
- [ ] Fallback to direct prompting for simple queries (detect trivial cases, skip unnecessary reasoning, optimize for common paths)
- [ ] Performance benchmarked with and without CoT (measure accuracy improvement, validate cost-benefit, document when to use)

## Metadata

**Category**: Technology
**Principle Number**: 48
**Related Patterns**: Prompt Chaining, ReAct Pattern, Cognitive Scaffolding, Multi-Agent Reasoning, Self-Refinement
**Prerequisites**: Understanding of prompt engineering, token economics, API usage patterns, model capabilities
**Difficulty**: Medium
**Impact**: High

---

**Status**: Complete
**Last Updated**: 2025-09-30
**Version**: 1.0
