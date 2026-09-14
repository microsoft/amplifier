# Request retention integration proof

This opt-in fixture tests current hook delivery under forced context pressure.
It is test infrastructure, never a normal bundle dependency. It appends synthetic
assistant progress and advertises a small input budget to the context manager.
LLM responses, provider requests, tool dispatch and CLI persistence remain real.
Random-looking facts in the fixture are invented test data.

Use an isolated DTU. Serve unpublished commits through Gitea, pin sources, enable
raw provider logging with the context-intelligence hook, and compare exported
requests against canonical history. The fixture records imported source hashes
and the unchanged core version so a passing run cannot use cached old modules
unnoticed. Do not publish credential files or real user transcripts.

The runner and proof results accompany this fixture. See the results for exact
limits: this is not a weeks-long workload or a production cache-cost benchmark.
