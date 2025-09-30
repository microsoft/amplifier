# Principle #15 - Git-Based Everything

## Plain-Language Definition

Store all project artifacts—code, documentation, configuration, data schemas, and infrastructure definitions—in Git repositories. Git provides version control, audit trails, and rollback capabilities for everything that matters to your project.

## Why This Matters for AI-First Development

When AI agents build and modify systems, they need complete visibility into what has changed, why, and when. Git provides this foundation by tracking every change to every artifact with full history and context. Without Git as the source of truth, AI agents operate in a fog—unable to understand the evolution of the codebase, unable to roll back mistakes, and unable to coordinate changes across multiple artifacts.

AI-first development introduces unique challenges that Git-based workflows directly address:

1. **AI agents make mistakes**: When an AI agent generates broken code or invalid configuration, you need to roll back cleanly. Git's atomic commits and branch-based workflows make this trivial. Without Git, you're manually comparing files and hoping you can reconstruct the working state.

2. **AI agents need context**: To generate correct code, AI agents need to understand the current state of the system and how it evolved. Git commits provide this narrative—each commit tells a story about what changed and why. This context makes AI generations more accurate and aligned with the project's direction.

3. **Multiple AI agents must coordinate**: When multiple agents work on different parts of the system, Git's branching and merging capabilities prevent conflicts. Each agent works in isolation on a branch, and Git handles the integration. Without Git, agents overwrite each other's work and create chaos.

Beyond coordination, Git provides three critical capabilities for AI-driven development:

**Auditability**: Every change is tracked with who, what, when, and why. When an AI agent introduces a bug, you can trace exactly what changed and when. This audit trail is essential for debugging, compliance, and learning from mistakes.

**Safety**: Git's branching model allows AI agents to experiment without risk. Create a branch, try something bold, and if it fails, delete the branch. The main codebase remains untouched. This safety net encourages innovation and rapid iteration.

**Reproducibility**: With everything in Git, you can reproduce any historical state of the system. Need to debug an issue from last month? Check out that commit. Want to compare performance before and after a major refactor? Git makes this instant. AI agents can analyze historical data to learn patterns and avoid repeating mistakes.

## Implementation Approaches

### 1. **Code in Git**

All source code lives in Git repositories with clear branch strategies:

- **Main branch protection**: Require pull requests and CI checks before merging to main
- **Feature branches**: One branch per feature or fix, short-lived and focused
- **Commit conventions**: Use Conventional Commits (feat:, fix:, docs:) for clarity
- **Atomic commits**: Each commit represents one logical change that could be reverted independently

**When to use**: Always, for every project. This is non-negotiable.

**Success looks like**: Every developer and AI agent commits to Git. The main branch is always deployable. The commit history tells a clear story of the project's evolution.

### 2. **Documentation in Git**

Documentation lives alongside code in the same repository, written in markdown:

- **Co-location**: Store docs in `/docs` or alongside the code they document
- **Versioning**: Documentation versions match code versions automatically
- **Review process**: Documentation changes go through the same PR process as code
- **Generation**: AI agents can generate and update docs automatically from code

**When to use**: For all project documentation—architecture, API specs, runbooks, onboarding guides.

**Success looks like**: Documentation is always in sync with code. Finding docs is trivial. Historical documentation is available by checking out old commits.

### 3. **Configuration in Git**

All configuration files—environment configs, feature flags, infrastructure settings—live in Git:

- **Environment files**: Separate configs for dev, staging, production (secrets excluded)
- **Feature flags**: Configuration as code for gradual rollouts
- **Infrastructure config**: Terraform, Kubernetes manifests, Docker compose files
- **Validation**: CI validates configuration syntax and consistency

**When to use**: For any configuration that affects system behavior or deployment.

**Success looks like**: Configuration changes are tracked, reviewed, and reversible. You can reproduce any environment configuration from Git history.

### 4. **Data Schemas in Git**

Database schemas, API contracts, and data models are versioned in Git:

- **Migration files**: Sequential migration scripts with clear naming (001_initial.sql, 002_add_users.sql)
- **Schema documentation**: Generated from code or hand-written, stored alongside schemas
- **API contracts**: OpenAPI specs, GraphQL schemas, protobuf definitions
- **Validation**: CI validates schema changes for breaking changes

**When to use**: For all data structure definitions that multiple components depend on.

**Success looks like**: Schema changes are reviewed before deployment. You can trace when and why a field was added or removed. API contracts are enforced through automated validation.

### 5. **Infrastructure as Code in Git**

Infrastructure definitions live in Git, making infrastructure reproducible and versionable:

