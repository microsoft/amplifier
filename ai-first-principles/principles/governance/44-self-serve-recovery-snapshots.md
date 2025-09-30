# Principle #44 - Self-Serve Recovery with Known-Good Snapshots

## Plain-Language Definition

Self-serve recovery means enabling any team member to restore systems to a verified working state without expert intervention. Known-good snapshots are validated, timestamped copies of working configurations, data, and code that can be restored with a single action.

## Why This Matters for AI-First Development

When AI agents modify systems, the probability of introducing breaking changes increases dramatically. Unlike human developers who carefully test each change, AI agents can generate and deploy modifications at scale across multiple components simultaneously. A single incorrect assumption can cascade through dozens of automated changes before anyone notices. Without reliable recovery mechanisms, these failures can compound into system-wide outages that require expert intervention to resolve.

Known-good snapshots provide three critical capabilities for AI-driven development:

1. **Fearless experimentation**: AI agents can explore multiple solution paths in parallel when they know any path can be abandoned instantly. This enables the "build multiple variants" philosophy where agents try several approaches and revert the unsuccessful ones. Without reliable rollback, agents must be overly conservative, limiting innovation.

2. **Automated recovery**: When AI agents detect that their changes broke something, they need a reliable way to self-correct. Snapshots enable agents to implement automatic recovery workflows: deploy change, validate, revert if validation fails. This closes the feedback loop without human intervention, allowing AI systems to operate autonomously.

3. **Reduced mean time to recovery (MTTR)**: When failures do occur, the difference between 2-minute recovery and 2-hour recovery is often the difference between minor incident and major outage. Self-serve snapshots enable anyone (including AI agents) to restore service immediately rather than waiting for experts to diagnose and fix the problem manually.

Without self-serve recovery, AI-first development becomes too risky. Organizations limit AI agent capabilities to prevent catastrophic failures, which defeats the purpose of AI-driven development. Teams spend more time on incident response than on building features. The fear of breaking things creates a culture of caution rather than innovation.

## Implementation Approaches

### 1. **Automated Snapshot Creation on Successful Validation**

Create snapshots automatically whenever the system passes all validation checks:

```python
def create_snapshot_after_validation():
    """Automatically snapshot after successful validation"""
    validation_result = run_full_validation_suite()

    if validation_result.passed:
        snapshot_id = create_snapshot(
            timestamp=now(),
            commit_sha=get_current_commit(),
            validation_results=validation_result,
            metadata={"trigger": "automated_validation"}
        )
        tag_snapshot_as_known_good(snapshot_id)
        logger.info(f"Created known-good snapshot: {snapshot_id}")
```

This ensures you always have recent snapshots from working states, not just arbitrary points in time. Use this approach in CI/CD pipelines and after major deployments.

### 2. **One-Click Rollback from UI or CLI**

Provide a simple interface for restoring any snapshot:

```bash
# CLI version
amplifier snapshot restore --id snap_20250930_143022 --confirm

# Or interactive
amplifier snapshot restore --latest-known-good

# With automatic validation
amplifier snapshot restore --id snap_20250930_143022 --validate
```

The command should handle all complexity internally: stopping services, restoring files and database state, restarting services, and validating the restoration. Success looks like: team member runs one command, system restores to working state in under 2 minutes.

### 3. **Immutable Snapshot Storage with Metadata**

Store snapshots immutably with rich metadata for searchability:

```python
@dataclass
class Snapshot:
    id: str  # snap_YYYYMMDD_HHMMSS
    timestamp: datetime
    commit_sha: str
    branch: str
    validation_status: str  # "passed" | "failed" | "unknown"
    test_results: dict
    performance_metrics: dict
    config_hash: str
    database_schema_version: str
    tags: list[str]  # ["known-good", "pre-deployment", "manual"]
    created_by: str  # "ci-pipeline" | "user@example.com" | "ai-agent"

    # What this snapshot contains
    artifacts: list[str]  # ["database", "config", "code", "dependencies"]

    # Restoration metadata
    restore_count: int
    last_restored: datetime | None
```

This metadata enables finding the right snapshot quickly: "Show me the last known-good snapshot from main branch before yesterday's deployment."

### 4. **Validation Before Snapshot Creation**

