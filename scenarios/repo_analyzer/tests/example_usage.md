# Repository Analyzer - Example Usage

## Basic Analysis

Compare two repositories to find improvement opportunities:

```bash
make repo-analyze \
  SOURCE=./well-designed-api \
  TARGET=./my-api \
  REQUEST="Find architectural improvements and missing features"
```

## With Focus Areas

Analyze specific aspects:

```bash
make repo-analyze \
  SOURCE=./production-app \
  TARGET=./my-app \
  REQUEST="Improve code quality" \
  FOCUS="testing,error-handling,documentation"
```

## Filter Specific Files

Only analyze Python files:

```bash
make repo-analyze \
  SOURCE=./reference \
  TARGET=./my-project \
  REQUEST="Analyze Python architecture" \
  INCLUDE="*.py,src/**/*.py" \
  EXCLUDE="test/**,*_test.py"
```

## Resume Session

If analysis was interrupted:

```bash
make repo-resume
```

## Test Example Repositories

You can test with any two git repositories on your system:

```bash
# Example: Compare two open source projects
make repo-analyze \
  SOURCE=~/repos/fastapi \
  TARGET=~/repos/my-api \
  REQUEST="Find patterns from FastAPI that could improve my API"
```

## Output

Results are saved to `.data/repo_analyzer/<timestamp>/`:
- `opportunities.json` - Final analysis results
- `opportunities_iter_N.json` - Results from each iteration
- `state.json` - Session state for resume
- `source_repo.xml` - Processed source repository
- `target_repo.xml` - Processed target repository

## Feedback Loop

During analysis, you'll be prompted with options:
1. **approve** - Accept the analysis
2. **filter** - Filter by priority/category
3. **refine** - Request specific improvements
4. **focus** - Change focus areas
5. **skip** - Continue without changes

The tool iterates up to 3 times (configurable) based on your feedback.