- **Terraform/Pulumi**: Declarative infrastructure with state files in remote backends
- **Kubernetes manifests**: YAML definitions for all cluster resources
- **Docker files**: Container definitions and multi-stage build configurations
- **CI/CD pipelines**: GitHub Actions, GitLab CI, or Jenkins pipeline definitions

**When to use**: For all infrastructure that can be defined as code rather than manually configured.

**Success looks like**: You can recreate your entire infrastructure from Git. Infrastructure changes are reviewed and tested like code changes. Disaster recovery is a `git clone` and `terraform apply` away.

### 6. **AI-Generated Artifacts in Git**

Outputs from AI agents—generated code, documentation, test cases, migration scripts—are committed to Git:

- **Attribution**: Git commit metadata shows which AI agent generated what
- **Review**: AI-generated code goes through the same review process as human code
- **Iteration**: AI can improve its outputs based on feedback captured in PR comments
- **Learning**: AI agents can analyze their own past outputs to improve future generations

**When to use**: For all AI-generated content that becomes part of the project.

**Success looks like**: AI outputs are indistinguishable from human outputs in the Git history (except for attribution). Poor AI outputs are caught in review and improved before merging.

## Good Examples vs Bad Examples

### Example 1: Environment Configuration

**Good:**
```bash
# All environments defined in Git
# .env.development (committed)
DATABASE_URL=postgresql://localhost:5432/dev_db
API_TIMEOUT=30
FEATURE_NEW_UI=true
LOG_LEVEL=debug

# .env.production (committed)
DATABASE_URL={{ secret:prod_db_url }}  # Placeholder for secret injection
API_TIMEOUT=10
FEATURE_NEW_UI=false
LOG_LEVEL=info

# Secrets injected at deploy time from secure vault
# Git tracks structure and non-sensitive defaults
```

**Bad:**
```bash
# Configuration scattered and untracked
# Production config stored in cloud console UI
# Developer copies values from Slack messages into local .env
# No version control, no audit trail
# When something breaks, no way to know what changed

# .env (local file, gitignored)
DATABASE_URL=postgresql://prod-server:5432/prod_db?password=hunter2
API_TIMEOUT=10
FEATURE_NEW_UI=false
# Values are different on each server, no consistency
```

**Why It Matters:** Git-tracked configuration provides a single source of truth. When production breaks, you can instantly see what changed. When spinning up new environments, you clone the config. When secrets are separate, you maintain security without sacrificing traceability.

### Example 2: Database Schema Evolution

**Good:**
```sql
-- migrations/001_initial.sql (committed)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- migrations/002_add_user_roles.sql (committed)
ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'user';
CREATE INDEX idx_users_role ON users(role);

-- migrations/003_split_user_names.sql (committed)
ALTER TABLE users ADD COLUMN first_name VARCHAR(100);
ALTER TABLE users ADD COLUMN last_name VARCHAR(100);
-- Migration script includes data migration from old 'name' column

-- Schema evolution is clear and reproducible from Git history
```

**Bad:**
```sql
-- Developer runs SQL directly in production console
ALTER TABLE users ADD COLUMN role VARCHAR(50);

-- Another developer doesn't know about the change
-- Runs their own ALTER on their local database
ALTER TABLE users ADD COLUMN user_type VARCHAR(50);

-- Now production and development have different schemas
-- No record of changes, no way to reproduce
-- Breaking changes deployed without review
```

**Why It Matters:** Git-tracked migrations make schema evolution safe and reproducible. Every database in every environment runs the same migrations in the same order. You can recreate the production schema locally with one command. Breaking changes are caught in code review before they break production.

### Example 3: Infrastructure Deployment

**Good:**
```hcl
# terraform/main.tf (committed)
terraform {
  backend "s3" {
    bucket = "myapp-terraform-state"
    key    = "prod/terraform.tfstate"
    region = "us-west-2"
  }
}

resource "aws_instance" "app_server" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.medium"

  tags = {
    Name        = "app-server"
    Environment = "production"
    ManagedBy   = "terraform"
  }
}

# All infrastructure defined as code
# Changes reviewed in PR, applied with `terraform apply`
# Full audit trail of infrastructure changes
```

**Bad:**
```bash
# Infrastructure created manually through AWS console
# Developer clicks through UI to create EC2 instance
# No record of configuration choices
# Instance IDs copied into shared Google doc
# When instance needs recreation, settings are guessed
# Different team members use different configurations

# Documentation:
# "Create t3.medium in us-west-2 with our usual settings"
# (What are "our usual settings"? Nobody remembers.)
```

**Why It Matters:** Infrastructure as code in Git makes infrastructure reproducible and reviewable. Disaster recovery is fast and reliable. Infrastructure changes go through the same rigorous review as application code. New team members can understand the entire infrastructure by reading Git.

