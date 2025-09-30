# Principle #41 - Adaptive Sandboxing with Explicit Approvals

## Plain-Language Definition

AI operations run in sandboxed environments with limited permissions by default, escalating to higher privileges only when explicitly approved by humans. Sandboxes contain the blast radius of mistakes while approval workflows ensure critical operations receive appropriate oversight.

## Why This Matters for AI-First Development

When AI agents modify systems autonomously, they operate with code-level access that can affect entire infrastructures, databases, and production environments. Unlike human developers who intuitively sense risk and self-regulate their actions, AI agents execute instructions based on their understanding of requirements, which can be imperfect or incomplete. An AI agent with unrestricted permissions might confidently delete production data, expose secrets, or modify security configurations while attempting to "optimize" the system.

Adaptive sandboxing addresses this by creating layered permission boundaries that adjust based on the risk profile of operations. Low-risk operations like reading files or running tests execute immediately within the sandbox. Medium-risk operations like modifying configuration files trigger notifications and monitoring. High-risk operations like database migrations or production deployments require explicit human approval before proceeding. This adaptive model enables AI agents to work at full speed for routine tasks while ensuring critical operations receive appropriate human oversight.

The "adaptive" aspect is crucial: static sandboxes that never grant elevated permissions render AI agents unable to perform valuable work like deployments or infrastructure changes. Sandboxes that require approval for every operation create bottlenecks that negate automation benefits. Adaptive sandboxing strikes the balance by starting with minimal permissions and providing clear escalation paths when agents need more capabilities. The sandbox learns from approval patterns, expanding automatic permissions for repeatedly-approved operations while maintaining strict controls on novel or risky actions.

Without adaptive sandboxing, AI-first systems face two failure modes: either agents operate with excessive permissions and occasionally cause catastrophic damage, or they operate with such restricted permissions that humans must constantly intervene, eliminating automation benefits. Adaptive sandboxing creates a middle path where agents work autonomously within safe boundaries and escalate only when truly necessary, with clear approval workflows that make elevated operations visible and auditable.

## Implementation Approaches

### 1. **Capability-Based Permission Tokens**

Grant AI agents unforgeable capability tokens that encode specific permissions for specific resources. Tokens are time-limited and scoped to exact operations needed, preventing privilege escalation.

```python
def create_capability_token(
    agent_id: str,
    resource_pattern: str,
    operations: list[str],
    expiration_minutes: int = 60
) -> CapabilityToken:
    """Generate time-limited capability token for specific operations"""
    return CapabilityToken(
        agent=agent_id,
        resources=resource_pattern,  # e.g., "workspace/src/**/*.py"
        allowed_ops=operations,       # e.g., ["read", "write"]
        expires_at=now() + timedelta(minutes=expiration_minutes),
        token=sign_capability(agent_id, resource_pattern, operations)
    )

# Agent receives token scoped to their task
token = create_capability_token(
    agent_id="refactor-agent-123",
    resource_pattern="workspace/src/utils/*.py",
    operations=["read", "write"],
    expiration_minutes=30
)

# Token proves authorization without complex checks
agent.execute_with_token(token)
```

**When to use:** For file system access, API calls, and resource modifications where you want fine-grained control over what agents can access.

**Success looks like:** Agents can only perform operations explicitly granted by their capability tokens, tokens expire automatically limiting risk window, and token violations are immediately detected and logged.

### 2. **Permission Escalation with Approval Workflows**

Implement multi-tier permission levels where agents start with minimal permissions and request escalation for operations requiring higher privileges.

```python
class PermissionEscalationManager:
    """Manage permission escalation with approval workflows"""

    def __init__(self):
        self.base_permissions = PermissionSet(["read", "analyze", "test"])
        self.escalation_rules = self.load_escalation_rules()

    async def execute_with_escalation(
        self,
        agent_id: str,
        operation: Operation,
        context: dict
    ) -> ExecutionResult:
        """Execute operation, escalating permissions if needed"""
        required_perms = self.analyze_required_permissions(operation)

        # Check if agent has sufficient permissions
        agent_perms = self.get_agent_permissions(agent_id)
        if agent_perms.contains_all(required_perms):
            return await self.execute_operation(operation)

        # Determine escalation tier
        escalation_tier = self.classify_escalation(
            current=agent_perms,
            required=required_perms
        )

        if escalation_tier == EscalationTier.LOW:
            # Auto-approve low-risk escalations
            await self.grant_temporary_permissions(agent_id, required_perms)
            self.notify_team_async(f"Auto-approved escalation: {operation}")
            return await self.execute_operation(operation)

        elif escalation_tier == EscalationTier.MEDIUM:
            # Require notification and timeout
            self.notify_team_sync(f"Agent requesting: {operation}")
            await self.wait_with_timeout(seconds=300)  # 5 min timeout
            return await self.execute_operation(operation)

        elif escalation_tier == EscalationTier.HIGH:
            # Require explicit approval
            approval = await self.request_approval(
                agent=agent_id,
                operation=operation,
                context=context,
                risk_assessment=self.assess_risk(operation),
                timeout_minutes=30
            )

            if approval.granted:
                await self.grant_temporary_permissions(
                    agent_id,
                    required_perms,
                    duration_minutes=approval.duration
                )
                return await self.execute_operation(operation)
            else:
                raise PermissionDenied(f"Approval denied: {approval.reason}")

        else:  # CRITICAL
            raise PermissionDenied("Operation requires manual execution")
```