Never create snapshots without verifying they actually work:

```python
def create_validated_snapshot(description: str):
    """Only create snapshot if system is healthy"""
    health_checks = run_health_checks()

    if not health_checks.all_passed():
        logger.error("System unhealthy, refusing to create snapshot")
        logger.error(f"Failed checks: {health_checks.failed}")
        return None

    smoke_tests = run_smoke_tests()
    if not smoke_tests.passed:
        logger.error("Smoke tests failed, refusing to create snapshot")
        return None

    # System is healthy, safe to snapshot
    return create_snapshot(
        description=description,
        validation={"health": health_checks, "smoke": smoke_tests},
        tags=["validated", "known-good"]
    )
```

A snapshot of a broken system is worse than no snapshot at all. Validate before snapshotting.

### 5. **Snapshot Testing in Non-Production**

Test snapshot restoration regularly in non-production environments:

```python
def test_snapshot_recovery():
    """Verify snapshots can actually be restored"""
    # Schedule weekly in staging
    latest_prod_snapshot = get_latest_snapshot(env="production", tag="known-good")

    # Restore to staging
    restore_snapshot(snapshot_id=latest_prod_snapshot.id, target_env="staging")

    # Validate restored system
    validation = run_full_validation_suite(env="staging")

    if not validation.passed:
        alert_team(
            "Snapshot restoration failed in staging",
            snapshot_id=latest_prod_snapshot.id,
            failures=validation.failures
        )

    # Cleanup staging
    cleanup_staging_environment()
```

This catches snapshot corruption, missing dependencies, or restoration logic bugs before you need to use snapshots in production.

### 6. **Granular Snapshot Scopes**

Support different snapshot scopes for different recovery needs:

```python
class SnapshotScope(Enum):
    """Different levels of snapshot granularity"""
    FULL_SYSTEM = "full"  # Everything: code, config, data, dependencies
    DATABASE_ONLY = "database"  # Just database state
    CONFIG_ONLY = "config"  # Just configuration files
    CODE_ONLY = "code"  # Just code (git commit)
    DEPENDENCIES = "dependencies"  # Just installed packages

def create_snapshot(scope: SnapshotScope, description: str):
    """Create snapshot with specified scope"""
    if scope == SnapshotScope.DATABASE_ONLY:
        # Fast: just dump database
        snapshot_id = dump_database()
    elif scope == SnapshotScope.FULL_SYSTEM:
        # Comprehensive: everything needed for full recovery
        snapshot_id = snapshot_full_system()
    # etc.

    return snapshot_id
```

Full system snapshots provide complete recovery but take time and storage. Database-only snapshots enable quick recovery from data corruption. Choose based on recovery needs.

## Good Examples vs Bad Examples

### Example 1: Automated Snapshot Creation

**Good:**
```python
def deploy_with_automatic_snapshot(version: str):
    """Create snapshot before deployment for easy rollback"""
    logger.info("Creating pre-deployment snapshot...")

    # Snapshot current working state before making changes
    pre_deploy_snapshot = create_validated_snapshot(
        description=f"Before deploying {version}",
        tags=["pre-deployment", "auto-rollback-point"]
    )

    if not pre_deploy_snapshot:
        logger.error("Cannot create snapshot, aborting deployment")
        return False

    try:
        # Deploy new version
        deploy_result = deploy_version(version)

        # Validate deployment
        validation = run_full_validation_suite()

        if validation.passed:
            # Create snapshot of successful deployment
            post_deploy_snapshot = create_validated_snapshot(
                description=f"After successful deployment of {version}",
                tags=["post-deployment", "known-good"]
            )
            return True
        else:
            # Validation failed, automatic rollback
            logger.error("Deployment validation failed, rolling back...")
            restore_snapshot(pre_deploy_snapshot.id)
            return False

    except Exception as e:
        logger.error(f"Deployment failed: {e}, rolling back...")
        restore_snapshot(pre_deploy_snapshot.id)
        return False
```

**Bad:**
```python
def deploy_with_automatic_snapshot(version: str):
    """No validation, snapshots at wrong times"""
    # Create snapshot AFTER deployment (too late)
    deploy_version(version)

    # No validation before snapshot
    snapshot_id = create_snapshot("Deployment snapshot")

    # No automatic rollback on failure
    # If deployment broke something, snapshot captures the broken state
```