### Example 4: API Contract Definition

**Good:**
```yaml
# api/openapi.yaml (committed)
openapi: 3.0.0
info:
  title: User Service API
  version: 1.0.0

paths:
  /users:
    post:
      summary: Create a new user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [email, name]
              properties:
                email:
                  type: string
                  format: email
                name:
                  type: string
                  minLength: 1
      responses:
        '201':
          description: User created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'

# Contract versioned in Git
# CI validates implementation matches spec
# Breaking changes caught in PR review
```

**Bad:**
```python
# API defined only in implementation code
@app.post("/users")
def create_user(email: str, name: str):
    # No formal contract
    # Frontend team guesses parameter names
    # Breaking changes deployed without notice
    user = User(email=email, name=name)
    return user

# API behavior documented in Slack threads
# "I think the user endpoint needs email and name? Maybe?"
# Different clients make different assumptions
```

**Why It Matters:** API contracts in Git create a single source of truth for interfaces. CI validates that implementation matches specification, catching breaking changes before deployment. Clients generate their code from the contract, ensuring compatibility. Historical contracts show API evolution clearly.

### Example 5: AI-Generated Migration Script

**Good:**
```python
# migrations/004_add_user_preferences_generated_by_ai.py (committed)
# Generated by: Claude Code Agent v1.2.3
# Date: 2025-09-30
# PR: #142
# Reviewed by: @human-reviewer

def upgrade():
    """Add user preferences table"""
    op.create_table(
        'user_preferences',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('theme', sa.String(50), default='light'),
        sa.Column('language', sa.String(10), default='en'),
        sa.Column('notifications_enabled', sa.Boolean(), default=True),
    )
    op.create_index('idx_user_prefs_user_id', 'user_preferences', ['user_id'])

def downgrade():
    """Remove user preferences table"""
    op.drop_index('idx_user_prefs_user_id', table_name='user_preferences')
    op.drop_table('user_preferences')

# AI-generated, human-reviewed, fully tracked in Git
```

**Bad:**
```python
# AI agent generates migration script
# Script sent via Slack
# Developer copies into local file
# Applied to database manually
# No record of AI generation
# No review process
# Script lost after database is migrated

# Later: "How did user_preferences get created?"
# Answer: Nobody knows
```

**Why It Matters:** AI-generated code in Git receives the same scrutiny as human code. Attribution in commits shows what was AI-generated for future reference. The review process catches AI mistakes before they reach production. Complete audit trail of AI contributions builds trust and enables learning.

## Related Principles

