# Principle #35 - Least-Privilege Automation with Scoped Permissions

## Plain-Language Definition

AI agents should operate with the minimum permissions necessary to accomplish their specific tasks. By limiting what each agent can access and modify, we reduce the potential damage from mistakes or security compromises.

## Why This Matters for AI-First Development

When AI agents build and modify systems, they operate with code-level access that can affect entire codebases, databases, and infrastructure. Unlike human developers who can apply judgment before executing risky operations, AI agents execute instructions based on their understanding of requirements, which can be imperfect. A well-intentioned agent with excessive permissions might accidentally delete production data, expose secrets, or break critical systems.

Least-privilege automation provides three critical benefits for AI-driven development:

1. **Limited blast radius**: When an AI agent makes a mistake or gets compromised, scoped permissions contain the damage. An agent with read-only database access can't accidentally truncate tables. An agent scoped to a single repository can't modify other projects.

2. **Clearer accountability**: Fine-grained permissions make it obvious which agent performed which action. When every agent has admin access, it's impossible to trace problems back to their source. With scoped permissions, audit logs become meaningful.

3. **Safer experimentation**: AI agents often explore different approaches and iterate rapidly. Restrictive permissions let agents experiment safely. They can try alternative implementations, test different configurations, or refactor code without risk of breaking production systems or accessing sensitive data.

Without least-privilege automation, AI systems become dangerous. An agent debugging a performance issue might accidentally read customer passwords from the database. A code generation agent might commit API keys to public repositories. A deployment agent might delete production resources while cleaning up test environments. These failures become catastrophic when agents have unrestricted access, but remain manageable when permissions are properly scoped.

## Implementation Approaches

### 1. **Minimal Permission Sets by Task Type**

Define explicit permission sets for each category of task, granting only what's necessary:

- **Read-only analysis**: File read, repository metadata, log viewing
- **Code generation**: File read/write in specific directories, no execution
- **Testing**: File read, test execution, no production access
- **Deployment**: Specific resource creation, no deletion or admin access
- **Monitoring**: Read metrics and logs, no write access

When creating an AI agent, start with the most restrictive permission set that might work, then expand only when you hit legitimate limitations.

### 2. **Scoped Credentials with Time Limits**

Use temporary, purpose-specific credentials rather than long-lived admin tokens:

```python
def create_scoped_credential(
    task: str,
    permissions: List[str],
    duration_hours: int = 1
) -> Credential:
    """Generate time-limited credential for specific task"""
    return issue_credential(
        scope=permissions,
        expires_at=now() + timedelta(hours=duration_hours),
        description=f"Temp access for {task}"
    )
```

Credentials expire automatically, limiting the window of risk if they're leaked or misused.

### 3. **Role-Based Access with Narrow Roles**

Define roles that match specific agent responsibilities:

- **CodeReader**: Read source files, no modifications
- **TestRunner**: Execute tests, read test results, no code changes
- **SchemaReader**: Read database schema, no data access
- **ConfigWriter**: Update config files only, no code access
- **LogAnalyzer**: Read logs and metrics, no system modification

Assign agents to roles based on their purpose, not generic "developer" or "admin" roles.

### 4. **Capability-Based Security for Resource Access**

Issue unforgeable tokens that grant specific capabilities:

```python
# Agent receives a capability token for specific files only
capability = grant_capability(
    resource="project/src/**/*.py",
    operations=["read", "write"],
    constraints={"max_file_size": "1MB"}
)

# Agent can only access files matching the capability
agent.execute_with_capability(capability)
```

The capability itself proves authorization, eliminating need for complex permission checks.

### 5. **Sandboxed Execution Environments**

Run AI agents in isolated environments with explicit resource limits:

```python
sandbox = create_sandbox(
    allowed_paths=["/workspace/project"],
    network_access=False,
    max_memory_mb=512,
    max_cpu_percent=50,
    allowed_syscalls=["read", "write", "stat"]
)

sandbox.execute_agent(agent, task)
```

Even if an agent tries to exceed its permissions, the sandbox enforces boundaries at the OS level.

### 6. **Approval Workflows for Sensitive Operations**

