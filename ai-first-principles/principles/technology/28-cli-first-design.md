# Principle #28 - CLI-First Design

## Plain-Language Definition

CLI-First Design means building command-line interfaces as the primary way to interact with your system, treating graphical interfaces as optional layers on top. Every core operation should be accessible through composable, scriptable CLI commands that AI agents can easily invoke and chain together.

## Why This Matters for AI-First Development

AI agents excel at using command-line interfaces but struggle with graphical user interfaces. When an AI agent needs to deploy code, query a database, or configure a service, a CLI command is trivial to invoke: generate the command string, execute it, parse the output. In contrast, GUIs require complex browser automation, visual recognition, and fragile click-coordinate mapping that breaks with minor UI changes.

CLI-First design creates a natural interface layer between AI agents and your systems. Commands are self-documenting through `--help` flags, composable through pipes and redirects, testable through exit codes, and scriptable through shell automation. An AI agent can discover capabilities by running `tool --help`, chain operations with `tool1 | tool2`, and verify success through exit codes. This composability means AI agents can build sophisticated workflows from simple commands without requiring special integration code.

The benefits compound in AI-first systems. When every operation has a CLI interface, AI agents can automate anything a human can do manually. Need to orchestrate a complex deployment? The AI agent chains CLI commands. Need to debug a production issue? The AI agent runs diagnostic commands and analyzes output. Need to generate reports? The AI agent queries services via CLI and formats results. Without CLI-first design, each of these workflows requires custom API integration, increasing complexity and reducing the AI agent's autonomy.

Beyond AI automation, CLI-first design improves human workflows too. Developers can script operations, CI/CD pipelines can orchestrate complex workflows, and power users can compose tools in ways GUI designers never anticipated. The CLI becomes the universal interface that serves both humans and machines, with GUIs providing convenience for specific use cases without becoming the only access method.

## Implementation Approaches

### 1. **CLI as Primary Interface**

Design your CLI first, before building any GUI or API. Every core operation should be accessible via command-line:

```bash
# User management
app users create --email user@example.com --role admin
app users list --role admin --format json
app users delete --email user@example.com --confirm

# Deployment operations
app deploy --environment production --version v1.2.3
app rollback --environment production --to-version v1.2.0

# Data operations
app data export --table users --format csv --output users.csv
app data import --table users --input users.csv --mode upsert
```

Success looks like: Every feature accessible via CLI before adding GUI, no "GUI-only" features.

### 2. **Composable Commands with Standard I/O**

Design commands to work together through Unix pipes and standard streams:

```bash
# Commands accept input from stdin and write to stdout
app users list --format json | jq '.[] | select(.active == true)' | app notify --message "User list"

# Filter and transform through pipes
app logs fetch --since 1h | grep ERROR | app alerts create --severity high

# Combine with standard Unix tools
app metrics export | sort | uniq | wc -l
```

Commands should:
- Accept data via stdin when appropriate
- Output structured data (JSON, CSV) to stdout
- Write errors and logs to stderr
- Use exit codes to signal success/failure

Success looks like: Commands chain naturally with pipes, AI agents can build complex workflows from simple commands.

### 3. **Machine-Readable Output Formats**

Provide structured output formats that AI agents and scripts can parse reliably:

```bash
# JSON for structured data
app users list --format json
{"users": [{"id": "123", "email": "user@example.com", "role": "admin"}]}

# CSV for tabular data
app metrics fetch --format csv
timestamp,cpu_usage,memory_usage
2025-09-30T10:00:00,45.2,68.3

# YAML for configuration
app config show --format yaml
database:
  host: localhost
  port: 5432

# Plain text for human reading (default)
app users list
User: user@example.com (admin)
User: other@example.com (viewer)
```

Support `--format` flag on all commands that output data. Default to human-readable, but make machine-readable formats easily accessible.

Success looks like: AI agents can parse command output without fragile regex, scripts reliably extract data.

### 4. **Idempotent Operations**

Design CLI commands to be safely retryable without side effects:

```bash
# Idempotent configuration
app config set database.host=localhost  # Same result if run multiple times

# Idempotent resource creation
app users create --email user@example.com --idempotent
# Returns existing user if already exists, creates if not

# Declarative operations
app deploy --desired-state production.yml
# Converges to desired state regardless of current state
```

Commands should check current state before making changes, enabling safe retry and automation.

Success looks like: Commands can be run repeatedly without errors, AI agents don't need complex state tracking.

### 5. **Self-Documenting Commands**

Every command and subcommand should provide comprehensive help:

```bash
# Top-level help
app --help
Usage: app [OPTIONS] COMMAND [ARGS]...

Commands:
  users   Manage users
  deploy  Deploy applications
  config  Configuration management

# Command-specific help
app users --help
Usage: app users [OPTIONS] COMMAND [ARGS]...

Commands:
  create  Create a new user
  list    List users
  delete  Delete a user

# Subcommand help
app users create --help
Usage: app users create [OPTIONS]

Options:
  --email TEXT     User email address [required]
  --role TEXT      User role (admin, viewer, editor) [default: viewer]
  --idempotent     Return existing user if email already exists
  --format TEXT    Output format (json, yaml, text) [default: text]
```

Help text should explain:
- What the command does
- Required and optional parameters
- Default values
- Output formats
- Examples of common usage

Success looks like: AI agents can discover functionality through `--help`, humans can learn without external docs.

### 6. **Automation-Friendly Error Handling**

Provide clear exit codes and error messages that scripts can handle:

```bash
# Success: exit code 0
app users create --email new@example.com
echo $?  # 0

# User error: exit code 1
app users create --email invalid
Error: Invalid email format
echo $?  # 1

# System error: exit code 2
app users create --email user@example.com
Error: Database connection failed
echo $?  # 2

# Not found: exit code 3
app users delete --email nonexistent@example.com
Error: User not found
echo $?  # 3
```

