# Custom Methodology Demo

Creating a new development profile for machine learning experimentation workflows.

## Context

This represents creating a custom methodology for a specific domain where:
- Neither default nor waterfall profiles fit well
- Unique workflow patterns need to be captured
- Process should be optimized for ML experimentation

**Perfect for: `profile-meta` profile (Methodology Development)**

## The Need

ML experimentation has unique characteristics:
- Hypothesis-driven development
- Heavy emphasis on measurement and metrics
- Lots of parallel experiments
- Data versioning and reproducibility critical
- Model registry and lineage tracking
- Iterative refinement based on metrics

## Desired Profile: `ml-experiment`

Should embody:

### Philosophy
- Hypothesis-driven: Every experiment tests a specific hypothesis
- Measurement-obsessed: Track everything, compare rigorously
- Reproducible: Data, code, and environment must be versioned
- Parallel exploration: Run many experiments, pick winners

### Process
1. Define hypothesis and success metrics
2. Version data and create experiment branch
3. Implement experiment with tracking
4. Run experiment and collect metrics
5. Compare to baseline and other experiments
6. Decide: adopt, iterate, or discard
7. Document learnings

### Tools Needed
- `/ml-experiment:hypothesis` - Define experiment and metrics
- `/ml-experiment:setup` - Version data, create branch, set up tracking
- `/ml-experiment:run` - Execute with metric collection
- `/ml-experiment:compare` - Compare results to baseline
- `/ml-experiment:adopt` - Merge winning experiment

### Success Metrics
- Experiment velocity (time to test hypothesis)
- Reproducibility rate (can experiments be reproduced?)
- Learning capture (are insights documented?)
- Metric improvement (are we getting better?)

## The Task

Use `profile-meta` to:
1. Analyze the ML experimentation workflow
2. Design the `ml-experiment` profile
3. Create the profile structure
4. Implement core commands
5. Test on a sample ML project
6. Refine based on friction points
