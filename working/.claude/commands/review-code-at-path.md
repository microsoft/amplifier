# Review and test code changes

Everything below assumes you are in the repo root directory, change there if needed before running.

RUN:
make install
source .venv/bin/activate
make check
make test

If all tests pass, let's take a look at the implementation philosophy documents to ensure we are aligned with the project's design principles.

READ:
@ai_context/IMPLEMENTATION_PHILOSOPHY.md
@ai_context/MODULAR_DESIGN_PHILOSOPHY.md

Now go and look at the code in $ARGUMENTS. Ultrathink and review each of the files thoroughly and make sure they are aligned with the implementation philosophy documents. Create a todo list and use the appropriate sub-agents at each step. Follow the breadcrumbs in the files to their dependencies or files they are importing and make sure those are also aligned with the implementation philosophy documents.

Give me a comprehensive report on how well the current code aligns with the implementation philosophy documents. If there are any discrepancies or areas for improvement, please outline them clearly with suggested changes or refactoring ideas.
