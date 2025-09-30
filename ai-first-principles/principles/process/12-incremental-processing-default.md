# Principle #12 - Incremental Processing as Default

## Plain-Language Definition

Incremental processing means breaking long-running operations into small, resumable steps with frequent checkpoints. Instead of processing everything at once and losing all progress if interrupted, save progress after each step so work can resume from where it left off.

## Why This Matters for AI-First Development

AI agents generate and process large amounts of data through operations that can take minutes or hours: code generation, documentation synthesis, test execution, data analysis, and model training. These long-running operations are vulnerable to interruptions—network failures, API rate limits, timeouts, resource constraints, or simple user cancellation.

Without incremental processing, interruptions are catastrophic. An AI agent synthesizing documentation from 100 files loses all progress if interrupted at file 99. A code generation task spanning 50 modules has to restart from scratch after a network hiccup. Test suites with thousands of tests can't be stopped and resumed. These all-or-nothing operations waste computational resources, frustrate users, and make AI-driven development feel fragile and unpredictable.

Incremental processing transforms long-running operations from fragile all-or-nothing tasks into robust, resumable workflows. AI agents can checkpoint their progress after each step, enabling graceful recovery from interruptions. Users can stop and resume operations without losing work. Operations can be monitored and debugged incrementally rather than waiting for complete failure. This resilience is essential when AI agents work autonomously—they need to survive the inevitable interruptions without human intervention to restart everything.

The principle also enables better feedback and control. With incremental processing, users see progress in real-time rather than waiting for completion. Partial results become available immediately. Problems are detected early when they affect a small batch rather than discovered after hours of wasted processing. AI agents can adapt their strategy mid-operation based on early results. This rapid feedback loop aligns perfectly with AI-first development's emphasis on iteration and learning.

## Implementation Approaches

### 1. **Checkpoint Files with Resume Logic**

Save progress to disk after processing each logical unit (file, record, batch). On restart, check for existing checkpoint and resume from the last completed step.

```python
def process_with_checkpoints(items: list[str], checkpoint_file: Path):
    completed = load_checkpoint(checkpoint_file) if checkpoint_file.exists() else set()

    for item in items:
        if item in completed:
            continue  # Skip already processed items

        result = process_item(item)
        completed.add(item)
        save_checkpoint(checkpoint_file, completed)  # Save after each item

    checkpoint_file.unlink()  # Clean up when done
```

**When to use:** File processing, data migration, batch operations, any task with discrete units.

**Success looks like:** Interrupting and restarting completes in seconds, not minutes. No duplicate work.

### 2. **Append-Only Progress Logs**

Write each completed step to an append-only log. On restart, replay the log to determine what's been done.

```python
def process_with_log(items: list[str], log_file: Path):
    completed = set(log_file.read_text().splitlines()) if log_file.exists() else set()

    with open(log_file, 'a') as log:
        for item in items:
            if item in completed:
                continue

            process_item(item)
            log.write(f"{item}\n")
            log.flush()  # Ensure written to disk immediately
```

**When to use:** Operations where you need an audit trail, debugging complex workflows, distributed processing.

**Success looks like:** Complete history of what happened, easy to debug failures, safe concurrent access.

### 3. **Database-Backed State Tracking**

Store progress in a database with status fields. Query for incomplete items on restart.

```python
def process_with_database(items: list[str]):
    # Initialize tracking records
    for item in items:
        db.tasks.upsert({"id": item, "status": "pending"})

    # Process only pending items
    for task in db.tasks.find({"status": "pending"}):
        result = process_item(task.id)
        db.tasks.update({"id": task.id}, {"status": "completed", "result": result})
```

**When to use:** Distributed systems, web applications, operations that need coordination across processes.

**Success looks like:** Multiple workers can process concurrently, status queryable from anywhere, atomic updates.

### 4. **Batch Processing with Partial Results**

Divide work into fixed-size batches. Save results after each batch completes.

```python
def process_in_batches(items: list[str], batch_size: int = 10, output_dir: Path):
    output_dir.mkdir(exist_ok=True)

    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]
        batch_file = output_dir / f"batch_{i//batch_size:04d}.json"

        if batch_file.exists():
            continue  # Skip completed batches

        results = [process_item(item) for item in batch]
        batch_file.write_text(json.dumps(results))
```