**Why It Matters:** Snapshots are only useful if they capture working states. Creating snapshots after changes without validation means you're snapshotting potentially broken systems. Without automatic rollback, deployment failures require manual intervention.

### Example 2: One-Click Recovery Interface

**Good:**
```python
@click.command()
@click.option("--id", help="Snapshot ID to restore")
@click.option("--latest-known-good", is_flag=True, help="Restore latest validated snapshot")
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
@click.option("--validate", is_flag=True, help="Run validation after restore")
def restore(id: str, latest_known_good: bool, confirm: bool, validate: bool):
    """Restore system from snapshot - one command, no expert needed"""

    # Determine which snapshot to restore
    if latest_known_good:
        snapshot = get_latest_known_good_snapshot()
        logger.info(f"Selected latest known-good: {snapshot.id} from {snapshot.timestamp}")
    elif id:
        snapshot = get_snapshot(id)
    else:
        # Show interactive menu
        snapshot = select_snapshot_interactive()

    # Show what will be restored
    logger.info(f"Will restore snapshot: {snapshot.id}")
    logger.info(f"  Created: {snapshot.timestamp}")
    logger.info(f"  Description: {snapshot.description}")
    logger.info(f"  Contains: {', '.join(snapshot.artifacts)}")
    logger.info(f"  Previous restores: {snapshot.restore_count}")

    # Confirm (unless --confirm flag)
    if not confirm:
        if not click.confirm("Proceed with restoration?"):
            logger.info("Restoration cancelled")
            return

    # Execute restoration
    logger.info("Starting restoration...")
    with progress_bar() as bar:
        restore_result = restore_snapshot(snapshot.id, progress=bar)

    if restore_result.success:
        logger.info("✓ Restoration completed successfully")

        # Optional validation
        if validate:
            logger.info("Running validation...")
            validation = run_full_validation_suite()
            if validation.passed:
                logger.info("✓ System validation passed")
            else:
                logger.error("✗ Validation failed after restore")
                logger.error(f"Failed checks: {validation.failures}")
    else:
        logger.error("✗ Restoration failed")
        logger.error(f"Error: {restore_result.error}")
```

**Bad:**
```python
def restore(snapshot_id: str):
    """Complex multi-step restoration requiring expert knowledge"""
    # Stop services manually
    print("Step 1: Stop all services (run: systemctl stop app)")
    input("Press enter when done...")

    # Restore database
    print("Step 2: Restore database")
    print(f"  Run: pg_restore -d mydb {snapshot_id}/database.dump")
    input("Press enter when done...")

    # Restore config files
    print("Step 3: Copy config files")
    print(f"  Run: cp -r {snapshot_id}/config/* /etc/myapp/")
    input("Press enter when done...")

    # Restore code
    print("Step 4: Checkout code")
    print(f"  Run: git checkout {get_commit_from_snapshot(snapshot_id)}")
    input("Press enter when done...")

    # Restart services
    print("Step 5: Start services")
    print("  Run: systemctl start app")
    input("Press enter when done...")

    print("Restoration complete (hopefully)")
```

**Why It Matters:** Self-serve means anyone can do it, not just experts. Multi-step manual processes require knowledge, introduce human error, and take too long during incidents. One-click restoration means 2-minute recovery instead of 2-hour recovery.

### Example 3: Snapshot Metadata and Searchability

**Good:**
```python
def find_best_snapshot(criteria: dict):
    """Rich metadata enables finding the right snapshot quickly"""
    # Example queries:
    # "Last known-good before incident"
    # "Most recent snapshot that passed performance tests"
    # "Snapshot from before feature X was deployed"

    snapshots = query_snapshots(
        validation_status="passed",
        tags=["known-good"],
        created_after=criteria.get("after"),
        created_before=criteria.get("before"),
        branch=criteria.get("branch", "main"),
        order_by="timestamp DESC"
    )

    # Filter by additional criteria
    if "performance_threshold" in criteria:
        snapshots = [
            s for s in snapshots
            if s.performance_metrics["response_time_p95"] < criteria["performance_threshold"]
        ]

    if "before_commit" in criteria:
        commit_time = get_commit_timestamp(criteria["before_commit"])
        snapshots = [s for s in snapshots if s.timestamp < commit_time]

    return snapshots[0] if snapshots else None


# Example usage:
snapshot = find_best_snapshot({
    "after": datetime.now() - timedelta(days=7),  # Last 7 days
    "before": incident_time,  # Before the incident
    "performance_threshold": 100,  # Response time < 100ms
})

if snapshot:
    restore_snapshot(snapshot.id)
```