**When to use:** For operations with varying risk profiles—deployments, database changes, security configurations, infrastructure modifications.

**Success looks like:** Low-risk escalations happen automatically, medium-risk operations proceed with notification, high-risk operations require explicit approval, and all escalations are audited.

### 3. **Isolated Sandbox Environments**

Run AI agents in containerized sandboxes with explicit resource limits and network isolation, preventing them from affecting systems outside their designated workspace.

```python
class SandboxEnvironment:
    """Containerized sandbox for AI agent execution"""

    def __init__(self, agent_id: str, task_spec: TaskSpec):
        self.agent_id = agent_id
        self.task_spec = task_spec
        self.container = None

    def create_sandbox(self) -> SandboxConfig:
        """Create isolated sandbox with resource limits"""
        return SandboxConfig(
            # Filesystem isolation
            allowed_paths=[
                self.task_spec.workspace_path,
                "/tmp/agent-{agent_id}"
            ],
            readonly_paths=[
                "/usr/lib",
                "/usr/bin"
            ],
            denied_paths=[
                "/etc/passwd",
                "/etc/shadow",
                "**/.env",
                "**/.git/config"
            ],

            # Network isolation
            network_mode="restricted",
            allowed_domains=self.task_spec.allowed_api_endpoints,
            blocked_domains=["*"],  # Deny all except allowed

            # Resource limits
            max_memory_mb=2048,
            max_cpu_percent=50,
            max_disk_mb=5000,
            max_processes=20,

            # System call restrictions
            allowed_syscalls=[
                "read", "write", "open", "close",
                "stat", "fstat", "access",
                "execve", "fork", "clone"
            ],

            # Time limits
            max_execution_seconds=3600,
            idle_timeout_seconds=300
        )

    async def execute_in_sandbox(self, agent: Agent, task: Task):
        """Execute agent task in isolated sandbox"""
        sandbox_config = self.create_sandbox()

        # Create container with sandbox config
        self.container = await create_container(
            image="agent-runtime:latest",
            config=sandbox_config,
            labels={"agent_id": self.agent_id, "task_id": task.id}
        )

        try:
            # Run agent in isolated container
            result = await self.container.run_agent(agent, task)
            return result

        finally:
            # Always cleanup sandbox
            await self.container.destroy()
            self.cleanup_temp_files()
```

**When to use:** For any AI agent execution where you want complete isolation from the host system and other agents.

**Success looks like:** Agents cannot escape their sandboxes, resource exhaustion in one sandbox doesn't affect others, and sandbox violations are detected immediately with automatic termination.

### 4. **Progressive Permission Unlocking**

Start agents with minimal permissions and progressively unlock capabilities based on demonstrated safety and approval history.

```python
class ProgressivePermissionManager:
    """Unlock permissions progressively based on behavior"""

    def __init__(self):
        self.permission_history = PermissionHistory()
        self.trust_scores = TrustScoreTracker()

    def get_agent_permissions(self, agent_id: str) -> PermissionSet:
        """Determine permissions based on agent's history"""
        trust_score = self.trust_scores.get_score(agent_id)

        # Base permissions for all agents
        permissions = PermissionSet([
            "read:workspace",
            "write:workspace/tmp",
            "execute:tests"
        ])

        # Unlock additional permissions based on trust
        if trust_score >= 50:
            # Proven safe, add write permissions
            permissions.add([
                "write:workspace/src",
                "create:branches",
                "commit:code"
            ])

        if trust_score >= 75:
            # High trust, add integration permissions
            permissions.add([
                "create:pull_requests",
                "merge:non_protected_branches",
                "deploy:development"
            ])

        if trust_score >= 90:
            # Exceptional trust, add production permissions
            # (still requires approval for execution)
            permissions.add([
                "request:production_deploy",
                "modify:staging_config"
            ])

        # Never auto-unlock critical permissions
        # These always require explicit approval
        critical_perms = [
            "delete:production_data",
            "modify:security_config",
            "access:secrets",
            "sudo:any"
        ]

        return permissions

    def update_trust_score(
        self,
        agent_id: str,
        event: AgentEvent
    ):
        """Update trust score based on agent behavior"""
        current = self.trust_scores.get_score(agent_id)

        if event.type == "successful_task":
            current += 2
        elif event.type == "test_passed":
            current += 1
        elif event.type == "permission_violation":
            current -= 10
        elif event.type == "approval_required":
            # Requesting approval shows good judgment
            current += 1
        elif event.type == "human_override":
            # Human had to intervene
            current -= 5

        # Decay over time to require consistent good behavior
        current = current * 0.99  # 1% daily decay

        self.trust_scores.set_score(agent_id, clamp(current, 0, 100))
```

**When to use:** For long-running AI agents that execute many tasks over time, where you want to reward safe behavior with expanded permissions.

**Success looks like:** New agents start restricted, proven agents gain autonomy, trust scores decay requiring ongoing good behavior, and critical permissions always require approval regardless of trust.

### 5. **Approval Context with Risk Assessment**

When escalating for approval, provide comprehensive context including risk assessment, blast radius analysis, and rollback plans.

