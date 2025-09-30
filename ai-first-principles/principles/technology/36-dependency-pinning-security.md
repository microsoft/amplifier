# Principle #36 - Dependency Pinning and Security Scanning

## Plain-Language Definition

Dependency pinning means locking every dependency to an exact version so your software builds the same way every time. Security scanning means automatically checking those dependencies for known vulnerabilities so you can update deliberately when needed.

## Why This Matters for AI-First Development

When AI agents build and regenerate code, they need reproducible environments. An AI agent that builds a module today should create exactly the same binary tomorrow. Without dependency pinning, "latest" versions can silently change, breaking functionality or introducing vulnerabilities that weren't present when the AI agent validated the code.

AI-driven development amplifies three critical risks:

1. **Reproducibility failures**: AI agents regenerate modules frequently. If dependencies aren't pinned, the regenerated code might pull different library versions than the original, causing subtle bugs. What worked in testing might fail in production because the AI agent unknowingly used a different dependency version.

2. **Security drift**: AI agents don't inherently track security advisories. Without automated scanning, a dependency that was safe when initially selected can become vulnerable. The AI agent has no way to know that yesterday's safe library version is today's attack vector.

3. **Update cascades**: Unpinned dependencies create cascading updates where one library's update forces updates across the entire dependency tree. AI agents can't reason about these cascades without explicit version constraints, making it impossible to predict what will actually run.

With pinned dependencies and security scanning, AI agents gain predictability. They know exactly what versions will be installed, can regenerate modules with confidence, and receive explicit signals when updates are needed for security reasons. This transforms dependency management from an invisible source of chaos into a controlled, auditable process.

## Implementation Approaches

### 1. **Lock File Generation and Validation**

Generate lock files that capture the complete dependency tree with exact versions:

```bash
# Python with pip-tools
pip-compile requirements.in --output-file requirements.txt

# Node.js with npm
npm install --package-lock-only

# Rust with cargo
cargo generate-lockfile

# Go with modules
go mod download
```

Commit lock files to version control and validate them in CI. The lock file becomes the source of truth for what actually runs.

**When to use**: Every project, every language. Lock files are the foundation of reproducible builds.

**Success looks like**: `git diff` shows exactly what dependency versions changed. CI fails if lock file is out of sync with dependency declarations.

### 2. **Exact Version Pinning in Manifests**

Pin dependencies to exact versions, not version ranges:

```toml
# Good: Exact version
requests = "==2.31.0"

# Bad: Range allows drift
requests = ">=2.30.0,<3.0.0"
```

This prevents automated tools or AI agents from silently upgrading to "compatible" versions that might introduce breaking changes.

**When to use**: Production systems, libraries used across multiple projects, dependencies with history of breaking changes.

**Success looks like**: Dependency updates only happen when explicitly requested. No surprise version changes during routine operations.

### 3. **Automated Vulnerability Scanning**

Integrate security scanning into CI/CD pipeline:

```yaml
# GitHub Actions example
- name: Security scan
  run: |
    pip install safety
    safety check --file requirements.txt --json
```

Scan runs on every pull request and blocks merging if high-severity vulnerabilities are found.

**When to use**: All projects, especially those handling sensitive data or exposed to the internet.

**Success looks like**: Vulnerabilities are caught before reaching production. Security updates are prioritized based on severity.

### 4. **Automated Dependency Updates**

Use tools like Dependabot or Renovate to automate dependency update PRs:

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
```

Tools create PRs with updated versions, which are tested by CI before merging.

**When to use**: Projects with active development, teams that can review PRs regularly.

**Success looks like**: Dependency updates are reviewed and tested before merging. Security patches are applied within days of release.

### 5. **Software Bill of Materials (SBOM)**

Generate and maintain an SBOM that lists all dependencies:

```bash
# Using cyclonedx
pip install cyclonedx-bom
cyclonedx-py -r requirements.txt -o sbom.json

# Using syft
syft packages dir:. -o json > sbom.json
```

SBOMs provide a complete inventory for security audits and compliance.

**When to use**: Regulated industries, security-critical applications, enterprise deployments.

**Success looks like**: You can answer "what versions of library X are running in production?" instantly. Compliance audits have complete dependency lists.

### 6. **Dependency Layer Separation**

Separate direct dependencies from transitive dependencies:

```python
# requirements.in (direct dependencies only)
django==4.2.7
celery==5.3.4

