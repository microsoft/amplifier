"""Advanced healing prompts for different complexity scenarios."""


def get_aggressive_healing_prompt(module_path: str, health_score: float, complexity: int, loc: int) -> str:
    """Generate an aggressive healing prompt based on module metrics."""

    base_prompt = f"""CRITICAL REFACTORING REQUIRED for {module_path}

Current metrics show severe issues:
- Health Score: {health_score:.1f}/100 (FAILING)
- Complexity: {complexity} (NEEDS 70% REDUCTION)
- Lines of Code: {loc} (TARGET: <{loc // 3})

MANDATORY TRANSFORMATIONS:
1. ELIMINATE all nested if/else blocks deeper than 2 levels
2. EXTRACT complex logic into small, single-purpose functions (max 10 lines each)
3. REMOVE all unnecessary parameters and variables
4. USE early returns to eliminate else blocks
5. APPLY guard clauses at function start
6. REPLACE complex conditionals with clear helper functions
7. DELETE commented code and verbose comments
8. SIMPLIFY data structures - prefer simple types over complex objects

SPECIFIC REQUIREMENTS:
- Each function must do ONE thing only
- No function longer than 20 lines
- No more than 3 parameters per function
- Cyclomatic complexity must be < 5 per function
- Remove ALL code duplication
- Use descriptive names, no comments needed

PHILOSOPHY: "Perfection is achieved not when there is nothing more to add, but when there is nothing left to take away."

Transform this module into clean, simple, readable code that a junior developer could understand instantly.
"""

    # Add specific guidance based on complexity level
    if complexity > 50:
        base_prompt += """
EXTREME COMPLEXITY DETECTED:
- This module is a nightmare of nested logic
- Break it into 5+ smaller modules if needed
- Each extracted module should have a single, clear purpose
- Don't preserve the original structure - completely reimagine it
"""

    if loc > 300:
        base_prompt += """
EXCESSIVE SIZE DETECTED:
- This module is doing too much
- Identify the 2-3 core responsibilities
- Extract everything else to separate modules
- Aim for 100 lines or less in the main module
"""

    return base_prompt


def get_decoupling_prompt(module_path: str, dependencies: list[str]) -> str:
    """Generate a prompt for decoupling highly connected modules."""

    return f"""DECOUPLE AND SIMPLIFY {module_path}

This module has tight coupling with: {", ".join(dependencies[:5])}

DECOUPLING STRATEGY:
1. IDENTIFY the core responsibility of this module (ONE thing)
2. EXTRACT all secondary responsibilities to separate modules
3. REPLACE direct dependencies with:
   - Dependency injection
   - Simple interfaces
   - Event-based communication
   - Configuration objects

REFACTORING STEPS:
1. Create clean interfaces for external dependencies
2. Move all business logic to pure functions
3. Separate I/O operations from logic
4. Use composition over inheritance
5. Apply the Dependency Inversion Principle

GOAL: This module should work independently with mock dependencies.
"""


def get_zen_prompt(module_path: str) -> str:
    """Generate a Zen-philosophy prompt for ultimate simplicity."""

    return f"""APPLY ZEN PHILOSOPHY to {module_path}

"The code that isn't there has no bugs, requires no maintenance, and executes instantly."

ZEN PRINCIPLES:
1. If you can't explain it simply, it's too complex
2. Every line must earn its place
3. Prefer 10 lines that are obvious over 5 that are clever
4. Delete first, refactor second, add third
5. The best abstraction is no abstraction
6. Make it work, make it right, make it gone

PRACTICAL STEPS:
- Question every function: "Is this necessary?"
- Question every parameter: "Can this be eliminated?"
- Question every condition: "Is there a simpler way?"
- Remove all "just in case" code
- Delete all defensive programming that isn't critical
- Trust the caller, validate only at boundaries

REMEMBER: The goal is code so simple it seems almost trivial.
"""


def get_complexity_killer_prompt(module_path: str, complexity: int) -> str:
    """Generate a prompt specifically targeting cyclomatic complexity."""

    return f"""ELIMINATE COMPLEXITY in {module_path}

Current cyclomatic complexity: {complexity} (UNACCEPTABLE)
Target: < 10 total, < 3 per function

COMPLEXITY ELIMINATION TACTICS:

1. REPLACE nested conditionals with:
   - Guard clauses (return early)
   - Lookup tables/dictionaries
   - Polymorphism for type-based branching
   - Strategy pattern for algorithm selection

2. SIMPLIFY loop logic:
   - Use built-in functions (map, filter, reduce)
   - Extract loop body to separate function
   - Replace complex iterations with list comprehensions
   - Use generator expressions for memory efficiency

3. FLATTEN deep nesting:
   ```python
   # BAD: Deep nesting
   if x:
       if y:
           if z:
               do_something()

   # GOOD: Guard clauses
   if not x: return
   if not y: return
   if not z: return
   do_something()
   ```

4. EXTRACT complex expressions:
   ```python
   # BAD: Complex condition
   if user.age > 18 and user.country == "US" and user.verified and not user.banned:

   # GOOD: Extracted function
   if user.can_access_content():
   ```

RESULT: Each function should be scannable in 5 seconds.
"""


def select_best_prompt(
    module_path: str, health_score: float, complexity: int, loc: int, dependencies: list[str] | None = None
) -> str:
    """Select the most appropriate healing prompt based on module characteristics."""

    # For extremely unhealthy modules, use the most aggressive approach
    if health_score < 50:
        return get_aggressive_healing_prompt(module_path, health_score, complexity, loc)

    # For highly complex modules, focus on complexity reduction
    if complexity > 40:
        return get_complexity_killer_prompt(module_path, complexity)

    # For highly coupled modules, focus on decoupling
    if dependencies and len(dependencies) > 10:
        return get_decoupling_prompt(module_path, dependencies)

    # For moderately unhealthy modules, use Zen philosophy
    return get_zen_prompt(module_path)