```python
class ApprovalRequest:
    """Comprehensive approval request with risk context"""

    def __init__(
        self,
        agent_id: str,
        operation: Operation,
        context: dict
    ):
        self.agent_id = agent_id
        self.operation = operation
        self.context = context
        self.risk_assessment = self.assess_risk()

    def assess_risk(self) -> RiskAssessment:
        """Analyze risk profile of requested operation"""
        return RiskAssessment(
            # What could go wrong
            failure_modes=self.identify_failure_modes(),

            # How bad could it be
            blast_radius=self.calculate_blast_radius(),

            # How likely is failure
            confidence_score=self.estimate_confidence(),

            # Can we recover
            reversibility=self.check_reversibility(),
            rollback_plan=self.generate_rollback_plan(),

            # What are we changing
            affected_systems=self.identify_affected_systems(),
            affected_users=self.estimate_affected_users(),

            # Similar operations
            historical_success_rate=self.query_historical_data(),
            similar_operations=self.find_similar_operations()
        )

    async def request_approval(self, timeout_minutes: int = 30) -> Approval:
        """Request human approval with comprehensive context"""

        # Build approval UI/notification with all context
        approval_request = {
            "agent": self.agent_id,
            "operation": self.operation.summary,
            "reason": self.context["reason"],

            "risk_assessment": {
                "level": self.risk_assessment.level,
                "blast_radius": self.risk_assessment.blast_radius,
                "confidence": f"{self.risk_assessment.confidence_score}%",
                "reversible": self.risk_assessment.reversibility.is_reversible
            },

            "what_will_happen": self.generate_execution_preview(),

            "rollback_plan": {
                "can_rollback": self.risk_assessment.rollback_plan.is_available,
                "rollback_time": self.risk_assessment.rollback_plan.estimated_time,
                "rollback_steps": self.risk_assessment.rollback_plan.steps
            },

            "similar_operations": [
                {
                    "description": op.description,
                    "outcome": op.outcome,
                    "date": op.timestamp
                }
                for op in self.risk_assessment.similar_operations[:5]
            ],

            "decision_options": [
                {"action": "approve", "label": "Approve and Execute"},
                {"action": "approve_with_monitoring", "label": "Approve with Enhanced Monitoring"},
                {"action": "deny", "label": "Deny - Too Risky"},
                {"action": "defer", "label": "Need More Information"}
            ]
        }

        # Send to appropriate approvers based on risk level
        approvers = self.select_approvers(self.risk_assessment.level)

        # Wait for approval with timeout
        approval = await self.wait_for_approval(
            request=approval_request,
            approvers=approvers,
            timeout_minutes=timeout_minutes
        )

        return approval
```

**When to use:** For all approval workflows where humans need to make informed decisions about allowing elevated operations.

**Success looks like:** Approval requests contain all information needed for quick decisions, risk assessment is accurate and actionable, and humans can approve confidently or deny with clear reasoning.

### 6. **Fallback to Safe Mode on Violations**

When agents violate sandbox boundaries or permissions, automatically revert to safe mode with minimal permissions until reviewed.

```python
class SandboxViolationHandler:
    """Handle sandbox violations with automatic safe mode"""

    def __init__(self):
        self.violation_detector = ViolationDetector()
        self.safe_mode_enforcer = SafeModeEnforcer()

    async def monitor_sandbox(self, agent_id: str, sandbox: Sandbox):
        """Monitor sandbox for violations and enforce safe mode"""
        while sandbox.is_running():
            # Check for various violation types
            violations = await self.detect_violations(sandbox)

            if violations:
                await self.handle_violations(agent_id, violations, sandbox)

            await asyncio.sleep(1)

    async def detect_violations(self, sandbox: Sandbox) -> list[Violation]:
        """Detect sandbox boundary violations"""
        violations = []

        # Permission violations
        if unauthorized_ops := sandbox.get_unauthorized_operations():
            violations.extend([
                Violation(
                    type="permission_denied",
                    details=f"Attempted {op} without permission",
                    severity="high"
                )
                for op in unauthorized_ops
            ])

        # Resource violations
        if sandbox.memory_usage() > sandbox.config.max_memory_mb:
            violations.append(Violation(
                type="resource_limit",
                details="Memory limit exceeded",
                severity="medium"
            ))

        # Network violations
        if blocked_requests := sandbox.get_blocked_network_requests():
            violations.extend([
                Violation(
                    type="network_policy",
                    details=f"Blocked request to {req.url}",
                    severity="medium"
                )
                for req in blocked_requests
            ])

        # Filesystem violations
        if denied_paths := sandbox.get_denied_path_access():
            violations.extend([
                Violation(
                    type="filesystem_access",
                    details=f"Attempted access to denied path: {path}",
                    severity="high"
                )
                for path in denied_paths
            ])

        return violations

    async def handle_violations(
        self,
        agent_id: str,
        violations: list[Violation],
        sandbox: Sandbox
    ):
        """Handle violations by entering safe mode"""

        # Log all violations
        for violation in violations:
            logger.warning(
                f"Sandbox violation by {agent_id}: "
                f"{violation.type} - {violation.details}"
            )

        # Enter safe mode based on severity
        high_severity = any(v.severity == "high" for v in violations)

        if high_severity:
            # Immediate safe mode for high severity
            await self.enter_safe_mode_immediate(agent_id, sandbox)
        else:
            # Warning for medium severity, safe mode if repeated
            self.record_violations(agent_id, violations)
            if self.violation_count(agent_id) > 3:
                await self.enter_safe_mode_immediate(agent_id, sandbox)

        # Notify humans
        await self.notify_security_team(agent_id, violations)

    async def enter_safe_mode_immediate(
        self,
        agent_id: str,
        sandbox: Sandbox
    ):
        """Enter safe mode immediately"""
        logger.error(f"Agent {agent_id} entering safe mode due to violations")

        # Pause agent execution
        await sandbox.pause_agent()

        # Revoke all elevated permissions
        await self.revoke_elevated_permissions(agent_id)

        # Switch to safe mode permissions (read-only)
        safe_permissions = PermissionSet(["read:workspace", "read:logs"])
        await self.set_agent_permissions(agent_id, safe_permissions)

        # Create incident for human review
        await self.create_security_incident(
            agent=agent_id,
            reason="Sandbox violations",
            requires_review=True
        )

        # Resume agent in safe mode
        await sandbox.resume_agent()
```