# requirements.txt (complete tree with versions)
# Generated from requirements.in via pip-compile
django==4.2.7
celery==5.3.4
kombu==5.3.4  # transitive dependency
vine==5.1.0   # transitive dependency
...
```

This separates what you explicitly depend on from what gets pulled in transitively.

**When to use**: Large projects with many dependencies, when you need to audit direct vs transitive risk.

**Success looks like**: Security updates distinguish between vulnerabilities in your choices vs transitive dependencies.

## Good Examples vs Bad Examples

### Example 1: Python Dependency Management

**Good:**
```python
# requirements.in (what you want)
django==4.2.7
psycopg2-binary==2.9.9
celery==5.3.4

# Generate lock file
# $ pip-compile requirements.in --output-file requirements.txt

# requirements.txt (exact versions, all deps)
django==4.2.7
    # via -r requirements.in
psycopg2-binary==2.9.9
    # via -r requirements.in
celery==5.3.4
    # via -r requirements.in
kombu==5.3.4
    # via celery
vine==5.1.0
    # via
    #   celery
    #   kombu
# ... complete dependency tree with exact versions
```

**Bad:**
```python
# requirements.txt (ranges allow drift)
django>=4.0.0
psycopg2-binary
celery~=5.3

# Running pip install today vs tomorrow can yield different versions
# AI agent regenerating this module gets unpredictable results
```

**Why It Matters:** The good example ensures that `pip install -r requirements.txt` installs identical versions every time. An AI agent regenerating a module will get the exact same dependencies, making builds reproducible. The bad example allows version drift—today's Django 4.2.7 could become tomorrow's Django 4.2.8, introducing unexpected behavior.

### Example 2: Node.js Lock File Validation

**Good:**
```json
// package.json
{
  "name": "my-app",
  "dependencies": {
    "express": "4.18.2",
    "lodash": "4.17.21"
  }
}

// .github/workflows/ci.yml
name: CI
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
      - run: npm ci  # Uses package-lock.json, fails if out of sync
      - run: npm run test
```

**Bad:**
```json
// package.json
{
  "name": "my-app",
  "dependencies": {
    "express": "^4.18.0",  // Caret allows minor/patch updates
    "lodash": "*"          // Star allows any version
  }
}

// .github/workflows/ci.yml
name: CI
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm install  # Ignores lock file, fetches "latest compatible"
      - run: npm run test
```

**Why It Matters:** `npm ci` enforces that the lock file matches package.json and fails if they're out of sync. This catches dependency drift immediately. `npm install` updates the lock file silently, allowing different versions in different environments. An AI agent running tests could pass in CI but fail in production due to version mismatches.

### Example 3: Security Scanning in CI Pipeline

**Good:**
```yaml
# .github/workflows/security.yml
name: Security Scan
on: [push, pull_request]

jobs:
  dependency-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run safety check
        run: |
          pip install safety
          safety check --file requirements.txt --exit-code 1

      - name: Run Snyk scan
        run: |
          npm install -g snyk
          snyk test --severity-threshold=high

      - name: Generate SBOM
        run: |
          pip install cyclonedx-bom
          cyclonedx-py -r requirements.txt -o sbom.json

      - name: Upload SBOM
        uses: actions/upload-artifact@v3
        with:
          name: sbom
          path: sbom.json
```

**Bad:**
```yaml
# .github/workflows/security.yml
name: Security Scan
on:
  schedule:
    - cron: '0 0 * * 0'  # Only runs weekly

jobs:
  dependency-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Check for vulnerabilities
        run: |
          pip install safety
          safety check --file requirements.txt || true  # Ignores failures
        continue-on-error: true  # Doesn't block merge
```

**Why It Matters:** The good example scans on every push and PR, blocking merges if vulnerabilities are found. It generates an SBOM for audit trails. The bad example only scans weekly and ignores failures, allowing vulnerable code to reach production. An AI agent submitting code has no feedback that it's introducing security risks.

### Example 4: Rust Cargo Lock File

**Good:**
```toml
# Cargo.toml
[package]
name = "my-app"
version = "0.1.0"
edition = "2021"

[dependencies]
serde = { version = "1.0.193", features = ["derive"] }
tokio = { version = "1.35.0", features = ["full"] }

# Cargo.lock is committed to version control
# Running `cargo build` uses exact versions from Cargo.lock
# CI validates Cargo.lock is up to date

# .github/workflows/ci.yml
name: CI
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions-rs/toolchain@v1
        with:
          toolchain: stable
      - name: Check lock file
        run: cargo update --dry-run
      - name: Build
        run: cargo build --locked  # Fails if lock file is stale
```

**Bad:**
```toml
# Cargo.toml
[package]
name = "my-app"
version = "0.1.0"
edition = "2021"

[dependencies]
serde = "1"  # Allows any 1.x version
tokio = "*"  # Allows any version

# Cargo.lock is in .gitignore (not committed)
# Every developer and CI run gets different versions

