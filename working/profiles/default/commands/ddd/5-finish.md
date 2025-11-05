---
description: DDD Phase 5 - Cleanup and finalize (project:ddd)
argument-hint: [optional instructions]
allowed-tools: TodoWrite, Read, Write, Bash(git:*), Bash(make check:*), Bash(rm:*), Glob, Task
---

# DDD Phase 5: Wrap-Up & Cleanup

Loading context:

@docs/document_driven_development/phases/06_cleanup_and_push.md
@ai_working/ddd/

Instructions: $ARGUMENTS

---

## Your Task: Clean Up & Finalize

**Goal**: Remove temporary files, verify clean state, push/PR with explicit authorization

**Every git operation requires EXPLICIT user authorization**

---

## Phase 5 Steps

### Step 1: Cleanup Temporary Files

Remove all DDD working artifacts:

```bash
# Show what will be deleted
ls -la ai_working/ddd/

# Ask user: "Delete DDD working files?"
# If yes:
rm -rf ai_working/ddd/

# Check for other temporary files
find . -name "*.tmp" -o -name "*.bak" -o -name "*~"

# Ask user: "Delete these temporary files?"
# If yes, delete them
```

Remove any test artifacts:

```bash
# Common locations
rm -rf .pytest_cache/
rm -rf __pycache__/
rm -f .coverage
rm -rf htmlcov/

# Project-specific cleanup
[check for test output, debug files, etc.]
```

Remove debug code:

```bash
# Search for common debug patterns
grep -r "console.log" src/
grep -r "print(" src/  # except legitimate logging
grep -r "debugger" src/
grep -r "TODO.*debug" src/

# If found, ask user: "Remove debug code?"
# Show locations, get confirmation, then remove
```

### Step 2: Final Verification

Run complete quality check:

```bash
make check
```

**Status**: ✅ All passing / ❌ Issues found

If issues found:

- List all issues clearly
- Ask user: "Fix these before finishing?"
- If yes, fix and re-run
- If no, note in summary

Check git status:

```bash
git status
```

**Questions to answer**:

- Are there uncommitted changes? (Should there be?)
- Are there untracked files? (Should they be added/ignored?)
- Is working tree clean? (Or remaining work?)

List all commits from this DDD session:

```bash
# Assuming session started after last push
git log --oneline origin/$(git branch --show-current)..HEAD

# Or since specific commit
git log --oneline [start-commit]..HEAD
```

**Show user**:

- Number of commits
- Summary of each commit
- Overall changes (insertions/deletions)

### Step 3: Commit Any Remaining Changes

Check for uncommitted changes:

```bash
git status --short
```

If changes exist:

**Ask user**: "There are uncommitted changes. Commit them?"

If YES:

- Show the diff
- Ask for commit message or suggest one
- Request explicit authorization
- Commit with provided/suggested message

If NO:

- Leave changes uncommitted
- Note in final summary

### Step 4: Push to Remote

**Ask user**: "Push to remote?"

Show context:

```bash
# Current branch
git branch --show-current

# Commits to push
git log --oneline origin/$(git branch --show-current)..HEAD

# Remote branch exists?
git ls-remote --heads origin $(git branch --show-current)
```

If YES:

- Confirm which remote and branch
- Push with: `git push -u origin [branch]`
- Show result

If NO:

- Leave local only
- Note in final summary

### Step 5: Create Pull Request (If Appropriate)

**Determine if PR is appropriate**:

- Are we on a feature branch? (not main/master)
- Has branch been pushed?
- Does user want a PR?

If appropriate, **ask user**: "Create pull request?"

Show context:

```bash
# Current branch vs main
git log --oneline main..HEAD

# Files changed
git diff --stat main..HEAD
```

If YES:

**Generate PR description** from DDD artifacts:

```markdown
## Summary

[From plan.md: Problem statement and solution]

## Changes

### Documentation

[List docs changed]

### Code

[List code changed]

### Tests

[List tests added]

## Testing

[From test_report.md: Key test scenarios]

## Verification Steps

[From test_report.md: Recommended smoke tests]

## Related

[Link to any related issues/discussions]
```

**Create PR** (using existing /commit command or gh pr create):

```bash
gh pr create --title "[Feature name]" --body "[generated description]"
```

Show PR URL to user.

If NO:

- Skip PR creation
- Note in final summary

### Step 6: Post-Cleanup Check

Consider spawning specialized cleanup agent:

```bash
Task post-task-cleanup: "Review workspace for any remaining
temporary files, test artifacts, or unnecessary complexity"
```

Final workspace verification:

```bash
# Working tree clean?
git status

# No untracked files that shouldn't be there?
git ls-files --others --exclude-standard

# Quality checks pass?
make check
```

### Step 7: Generate Final Summary

Create comprehensive completion summary:

````markdown
# DDD Workflow Complete! 🎉

## Feature: [Name from plan.md]

**Problem Solved**: [from plan.md]
**Solution Implemented**: [from plan.md]

## Changes Made

### Documentation (Phase 2)

- Files updated: [count]
- Key docs: [list 3-5 most important]
- Commit: [hash and message]

### Code (Phase 4)

- Files changed: [count]
- Implementation chunks: [count]
- Commits: [list all commit hashes and messages]

### Tests