**When to use:** For production AI agent deployments where you need automatic enforcement of sandbox boundaries and security policies.

**Success looks like:** Violations are detected immediately, agents automatically enter safe mode preventing further damage, security team is notified, and agents require human review before resuming normal permissions.

## Good Examples vs Bad Examples

### Example 1: File System Access in Sandbox

**Good:**
```python
class SandboxedFileAgent:
    """File operations within strict sandbox boundaries"""

    def __init__(self, workspace_path: Path):
        # Create sandbox with explicit allowed/denied paths
        self.sandbox = FileSandbox(
            allowed_roots=[workspace_path],
            allowed_patterns=[
                "src/**/*.py",
                "tests/**/*.py",
                "docs/**/*.md"
            ],
            denied_patterns=[
                "**/.env",
                "**/.git/config",
                "**/secrets/**",
                "**/*.key",
                "**/*.pem"
            ],
            read_only_paths=[
                ".git/",
                "pyproject.toml"
            ]
        )

    def read_file(self, path: Path) -> str:
        """Read file with sandbox enforcement"""
        # Sandbox validates path before access
        if not self.sandbox.can_read(path):
            raise PermissionDenied(f"Cannot read {path}: outside sandbox")

        return path.read_text()

    def write_file(self, path: Path, content: str):
        """Write file with sandbox enforcement"""
        # Check write permissions
        if not self.sandbox.can_write(path):
            raise PermissionDenied(f"Cannot write {path}: outside sandbox or read-only")

        # Check for dangerous patterns in content
        if self.contains_secrets(content):
            raise SecurityViolation("Content contains potential secrets")

        path.write_text(content)
        logger.info(f"Wrote file: {path} ({len(content)} chars)")

# Agent can safely operate within boundaries
agent = SandboxedFileAgent(workspace_path=Path("/workspace/myproject"))
agent.read_file(Path("/workspace/myproject/src/main.py"))  # ✓ Works
agent.write_file(Path("/workspace/myproject/src/util.py"), code)  # ✓ Works
agent.read_file(Path("/workspace/myproject/.env"))  # ✗ Denied - secrets
agent.write_file(Path("/etc/passwd"), "malicious")  # ✗ Denied - outside sandbox
```

**Bad:**
```python
class UnsandboxedFileAgent:
    """File operations with no boundaries"""

    def read_file(self, path: Path) -> str:
        """Read any file on system"""
        return path.read_text()  # No restrictions!

    def write_file(self, path: Path, content: str):
        """Write any file on system"""
        path.write_text(content)  # No restrictions!

# Agent can access anything
agent = UnsandboxedFileAgent()
agent.read_file(Path("/workspace/myproject/src/main.py"))  # ✓ Works
agent.read_file(Path("/etc/passwd"))  # ✓ Works but DANGEROUS
agent.read_file(Path("/workspace/myproject/.env"))  # ✓ Works but DANGEROUS
agent.write_file(Path("/etc/passwd"), "hacked")  # ✓ Works but CATASTROPHIC
```

**Why It Matters:** The sandboxed version restricts file access to workspace boundaries and denies access to sensitive files. Even if the agent is compromised or makes mistakes, it cannot access secrets or system files. The unsandboxed version allows unrestricted file access, enabling agents to read secrets, modify system files, or corrupt critical configuration.

### Example 2: Database Operations with Escalation

**Good:**
```python
class SandboxedDatabaseAgent:
    """Database operations with permission escalation"""

    def __init__(self, escalation_manager: PermissionEscalationManager):
        self.escalation = escalation_manager
        # Start with read-only access
        self.permissions = PermissionSet(["SELECT"])

    async def analyze_data(self, query: str) -> pd.DataFrame:
        """Read-only analysis (no escalation needed)"""
        # Read operations work within base permissions
        return await self.execute_query(query)

    async def update_config(self, table: str, updates: dict):
        """Update configuration (requires escalation)"""
        # Check if we have write permission
        if "UPDATE" not in self.permissions:
            # Request escalation
            approval = await self.escalation.request_approval(
                operation=f"UPDATE {table}",
                reason="Updating configuration values",
                risk_level="medium",
                rollback_plan="Backup current values before update",
                affected_rows=len(updates)
            )

            if not approval.granted:
                raise PermissionDenied("Update not approved")

            # Temporarily grant UPDATE permission
            self.permissions.add("UPDATE")

        # Execute with monitoring
        return await self.execute_update(table, updates)

    async def migrate_schema(self, migration: Migration):
        """Schema changes (requires explicit approval)"""
        # Schema changes always require approval
        approval = await self.escalation.request_approval(
            operation=f"Schema migration: {migration.name}",
            reason=migration.description,
            risk_level="high",
            rollback_plan=migration.rollback_script,
            affected_tables=migration.tables,
            estimated_downtime=migration.estimated_downtime
        )

        if not approval.granted:
            raise PermissionDenied(f"Migration denied: {approval.reason}")

        # Execute migration with rollback capability
        try:
            await self.execute_migration(migration)
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            await self.execute_rollback(migration.rollback_script)
            raise

# Agent operates with appropriate escalation
agent = SandboxedDatabaseAgent(escalation_manager)
await agent.analyze_data("SELECT * FROM users")  # ✓ Works - read-only
await agent.update_config("settings", {"timeout": 30})  # ✓ Approval request
await agent.migrate_schema(migration)  # ✓ Approval required
# await agent.execute_query("DROP TABLE users")  # ✗ Denied - no permission
```