**Bad:**
```python
def find_best_snapshot(criteria: dict):
    """Minimal metadata makes finding right snapshot hard"""
    # Only have filename and timestamp
    snapshots = list(Path("/backups").glob("snapshot_*.tar.gz"))
    snapshots.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    # Can't tell which snapshots were validated
    # Can't tell which branch they're from
    # Can't tell what's in them
    # Can't tell if they passed tests

    # Just return most recent and hope it works
    return snapshots[0] if snapshots else None
```

**Why It Matters:** During an incident, you need to find the right snapshot quickly. Minimal metadata means guessing which snapshot to try. Rich metadata enables precise queries: "Last known-good snapshot from main branch that passed all tests before yesterday's deployment."

### Example 4: Validation Before Snapshotting

**Good:**
```python
def create_snapshot_with_validation(description: str):
    """Never snapshot a broken system"""

    logger.info("Validating system health before snapshot...")

    # Check 1: Services are running
    services = check_service_health()
    if not services.all_healthy():
        logger.error(f"Services unhealthy: {services.unhealthy}")
        logger.error("Refusing to create snapshot of unhealthy system")
        return None

    # Check 2: Database connectivity and integrity
    db_health = check_database_health()
    if not db_health.passed:
        logger.error(f"Database issues: {db_health.issues}")
        logger.error("Refusing to snapshot with database problems")
        return None

    # Check 3: Core functionality works
    smoke_tests = run_smoke_tests()
    if smoke_tests.failed_count > 0:
        logger.error(f"Smoke tests failed: {smoke_tests.failures}")
        logger.error("Refusing to snapshot failing system")
        return None

    # Check 4: No active alerts
    alerts = get_active_alerts()
    if alerts:
        logger.warning(f"Active alerts: {alerts}")
        if not click.confirm("System has active alerts. Create snapshot anyway?"):
            return None

    # All checks passed, safe to snapshot
    logger.info("✓ All validation passed, creating snapshot...")
    snapshot = create_snapshot(
        description=description,
        validation_results={
            "services": services,
            "database": db_health,
            "smoke_tests": smoke_tests,
        },
        tags=["validated", "known-good"]
    )

    logger.info(f"✓ Created validated snapshot: {snapshot.id}")
    return snapshot
```

**Bad:**
```python
def create_snapshot_with_validation(description: str):
    """Creates snapshot without verification"""
    # No validation, just snapshot whatever state exists
    snapshot = create_snapshot(description=description)

    # Might snapshot:
    # - Broken system mid-deployment
    # - Database in inconsistent state
    # - Services crashed
    # - Config files corrupted

    # You won't know until you try to restore it during an incident
    return snapshot
```

**Why It Matters:** A snapshot of a broken system is worse than no snapshot. During recovery, you need confidence that the snapshot represents a working state. Restoring an unvalidated snapshot might make the situation worse.

### Example 5: Automated Snapshot Testing