**When to use:** Memory-constrained operations, parallel processing, operations with natural batch boundaries.

**Success looks like:** Predictable memory usage, easy to parallelize, partial results available immediately.

### 5. **Progress Metrics with Continuation Tokens**

Return continuation tokens that encode where processing stopped. Pass token back to resume.

```python
def process_with_continuation(items: list[str], continuation_token: str | None = None) -> tuple[list, str | None]:
    start_index = int(continuation_token) if continuation_token else 0
    batch_size = 50

    results = []
    for i in range(start_index, min(start_index + batch_size, len(items))):
        results.append(process_item(items[i]))

    next_token = str(start_index + batch_size) if start_index + batch_size < len(items) else None
    return results, next_token
```

**When to use:** APIs, streaming operations, paginated results, operations that need to respect time limits.

**Success looks like:** Stateless resumption, works across API boundaries, easy to implement timeouts.

### 6. **Atomic Work Queues**

Push items to a work queue. Workers claim items atomically, process them, and mark complete.

```python
def process_with_queue(items: list[str]):
    # Populate queue
    for item in items:
        work_queue.push(item)

    # Workers claim and process
    while not work_queue.empty():
        item = work_queue.claim(timeout=30)  # Claim with timeout
        if item:
            process_item(item)
            work_queue.complete(item)
        # If worker dies, item automatically returns to queue after timeout
```

**When to use:** Distributed processing, fault-tolerant systems, operations needing load balancing.

**Success looks like:** Automatic recovery from worker failures, scalable to many workers, no duplicate work.

## Good Examples vs Bad Examples

### Example 1: Document Synthesis

**Good:**
```python
def synthesize_documents(files: list[Path], output_file: Path):
    """Incremental: checkpoints progress after each file"""
    checkpoint_file = output_file.with_suffix('.checkpoint.json')

    # Load previous progress
    if checkpoint_file.exists():
        checkpoint = json.loads(checkpoint_file.read_text())
        processed_files = set(checkpoint['processed'])
        results = checkpoint['results']
    else:
        processed_files = set()
        results = []

    # Process remaining files
    for file in files:
        if str(file) in processed_files:
            continue

        content = synthesize_file(file)
        results.append(content)
        processed_files.add(str(file))

        # Save checkpoint after each file
        checkpoint_file.write_text(json.dumps({
            'processed': list(processed_files),
            'results': results
        }))

    # Save final output and clean up checkpoint
    output_file.write_text(json.dumps(results))
    checkpoint_file.unlink()
```

**Bad:**
```python
def synthesize_documents(files: list[Path], output_file: Path):
    """NOT incremental: all-or-nothing processing"""
    results = []

    # Process all files - if interrupted, lose everything
    for file in files:
        content = synthesize_file(file)
        results.append(content)

    # Only save at the end
    output_file.write_text(json.dumps(results))
    # Interruption before this line loses all work
```

**Why It Matters:** AI document synthesis often processes dozens or hundreds of files. Without checkpoints, a network timeout after 99 of 100 files loses hours of LLM API calls and costs. With checkpoints, resuming takes seconds and wastes nothing.

### Example 2: Code Generation

**Good:**
```python
def generate_modules(specs: list[ModuleSpec], output_dir: Path):
    """Incremental: tracks completion per module"""
    status_file = output_dir / '.generation_status.json'

    # Load status
    if status_file.exists():
        status = json.loads(status_file.read_text())
    else:
        status = {spec.name: 'pending' for spec in specs}

    for spec in specs:
        if status[spec.name] == 'completed':
            continue

        # Generate code
        code = generate_module_code(spec)
        module_file = output_dir / f"{spec.name}.py"
        module_file.write_text(code)

        # Mark completed
        status[spec.name] = 'completed'
        status_file.write_text(json.dumps(status, indent=2))

    # Clean up status file when all done
    if all(s == 'completed' for s in status.values()):
        status_file.unlink()
```