**Bad:**
```python
class UnsandboxedDatabaseAgent:
    """Database operations with admin access"""

    def __init__(self, admin_connection: Connection):
        # Agent has full admin access
        self.db = admin_connection

    async def analyze_data(self, query: str) -> pd.DataFrame:
        """Execute any query"""
        return await self.db.execute(query)

    async def update_config(self, table: str, updates: dict):
        """Execute any update"""
        query = f"UPDATE {table} SET ..."
        return await self.db.execute(query)

    async def migrate_schema(self, migration: Migration):
        """Execute any DDL"""
        return await self.db.execute(migration.sql)

# Agent has unrestricted access
agent = UnsandboxedDatabaseAgent(admin_connection)
await agent.analyze_data("SELECT * FROM users")  # ✓ Works
await agent.update_config("settings", {"timeout": 30})  # ✓ Works
await agent.execute_query("DROP TABLE users")  # ✓ Works but CATASTROPHIC
await agent.execute_query("SELECT * FROM credit_cards")  # ✓ Works but DANGEROUS
```

**Why It Matters:** The sandboxed version starts with read-only access and escalates permissions only when needed, with approval workflows for risky operations. Schema changes require explicit approval with rollback plans. The unsandboxed version gives the agent full admin access, allowing it to drop tables, access sensitive data, or corrupt the database without any approval or oversight.

### Example 3: Production Deployment with Approval

**Good:**
```python
class SandboxedDeploymentAgent:
    """Production deployments with explicit approvals"""

    def __init__(self):
        self.environments = {
            "development": PermissionTier.AUTO,
            "staging": PermissionTier.NOTIFY,
            "production": PermissionTier.APPROVE
        }

    async def deploy(self, environment: str, version: str):
        """Deploy with environment-appropriate approvals"""
        tier = self.environments.get(environment, PermissionTier.APPROVE)

        if tier == PermissionTier.AUTO:
            # Development: auto-deploy
            logger.info(f"Auto-deploying {version} to {environment}")
            return await self.execute_deployment(environment, version)

        elif tier == PermissionTier.NOTIFY:
            # Staging: notify and proceed
            self.notify_team(f"Deploying {version} to {environment}")
            await asyncio.sleep(5)  # Brief pause for cancellation
            return await self.execute_deployment(environment, version)

        elif tier == PermissionTier.APPROVE:
            # Production: require approval
            approval = await self.request_deployment_approval(
                environment=environment,
                version=version,
                changes=self.get_changelog(version),
                tests_passed=await self.verify_tests(version),
                rollback_plan=self.generate_rollback_plan(version),
                affected_users="all production users"
            )

            if not approval.granted:
                raise DeploymentDenied(f"Production deployment denied: {approval.reason}")

            # Execute with enhanced monitoring
            return await self.execute_deployment_with_monitoring(
                environment,
                version,
                monitoring_duration=600  # 10 minutes
            )

    async def execute_deployment_with_monitoring(
        self,
        environment: str,
        version: str,
        monitoring_duration: int
    ):
        """Deploy and monitor for issues"""
        # Create restore point
        restore_point = await self.create_restore_point(environment)

        try:
            # Execute deployment
            await self.execute_deployment(environment, version)

            # Monitor for issues
            health_status = await self.monitor_health(
                duration=monitoring_duration
            )

            if not health_status.healthy:
                # Automatic rollback on health failure
                logger.error(f"Health check failed, rolling back {version}")
                await self.rollback_to(restore_point)
                raise DeploymentFailed("Health checks failed after deployment")

            logger.info(f"Successfully deployed {version} to {environment}")
            return DeploymentResult.SUCCESS

        except Exception as e:
            # Rollback on any error
            logger.exception(f"Deployment failed: {e}")
            await self.rollback_to(restore_point)
            raise

# Adaptive deployment based on environment
agent = SandboxedDeploymentAgent()
await agent.deploy("development", "v1.2.3")  # ✓ Auto-deploys
await agent.deploy("staging", "v1.2.3")  # ✓ Notifies and deploys
await agent.deploy("production", "v1.2.3")  # ✓ Requires approval
```

**Bad:**
```python
class UnsandboxedDeploymentAgent:
    """Deployment with no approvals or safety"""

    async def deploy(self, environment: str, version: str):
        """Deploy to any environment immediately"""
        # No approval workflow
        # No health monitoring
        # No rollback capability
        await self.execute_deployment(environment, version)
        logger.info(f"Deployed {version} to {environment}")

# All deployments treated equally
agent = UnsandboxedDeploymentAgent()
await agent.deploy("development", "v1.2.3")  # ✓ Deploys
await agent.deploy("production", "v1.2.3")  # ✓ Deploys but DANGEROUS
# No approval, no monitoring, no rollback if something breaks
```