- **[Principle #10 - Git as Safety Net](10-git-as-safety-net.md)** - Git-Based Everything is the foundation that makes Git as Safety Net possible; you can only roll back what's tracked in Git

- **[Principle #16 - Docs Define, Not Describe](16-everything-as-code.md)** - Git-Based Everything enables Everything as Code by providing version control for all code artifacts (infrastructure, configuration, documentation)

- **[Principle #18 - Contract Evolution with Migration Paths](18-agent-task-summaries.md)** - Git commits serve as the storage mechanism for agent task summaries, creating a searchable history of AI agent work

- **[Principle #40 - Knowledge Stewardship and Institutional Memory](../technology/40-test-driven-generation.md)** - Tests stored in Git provide the specifications that guide AI code generation and validate outputs

- **[Principle #44 - Self-Serve Recovery with Known-Good Snapshots](../governance/44-immutable-production-deployments.md)** - Immutable deployments require exact reproduction of a specific Git commit in production

- **[Principle #13 - Parallel Exploration by Default](13-ccsdk-recipes-capture-workflows.md)** - Recipes stored in Git enable repeatable AI-driven workflows across team members and time

## Common Pitfalls

1. **Committing Secrets**: Accidentally committing API keys, passwords, or tokens into Git creates security vulnerabilities that persist in Git history forever.
   - Example: `.env` file with `DATABASE_PASSWORD=hunter2` committed to public GitHub repo
   - Impact: Exposed credentials must be rotated immediately. Attackers can scan Git history for leaked secrets. Once in Git, secrets are nearly impossible to fully remove.

2. **Ignoring Generated Artifacts**: Treating AI-generated code as "temporary" and not committing it to Git loses the audit trail and prevents review.
   - Example: AI generates migration script, developer applies it locally, script is discarded
   - Impact: No record of what changed or why. Can't reproduce the migration. Can't review AI output for correctness.

3. **Binary Files in Git**: Committing large binary files (images, videos, compiled artifacts) bloats the repository and slows operations.
   - Example: Committing `node_modules/` or `build/` directories with thousands of compiled files
   - Impact: Repository size grows unbounded. Clone and fetch operations become painfully slow. Git LFS or artifact storage is required.

4. **Configuration Drift**: Allowing manual configuration changes in production that aren't reflected back in Git creates divergence.
   - Example: Engineer edits Kubernetes config in cluster with `kubectl edit`, doesn't update Git
   - Impact: Git no longer reflects reality. Next deployment overwrites manual changes. Infrastructure becomes undocumented.

5. **Monolithic Commits**: Committing multiple unrelated changes in a single commit makes history unclear and rollbacks dangerous.
   - Example: Single commit contains feature implementation, bug fix, refactoring, and documentation update
   - Impact: Can't roll back just the bug fix without reverting everything. Unclear what changed. Hard to review.

6. **Lost Documentation**: Writing documentation in wikis, Google Docs, or Notion instead of Git-tracked markdown loses version control and co-location benefits.
   - Example: API documentation lives in Confluence, code in GitHub. They diverge immediately.
   - Impact: Documentation becomes outdated. No version matching. Can't review docs changes with code changes.

7. **Untracked Dependencies**: Specifying dependency versions only in documentation instead of lockfiles creates non-reproducible builds.
   - Example: README says "install Python 3.9+" but no `requirements.txt` with pinned versions
   - Impact: Different environments use different dependency versions. Builds become non-reproducible. Debugging is nightmare.

## Tools & Frameworks

### Git Platforms
- **GitHub**: Industry-standard platform with excellent CI/CD integration, pull requests, code review, and AI agent integrations
- **GitLab**: Self-hosted option with built-in CI/CD, security scanning, and comprehensive DevOps toolchain
- **Bitbucket**: Atlassian-integrated platform for teams using Jira and Confluence

### Infrastructure as Code
- **Terraform**: Cloud-agnostic infrastructure as code with extensive provider ecosystem and state management
- **Pulumi**: Infrastructure as code using real programming languages (Python, TypeScript) instead of HCL
- **AWS CloudFormation**: Native AWS infrastructure as code with deep AWS service integration
- **Kubernetes**: Container orchestration with all configuration as YAML manifests in Git

### Configuration Management
- **Ansible**: Agentless configuration management with idempotent playbooks stored in Git
- **Chef/Puppet**: More complex configuration management for large-scale infrastructure
- **Kustomize**: Kubernetes-native configuration management with overlay-based customization

### Schema Management
- **Liquibase**: Database schema migration tool with XML/YAML/SQL changesets in Git
- **Flyway**: SQL-based migration tool with simple, sequential migration scripts
- **Alembic**: Python-based migration tool for SQLAlchemy projects
- **Prisma**: Modern ORM with schema-first design and automatic migration generation

### Secret Management
- **git-crypt**: Transparent file encryption in Git repositories for secrets
- **SOPS**: Editor of encrypted files supporting various key management systems (AWS KMS, GCP KMS, Azure Key Vault)
- **HashiCorp Vault**: Centralized secret management with dynamic secret generation
- **AWS Secrets Manager**: Cloud-native secret storage with automatic rotation

### Documentation
- **MkDocs**: Static site generator for project documentation from markdown in Git
- **Docusaurus**: React-based documentation site generator with versioning support
- **Sphinx**: Python documentation generator with extensive plugin ecosystem

## Implementation Checklist

When implementing this principle, ensure:

- [ ] All source code is committed to Git with meaningful commit messages following Conventional Commits
- [ ] Documentation is co-located with code in markdown format within the same repository
- [ ] Configuration files for all environments are in Git (with secrets properly externalized)
- [ ] Database schema migrations are stored as sequential files in Git
- [ ] Infrastructure definitions (Terraform, Kubernetes manifests, Docker files) are in Git
- [ ] API contracts (OpenAPI, GraphQL schemas, protobuf) are versioned in Git
- [ ] CI/CD pipeline definitions are stored in Git alongside the code they build
- [ ] `.gitignore` properly excludes secrets, generated artifacts, and local environment files
- [ ] Branch protection rules enforce code review before merging to main
- [ ] Commit history is clean and tells a clear story (no "WIP" or "fix" commits in main)
- [ ] Large binary files use Git LFS or external artifact storage
- [ ] All team members and AI agents follow the same Git workflow conventions

## Metadata

**Category**: Process
**Principle Number**: 15
**Related Patterns**: Infrastructure as Code, GitOps, Configuration as Code, Documentation as Code, Version Control
**Prerequisites**: Basic Git knowledge, understanding of branching strategies, CI/CD familiarity
**Difficulty**: Low
**Impact**: High

---

**Status**: Complete
**Last Updated**: 2025-09-30
**Version**: 1.0