# .github/workflows/ci.yml
name: CI
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions-rs/toolchain@v1
      - run: cargo build  # Generates new lock file each time
```

**Why It Matters:** Committing Cargo.lock ensures everyone builds with the same dependency versions. Using `--locked` flag fails fast if versions drift. Not committing the lock file means different developers and CI runs can get different versions, making bugs irreproducible. An AI agent regenerating a module needs the lock file to ensure consistency.

### Example 5: Python Poetry with Version Groups

**Good:**
```toml
# pyproject.toml
[tool.poetry.dependencies]
python = "^3.11"
django = "4.2.7"
celery = "5.3.4"
redis = "5.0.1"

[tool.poetry.group.dev.dependencies]
pytest = "7.4.3"
black = "23.12.0"
mypy = "1.7.1"

# poetry.lock committed to repo
# CI runs:
# $ poetry install --sync  # Enforces exact versions from lock
# $ poetry check            # Validates pyproject.toml and lock consistency
# $ poetry export -f requirements.txt --output requirements.txt

# .github/workflows/ci.yml
name: CI
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install poetry
        run: pip install poetry==1.7.1
      - name: Validate lock
        run: poetry check --lock
      - name: Install deps
        run: poetry install --sync
      - name: Run tests
        run: poetry run pytest
```

**Bad:**
```toml
# pyproject.toml
[tool.poetry.dependencies]
python = "^3.9"
django = "^4.0"     # Caret allows minor updates
celery = "~5.3"     # Tilde allows patch updates
redis = "*"         # Any version

[tool.poetry.group.dev.dependencies]
pytest = ">=7.0"    # Range allows upgrades
black = "latest"    # Not a valid version
mypy = "*"

# poetry.lock not committed (in .gitignore)

# .github/workflows/ci.yml
name: CI
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install poetry
      - run: poetry install  # Generates new lock file
      - run: poetry run pytest
