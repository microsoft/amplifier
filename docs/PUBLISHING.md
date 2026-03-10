# Publishing Guide

This guide covers how to publish Amplifier to PyPI and update the Homebrew formula.

## PyPI Trusted Publishing Setup

Amplifier uses GitHub Actions with OpenID Connect (OIDC) for secure, keyless publishing to PyPI. This eliminates the need for API tokens.

### Prerequisites

1. A PyPI account with permissions to create new projects (or manage the `amplifier` project)
2. Admin access to the `microsoft/amplifier` GitHub repository

### Step 1: Create the PyPI Project

1. Go to [PyPI](https://pypi.org/) and log in
2. If this is the first release:
   - The project will be created automatically on first publish
   - Ensure your PyPI account is verified (email confirmation)

### Step 2: Configure Trusted Publishing on PyPI

1. Go to your PyPI project page (after first release) or pre-register at: https://pypi.org/manage/account/publishing/
2. Navigate to "Publishing" → "Add a new publisher"
3. Fill in the form:
   - **PyPI Project Name**: `amplifier`
   - **Owner**: `microsoft`
   - **Repository name**: `amplifier`
   - **Workflow name**: `publish.yml`
   - **Environment name**: `pypi` (must match the environment in `.github/workflows/publish.yml`)
4. Click "Add"

### Step 3: Create GitHub Environment

1. Go to GitHub: `https://github.com/microsoft/amplifier/settings/environments`
2. Click "New environment"
3. Name it: `pypi` (must match PyPI configuration)
4. Configure environment protection rules (recommended):
   - ✅ Required reviewers (optional but recommended for production)
   - ✅ Restrict to specific branches: `main`
5. Click "Save protection rules"

### Step 4: Test the Workflow

1. Create a test release or manually trigger the workflow
2. The workflow should:
   - Build the package with `uv build`
   - Publish to PyPI using OIDC (no API tokens needed)
   - Complete without errors

### Troubleshooting

**Error: "Permission denied" or "OIDC token not found"**
- Ensure the `pypi` environment exists in GitHub
- Verify the workflow has `permissions: id-token: write`
- Check that the environment name matches in both PyPI and GitHub

**Error: "Project does not exist"**
- For first-time publishing, you may need to pre-register the project name on PyPI
- Go to: https://pypi.org/manage/account/publishing/

**Error: "Publishing not configured"**
- Double-check the PyPI trusted publisher settings
- Ensure owner/repo/workflow/environment names match exactly

## Publishing a New Release

### 1. Prepare the Release

```bash
# Ensure all changes are committed and pushed
git checkout main
git pull origin main

# Update version in pyproject.toml if needed
# Update CHANGELOG.md with release notes
```

### 2. Create and Push a Git Tag

```bash
# Create an annotated tag
git tag -a v0.1.0 -m "Release v0.1.0"

# Push the tag
git push origin v0.1.0
```

### 3. Create a GitHub Release

1. Go to: `https://github.com/microsoft/amplifier/releases/new`
2. Select the tag you just created (e.g., `v0.1.0`)
3. Title: `v0.1.0`
4. Description: Copy from CHANGELOG.md or write release notes
5. Click "Publish release"

### 4. Automated Publishing

Once you create a GitHub release:

1. **PyPI Publishing** (`.github/workflows/publish.yml`):
   - Triggers automatically on release
   - Builds the package with `uv build`
   - Publishes to PyPI via trusted publishing
   - ✅ Check: https://pypi.org/project/amplifier/

2. **Homebrew Formula Update** (`.github/workflows/update-homebrew.yml`):
   - Triggers automatically on release
   - Downloads the release tarball
   - Calculates SHA256 hash
   - Creates a PR to update `homebrew-amplifier/Formula/amplifier.rb`
   - ⚠️ Review and merge the auto-generated PR

### 5. Verify the Release

```bash
# Test PyPI installation
uv pip install amplifier
amplifier --version

# Test Homebrew installation (after merging formula PR)
brew update
brew upgrade amplifier
amplifier --version
```

## Homebrew Tap Setup

### First-Time Setup

The Homebrew formula lives in this repo under `homebrew-amplifier/`. After the first release:

1. Create a separate tap repository: `microsoft/homebrew-amplifier`
2. Copy contents from `homebrew-amplifier/` to the new repo
3. Users can then install with:
   ```bash
   brew tap microsoft/amplifier
   brew install amplifier
   ```

### Manual Formula Updates

If the automated workflow fails, update the formula manually:

```bash
# Download and hash the release tarball
VERSION="v0.1.0"
curl -sL "https://github.com/microsoft/amplifier/archive/refs/tags/${VERSION}.tar.gz" | shasum -a 256

# Update homebrew-amplifier/Formula/amplifier.rb
# Replace the url and sha256 values
# Create a PR with the changes
```

## Dependencies

### Publishing Dependencies to PyPI

Before publishing `amplifier` to PyPI, ensure dependencies are also published:

- ✅ `amplifier-core` - Check [PyPI](https://pypi.org/project/amplifier-core/)
- ✅ `amplifier-app-cli` - Check [PyPI](https://pypi.org/project/amplifier-app-cli/)

If dependencies are not on PyPI yet, they must be published first, or keep using git references in `[tool.uv.sources]` for development.

## Security Notes

- ✅ **No API tokens stored** - Trusted publishing uses short-lived OIDC tokens
- ✅ **Environment protection** - GitHub environments add approval gates
- ✅ **Automated formula updates** - Reduces manual errors in SHA256 hashes
- ⚠️ Always verify the SHA256 hash matches the release tarball before merging Homebrew PRs
