# Guide: Submitting PR to Microsoft/Amplifier

## Current Status
- ✅ Your branch: `feature/aider-integration`
- ✅ Your fork: `michaeljabbour/amplifier`
- ✅ Upstream: `microsoft/amplifier`
- ✅ Changes committed and pushed to your fork

## Step-by-Step Process

### 1. Sync Your Fork with Upstream (Recommended)

First, ensure your fork is up-to-date with Microsoft's main branch:

```bash
# Fetch latest from Microsoft
git fetch upstream

# Check out your main branch
git checkout main

# Merge upstream changes
git merge upstream/main

# Push updated main to your fork
git push origin main
```

### 2. Rebase Your Feature Branch (If Needed)

If upstream has new commits, rebase your feature branch:

```bash
# Go back to your feature branch
git checkout feature/aider-integration

# Rebase on updated main
git rebase main

# Force push if rebase was needed
git push --force-with-lease origin feature/aider-integration
```

### 3. Create Pull Request to Microsoft

#### Option A: Via GitHub Web Interface (Recommended)

1. Go to: https://github.com/microsoft/amplifier
2. You should see a banner: "michaeljabbour recently pushed branches"
3. Click **"Compare & pull request"**
4. Or manually go to: https://github.com/microsoft/amplifier/compare/main...michaeljabbour:amplifier:feature/aider-integration

#### Option B: Via GitHub CLI

```bash
# Create PR from your fork to Microsoft's repo
gh pr create \
  --repo microsoft/amplifier \
  --base main \
  --head michaeljabbour:feature/aider-integration \
  --title "feat: Add Aider integration for AI-powered code regeneration" \
  --body-file PR_BODY.md
```

### 4. PR Template

Use this template for your PR description:

```markdown
## Summary

This PR integrates [Aider](https://aider.chat/) into Amplifier, enabling AI-powered code generation and regeneration that follows Amplifier's development philosophies.

## Motivation

- Enable automatic module regeneration following established philosophies
- Support multiple cognitive styles (fractalized, modular, zen)
- Reduce manual refactoring effort while maintaining code quality
- Integrate AI assistance directly into the development workflow

## Key Features

### 🔧 Isolated Installation
- Aider runs in separate `.aider-venv` to avoid dependency conflicts
- One-command setup via `./scripts/setup-aider.sh`

### 🎯 Philosophy-Based Regeneration
Three approaches supported:
- **Fractalized Thinking**: Patient knot-untying approach
- **Modular Design**: Brick-and-stud architecture
- **Zen Architecture**: Ruthless simplicity

### 📦 CLI Integration
Full command suite under `amplifier aider`:
- `status` - Check installation status
- `regenerate` - Regenerate single modules
- `batch` - Batch regeneration with patterns
- `edit` - Direct AI-powered editing

### 🔄 Pre-commit Hooks
Optional automatic regeneration before commits:
```bash
export AIDER_REGENERATE=true
git commit -m "Auto-regenerated code"
```

## Changes

### New Files
- `amplifier/cli_tools/aider.py` - Core Aider integration module
- `scripts/setup-aider.sh` - Installation script
- `.githooks/pre-commit-aider` - Pre-commit regeneration hook
- `docs/aider-integration.md` - Usage documentation
- `ai_context/FRACTALIZED_THINKING_*.md` - Philosophy documents

### Modified Files
- `amplifier/cli.py` - Added Aider command group
- `pyproject.toml` - Excluded `.aider-venv` from pyright

## Testing

- [x] Aider installs in isolated environment
- [x] No dependency conflicts with main environment
- [x] CLI commands accessible via `amplifier aider`
- [x] Status command shows installation details
- [x] Regeneration creates proper logs
- [x] Pre-commit hook structure validated

## Usage Example

```bash
# Setup
./scripts/setup-aider.sh

# Check status
amplifier aider status --verbose

# Regenerate a module
export ANTHROPIC_API_KEY=your_key
amplifier aider regenerate module.py --philosophy fractalized

# Batch regeneration
amplifier aider batch "src/**/*.py" --dry-run
```

## Requirements

- Users need to provide their own API keys (Anthropic/OpenAI)
- Python 3.11+
- uv package manager

## Documentation

Comprehensive documentation added in `docs/aider-integration.md` covering:
- Installation process
- All available commands
- Philosophy explanations
- Pre-commit hook configuration
- Troubleshooting guide

## Future Enhancements

- Parallel regeneration for multiple modules
- Incremental regeneration of changed sections
- Team synchronization of regeneration patterns
- Philosophy learning from codebase patterns

## Breaking Changes

None. This is a purely additive feature.

## Checklist

- [x] Code follows project style guidelines
- [x] Tests pass locally
- [x] Documentation updated
- [x] No breaking changes
- [x] Commits follow conventional format
- [x] Branch is up-to-date with main

Closes #[issue_number] (if applicable)
```

### 5. After Creating the PR

1. **Monitor CI/CD**: Watch for any automated checks
2. **Address Feedback**: Be responsive to reviewer comments
3. **Keep Updated**: If main branch updates, rebase as needed
4. **Sign CLA**: Microsoft may require a Contributor License Agreement

### 6. Common Issues & Solutions

#### Merge Conflicts
```bash
# If conflicts arise
git fetch upstream
git rebase upstream/main
# Resolve conflicts manually
git add .
git rebase --continue
git push --force-with-lease origin feature/aider-integration
```

#### CLA Required
- Microsoft requires CLA signing for contributions
- The bot will comment with instructions
- Follow the link to sign electronically

#### CI Failures
- Check the Actions tab on your PR
- Fix any linting/testing issues
- Push fixes to your branch (automatically updates PR)

## Your Next Steps

1. Sync with upstream (Step 1 above)
2. Go to https://github.com/microsoft/amplifier
3. Create the pull request
4. Use the template provided above
5. Monitor and respond to feedback

## Useful Links

- Your fork: https://github.com/michaeljabbour/amplifier
- Upstream: https://github.com/microsoft/amplifier
- PR comparison: https://github.com/microsoft/amplifier/compare/main...michaeljabbour:amplifier:feature/aider-integration