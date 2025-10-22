# Execute a plan

Everything below assumes you are in the repo root directory, change there if needed before running.

RUN:
make install
source .venv/bin/activate

READ:
@ai_context/IMPLEMENTATION_PHILOSOPHY.md
@ai_context/MODULAR_DESIGN_PHILOSOPHY.md

Execute the plan created in $ARGUMENTS to implement the changes needed to complete the task. Follow the detailed instructions provided in the plan, ensuring that each step is executed as described.

Make sure to follow the philosophies outlined in the implementation philosophy documents. Create todo lists and use your sub-agents for each step. Pay attention to the modular design principles and ensure that the code is structured in a way that promotes maintainability, readability, and reusability while executing the plan.

Update the plan as you go, to track status and any changes made during the implementation process. If you encounter any issues or need to make adjustments to the plan, confirm with the user before proceeding with changes and then document the adjustments made.

Upon completion, provide a summary of the changes made, any challenges faced, and how they were resolved. Ensure that the final implementation is thoroughly tested and validated against the requirements outlined in the plan.

RUN:
make check
make test