**Bad:**
```python
def generate_modules(specs: list[ModuleSpec], output_dir: Path):
    """NOT incremental: regenerates everything on restart"""
    for spec in specs:
        code = generate_module_code(spec)
        module_file = output_dir / f"{spec.name}.py"
        module_file.write_text(code)
    # No tracking of what's complete
    # Restart regenerates already-completed modules
```

**Why It Matters:** Code generation via LLM is expensive and time-consuming. Regenerating already-completed modules wastes API quota and time. Status tracking ensures each module is generated exactly once, even across multiple runs.

### Example 3: Test Suite Execution

**Good:**
```python
def run_test_suite_incremental(test_files: list[Path], results_dir: Path):
    """Incremental: can stop and resume test execution"""
    results_dir.mkdir(exist_ok=True)

    for test_file in test_files:
        result_file = results_dir / f"{test_file.stem}.result.json"

        if result_file.exists():
            continue  # Skip already-run tests

        # Run test and save result immediately
        result = run_pytest(test_file)
        result_file.write_text(json.dumps({
            'test_file': str(test_file),
            'passed': result.passed,
            'failed': result.failed,
            'duration': result.duration
        }))

    # Aggregate results from individual files
    all_results = [json.loads(f.read_text()) for f in results_dir.glob('*.result.json')]
    return summarize_results(all_results)
```

**Bad:**
```python
def run_test_suite_all_or_nothing(test_files: list[Path]):
    """NOT incremental: must complete entire suite"""
    results = []

    # Run all tests without saving intermediate results
    for test_file in test_files:
        result = run_pytest(test_file)
        results.append(result)

    # Only report after all tests complete
    return summarize_results(results)
    # Can't stop partway through
    # Interruption loses all test results
```

**Why It Matters:** Large test suites can take hours. Developers need to stop testing to fix urgent issues. Without incremental execution, stopping loses all results. With incremental execution, you can review results so far and resume later.

### Example 4: Data Migration

**Good:**
```python
def migrate_records_incremental(source_db, target_db, batch_size: int = 100):
    """Incremental: tracks migration progress in database"""
    # Create migration tracking table
    target_db.execute("""
        CREATE TABLE IF NOT EXISTS migration_progress (
            last_migrated_id INTEGER,
            total_migrated INTEGER,
            updated_at TIMESTAMP
        )
    """)

    # Get last migrated ID
    row = target_db.query("SELECT last_migrated_id FROM migration_progress")
    last_id = row[0] if row else 0

    while True:
        # Get next batch
        records = source_db.query(
            f"SELECT * FROM records WHERE id > {last_id} ORDER BY id LIMIT {batch_size}"
        )

        if not records:
            break  # Migration complete

        # Migrate batch
        for record in records:
            target_db.insert("records", record)
            last_id = record['id']

        # Update progress
        target_db.execute(
            "UPDATE migration_progress SET last_migrated_id = ?, updated_at = ?",
            (last_id, datetime.now())
        )
        target_db.commit()  # Commit after each batch
```

**Bad:**
```python
def migrate_records_all_at_once(source_db, target_db):
    """NOT incremental: migrates everything in one transaction"""
    # Load all records into memory
    all_records = source_db.query("SELECT * FROM records")

    # Migrate all at once
    target_db.begin_transaction()
    for record in all_records:
        target_db.insert("records", record)
    target_db.commit()  # Single commit at end

    # Failure before commit loses all work
    # Can't track progress
    # Can't resume partway through
```

**Why It Matters:** Data migrations often involve millions of records. Loading everything into memory fails on large datasets. Without batch commits, a failure near the end rolls back hours of work. Incremental migration with progress tracking ensures forward progress even through interruptions.

### Example 5: Content Analysis Pipeline