**Good:**
```python
@scheduled_task(cron="0 2 * * 0")  # Weekly, Sunday 2 AM
def test_snapshot_recovery_process():
    """Verify snapshots can actually be restored (run weekly in staging)"""

    logger.info("Starting weekly snapshot recovery test...")

    # Get latest production snapshot
    prod_snapshot = get_latest_snapshot(
        env="production",
        tags=["known-good"],
        validation_status="passed"
    )

    if not prod_snapshot:
        alert_team("No production snapshots found for recovery testing")
        return

    logger.info(f"Testing recovery of snapshot: {prod_snapshot.id}")

    # Restore to staging environment
    staging_state = snapshot_staging_environment()  # Save staging state

    try:
        # Attempt restoration
        restore_result = restore_snapshot(
            snapshot_id=prod_snapshot.id,
            target_env="staging"
        )

        if not restore_result.success:
            alert_team(
                title="Snapshot restoration failed in test",
                snapshot=prod_snapshot.id,
                error=restore_result.error,
                severity="high"
            )
            return

        # Validate restored system
        validation = run_full_validation_suite(env="staging")

        if not validation.passed:
            alert_team(
                title="Restored snapshot failed validation",
                snapshot=prod_snapshot.id,
                failures=validation.failures,
                severity="high"
            )
        else:
            logger.info(f"✓ Snapshot {prod_snapshot.id} restored and validated successfully")

            # Record successful test
            record_snapshot_test(
                snapshot_id=prod_snapshot.id,
                test_result="passed",
                timestamp=now()
            )

    finally:
        # Restore staging to original state
        restore_snapshot(staging_state.id, target_env="staging")


def get_snapshot_reliability_metrics():
    """Track how often snapshot restoration succeeds"""
    tests = get_snapshot_tests(days=90)

    return {
        "total_tests": len(tests),
        "passed": len([t for t in tests if t.result == "passed"]),
        "failed": len([t for t in tests if t.result == "failed"]),
        "success_rate": len([t for t in tests if t.result == "passed"]) / len(tests),
        "avg_restore_time": mean([t.duration for t in tests]),
    }
```

**Bad:**
```python
def test_snapshot_recovery_process():
    """Never test snapshot restoration until production incident"""
    # Assume snapshots work
    # Never test restoration process
    # First time you try to restore is during a critical incident
    # Discover then that:
    #   - Snapshots are corrupted
    #   - Restoration script has bugs
    #   - Dependencies are missing
    #   - Database dumps are incomplete
    #   - Process takes 3 hours, not 3 minutes
    pass
```

**Why It Matters:** Untested snapshots are useless during incidents. Regular testing catches corruption, missing dependencies, and restoration bugs before you need snapshots in production. Testing also trains the team on the recovery process and measures actual recovery time.

## Related Principles

