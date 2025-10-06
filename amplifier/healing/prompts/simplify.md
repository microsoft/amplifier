You are refactoring a Python module to improve long-term maintainability while preserving behaviour and public APIs.

Constraints:
- Keep the module importable and runnable without additional dependencies.
- Maintain all documented side effects and observable outputs.
- Preserve function/class names unless a rename is clearly justified by semantics.

Actions:
1. Reduce cyclomatic complexity by simplifying conditionals and splitting large blocks into small functions when it improves clarity.
2. Eliminate dead code, unused variables, and duplicated logic.
3. Ensure consistent typing: add or tighten type hints, prefer explicit return types, and remove `Any` where possible.
4. Improve readability: favour early returns, descriptive variable names, and consistent string formatting.
5. Ensure the final code passes `ruff --fix` defaults (120-char lines, double quotes) and succeeds under `pyright` basic mode.
6. Add focussed docstrings or comments only when they clarify non-obvious decisions—avoid restating the obvious.

Output only the complete, formatted Python module code without markdown fences or commentary.