**Good:**
```python
def analyze_content_incremental(content_files: list[Path], output_dir: Path):
    """Incremental: multi-stage pipeline with checkpoints"""
    output_dir.mkdir(exist_ok=True)

    for content_file in content_files:
        stages = ['extracted', 'analyzed', 'summarized']

        # Check which stages are complete
        checkpoint = output_dir / f"{content_file.stem}.checkpoint"
        completed_stages = set(checkpoint.read_text().splitlines() if checkpoint.exists() else [])

        # Stage 1: Extract
        if 'extracted' not in completed_stages:
            extracted = extract_content(content_file)
            (output_dir / f"{content_file.stem}.extracted.json").write_text(json.dumps(extracted))
            completed_stages.add('extracted')
            checkpoint.write_text('\n'.join(completed_stages))

        # Stage 2: Analyze
        if 'analyzed' not in completed_stages:
            extracted = json.loads((output_dir / f"{content_file.stem}.extracted.json").read_text())
            analyzed = analyze_with_llm(extracted)
            (output_dir / f"{content_file.stem}.analyzed.json").write_text(json.dumps(analyzed))
            completed_stages.add('analyzed')
            checkpoint.write_text('\n'.join(completed_stages))

        # Stage 3: Summarize
        if 'summarized' not in completed_stages:
            analyzed = json.loads((output_dir / f"{content_file.stem}.analyzed.json").read_text())
            summary = summarize(analyzed)
            (output_dir / f"{content_file.stem}.summary.json").write_text(json.dumps(summary))
            checkpoint.unlink()  # All stages complete
```

**Bad:**
```python
def analyze_content_all_stages(content_files: list[Path], output_dir: Path):
    """NOT incremental: must complete all stages for all files"""
    results = []

    # Process each file through all stages before moving to next file
    # Can't resume mid-pipeline
    for content_file in content_files:
        extracted = extract_content(content_file)
        analyzed = analyze_with_llm(extracted)
        summary = summarize(analyzed)
        results.append(summary)

    # No intermediate results saved
    # Failure in summarize stage loses extraction and analysis work
    output_dir.mkdir(exist_ok=True)
    (output_dir / 'results.json').write_text(json.dumps(results))
```

**Why It Matters:** Multi-stage pipelines with expensive operations (LLM calls, data processing) accumulate significant work. Without stage checkpoints, a failure in the final stage loses all previous work. Stage-level checkpoints ensure each expensive operation is performed exactly once.

## Related Principles