- **[Principle #10 - Git as Safety Net](../process/10-git-as-safety-net.md)** - Git provides code-level snapshots; this principle extends snapshot thinking to entire system state including configuration and data

- **[Principle #23 - Protected Self-Healing Kernel](../technology/23-protected-self-healing-kernel.md)** - Self-healing requires reliable snapshots to restore from; snapshots enable automated recovery workflows

- **[Principle #32 - Error Recovery Patterns Built In](../technology/32-error-recovery-patterns.md)** - Snapshots are the foundational recovery pattern that enables other recovery strategies

- **[Principle #15 - Continuous Deployment Safety](../process/15-continuous-deployment-safety.md)** - Snapshots enable safe continuous deployment by providing instant rollback capability

- **[Principle #31 - Idempotency by Design](../technology/31-idempotency-by-design.md)** - Snapshot restoration must be idempotent; restoring the same snapshot multiple times should produce identical results

- **[Principle #6 - Parallel Experimentation](../process/06-parallel-experimentation.md)** - Snapshots enable fearless parallel experimentation because any experiment can be abandoned instantly without affecting other variants

## Common Pitfalls

1. **Creating Snapshots Without Validation**: Snapshotting systems in unknown or broken states defeats the purpose of "known-good" snapshots.
   - Example: Automated snapshot creation that runs regardless of system health, capturing broken states mid-deployment.
   - Impact: During recovery, you restore to a snapshot only to discover it's also broken. No actual recovery occurs.

2. **Insufficient Snapshot Metadata**: Minimal metadata makes finding the right snapshot during incidents impossible.
   - Example: Snapshots named only by timestamp with no indication of what they contain, which branch, or whether they were validated.
   - Impact: During incidents, teams waste critical time guessing which snapshot to try, often trying multiple before finding one that works.

3. **Never Testing Snapshot Restoration**: Assuming snapshots work without regular testing means discovering problems during production incidents.
   - Example: Weekly automated snapshots for 6 months, never tested. During incident, discover snapshots are missing database sequences, restoration takes 4 hours instead of 5 minutes.
   - Impact: MTTR extends from minutes to hours. Team loses confidence in recovery process.

4. **Incomplete Snapshot Scope**: Snapshotting code but not configuration, or database but not uploaded files, means partial recovery.
   - Example: Database snapshot without the uploaded user avatars, or code snapshot without the environment configuration.
   - Impact: After restoration, system appears to work but features are broken due to missing data or configuration.

5. **No Snapshot Retention Policy**: Keeping all snapshots forever fills storage; deleting all old snapshots eliminates recovery options.
   - Example: Snapshot storage fills up, automated snapshots start failing. Or aggressive deletion means no snapshots from before last week's breaking change.
   - Impact: Either snapshots stop working (storage full) or you can't recover from older issues (all old snapshots deleted).

6. **Manual Multi-Step Recovery Process**: Requiring expert knowledge and multiple manual steps means recovery takes too long and is error-prone.
   - Example: 15-step recovery runbook requiring database knowledge, deployment expertise, and specific command-line incantations.
   - Impact: Only experts can recover systems. Recovery takes hours. Mistakes during manual process make situation worse.

7. **Snapshots Not Accessible During Outages**: Storing snapshots in the same system that's failing means you can't access them when you need them.
   - Example: Snapshots stored in database that's corrupted, or on disk that's full, or in cloud region that's down.
   - Impact: Complete inability to recover. Snapshots exist but are unreachable during the incident they're meant to solve.

## Tools & Frameworks

### Database Snapshot Tools
- **pg_dump / pg_restore (PostgreSQL)**: Native backup and restore with consistent snapshots, supports compression and parallel restore
- **MySQL Enterprise Backup**: Hot backup solution with point-in-time recovery and partial backup support
- **MongoDB Cloud Backup**: Continuous backup with point-in-time restore and automatic retention policies
- **Redis RDB/AOF**: Snapshot-based and append-only persistence with configurable snapshot frequency

### Infrastructure Snapshot Tools
- **AWS EC2 Snapshots**: Block-level volume snapshots with incremental storage, supports automated scheduling via Lambda
- **Terraform State Snapshots**: Version-controlled infrastructure state with built-in rollback via state files
- **Docker Image Tags**: Immutable container snapshots with content-addressable storage and automated tagging
- **Kubernetes Velero**: Backup and restore for entire Kubernetes clusters including persistent volumes and namespaces

### Application-Level Snapshot Tools
- **Git Tags/Releases**: Code snapshots with semantic versioning and automated release workflows
- **Restic**: Fast incremental backup tool with deduplication, encryption, and multiple storage backend support
- **Borg Backup**: Deduplicating backup with compression, supporting remote repositories and append-only mode
- **Bacula**: Enterprise backup solution with snapshot integration and bare-metal recovery

### Testing and Validation Tools
- **Chaos Engineering Tools (Chaos Monkey, Gremlin)**: Test recovery by randomly creating failures that require snapshot restoration
- **Synthetic Monitoring**: Continuous validation that can trigger snapshot creation when all checks pass
- **pytest-postgresql**: Test fixtures that automatically create and restore database snapshots between tests

## Implementation Checklist

When implementing this principle, ensure:

- [ ] Snapshots are only created after successful validation of system health
- [ ] Every snapshot includes rich metadata (commit SHA, branch, validation results, performance metrics)
- [ ] One-command restoration process that requires no expert knowledge
- [ ] Snapshots include complete system state (code, config, database, uploaded files, dependencies)
- [ ] Automated snapshot creation after successful deployments and validation
- [ ] Regular testing of snapshot restoration in non-production environments (at least monthly)
- [ ] Snapshot retention policy balances storage costs with recovery needs
- [ ] Snapshots stored outside the system they snapshot (different disk, region, or cloud provider)
- [ ] Clear tagging system to identify known-good snapshots vs experimental snapshots
- [ ] Restoration process validates restored system automatically
- [ ] Searchable snapshot catalog enables finding right snapshot during incidents
- [ ] MTTR metrics tracked for snapshot restoration (target: under 5 minutes)

## Metadata

**Category**: Governance
**Principle Number**: 44
**Related Patterns**: Snapshot Pattern, Memento Pattern, Command Pattern, Blue-Green Deployment, Canary Deployment
**Prerequisites**: Automated validation suite, consistent deployment process, version control
**Difficulty**: Medium
**Impact**: High

---

**Status**: Complete
**Last Updated**: 2025-09-30
**Version**: 1.0