```

**Why It Matters:** Poetry with exact versions and committed lock file creates reproducible environments. The `--sync` flag removes packages not in the lock file, preventing pollution. Version ranges and uncommitted lock files allow drift—CI might pass with Django 4.2.7 while production runs 4.2.8. An AI agent can't reason about this drift without explicit version constraints.

## Related Principles

- **[Principle #31 - Idempotency by Design](31-idempotency-by-design.md)** - Pinned dependencies make builds idempotent; running install twice produces the same environment

- **[Principle #18 - Automated Testing as Specification](../process/18-automated-testing-as-specification.md)** - Tests validate that pinned versions work correctly; updating dependencies requires test validation

- **[Principle #15 - Branch-Per-Task Workflow](../process/15-branch-per-task-workflow.md)** - Dependency updates happen in dedicated branches with full CI validation before merging

- **[Principle #38 - Container-Native Deployment](38-container-native-deployment.md)** - Containers bundle pinned dependencies, making the entire environment reproducible

- **[Principle #42 - Infrastructure as Code](../governance/42-infrastructure-as-code.md)** - Infrastructure dependencies (Terraform providers, Ansible modules) must be pinned like application dependencies

- **[Principle #11 - Continuous Validation with Fast Feedback](../process/11-continuous-validation-fast-feedback.md)** - Security scanning provides fast feedback on vulnerable dependencies before they reach production

## Common Pitfalls

1. **Pinning Only Direct Dependencies**: Pinning only the libraries you explicitly import leaves transitive dependencies unpinned, allowing them to drift.
   - Example: Pinning `django==4.2.7` but not `sqlparse` (a transitive dependency) means SQL parsing behavior can change unexpectedly.
   - Impact: Transitive dependency updates can introduce bugs or vulnerabilities that appear to come from your direct dependencies.

2. **Ignoring Lock File Conflicts**: When merging branches, lock file conflicts are often resolved by running `npm install` or `pip install`, which silently updates versions.
   - Example: Two branches pin different versions of a library. Merge conflict is "resolved" by installing both, which picks one version arbitrarily.
   - Impact: The merged lock file may not reflect what either branch tested, causing unexpected failures.

3. **Security Scanning Without Action**: Running security scans but not acting on results (or setting `continue-on-error: true`) makes scanning useless.
   - Example: Safety finds a critical vulnerability in `requests==2.28.0`, but CI is configured to ignore failures.
   - Impact: Vulnerable code reaches production because the security signal was ignored. AI agents have no feedback to avoid vulnerable versions.

4. **Over-Constraining Dependencies in Libraries**: Library authors pinning exact versions force downstream users into dependency conflicts.
   - Example: A library pins `pytest==7.4.0` exactly. Users can't use `pytest==7.4.3` even though it's compatible.
   - Impact: Dependency resolution fails, forcing users to avoid your library or hack around the constraints.

5. **Stale Lock Files**: Lock files that are out of sync with dependency declarations cause confusion about what's actually installed.
   - Example: `package.json` says `lodash: "4.17.21"` but `package-lock.json` has `lodash@4.17.20`. Running `npm ci` installs 4.17.20.
   - Impact: Developers think they're using one version but are actually using another. Bugs are hard to reproduce.

6. **Not Committing Lock Files**: Treating lock files as build artifacts rather than source code allows every environment to diverge.
   - Example: `poetry.lock` is in `.gitignore`. Every developer runs `poetry install` and gets different dependency versions.
   - Impact: "Works on my machine" becomes impossible to debug because no two machines have the same dependencies.

7. **Automated Updates Without Review**: Auto-merging dependency updates without human or CI review can introduce breaking changes.
   - Example: Dependabot auto-merges a "patch" update that actually breaks the API (semantic versioning violated by upstream).
   - Impact: Production breaks because a dependency update was assumed safe but wasn't tested.

## Tools & Frameworks

### Python Dependency Management
- **pip-tools**: Compiles `requirements.in` to `requirements.txt` with exact versions and full dependency tree. Simple, focused, widely compatible.
- **Poetry**: Modern dependency management with virtual environments, lock files, and version resolution. Best for new projects.
- **pipenv**: Combines pip and virtualenv with lock files. Older alternative to Poetry.
- **uv**: Ultra-fast Python package installer with lock file support. Drop-in replacement for pip-tools workflows.

### Node.js Dependency Management
- **npm**: Built-in package manager with `package-lock.json`. Use `npm ci` for reproducible installs.
- **yarn**: Alternative package manager with `yarn.lock`. Faster than npm in many cases.
- **pnpm**: Efficient package manager using symlinks to save disk space. Creates `pnpm-lock.yaml`.

### Rust Dependency Management
- **Cargo**: Built-in dependency manager with `Cargo.lock`. Commit lock file for applications, ignore for libraries.

### Security Scanning
- **Safety**: Python vulnerability scanner using a database of known CVEs. Free for open source.
- **Snyk**: Multi-language security scanner with detailed remediation advice. Integrates with GitHub, GitLab, CI/CD.
- **Dependabot**: GitHub's built-in tool for automated dependency updates and security alerts.
- **Renovate**: Open-source alternative to Dependabot with more configuration options.
- **OWASP Dependency-Check**: Language-agnostic security scanner that generates reports on vulnerabilities.
- **Trivy**: Container and filesystem scanner for vulnerabilities and misconfigurations.

### SBOM Generation
- **CycloneDX**: Industry-standard SBOM format with tools for Python, Node.js, Java, .NET.
- **Syft**: CLI tool to generate SBOMs from containers, filesystems, or package manifests.
- **Grype**: Vulnerability scanner that works with Syft-generated SBOMs.

### CI/CD Integration
- **GitHub Actions**: Supports dependency caching, security scanning workflows, and artifact uploads.
- **GitLab CI**: Built-in dependency scanning and license compliance checking.
- **CircleCI**: Supports orbs for dependency caching and security scanning.

## Implementation Checklist

When implementing this principle, ensure:

- [ ] All dependency declarations use exact versions or are compiled to exact versions via lock files
- [ ] Lock files are committed to version control and treated as source code
- [ ] CI validates that lock files are in sync with dependency declarations
- [ ] Installation commands in CI use flags that enforce lock file usage (`npm ci`, `pip install --require-hashes`, `cargo build --locked`)
- [ ] Security scanning runs on every push and pull request, blocking merge on high-severity vulnerabilities
- [ ] Automated dependency update tools (Dependabot, Renovate) are configured and creating PRs
- [ ] Dependency updates are reviewed and tested before merging, not auto-merged
- [ ] SBOMs are generated and stored for production deployments
- [ ] Transitive dependencies are included in lock files, not just direct dependencies
- [ ] Libraries use version ranges in their dependency declarations but commit lock files for development
- [ ] Security alerts are monitored and acted upon within SLA (e.g., critical vulnerabilities patched within 48 hours)
- [ ] Documentation explains how to update dependencies and regenerate lock files

## Metadata

**Category**: Technology
**Principle Number**: 36
**Related Patterns**: Reproducible Builds, Bill of Materials, Security-by-Default, Continuous Security, Semantic Versioning
**Prerequisites**: Version control system, CI/CD pipeline, package manager for your language
**Difficulty**: Medium
**Impact**: High

---

**Status**: Complete
**Last Updated**: 2025-09-30
**Version**: 1.0