**Why It Matters:** The sandboxed version adapts approval requirements to environment risk—development auto-deploys, staging notifies, production requires explicit approval with monitoring and rollback. The unsandboxed version deploys to any environment without approval, monitoring, or rollback capability, making production deployments as risky as development ones.

### Example 4: API Access with Capability Tokens

**Good:**
```python
class SandboxedAPIAgent:
    """API access with capability tokens"""

    def __init__(self, token_manager: CapabilityTokenManager):
        self.tokens = token_manager
        self.current_token = None

    async def fetch_user_data(self, user_id: str) -> dict:
        """Fetch user data with scoped token"""
        # Request token scoped to user data read
        token = await self.tokens.request_token(
            scope=f"user:{user_id}:read",
            operations=["GET"],
            endpoints=[f"/api/users/{user_id}"],
            expiration_minutes=5
        )

        # Use token for request
        response = await self.api_request(
            url=f"/api/users/{user_id}",
            method="GET",
            token=token
        )

        return response.json()

    async def update_user_profile(self, user_id: str, updates: dict):
        """Update user profile with escalated token"""
        # Request token with write permissions
        token = await self.tokens.request_token(
            scope=f"user:{user_id}:write",
            operations=["PUT", "PATCH"],
            endpoints=[f"/api/users/{user_id}"],
            requires_approval=True,  # Write operations require approval
            reason=f"Updating user profile with {list(updates.keys())}",
            expiration_minutes=10
        )

        # Token request may require approval
        if not token:
            raise PermissionDenied("Write token request denied")

        # Execute update with scoped token
        response = await self.api_request(
            url=f"/api/users/{user_id}",
            method="PATCH",
            token=token,
            json=updates
        )

        return response.json()

    async def delete_user(self, user_id: str):
        """Delete user (always requires approval)"""
        # Deletion requires explicit approval
        approval = await self.request_deletion_approval(
            user_id=user_id,
            user_data=await self.fetch_user_data(user_id),
            related_data=await self.find_related_data(user_id)
        )

        if not approval.granted:
            raise PermissionDenied(f"User deletion denied: {approval.reason}")

        # Request token for deletion
        token = await self.tokens.request_token(
            scope=f"user:{user_id}:delete",
            operations=["DELETE"],
            endpoints=[f"/api/users/{user_id}"],
            approved_by=approval.approver,
            expiration_minutes=5
        )

        # Execute deletion
        await self.api_request(
            url=f"/api/users/{user_id}",
            method="DELETE",
            token=token
        )

        logger.info(f"Deleted user {user_id} (approved by {approval.approver})")

# Agent uses scoped tokens per operation
agent = SandboxedAPIAgent(token_manager)
await agent.fetch_user_data("123")  # ✓ Read token issued
await agent.update_user_profile("123", {"name": "John"})  # ✓ Write approval
await agent.delete_user("123")  # ✓ Explicit approval required
# await agent.api_request("/api/admin/config", "POST", {})  # ✗ No token for admin
```

**Bad:**
```python
class UnsandboxedAPIAgent:
    """API access with admin token"""

    def __init__(self, admin_api_key: str):
        # Agent has one admin token for everything
        self.api_key = admin_api_key

    async def fetch_user_data(self, user_id: str) -> dict:
        """Fetch user data"""
        return await self.api_request(
            url=f"/api/users/{user_id}",
            method="GET"
        )

    async def update_user_profile(self, user_id: str, updates: dict):
        """Update user profile"""
        return await self.api_request(
            url=f"/api/users/{user_id}",
            method="PATCH",
            json=updates
        )

    async def delete_user(self, user_id: str):
        """Delete user"""
        return await self.api_request(
            url=f"/api/users/{user_id}",
            method="DELETE"
        )

    async def api_request(self, url: str, method: str, **kwargs):
        """Make API request with admin key"""
        # Single admin key for all operations
        headers = {"Authorization": f"Bearer {self.api_key}"}
        return await http_request(url, method, headers=headers, **kwargs)

# Agent can do anything with admin key
agent = UnsandboxedAPIAgent(admin_api_key)
await agent.fetch_user_data("123")  # ✓ Works
await agent.delete_user("123")  # ✓ Works but DANGEROUS - no approval
await agent.api_request("/api/admin/delete_all_users", "POST")  # ✓ Works but CATASTROPHIC
```

**Why It Matters:** The sandboxed version uses short-lived capability tokens scoped to specific operations and resources. Read operations get read tokens, write operations require approval, deletions always require explicit approval. The unsandboxed version uses one admin API key for everything, giving the agent unrestricted access to all API endpoints including dangerous operations like bulk deletions.

### Example 5: Container Execution with Resource Limits