- Unit tests added: [count]
- Integration tests added: [count]
- All tests passing: ✅ / ❌

## Quality Metrics

- `make check`: ✅ Passing / ❌ Issues
- Code matches documentation: ✅ Yes
- Examples work: ✅ Yes
- User testing: ✅ Complete

## Git Summary

- Total commits: [count]
- Branch: [name]
- Pushed to remote: Yes / No
- Pull request: [URL] / Not created

## Artifacts Cleaned

- DDD working files: ✅ Removed
- Temporary files: ✅ Removed
- Debug code: ✅ Removed
- Test artifacts: ✅ Removed

## Recommended Next Steps for User

### Verification Steps

Please verify the following:

1. **Basic functionality**:
   ```bash
   [command]
   # Expected: [output]
   ```
````

2. **Edge cases**:

   ```bash
   [command]
   # Expected: [output]
   ```

3. **Integration**:
   ```bash
   [command]
   # Verify works with [existing features]
   ```

[List 3-5 key smoke tests from test_report.md]

### If Issues Found

If you find any issues:

1. Provide specific feedback
2. Re-run `/ddd:4-code` with feedback
3. Iterate until resolved
4. Re-run `/ddd:5-finish` when ready

## Follow-Up Items

[Any remaining TODOs or future considerations from plan.md]

## Workspace Status

- Working tree: Clean / [uncommitted changes]
- Branch: [name]
- Ready for: Next feature

---

**DDD workflow complete. Ready for next work!**

````

---

## Using TodoWrite

Track finalization tasks:

```markdown
- [ ] Temporary files cleaned
- [ ] Final verification passed
- [ ] Remaining changes committed (if any)
- [ ] Pushed to remote (if authorized)
- [ ] PR created (if authorized)
- [ ] Post-cleanup check complete
- [ ] Final summary generated
````

---

## Agent Suggestions

**post-task-cleanup** - For thorough cleanup:

```
Task post-task-cleanup: "Review entire workspace for any remaining
temporary files, test artifacts, or unnecessary complexity after
DDD workflow completion"
```

---

## Authorization Checkpoints

### 1. Delete DDD Working Files

⚠️ **Ask**: "Delete ai_working/ddd/ directory?"

- Show what will be deleted
- Get explicit yes/no

### 2. Delete Temporary Files

⚠️ **Ask**: "Delete temporary/test artifacts?"

- Show what will be deleted
- Get explicit yes/no

### 3. Remove Debug Code

⚠️ **Ask**: "Remove debug code?"

- Show locations found
- Get explicit yes/no

### 4. Commit Remaining Changes

⚠️ **Ask**: "Commit these changes?"

- Show git diff
- Get explicit yes/no
- If yes, get/suggest commit message

### 5. Push to Remote

⚠️ **Ask**: "Push to remote?"

- Show branch and commit count
- Get explicit yes/no

### 6. Create PR

⚠️ **Ask**: "Create pull request?"

- Show PR description preview
- Get explicit yes/no
- If yes, create and show URL

---

## Important Notes

**Never assume**:

- Always ask before git operations
- Show what will happen
- Get explicit authorization
- Respect user's decisions

**Clean thoroughly**:

- DDD artifacts served their purpose
- Test artifacts aren't needed
- Debug code shouldn't ship
- Working tree should be clean

**Verify completely**:

- All tests passing
- Quality checks clean
- No unintended changes
- Ready for production

**Document everything**:

- Final summary should be comprehensive
- Include verification steps
- Note any follow-up items
- Preserve commit history

---

## Completion Message

```
✅ DDD Phase 5 Complete!

Feature: [name]
Status: Complete and verified

All temporary files cleaned.
Workspace ready for next work.

Summary saved above.

---

Thank you for using Document-Driven Development! 🚀

For your next feature, start with:

    /ddd:1-plan [feature description]

Or check current status anytime:

    /ddd:status

Need help? Run: /ddd:0-help
```

## Process

- Ultrathink step-by-step, laying out assumptions and unknowns, use the TodoWrite tool to capture all tasks and subtasks.
  - VERY IMPORTANT: Make sure to use the actual TodoWrite tool for todo lists, don't do your own task tracking, there is code behind use of the TodoWrite tool that is invisible to you that ensures that all tasks are completed fully.
  - Adhere to the @ai_context/IMPLEMENTATION_PHILOSOPHY.md and @ai_context/MODULAR_DESIGN_PHILOSOPHY.md files.
- For each sub-agent, clearly delegate its task, capture its output, and summarise insights.
- Perform an "ultrathink" reflection phase where you combine all insights to form a cohesive solution.
- If gaps remain, iterate (spawn sub-agents again) until confident.
- Where possible, spawn sub-agents in parallel to expedite the process.

---

## Troubleshooting

**"Make check is failing"**

- Fix the issues before finishing
- Or ask user if acceptable to finish with issues
- Note failures in final summary

**"Uncommitted changes remain"**

- That might be intentional
- Ask user what to do with them
- Document decision in summary

**"Can't push to remote"**

- Check remote exists
- Check permissions
- Check branch name
- Provide error details to user

**"PR creation failed"**

- Check gh CLI is installed and authenticated
- Check remote branch exists
- Provide error details to user
- User can create PR manually

---

Need help? Run `/ddd:0-help` for complete guide