Require human approval for operations that cross permission boundaries:

```python
def deploy_to_production(agent_id: str, deployment_config: dict):
    """High-risk operation requires approval"""
    approval_request = create_approval_request(
        agent=agent_id,
        operation="production_deployment",
        config=deployment_config,
        risk_level="high"
    )

    # Block until human approves
    approval = wait_for_approval(approval_request, timeout_minutes=30)

    if approval.granted:
        execute_deployment(deployment_config)
    else:
        raise PermissionDenied(approval.reason)
```

This provides a human checkpoint for operations that could cause significant damage.

## Good Examples vs Bad Examples

### Example 1: Database Access for Analysis

**Good:**
```python
# Agent gets read-only access to specific tables
def create_analysis_agent():
    db_credential = create_scoped_credential(
        task="analyze_user_activity",
        permissions=[
            "SELECT on analytics.page_views",
            "SELECT on analytics.user_sessions"
        ],
        duration_hours=2
    )

    return AnalysisAgent(
        credentials=db_credential,
        allowed_operations=["read", "analyze"]
    )

# Agent cannot modify data or access sensitive tables
agent = create_analysis_agent()
agent.analyze_user_trends()  # ✓ Works - has read access
agent.update_user_profile()  # ✗ Fails - no write permissions
agent.read_user_passwords()  # ✗ Fails - no access to sensitive tables
```

**Bad:**
```python
# Agent gets full database admin access
def create_analysis_agent():
    db_credential = get_admin_database_credential()  # Too broad!

    return AnalysisAgent(
        credentials=db_credential,
        allowed_operations=["read", "analyze"]
    )

# Agent has full database access despite only needing read
agent = create_analysis_agent()
agent.analyze_user_trends()  # ✓ Works
agent.drop_table("users")  # ✓ Works but DISASTROUS - agent has admin access
agent.read_credit_cards()  # ✓ Works but DANGEROUS - can access all tables
```

**Why It Matters:** The bad example gives the agent administrative database credentials when it only needs to read two analytics tables. If the agent is compromised or makes a mistake, it could delete critical data or leak sensitive information. The good example limits access to exactly what's needed, containing potential damage.

### Example 2: File System Access for Code Generation

**Good:**
```python
# Agent gets scoped access to specific project directories
def create_code_generator(project_path: Path):
    sandbox = create_filesystem_sandbox(
        allowed_paths=[
            project_path / "src",
            project_path / "tests"
        ],
        allowed_operations={
            "src": ["read", "write"],
            "tests": ["read", "write"]
        },
        denied_paths=[
            project_path / ".env",
            project_path / "secrets",
            project_path / ".git/config"
        ]
    )

    return CodeGeneratorAgent(sandbox=sandbox)

agent = create_code_generator(Path("/workspace/myapp"))
agent.generate_module("src/auth.py")  # ✓ Works
agent.generate_test("tests/test_auth.py")  # ✓ Works
agent.read_file(".env")  # ✗ Fails - secrets are denied
agent.modify_git_config()  # ✗ Fails - git config is denied
```

**Bad:**
```python
# Agent gets unrestricted filesystem access
def create_code_generator(project_path: Path):
    # No restrictions - agent can access anything
    return CodeGeneratorAgent(
        root_path="/",  # Root access!
        allowed_operations=["read", "write", "delete"]
    )

agent = create_code_generator(Path("/workspace/myapp"))
agent.generate_module("src/auth.py")  # ✓ Works
agent.generate_test("tests/test_auth.py")  # ✓ Works
agent.read_file("/workspace/myapp/.env")  # ✓ Works but DANGEROUS
agent.delete_file("/etc/passwd")  # ✓ Works but CATASTROPHIC
```

**Why It Matters:** The bad example gives the agent unrestricted filesystem access with root permissions. A confused agent could read secrets, delete system files, or modify git configuration. The good example uses a sandbox that explicitly lists allowed paths and denies access to sensitive files.

### Example 3: API Credentials for Integration