**Good:**
```python
class SandboxedExecutionAgent:
    """Execute code in isolated containers with resource limits"""

    def __init__(self):
        self.container_runtime = ContainerRuntime()

    async def execute_code(self, code: str, language: str) -> ExecutionResult:
        """Execute code in isolated sandbox container"""
        # Create sandbox config with strict limits
        sandbox = await self.container_runtime.create_sandbox(
            image=f"{language}-runtime:latest",
            config=SandboxConfig(
                # Resource limits
                memory_limit_mb=512,
                cpu_limit_percent=25,
                disk_limit_mb=100,
                process_limit=10,

                # Network isolation
                network_mode="none",  # No network access

                # Filesystem isolation
                filesystem="tmpfs",  # Temporary filesystem
                readonly_root=True,
                allowed_mounts={"/workspace": "rw"},

                # Time limits
                max_execution_seconds=30,
                idle_timeout_seconds=10,

                # Security
                no_new_privileges=True,
                drop_capabilities=["ALL"],
                seccomp_profile="restricted",
                apparmor_profile="restricted"
            )
        )

        try:
            # Write code to workspace
            await sandbox.write_file("/workspace/code", code)

            # Execute with monitoring
            result = await sandbox.execute(
                command=[language, "/workspace/code"],
                timeout=30,
                capture_output=True
            )

            return ExecutionResult(
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.exit_code,
                execution_time=result.duration,
                resources_used=result.resource_usage
            )

        finally:
            # Always cleanup sandbox
            await sandbox.destroy()

    async def execute_with_network(self, code: str, language: str):
        """Execute code requiring network access (requires approval)"""
        # Network access requires approval
        approval = await self.request_approval(
            operation="Execute code with network access",
            code_preview=code[:500],
            reason="Code requires external API access",
            risk_level="medium"
        )

        if not approval.granted:
            raise PermissionDenied("Network access denied")

        # Create sandbox with limited network access
        sandbox = await self.container_runtime.create_sandbox(
            image=f"{language}-runtime:latest",
            config=SandboxConfig(
                memory_limit_mb=512,
                cpu_limit_percent=25,

                # Limited network access
                network_mode="restricted",
                allowed_domains=approval.allowed_domains,
                blocked_domains=["*"],  # Block all except allowed

                max_execution_seconds=60
            )
        )

        try:
            return await sandbox.execute_code(code)
        finally:
            await sandbox.destroy()

# Agent executes code in isolated containers
agent = SandboxedExecutionAgent()
result = await agent.execute_code("print('hello')", "python")  # ✓ Isolated
# result = await agent.execute_code("import requests", "python")  # ✗ Network denied
result = await agent.execute_with_network("import requests", "python")  # ✓ With approval
```

**Bad:**
```python
class UnsandboxedExecutionAgent:
    """Execute code directly on host system"""

    async def execute_code(self, code: str, language: str) -> ExecutionResult:
        """Execute code on host system"""
        # Write code to temp file
        with open("/tmp/code", "w") as f:
            f.write(code)

        # Execute directly on host
        process = await subprocess.run(
            [language, "/tmp/code"],
            capture_output=True,
            # No timeout, no resource limits, no isolation
        )

        return ExecutionResult(
            stdout=process.stdout,
            stderr=process.stderr,
            exit_code=process.returncode
        )

# Agent executes code directly on host
agent = UnsandboxedExecutionAgent()
result = await agent.execute_code("print('hello')", "python")  # ✓ Works
result = await agent.execute_code("import os; os.system('rm -rf /')", "python")  # ✓ Works but CATASTROPHIC
result = await agent.execute_code("while True: pass", "python")  # ✓ Works but HANGS SYSTEM
```

**Why It Matters:** The sandboxed version executes code in isolated containers with strict resource limits, no network access by default, and automatic cleanup. Resource exhaustion or malicious code cannot affect the host system. The unsandboxed version executes code directly on the host with no isolation, resource limits, or timeouts, allowing malicious code to damage the system or infinite loops to hang the machine.

## Related Principles