Use exit codes consistently:
- 0: Success
- 1: Usage error (invalid arguments, validation failure)
- 2: System error (network failure, dependency unavailable)
- 3: Not found (resource doesn't exist)
- 4+: Command-specific errors

Success looks like: Scripts can handle errors programmatically, AI agents can distinguish error types.

## Good Examples vs Bad Examples

### Example 1: User Management Commands

**Good:**
```bash
# CLI provides complete user management
$ app users create --email alice@example.com --role admin --format json
{"id": "usr_123", "email": "alice@example.com", "role": "admin", "created": "2025-09-30T10:00:00Z"}

$ app users list --role admin --format json
{"users": [{"id": "usr_123", "email": "alice@example.com", "role": "admin"}]}

$ app users update usr_123 --role editor
User usr_123 updated: role changed from admin to editor

$ app users delete usr_123 --confirm
User usr_123 deleted successfully

# All operations return proper exit codes
$ echo $?
0
```

**Bad:**
```bash
# Operations only available through GUI
$ app users create
Error: User management only available through web interface at http://localhost:8000

# No structured output
$ app users list
Alice (admin)
Bob (viewer)
Charlie (editor)
# No way to parse this reliably

# Poor error handling
$ app users delete usr_999
Something went wrong
$ echo $?
0  # Wrong! Should be non-zero for errors
```

**Why It Matters:** AI agents can fully manage users via CLI in the good example. In the bad example, AI agents would need to automate a web browser, parse HTML, and handle complex UI interactions - fragile and slow. The good example is scriptable, testable, and composable; the bad example requires human intervention.

### Example 2: Deployment Automation

**Good:**
```bash
# Deployment via CLI with idempotent operations
$ app deploy production --version v1.2.3 --format json
{
  "status": "deploying",
  "version": "v1.2.3",
  "environment": "production",
  "started_at": "2025-09-30T10:00:00Z"
}

# Check deployment status
$ app deploy status production --format json
{
  "status": "complete",
  "version": "v1.2.3",
  "health": "healthy",
  "completed_at": "2025-09-30T10:05:00Z"
}

# Rollback if needed (idempotent)
$ app rollback production --to-version v1.2.0
Rollback initiated: production → v1.2.0
Previous version: v1.2.3

# Chain with health checks
$ app deploy production --version v1.2.4 && \
  app health-check production --wait && \
  app notify --message "Deploy successful" || \
  app rollback production --to-version v1.2.3
```

**Bad:**
```bash
# No CLI deployment option
$ app deploy production --version v1.2.3
Error: Please use the deployment dashboard at http://localhost:8000/deploy

# Or deployment requires interactive prompts (breaks automation)
$ app deploy production
Environment: [enter environment name] _
Version: [enter version] _
Confirm deployment? (y/n): _

# No way to check status programmatically
$ app status production
Deploying... please check web dashboard for details
```

**Why It Matters:** The good example enables fully automated CI/CD pipelines. An AI agent can deploy, monitor, and rollback without human intervention. The bad example breaks automation by requiring GUI interaction or blocking on prompts. In production environments, this difference determines whether deployments are reliable and repeatable or manual and error-prone.

### Example 3: Data Export and Processing

**Good:**
```bash
# Export data in machine-readable format
$ app data export --table users --format json --since 2025-09-01
{"users": [
  {"id": "usr_123", "email": "alice@example.com", "created": "2025-09-15"},
  {"id": "usr_456", "email": "bob@example.com", "created": "2025-09-20"}
]}

# Compose with jq for processing
$ app data export --table users --format json | \
  jq '[.users[] | select(.created >= "2025-09-15")]' | \
  jq 'length'
2

# Pipe to other commands
$ app data export --table users --format csv | \
  csvstat --count
2

# Import with idempotency
$ app data import --table users --input users.json --mode upsert
Processed 2 records: 1 created, 1 updated, 0 skipped
```

**Bad:**
```bash
# Only GUI export option
$ app data export --table users
Error: Please use the export wizard at http://localhost:8000/export

# Or non-parseable output format
$ app data export --table users
User Report
===========
alice@example.com (created Sep 15)
bob@example.com (created Sep 20)

Total users: 2

# No composition with other tools (output mixed with logs)
$ app data export --table users
Loading database connection...
Fetching users table...
Processing 2 records...
{"id": "usr_123", "email": "alice@example.com"}
Export complete
```

**Why It Matters:** The good example enables sophisticated data processing pipelines. AI agents can extract, transform, and load data using standard Unix tools. The bad example forces manual export through GUI or produces unparseable output that requires fragile regex. Data pipelines should be automated, reliable, and composable - the good example achieves this, the bad example doesn't.

### Example 4: Configuration Management

**Good:**
```bash
# View configuration in structured format
$ app config show --format yaml
database:
  host: localhost
  port: 5432
  name: production
cache:
  enabled: true
  ttl: 3600

# Set configuration values (idempotent)
$ app config set database.host=db.example.com
Configuration updated: database.host = db.example.com

# Get specific values for scripting
$ app config get database.host --format plain
db.example.com

# Validate configuration
$ app config validate
✓ Configuration valid
All required fields present
Database connection: successful
Cache connection: successful
$ echo $?
0

# Load configuration from file (declarative)
$ app config load --file production.yml
Configuration loaded from production.yml
Changes: 3 settings updated
```

**Bad:**
```bash
# Configuration only via GUI
$ app config show
Error: Configuration must be managed through settings page

# Or non-structured output
$ app config show
Database host: localhost
Database port: 5432
Cache enabled: yes
TTL: 3600 seconds

# No programmatic access
$ app config get database.host
Error: Use 'app config show' to view all settings

# No validation command
$ app config validate
Error: Unknown command 'validate'
```

**Why It Matters:** Configuration management is critical for automation. The good example lets AI agents read, update, and validate configuration programmatically. This enables automated environment setup, configuration drift detection, and infrastructure-as-code workflows. The bad example requires manual GUI interaction, making automated configuration management impossible.

### Example 5: Diagnostic and Monitoring Commands

**Good:**
```bash
# Fetch logs with filtering
$ app logs fetch --service api --level error --since 1h --format json
{"logs": [
  {"timestamp": "2025-09-30T10:15:00Z", "level": "error", "message": "Database timeout", "service": "api"},
  {"timestamp": "2025-09-30T10:30:00Z", "level": "error", "message": "Rate limit exceeded", "service": "api"}
]}

# Stream logs in real-time
$ app logs stream --service api --follow
[2025-09-30T10:45:00Z] INFO: Request received
[2025-09-30T10:45:01Z] INFO: Response sent

# Get metrics
$ app metrics fetch --metric cpu_usage --period 5m --format csv
timestamp,cpu_usage
2025-09-30T10:40:00,45.2
2025-09-30T10:41:00,47.8
2025-09-30T10:42:00,44.1

# Health check with proper exit codes
$ app health-check --service api
✓ API service: healthy
✓ Database: connected
✓ Cache: connected
$ echo $?
0

# Compose diagnostics
$ app logs fetch --level error --since 1h | \
  jq -r '.logs[].message' | \
  sort | uniq -c | sort -rn
2 Database timeout
1 Rate limit exceeded
```

**Bad:**
```bash
# Logs only in web interface
$ app logs fetch
Error: View logs at http://localhost:8000/logs

# Or mixed output format
$ app logs fetch --service api
Fetching logs for api service...
Connected to log server
Found 2 logs

2025-09-30T10:15:00Z ERROR Database timeout
2025-09-30T10:30:00Z ERROR Rate limit exceeded

Done

# No structured metrics
$ app metrics fetch
CPU: 45%
Memory: 68%
Disk: 23%

# Health check doesn't use exit codes
$ app health-check
API service: healthy
Database: disconnected
$ echo $?
0  # Wrong! Should be non-zero if something is unhealthy
```

**Why It Matters:** Diagnostics and monitoring are essential for AI-driven operations. The good example enables automated log analysis, alerting, and incident response. An AI agent can detect error patterns, correlate metrics, and trigger remediation automatically. The bad example requires human interpretation of logs in a web interface, preventing automation and slowing incident response.

## Related Principles

- **[Principle #29 - Machine-Readable Everything](29-machine-readable-everything.md)** - CLI-first design produces machine-readable output, enabling AI agents to parse and process command results reliably.

- **[Principle #12 - Composable Tool Chains](../process/12-composable-tool-chains.md)** - CLIs are naturally composable through pipes and scripts, allowing AI agents to build sophisticated workflows from simple commands.

- **[Principle #31 - Idempotency by Design](31-idempotency-by-design.md)** - CLI commands should be idempotent, allowing AI agents to safely retry operations without side effects or state tracking.

- **[Principle #25 - APIs as First-Class Citizens](25-apis-as-first-class-citizens.md)** - CLI tools often wrap APIs, providing a scriptable interface to programmatic services.

- **[Principle #30 - Explicit State Management](30-explicit-state-management.md)** - CLI commands that query and modify state explicitly enable AI agents to understand and manage system state.

- **[Principle #13 - Automation as Default Path](../process/13-automation-as-default-path.md)** - CLI-first design makes automation the natural default, as every operation is scriptable from day one.

## Common Pitfalls

1. **GUI-Only Features**: Building features that are only accessible through graphical interfaces, making them impossible for AI agents to automate.
   - Example: User management requires clicking through a web form with no CLI equivalent.
   - Impact: AI agents cannot manage users, requiring manual intervention for user operations. Automation impossible, reduces system autonomy.

2. **Interactive Prompts in Scripts**: Using interactive prompts (like "Are you sure? (y/n)") that block automated execution.
   - Example: `app deploy production` prompts for confirmation, breaking CI/CD pipelines.
   - Impact: Scripts hang waiting for input, deployments fail in CI/CD, AI agents cannot complete operations without human intervention.

3. **Unparseable Output Format**: Mixing structured data with logs, progress messages, or decorative formatting in stdout.
   - Example: `app data export` prints "Exporting...", then JSON, then "Done!" all to stdout.
   - Impact: Parsing output requires fragile regex, AI agents cannot reliably extract data, compositions with other tools fail.

4. **Ignoring Exit Codes**: Returning success exit code (0) even when operations fail.
   - Example: `app users delete usr_999` returns 0 even though user doesn't exist.
   - Impact: Scripts cannot detect failures, error handling breaks, cascading failures in automation pipelines.

5. **Non-Idempotent Commands**: Commands that produce different results or fail when run multiple times.
   - Example: `app users create user@example.com` fails with "User already exists" instead of returning the existing user.
   - Impact: AI agents need complex state tracking, retry logic becomes fragile, automation requires error handling for normal cases.

6. **Missing Machine-Readable Formats**: Only providing human-readable output without JSON, YAML, or CSV options.
   - Example: `app metrics fetch` only outputs formatted tables with no `--format json` flag.
   - Impact: Parsing requires screen scraping, output format changes break scripts, AI agents cannot reliably extract data.

7. **Inconsistent Command Structure**: Using different patterns for similar operations across commands.
   - Example: `app users create --email` but `app deploy --target production` (inconsistent parameter names).
   - Impact: AI agents cannot infer command patterns, learning curve for automation, increased likelihood of errors.

## Tools & Frameworks

### CLI Framework Libraries
- **Click**: Python CLI framework with decorators, automatic help generation, parameter validation, and command groups. Excellent for building hierarchical command structures.
- **Typer**: Modern Python CLI framework built on Click, adds type hints for automatic validation and documentation. Ideal for type-safe CLIs.
- **argparse**: Python standard library CLI parser, good for simple CLIs without dependencies. Less feature-rich but widely available.
- **cobra**: Go CLI framework used by Kubernetes, Docker. Powerful command structure with automatic documentation generation.
- **clap**: Rust CLI framework with derive macros for automatic parsing from structs. Type-safe and performant.

### Output Formatting
- **rich**: Python library for beautiful terminal output, tables, progress bars, syntax highlighting. Makes human-readable output compelling.
- **tabulate**: Python library for formatting tabular data in various formats (plain, grid, markdown, HTML).
- **jq**: JSON processor for CLI, essential for transforming and filtering JSON output from commands.

### Testing and Validation
- **pytest**: Python testing framework with excellent CLI application testing support through fixtures and subprocess management.
- **bats**: Bash Automated Testing System for testing shell scripts and CLI tools with assertions.
- **shunit2**: Shell script unit testing framework for validating CLI behavior and output.

### Documentation Generation
- **click-man**: Generates man pages from Click CLI applications automatically.
- **sphinx-click**: Sphinx extension for documenting Click CLIs in project documentation.
- **cog**: Code generation tool for embedding command output in documentation (keeping examples up-to-date).

### Shell Integration
- **click-completion**: Adds shell completion support (bash, zsh, fish) to Click applications.
- **argcomplete**: Python package for intelligent shell completion based on argparse definitions.

## Implementation Checklist

When implementing this principle, ensure:

- [ ] Every core feature has a corresponding CLI command (no GUI-only features)
- [ ] Commands accept structured input (JSON, YAML, files) and produce structured output
- [ ] All commands support `--format` flag with at least JSON and plain text options
- [ ] Commands use proper exit codes (0 for success, non-zero for errors)
- [ ] Commands are idempotent where possible, safe to retry without side effects
- [ ] Interactive prompts can be bypassed with flags (e.g., `--yes`, `--confirm`)
- [ ] Every command and subcommand has comprehensive `--help` documentation
- [ ] Commands compose naturally with pipes and standard Unix tools
- [ ] Errors go to stderr, data goes to stdout, enabling clean composition
- [ ] Commands follow consistent naming and parameter conventions across the CLI
- [ ] Long-running operations provide progress feedback to stderr (not stdout)
- [ ] CLI is self-contained (no external dependencies on GUI or web services)

## Metadata

**Category**: Technology
**Principle Number**: 28
**Related Patterns**: Command Pattern, Pipes and Filters, Chain of Responsibility, Builder Pattern
**Prerequisites**: Understanding of Unix philosophy, command-line conventions, shell scripting, exit codes
**Difficulty**: Medium
**Impact**: High

---

**Status**: Complete
**Last Updated**: 2025-09-30
**Version**: 1.0