**Good:**
```python
# Agent gets time-limited token with specific API scopes
def create_integration_agent():
    # Generate token that expires in 1 hour
    api_token = create_scoped_api_token(
        scopes=["repos:read", "issues:write"],
        resources=["myorg/myrepo"],
        expires_in=3600  # 1 hour
    )

    return IntegrationAgent(
        credentials=api_token,
        allowed_endpoints=[
            "GET /repos/myorg/myrepo/issues",
            "POST /repos/myorg/myrepo/issues"
        ]
    )

agent = create_integration_agent()
agent.list_open_issues()  # ✓ Works - has repos:read scope
agent.create_issue(title="Bug", body="...")  # ✓ Works - has issues:write scope
agent.delete_repository()  # ✗ Fails - no delete permissions
agent.access_other_repo()  # ✗ Fails - token scoped to one repo
# After 1 hour, token expires automatically
```

**Bad:**
```python
# Agent gets personal access token with full permissions
def create_integration_agent():
    # Use long-lived PAT with all permissions
    api_token = os.getenv("GITHUB_PAT")  # Admin token with no expiration!

    return IntegrationAgent(
        credentials=api_token,
        # No restrictions on what agent can do
    )

agent = create_integration_agent()
agent.list_open_issues()  # ✓ Works
agent.create_issue(title="Bug", body="...")  # ✓ Works
agent.delete_repository()  # ✓ Works but CATASTROPHIC
agent.modify_org_settings()  # ✓ Works but DANGEROUS
agent.access_all_repos()  # ✓ Works but EXCESSIVE
# Token never expires, unlimited risk window
```

**Why It Matters:** The bad example uses a personal access token with full admin permissions and no expiration. If the agent is compromised or malfunctions, it could delete repositories, change organization settings, or access all private repos. The good example uses a time-limited token scoped to specific actions on a specific repository.

### Example 4: Cloud Infrastructure Access

**Good:**
```python
# Agent gets role with specific resource permissions
def create_deployment_agent():
    # Create IAM role for this specific deployment task
    role = create_iam_role(
        name="deploy-agent-role",
        policies=[
            {
                "effect": "allow",
                "actions": [
                    "ecs:UpdateService",
                    "ecs:DescribeServices"
                ],
                "resources": [
                    "arn:aws:ecs:us-east-1:123456789:service/myapp-staging"
                ]
            }
        ],
        max_session_duration=3600  # 1 hour
    )

    return DeploymentAgent(role=role)

agent = create_deployment_agent()
agent.update_staging_service(image="v1.2.3")  # ✓ Works
agent.describe_staging_service()  # ✓ Works
agent.delete_production_service()  # ✗ Fails - no access to production
agent.create_new_resources()  # ✗ Fails - can only update existing
```

**Bad:**
```python
# Agent gets admin credentials for entire AWS account
def create_deployment_agent():
    # Use admin credentials with full access
    credentials = get_aws_admin_credentials()  # Too powerful!

    return DeploymentAgent(credentials=credentials)

agent = create_deployment_agent()
agent.update_staging_service(image="v1.2.3")  # ✓ Works
agent.describe_staging_service()  # ✓ Works
agent.delete_production_database()  # ✓ Works but CATASTROPHIC
agent.terminate_all_instances()  # ✓ Works but DISASTROUS
agent.modify_iam_policies()  # ✓ Works but DANGEROUS
```

**Why It Matters:** The bad example gives the agent full AWS admin access when it only needs to update one specific ECS service. The agent could accidentally or maliciously delete production resources, terminate instances, or change security policies. The good example uses IAM to grant exactly the permissions needed for the specific task.

### Example 5: Secret Management Access

**Good:**
```python
# Agent gets capability token for specific secrets only
def create_config_agent():
    # Grant access to only the secrets this agent needs
    secret_capability = grant_secret_access(
        secrets=[
            "database_connection_string",
            "api_rate_limit"
        ],
        operations=["read"],  # Read-only
        expires_in=1800  # 30 minutes
    )

    return ConfigAgent(secret_access=secret_capability)

agent = create_config_agent()
db_url = agent.get_secret("database_connection_string")  # ✓ Works
rate_limit = agent.get_secret("api_rate_limit")  # ✓ Works
api_key = agent.get_secret("stripe_api_key")  # ✗ Fails - not in allowed list
agent.update_secret("database_password", "new_pass")  # ✗ Fails - read-only
```