- **[Principle #35 - Least-Privilege Automation with Scoped Permissions](../technology/35-least-privilege-automation.md)** - Foundational principle that sandboxing implements; starts with minimal permissions and grants more only when needed, with sandboxes enforcing the permission boundaries

- **[Principle #02 - Strategic Human Touchpoints Only](../people/02-strategic-human-touchpoints.md)** - Defines when humans should approve escalations; approval workflows implement strategic touchpoints for permission escalation beyond sandbox boundaries

- **[Principle #20 - Self-Modifying AI-First Codebase](../technology/20-self-modifying-ai-first-codebase.md)** - Self-modification requires sandboxing to contain blast radius; AI agents modifying their own code must operate within protected sandbox boundaries to prevent self-corruption

- **[Principle #23 - Protected Self-Healing Kernel](../technology/23-protected-self-healing-kernel.md)** - Provides protected infrastructure that sandboxes cannot modify; healing kernel remains isolated from sandboxed agents, ensuring recovery capability even when agents violate boundaries

- **[Principle #38 - Security Defaults Everywhere](38-security-defaults-everywhere.md)** - Sandboxing is a security default; all AI operations start in sandboxes by default, with explicit opt-in for elevated privileges rather than opt-out

- **[Principle #21 - Logging First Always](../technology/21-logging-first-always.md)** - Sandbox violations and approval requests must be comprehensively logged; audit trail of permission escalations and boundary violations is essential for security

## Common Pitfalls

1. **Static Sandboxes That Never Escalate**: Creating sandboxes so restrictive that agents cannot perform valuable work, forcing developers to disable sandboxing entirely.
   - Example: Sandbox that prevents all network access but agent needs to deploy code via SSH.
   - Impact: Developers bypass sandbox completely, losing all protection. Agents run with full privileges.

2. **Approval Fatigue from Too Many Requests**: Requiring approval for every minor escalation trains humans to approve reflexively without review.
   - Example: Agent requests approval for every configuration file change, even trivial ones.
   - Impact: Humans approve all requests without reading, defeating purpose of approvals.

3. **Insufficient Context in Approval Requests**: Approval requests that don't explain risk or provide rollback plans force humans to investigate before deciding.
   - Example: "Agent requests database write access" without explaining what will be written or why.
   - Impact: Humans either deny all requests to be safe or approve blindly to move quickly.

4. **No Automatic Fallback to Safe Mode**: Sandboxes that detect violations but don't automatically enforce safe mode allow continued damage.
   - Example: Logging permission violations but allowing agent to continue with elevated permissions.
   - Impact: Violations detected but not prevented; agent continues damaging behavior until human intervenes.

5. **Shared Sandboxes Between Agents**: Multiple agents sharing one sandbox allows one compromised agent to affect others.
   - Example: All code analysis agents share single container with shared filesystem.
   - Impact: One agent reads secrets, corrupts files, or exhausts resources affecting all others.

6. **Time-Unlimited Elevated Permissions**: Granting elevated permissions without expiration leaves long windows for exploitation.
   - Example: Approving database write access that never expires, even for one-time migration.
   - Impact: Permissions intended for specific task remain indefinitely, expanding attack surface.

7. **No Resource Limits in Sandboxes**: Sandboxes without memory, CPU, or disk limits allow resource exhaustion attacks.
   - Example: Container with no memory limit allows agent to allocate unlimited RAM.
   - Impact: Agent exhausts host resources, causing cascading failures across other services.

## Tools & Frameworks

### Container Sandboxing
- **Docker**: Container isolation with resource limits (--memory, --cpus), network modes (none, bridge, custom), and security profiles (AppArmor, SELinux, seccomp)
- **Podman**: Rootless containers by default, enhanced security, compatible with Docker but daemon-less
- **gVisor**: Application kernel for strong container sandboxing, syscall filtering, network policy enforcement
- **Firecracker**: Lightweight microVMs for serverless-grade isolation, minimal attack surface, fast startup

### Permission Management
- **HashiCorp Vault**: Dynamic secrets with automatic rotation, time-limited leases, policy-based access control
- **AWS IAM**: Fine-grained permission policies, temporary credentials via STS, role assumption with duration limits
- **Open Policy Agent (OPA)**: Policy-as-code for permission decisions, flexible policy language, audit logging
- **Casbin**: Access control library supporting RBAC, ABAC, ACL with multiple policy models

### Approval Workflows
- **Temporal**: Workflow orchestration with human-in-the-loop activities, durable execution, timeout handling
- **Camunda**: BPMN workflow engine with human tasks, escalation policies, approval routing
- **Apache Airflow**: DAG-based workflows with approval operators, task dependencies, retry logic
- **GitHub Actions with Manual Approval**: Deployment gates requiring manual approval before proceeding

### Sandbox Monitoring
- **Falco**: Runtime security for containers, syscall monitoring, anomaly detection, custom rules
- **Sysdig**: Container security and monitoring, behavioral analysis, threat detection
- **Cilium**: eBPF-based networking and security, network policy enforcement, observability
- **AppArmor/SELinux**: Mandatory access control for process confinement, profile-based restrictions

### Resource Management
- **Kubernetes**: Resource limits and requests per pod, namespace quotas, limit ranges
- **cgroups**: Linux kernel feature for resource isolation and limiting (CPU, memory, I/O)
- **systemd**: Resource management with slice units, dynamic resource allocation
- **Docker Compose**: Declarative resource limits, network isolation, volume management

### Capability Tokens
- **SPIFFE/SPIRE**: Workload identity with short-lived credentials, automatic rotation, zero-trust networking
- **Macaroons**: Capability-based authorization tokens with contextual caveats
- **JWT with Scoped Claims**: JSON Web Tokens with specific scope claims, audience validation
- **OAuth 2.0**: Token-based authorization with scopes, refresh tokens, client credentials flow

## Implementation Checklist

When implementing this principle, ensure:

- [ ] All AI agents start with minimal permissions (read-only by default)
- [ ] Sandboxes enforce filesystem boundaries preventing access to secrets and system files
- [ ] Network access is restricted by default with allow-lists for approved domains
- [ ] Resource limits (memory, CPU, disk) are enforced to prevent exhaustion attacks
- [ ] Permission escalation requests include comprehensive risk assessment and rollback plans
- [ ] Approval workflows route high-risk operations to appropriate humans with sufficient context
- [ ] Elevated permissions are time-limited and expire automatically after use
- [ ] Sandbox violations trigger automatic safe mode with revoked permissions
- [ ] All escalations and violations are logged with full audit trail
- [ ] Progressive permission unlocking rewards demonstrated safe behavior
- [ ] Containers are isolated per-agent preventing cross-contamination
- [ ] Capability tokens are scoped to specific resources and operations with expiration

## Metadata

**Category**: Governance
**Principle Number**: 41
**Related Patterns**: Sandbox Pattern, Capability-Based Security, Least Privilege, Human-in-the-Loop, Progressive Enhancement, Fail-Safe Defaults
**Prerequisites**: Container runtime, permission management system, approval workflow infrastructure, monitoring and alerting
**Difficulty**: High
**Impact**: High

---

**Status**: Complete
**Last Updated**: 2025-09-30
**Version**: 1.0