- **[Principle #31 - Idempotency by Design](../technology/31-idempotency-by-design.md)** - Incremental processing requires idempotent operations so resuming from checkpoints doesn't cause duplicate side effects or data corruption

- **[Principle #11 - Continuous Validation with Fast Feedback](11-continuous-validation-fast-feedback.md)** - Incremental processing enables continuous validation by providing partial results to validate immediately instead of waiting for complete execution

- **[Principle #24 - Observable Operations as Default](../technology/24-observable-operations-default.md)** - Checkpoints and progress tracking make operations observable, providing visibility into what's happening and how far along the process has progressed

- **[Principle #28 - Graceful Degradation Throughout](../technology/28-graceful-degradation-throughout.md)** - Incremental processing enables graceful degradation by allowing partial completion; some progress is better than no progress

- **[Principle #30 - Asynchronous Communication Default](../technology/30-asynchronous-communication-default.md)** - Long-running incremental operations naturally fit asynchronous patterns, communicating progress updates without blocking

- **[Principle #19 - Test in Small Batches](19-test-in-small-batches.md)** - Incremental processing enables testing smaller batches rather than waiting for complete execution, accelerating feedback and iteration

## Common Pitfalls

1. **Checkpointing Too Infrequently**: Saving progress only after large batches means interruptions still lose significant work.
   - Example: Processing 1000 files with checkpoints every 100 files. Interruption at file 199 loses 99 files of work.
   - Impact: Poor recovery, wasted computation, frustrating user experience.

2. **Non-Atomic Checkpoint Writes**: Writing checkpoints without ensuring atomicity can corrupt checkpoint files during interruption.
   - Example: `checkpoint_file.write_text(json.dumps(state))` can be interrupted mid-write, leaving invalid JSON.
   - Impact: Checkpoint corruption prevents resuming, forcing restart from beginning.

3. **Forgetting to Clean Up Checkpoints**: Leaving checkpoint files after completion clutters the filesystem and can confuse future runs.
   - Example: Checkpoint files accumulate, making it unclear which operations are in-progress vs completed.
   - Impact: Confusion, wasted disk space, potential for resuming already-completed operations.

4. **Not Handling Checkpoint Schema Evolution**: Changing the checkpoint format breaks resumption of older in-progress operations.
   - Example: Adding new fields to checkpoint JSON without version checking. Old checkpoints fail to parse.
   - Impact: Can't resume operations started before the schema change, forcing restarts.

5. **Checkpoint Data Too Large**: Storing full results in checkpoints instead of just tracking what's been processed causes performance issues.
   - Example: Checkpoint file contains all processed records instead of just IDs. Checkpoint grows to gigabytes.
   - Impact: Slow checkpoint writes, excessive disk usage, memory issues loading checkpoints.

6. **No Progress Visibility**: Implementing checkpoints but not showing progress to users leaves them wondering what's happening.
   - Example: Silent processing with checkpoints. User sees no activity and assumes system is hung.
   - Impact: User interrupts working process, poor user experience, loss of trust in system.

7. **Ignoring Failed Items**: Skipping failed items without tracking them loses visibility into problems and incomplete processing.
   - Example: File processing that catches exceptions and continues without logging failures. Completes successfully with some files silently skipped.
   - Impact: Silent partial failures, incomplete results, difficult debugging, false sense of completion.

## Tools & Frameworks

### Checkpoint Libraries
- **checkpoint-python**: Simple library for file-based checkpointing with atomic writes and automatic cleanup
- **shelve (Python stdlib)**: Persistent dictionary backed by database files, useful for checkpoint storage
- **SQLite**: Lightweight database perfect for checkpoint tracking with ACID guarantees

### Progress Tracking
- **tqdm**: Progress bars for Python with support for nested progress and dynamic updates
- **rich.progress**: Modern terminal progress bars with multiple progress bars and detailed statistics
- **progressbar2**: Highly customizable progress bars with extensive callback support

### Task Queues
- **Celery**: Distributed task queue with built-in retry logic and result backends
- **RQ (Redis Queue)**: Simple Python task queue with job tracking and failure handling
- **Dramatiq**: Fast distributed task processing with middleware for progress tracking

### Workflow Engines
- **Apache Airflow**: Workflow orchestration with built-in checkpoint capabilities and task retry logic
- **Prefect**: Modern workflow engine with automatic retries and state management
- **Temporal**: Durable execution framework with built-in checkpointing and recovery

### Data Processing
- **Dask**: Parallel computing library with automatic checkpointing for large datasets
- **Apache Spark**: Distributed data processing with RDD checkpointing for fault tolerance
- **Pandas**: `chunksize` parameter for incremental reading of large files

### Database Tools
- **SQLAlchemy**: ORM with session management for tracking processing state
- **PostgreSQL**: `RETURNING` clause for atomic operations with progress tracking
- **MongoDB**: Change streams and resumable queries for incremental processing

## Implementation Checklist

When implementing this principle, ensure:

- [ ] Operations are divided into logical units that can be processed independently
- [ ] Checkpoint files use atomic writes (write to temp file, then rename) to prevent corruption
- [ ] Checkpoint schema includes version information for future compatibility
- [ ] Resume logic checks for and loads existing checkpoints before starting work
- [ ] Progress is saved after each logical unit (file, record, batch) completes
- [ ] Failed items are tracked separately from skipped items with error details
- [ ] Checkpoint files are cleaned up after successful completion
- [ ] Progress visibility is provided to users (progress bars, logs, status endpoints)
- [ ] Partial results are available and usable even if operation is interrupted
- [ ] Resume logic is idempotent (resuming multiple times doesn't cause duplicate work)
- [ ] Large datasets use streaming/chunking instead of loading everything into memory
- [ ] Error handling preserves checkpoints so operations can resume after fixing issues

## Metadata

**Category**: Process
**Principle Number**: 12
**Related Patterns**: Checkpoint/Restart, Saga Pattern, Event Sourcing, Command Pattern, Memento Pattern, Circuit Breaker
**Prerequisites**: Understanding of file I/O, atomic operations, error handling, progress tracking
**Difficulty**: Medium
**Impact**: High

---

**Status**: Complete
**Last Updated**: 2025-09-30
**Version**: 1.0