**Bad:**
```python
# Agent gets master key for entire secret store
def create_config_agent():
    # Use master key with full access to all secrets
    master_key = os.getenv("VAULT_MASTER_KEY")  # Too powerful!

    return ConfigAgent(vault_key=master_key)

agent = create_config_agent()
db_url = agent.get_secret("database_connection_string")  # ✓ Works
rate_limit = agent.get_secret("api_rate_limit")  # ✓ Works
stripe_key = agent.get_secret("stripe_api_key")  # ✓ Works but DANGEROUS
passwords = agent.list_all_secrets()  # ✓ Works but EXCESSIVE
agent.delete_secret("prod_database_password")  # ✓ Works but CATASTROPHIC
```

**Why It Matters:** The bad example gives the agent a master key that can access and modify any secret in the vault. If the agent logs secrets, gets compromised, or makes a mistake, all secrets are at risk. The good example grants read-only access to only the specific secrets needed, with automatic expiration.

## Related Principles

- **[Principle #21 - Limited and Domain-Specific by Design](21-logging-first-always.md)** - Comprehensive logging becomes essential with least-privilege automation to track what each scoped agent does and identify when permissions need adjustment

- **[Principle #29 - Tool Ecosystems as Extensions](29-isolated-testing-environments.md)** - Isolated environments work synergistically with least privilege; each environment enforces its own permission boundaries, preventing test agents from affecting production

- **[Principle #38 - Access Control and Compliance as First-Class](38-security-defaults-everywhere.md)** - Least privilege is a foundational security default; starting with minimal permissions and explicitly granting more aligns with security-first design

- **[Principle #41 - Adaptive Sandboxing with Explicit Approvals](41-versioned-model-behavior-tracking.md)** - When tracking AI model behavior, least privilege ensures agents can only access the metrics and logs they need to analyze, not sensitive training data or model weights

- **[Principle #42 - Data Governance and Privacy Controls](42-human-in-loop-critical-actions.md)** - Least privilege determines which actions are "critical" requiring human approval; operations that exceed an agent's permissions trigger human review

- **[Principle #6 - Human Escape Hatches Always Available](../process/06-fail-fast-clear-signals.md)** - Permission denials should fail immediately with clear error messages, helping developers understand what permissions are needed without security risks

## Common Pitfalls

1. **Granting Temporary Admin Access "Just This Once"**: Starting with admin permissions for convenience and planning to restrict later rarely happens. Once agents have broad access, restricting it breaks existing functionality.
   - Example: Giving deployment agent admin AWS credentials to "debug an issue quickly" and forgetting to revoke them.
   - Impact: Agent retains excessive permissions indefinitely, creating ongoing security risk and blast radius for mistakes.

2. **Using Personal Credentials Instead of Service Accounts**: Developers sharing their own credentials with agents creates unclear accountability and excessive permissions tied to human access levels.
   - Example: Using `os.getenv("MY_GITHUB_TOKEN")` instead of creating a dedicated service account with limited scope.
   - Impact: Agent has all permissions the developer has, audit logs show developer's name instead of agent, credentials can't be rotated without breaking the agent.

3. **Forgetting to Expire Temporary Credentials**: Creating scoped credentials but setting no expiration or very long expiration times defeats the purpose of temporary access.
   - Example: `expires_at=now() + timedelta(days=365)` for a task that should take 1 hour.
   - Impact: Credentials persist long after they're needed, expanding the risk window if they're leaked or misused.

4. **Overly Broad Path Wildcards**: Using wildcards like `**/*` or `*` when defining file access permissions grants far more access than intended.
   - Example: `allowed_paths=["/workspace/*"]` includes `.env`, `.git/config`, and other sensitive files.
   - Impact: Agent can access secrets, configuration, and system files that should be protected.

5. **Missing Rate Limits on Scoped Access**: Even with minimal permissions, agents without rate limits can cause damage through excessive API calls or resource consumption.
   - Example: Agent with read-only database access running unlimited queries and causing performance degradation.
   - Impact: Denial of service through resource exhaustion, even without write permissions.

6. **Inheritance of Parent Process Permissions**: Running agents as child processes that inherit the parent's full permissions bypasses permission scoping.
   - Example: Running `subprocess.call(agent_command)` as root user; agent inherits root privileges.
   - Impact: Carefully designed agent permissions are ignored, agent has full system access.

7. **Assuming Developers Will Request Minimal Permissions**: Relying on developers to voluntarily request narrow permissions results in overly broad access requests out of convenience.
   - Example: "Give me read access to the database" instead of "Give me SELECT access to users and orders tables."
   - Impact: Agents receive more permissions than needed because defaults are too permissive and developers don't think about granularity.

## Tools & Frameworks

### Cloud Permission Management
- **AWS IAM**: Fine-grained policies with resource-level permissions, temporary credentials via STS, role assumption with session duration limits
- **Google Cloud IAM**: Predefined roles and custom roles with granular permissions, service account impersonation, short-lived tokens
- **Azure RBAC**: Role assignments at resource group or resource level, managed identities for Azure resources, just-in-time access

### Secret Management
- **HashiCorp Vault**: Dynamic secrets with automatic rotation, time-limited leases, policy-based access control, audit logging
- **AWS Secrets Manager**: Automatic rotation, fine-grained IAM policies, versioned secrets, cross-account access
- **Azure Key Vault**: Managed identities, access policies scoped to specific secrets, certificate management, soft delete protection

### Container Security
- **Docker**: User namespaces for non-root containers, capability dropping, read-only root filesystems, resource limits
- **Podman**: Rootless containers by default, SELinux integration, fine-grained capability control
- **gVisor**: Application kernel for container sandboxing, syscall filtering, network policy enforcement

### API Gateway & Auth
- **Kong**: Rate limiting per consumer, API key authentication, OAuth 2.0 scopes, JWT claim validation
- **AWS API Gateway**: Resource policies, IAM authorization, Lambda authorizers, usage plans with throttling
- **Nginx**: Access control rules, client certificate validation, rate limiting, request filtering

### Database Access Control
- **PostgreSQL**: Row-level security policies, role-based access, column-level privileges, GRANT statements with precise scope
- **MongoDB**: Role-based access control, collection-level permissions, field-level redaction, client-side field encryption
- **MySQL**: Stored procedure privileges, table-level grants, column-specific permissions, user account limits

### Filesystem Sandboxing
- **Firejail**: Linux namespace sandboxing, filesystem overlays, network isolation, resource limits
- **Bubblewrap**: Unprivileged container creation, bind mounts with restrictions, seccomp filtering
- **AppArmor**: Mandatory access control, path-based permissions, capability restrictions, profile enforcement

## Implementation Checklist

When implementing this principle, ensure:

- [ ] Each AI agent has a documented permission scope that lists exactly what it can access and modify
- [ ] Service accounts or dedicated credentials are used instead of personal developer credentials
- [ ] Credentials expire automatically with expiration times matching task duration (hours, not days)
- [ ] Sensitive operations require explicit approval workflows before execution
- [ ] Database access is scoped to specific tables and columns, not entire database
- [ ] Filesystem access uses deny-lists for sensitive paths (`.env`, `.git/config`, `secrets/`)
- [ ] API tokens are scoped to specific endpoints and HTTP methods, not admin access
- [ ] Cloud infrastructure access uses purpose-specific IAM roles, not root or admin accounts
- [ ] Rate limits are enforced on agent operations to prevent resource exhaustion attacks
- [ ] Permission denials are logged with context about what was attempted and why it failed
- [ ] Regular audits review agent permissions and remove unused or excessive access
- [ ] Agent sandboxes enforce permission boundaries at OS level, not just application level

## Metadata

**Category**: Technology
**Principle Number**: 35
**Related Patterns**: Capability-Based Security, Role-Based Access Control (RBAC), Principle of Least Privilege, Defense in Depth, Zero Trust Architecture
**Prerequisites**: Understanding of authentication vs authorization, IAM concepts, sandboxing techniques, secret management
**Difficulty**: High
**Impact**: High

---

**Status**: Complete
**Last Updated**: 2025-09-30
**Version**: 1.0