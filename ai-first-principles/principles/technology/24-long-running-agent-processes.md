# Principle #24 - Long-Running Agent Processes

## Plain-Language Definition

Long-running agent processes are AI operations that execute over extended periods, surviving interruptions, resuming from checkpoints, and maintaining state across sessions. Design for persistence, graceful interruption, and reliable resumption.

## Why This Matters for AI-First Development

AI agents don't operate like traditional synchronous functions. They analyze codebases, coordinate multiple tools, make iterative decisions, and execute complex multi-step workflows that can take minutes, hours, or even days. These operations must survive network failures, system restarts, resource exhaustion, and deliberate interruptions.

Traditional software development assumes human oversight. A developer writes code, runs it, watches it execute, and handles failures manually. But AI-first development inverts this model. AI agents operate autonomously, often unattended. A code generation agent might process hundreds of files overnight. A testing agent might run comprehensive test suites across multiple environments. A deployment agent might orchestrate rolling updates across distributed systems. These workflows cannot assume uninterrupted execution—they must be designed from the ground up to handle disruption.

Long-running agent processes introduce three critical challenges:

1. **State persistence**: Agents must save their progress continuously. When interrupted mid-workflow, they should resume from the last checkpoint, not restart from the beginning. This requires explicit state management, progress tracking, and recovery mechanisms.

2. **Resource management**: Long-running processes consume memory, file handles, API quotas, and compute resources. Without proper management, agents can exhaust resources, causing cascading failures across the system.

3. **Observable progress**: Users need visibility into what agents are doing, how far they've progressed, and when they'll complete. Silent, opaque processes erode trust and make debugging impossible.

Without proper design for long-running operations, AI agents become unreliable. A network hiccup destroys hours of work. An out-of-memory error forces complete restarts. Users have no idea whether agents are stuck, progressing, or failing silently. These failures compound in AI-first systems where multiple agents coordinate across distributed components, each depending on others to complete reliably.

## Implementation Approaches

### 1. **Checkpoint-Based State Persistence**

Save progress at regular intervals using durable storage. Each checkpoint captures enough state to resume the operation exactly where it left off:

```python
class StatefulAgent:
    def __init__(self, checkpoint_file: Path):
        self.checkpoint_file = checkpoint_file
        self.state = self.load_checkpoint()

    def load_checkpoint(self) -> dict:
        if self.checkpoint_file.exists():
            return json.loads(self.checkpoint_file.read_text())
        return {"processed_items": [], "current_index": 0, "metadata": {}}

    def save_checkpoint(self):
        self.checkpoint_file.write_text(json.dumps(self.state, indent=2))

    def process(self, items: list):
        start_index = self.state["current_index"]
        for i in range(start_index, len(items)):
            self.process_item(items[i])
            self.state["processed_items"].append(items[i].id)
            self.state["current_index"] = i + 1
            self.save_checkpoint()  # Persist progress after each item
```

**When to use**: Operations that process multiple independent items (files, records, API calls) where partial completion has value.

**Success looks like**: Agent interrupted at any point can resume within seconds, skipping already-processed items without data loss or duplication.

### 2. **Background Process Management with Async**

Run long operations in background tasks using Python's asyncio, allowing concurrent execution and graceful cancellation:

```python
import asyncio
from typing import Optional

class BackgroundAgent:
    def __init__(self):
        self.task: Optional[asyncio.Task] = None
        self.should_stop = False

    async def run_in_background(self, operation):
        """Start operation as background task"""
        self.task = asyncio.create_task(self._execute(operation))
        return self.task

    async def _execute(self, operation):
        """Execute with periodic check for cancellation"""
        while not self.should_stop:
            chunk = await operation.get_next_chunk()
            if chunk is None:
                break
            await self.process_chunk(chunk)
            await asyncio.sleep(0)  # Yield control

    async def stop_gracefully(self):
        """Request graceful shutdown"""
        self.should_stop = True
        if self.task:
            await self.task  # Wait for current chunk to complete
```

**When to use**: Operations that need to run in parallel with other work, or when users need the ability to cancel operations gracefully.

**Success looks like**: Multiple agents run concurrently without blocking. Cancellation stops work cleanly without leaving partial state.

### 3. **Progress Tracking with Observable State**

Provide real-time visibility into agent progress through structured logging and status updates:

```python
from dataclasses import dataclass, asdict
from enum import Enum

class AgentStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class AgentProgress:
    status: AgentStatus
    total_items: int
    processed_items: int
    current_item: str
    errors: list[str]
    estimated_completion: float

    def to_json(self) -> dict:
        return asdict(self)

class ObservableAgent:
    def __init__(self, progress_file: Path):
        self.progress_file = progress_file
        self.progress = AgentProgress(
            status=AgentStatus.IDLE,
            total_items=0,
            processed_items=0,
            current_item="",
            errors=[],
            estimated_completion=0.0
        )

    def update_progress(self):
        """Write current progress to observable file"""
        self.progress_file.write_text(json.dumps(self.progress.to_json(), indent=2))
        logger.info(f"Progress: {self.progress.processed_items}/{self.progress.total_items}")
```

**When to use**: Any long-running operation where users need visibility into progress, especially operations that take minutes or longer.

**Success looks like**: Users can check progress at any time without interrupting the agent. Progress updates are human-readable and actionable.

### 4. **Health Monitoring and Automatic Recovery**

Monitor agent health and implement automatic recovery from transient failures:

```python
import time
from contextlib import contextmanager

class HealthMonitoredAgent:
    def __init__(self, max_retries: int = 3, health_check_interval: int = 30):
        self.max_retries = max_retries
        self.health_check_interval = health_check_interval
        self.last_heartbeat = time.time()
        self.failure_count = 0

    def heartbeat(self):
        """Update heartbeat timestamp"""
        self.last_heartbeat = time.time()
        self.failure_count = 0  # Reset on successful operation

    def is_healthy(self) -> bool:
        """Check if agent is responding"""
        return time.time() - self.last_heartbeat < self.health_check_interval

    @contextmanager
    def retry_on_failure(self):
        """Retry operation on transient failures"""
        for attempt in range(self.max_retries):
            try:
                yield
                self.heartbeat()
                break
            except TransientError as e:
                self.failure_count += 1
                if attempt == self.max_retries - 1:
                    raise
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying...")
                time.sleep(2 ** attempt)  # Exponential backoff
```

**When to use**: Operations that interact with unreliable external systems (APIs, databases, file systems) where transient failures are expected.

**Success looks like**: Transient failures (network blips, API rate limits) don't crash the agent. Recovery happens automatically without human intervention.

### 5. **Incremental Processing with Streaming**

Process data incrementally using streaming patterns to avoid loading entire datasets into memory:

```python
from typing import Iterator, TypeVar

T = TypeVar('T')

class StreamingAgent:
    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size

    def stream_items(self, source) -> Iterator[list[T]]:
        """Yield batches of items instead of loading all at once"""
        batch = []
        for item in source:
            batch.append(item)
            if len(batch) >= self.batch_size:
                yield batch
                batch = []
        if batch:  # Don't forget final partial batch
            yield batch

    async def process_stream(self, source):
        """Process batches incrementally"""
        for batch in self.stream_items(source):
            await self.process_batch(batch)
            await self.checkpoint()  # Save progress after each batch
            # Memory used only for current batch, not entire dataset
```

**When to use**: Processing large datasets (thousands of files, millions of records) where loading everything into memory is impractical or impossible.

**Success looks like**: Memory usage remains constant regardless of dataset size. Processing completes successfully even for datasets larger than available RAM.

### 6. **Graceful Shutdown with Signal Handling**

Handle system signals (SIGTERM, SIGINT) to shut down cleanly, saving state before exit:

```python
import signal
import sys

class GracefulAgent:
    def __init__(self):
        self.should_exit = False
        signal.signal(signal.SIGTERM, self.handle_signal)
        signal.signal(signal.SIGINT, self.handle_signal)

    def handle_signal(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}. Shutting down gracefully...")
        self.should_exit = True

    def run(self):
        """Main processing loop with shutdown check"""
        while not self.should_exit:
            try:
                self.process_next_item()
                self.save_checkpoint()
            except Exception as e:
                logger.error(f"Error processing item: {e}")
                self.save_checkpoint()  # Save state even on error
                if self.should_exit:
                    break
        logger.info("Agent shutdown complete")
        sys.exit(0)
```

**When to use**: Any long-running process that might be terminated by system signals (container orchestration, systemd, user interruption).

**Success looks like**: Agent receives termination signal, finishes current operation, saves all state, and exits cleanly without data loss.

## Good Examples vs Bad Examples

### Example 1: File Processing with Checkpoints

**Good:**
```python
class CheckpointedFileProcessor:
    def __init__(self, checkpoint_file: Path):
        self.checkpoint_file = checkpoint_file
        self.processed_files = self.load_checkpoint()

    def load_checkpoint(self) -> set[str]:
        if self.checkpoint_file.exists():
            return set(json.loads(self.checkpoint_file.read_text()))
        return set()

    def save_checkpoint(self):
        self.checkpoint_file.write_text(json.dumps(list(self.processed_files)))

    def process_directory(self, directory: Path):
        all_files = list(directory.glob("**/*.py"))
        logger.info(f"Found {len(all_files)} files, {len(self.processed_files)} already processed")

        for file_path in all_files:
            file_key = str(file_path.relative_to(directory))

            if file_key in self.processed_files:
                logger.debug(f"Skipping already processed: {file_key}")
                continue

            try:
                self.process_file(file_path)
                self.processed_files.add(file_key)
                self.save_checkpoint()  # Save after each file
                logger.info(f"Processed {len(self.processed_files)}/{len(all_files)}")
            except Exception as e:
                logger.error(f"Failed to process {file_key}: {e}")
                # Save checkpoint even on failure
                self.save_checkpoint()
                raise
```

**Bad:**
```python
class NonCheckpointedFileProcessor:
    def process_directory(self, directory: Path):
        all_files = list(directory.glob("**/*.py"))
        processed = []  # Only in memory

        for file_path in all_files:
            try:
                self.process_file(file_path)
                processed.append(str(file_path))
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                raise  # Loses all progress

        # Save only at the end
        self.save_results(processed)
```

**Why It Matters:** Processing hundreds or thousands of files can take hours. Without checkpoints, any interruption (crash, network failure, user cancellation) loses all progress. With checkpoints, resuming skips already-processed files and completes in minutes instead of restarting from scratch.

### Example 2: Background Task with Cancellation

**Good:**
```python
class CancellableAgent:
    def __init__(self):
        self.cancel_requested = False
        self.current_task = None

    async def start(self, items: list):
        """Start long-running operation as async task"""
        self.current_task = asyncio.create_task(self._process_all(items))
        return self.current_task

    async def _process_all(self, items: list):
        for i, item in enumerate(items):
            if self.cancel_requested:
                logger.info(f"Cancellation requested at item {i}/{len(items)}")
                await self.save_checkpoint(i)
                return

            await self.process_item(item)
            await asyncio.sleep(0)  # Yield control periodically

    async def cancel(self):
        """Request graceful cancellation"""
        logger.info("Requesting cancellation...")
        self.cancel_requested = True
        if self.current_task:
            await self.current_task  # Wait for graceful shutdown
        logger.info("Cancellation complete")

# Usage
agent = CancellableAgent()
task = await agent.start(large_dataset)
# User can cancel at any time
await agent.cancel()
```

**Bad:**
```python
class NonCancellableAgent:
    def process_all(self, items: list):
        """Blocking synchronous processing"""
        for item in items:
            self.process_item(item)  # No way to cancel
            # No yield, no async, blocks forever
        self.save_results()

# Usage
agent = NonCancellableAgent()
agent.process_all(large_dataset)  # Blocks until complete, no cancellation possible
```

**Why It Matters:** Users need the ability to stop long-running operations without killing the entire process. Synchronous blocking code offers no cancellation mechanism—users must kill the process, losing all state and potentially corrupting data. Async with cancellation checks allows graceful shutdown.

### Example 3: Progress Visibility

**Good:**
```python
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class ProgressUpdate:
    total_items: int
    processed_items: int
    current_item: str
    start_time: datetime
    errors: list[str]

    @property
    def percent_complete(self) -> float:
        return (self.processed_items / self.total_items * 100) if self.total_items > 0 else 0

    @property
    def estimated_completion(self) -> datetime:
        if self.processed_items == 0:
            return datetime.max
        elapsed = datetime.now() - self.start_time
        rate = self.processed_items / elapsed.total_seconds()
        remaining = self.total_items - self.processed_items
        return datetime.now() + timedelta(seconds=remaining / rate)

class ProgressTrackingAgent:
    def __init__(self, progress_file: Path):
        self.progress_file = progress_file
        self.progress = ProgressUpdate(
            total_items=0,
            processed_items=0,
            current_item="",
            start_time=datetime.now(),
            errors=[]
        )

    def update_progress(self):
        """Write progress to observable file"""
        progress_dict = {
            "total_items": self.progress.total_items,
            "processed_items": self.progress.processed_items,
            "current_item": self.progress.current_item,
            "percent_complete": f"{self.progress.percent_complete:.1f}%",
            "estimated_completion": self.progress.estimated_completion.isoformat(),
            "errors": self.progress.errors
        }
        self.progress_file.write_text(json.dumps(progress_dict, indent=2))
        logger.info(f"Progress: {self.progress.processed_items}/{self.progress.total_items} "
                   f"({self.progress.percent_complete:.1f}%)")

    def process_items(self, items: list):
        self.progress.total_items = len(items)
        for i, item in enumerate(items):
            self.progress.current_item = item.name
            self.progress.processed_items = i
            self.update_progress()  # Update after each item

            try:
                self.process_item(item)
            except Exception as e:
                self.progress.errors.append(f"{item.name}: {str(e)}")
                self.update_progress()
```

**Bad:**
```python
class SilentAgent:
    def process_items(self, items: list):
        # No progress tracking
        for item in items:
            self.process_item(item)  # Silent processing
        # No visibility into progress
        # No error reporting
        # No time estimates
```

**Why It Matters:** Users lose trust in agents that operate silently. Without progress updates, users don't know if the agent is working, stuck, or failing. They can't estimate completion time or identify problems early. Progress visibility transforms opaque operations into observable, trustworthy systems.

### Example 4: Health Monitoring and Recovery

**Good:**
```python
import time
from typing import Optional

class HealthMonitoredAgent:
    def __init__(self, health_file: Path, max_silence: int = 60):
        self.health_file = health_file
        self.max_silence = max_silence
        self.last_heartbeat = time.time()

    def heartbeat(self):
        """Update health status"""
        self.last_heartbeat = time.time()
        health_status = {
            "status": "healthy",
            "last_heartbeat": datetime.fromtimestamp(self.last_heartbeat).isoformat(),
            "uptime_seconds": time.time() - self.start_time
        }
        self.health_file.write_text(json.dumps(health_status, indent=2))

    def check_health(self) -> bool:
        """Check if agent is still alive"""
        if not self.health_file.exists():
            return False

        health = json.loads(self.health_file.read_text())
        last_heartbeat = datetime.fromisoformat(health["last_heartbeat"])
        silence_duration = (datetime.now() - last_heartbeat).total_seconds()

        return silence_duration < self.max_silence

    def process_with_monitoring(self, items: list):
        self.start_time = time.time()

        for item in items:
            self.process_item(item)
            self.heartbeat()  # Update health after each item

            # Self-check for deadlock
            if not self.check_health():
                logger.error("Health check failed - possible deadlock")
                raise HealthCheckFailure("Agent appears to be stuck")

# External monitor
def monitor_agent(agent: HealthMonitoredAgent):
    """External process can monitor agent health"""
    while True:
        if not agent.check_health():
            logger.error("Agent is unhealthy - restarting")
            restart_agent(agent)
        time.sleep(30)
```

**Bad:**
```python
class UnmonitoredAgent:
    def process_items(self, items: list):
        for item in items:
            self.process_item(item)  # No health updates
            # If this hangs, no way to detect it
            # No external monitoring possible
            # No automatic recovery
```

**Why It Matters:** Long-running processes can hang, deadlock, or enter infinite loops. Without health monitoring, these failures go undetected for hours or days. With health checks, external monitors can detect problems and trigger automatic recovery, improving reliability dramatically.

### Example 5: Incremental Processing with Memory Management

**Good:**
```python
from typing import Iterator
import gc

class MemoryEfficientAgent:
    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size

    def stream_batches(self, source_file: Path) -> Iterator[list[dict]]:
        """Stream file in batches to avoid loading entire file"""
        batch = []
        with open(source_file, 'r') as f:
            for line in f:
                record = json.loads(line)
                batch.append(record)

                if len(batch) >= self.batch_size:
                    yield batch
                    batch = []  # Clear batch after yielding
                    gc.collect()  # Encourage garbage collection

        if batch:
            yield batch

    def process_large_file(self, source_file: Path):
        """Process file incrementally without loading into memory"""
        total_processed = 0

        for batch in self.stream_batches(source_file):
            self.process_batch(batch)
            total_processed += len(batch)
            logger.info(f"Processed {total_processed} records")
            self.save_checkpoint(total_processed)
            # Memory usage stays constant
```

**Bad:**
```python
class MemoryHogAgent:
    def process_large_file(self, source_file: Path):
        """Load entire file into memory"""
        with open(source_file, 'r') as f:
            all_records = [json.loads(line) for line in f]
        # If file is 10GB, this loads 10GB into memory

        for record in all_records:
            self.process_record(record)
        # Memory consumed until processing completes
```

**Why It Matters:** Large datasets exceed available memory. Loading gigabytes of data crashes the process or thrashes swap space, degrading performance catastrophically. Streaming processes data incrementally, maintaining constant memory usage regardless of dataset size, enabling reliable processing of arbitrarily large datasets.

## Related Principles

- **[Principle #12 - Incremental by Default](../process/12-incremental-by-default.md)** - Long-running processes must be incremental to save progress and resume after interruption

- **[Principle #26 - Stateless by Default](26-stateless-by-default.md)** - While processes are long-running, components should still be stateless; state lives in durable storage, not process memory

- **[Principle #30 - Infrastructure as Throwaway Code](30-infrastructure-as-throwaway-code.md)** - Long-running agents must survive infrastructure changes; containerization and orchestration enable this

- **[Principle #32 - Error Recovery Patterns Built In](32-error-recovery-patterns.md)** - Long-running processes need robust error recovery because they'll encounter more failure modes over time

- **[Principle #27 - Disposable Components Everywhere](27-disposable-components.md)** - Long-running agents should be disposable despite their duration; they can be stopped and restarted without data loss

- **[Principle #28 - Observable Internals Required](28-observable-internals.md)** - Long-running processes must expose progress, health, and internal state for monitoring and debugging

## Common Pitfalls

1. **No Checkpoint Strategy**: Running long operations without saving progress means any interruption loses hours or days of work.
   - Example: Processing 10,000 files without checkpoints. Crash at file 9,999 means starting over.
   - Impact: Wasted compute resources, delayed results, frustrated users, inability to complete large workloads.

2. **Checkpoints Too Infrequent**: Saving state only occasionally still loses significant progress on failure.
   - Example: Checkpointing every 1,000 items when processing takes 10 hours. Failure loses up to 1 hour of work.
   - Impact: Reduced reliability benefit, unnecessary rework, poor user experience during recovery.

3. **Blocking Synchronous Operations**: Using synchronous blocking calls prevents cancellation and parallel execution.
   - Example: `time.sleep(300)` blocks thread for 5 minutes with no way to cancel.
   - Impact: No graceful shutdown, no parallel operations, poor resource utilization.

4. **Silent Progress**: Long-running operations without progress updates leave users guessing about status.
   - Example: Processing files for 6 hours with no output. User doesn't know if it's working or stuck.
   - Impact: Lost trust, premature cancellation, inability to estimate completion, difficult debugging.

5. **No Health Monitoring**: Agents can hang or deadlock with no way to detect the problem.
   - Example: Agent waits indefinitely for external API that's down. No timeout, no health check.
   - Impact: Zombie processes consuming resources, undetected failures, no automatic recovery.

6. **Loading Entire Datasets into Memory**: Processing large files by loading them completely causes out-of-memory errors.
   - Example: Loading 50GB CSV file into pandas DataFrame on machine with 16GB RAM.
   - Impact: Crashes, swap thrashing, inability to process large datasets, poor performance.

7. **Ignoring Shutdown Signals**: Not handling SIGTERM/SIGINT means forced termination loses state.
   - Example: Container orchestrator sends SIGTERM. Process ignores it and gets SIGKILL after timeout.
   - Impact: Data loss, corrupted state, unclean shutdown, difficult deployments.

## Tools & Frameworks

### Async and Background Processing
- **asyncio**: Python's built-in async framework for concurrent operations with cancellation support
- **Celery**: Distributed task queue for running background jobs with retries and monitoring
- **APScheduler**: Schedule recurring jobs with persistence and error recovery
- **Dramatiq**: Fast distributed task processing with checkpointing support

### State Persistence
- **SQLite**: Lightweight database perfect for agent checkpoints and progress tracking
- **Redis**: In-memory store with persistence for fast checkpoint operations
- **Shelve**: Python's built-in persistent dictionary for simple state management
- **LMDB**: Lightning memory-mapped database for high-performance state storage

### Progress and Monitoring
- **tqdm**: Progress bars for command-line visibility
- **Rich**: Beautiful terminal output with live progress updates
- **Prometheus**: Metrics collection and monitoring for agent health
- **Grafana**: Dashboards for visualizing agent progress and performance

### Process Management
- **Supervisor**: Process control system for managing long-running services
- **systemd**: Linux service manager with automatic restart and health checks
- **Docker**: Containerization with health checks and graceful shutdown support
- **Kubernetes**: Container orchestration with health probes and rolling updates

### Error Recovery
- **Tenacity**: Retry library with exponential backoff and error classification
- **Circuit Breaker (pybreaker)**: Prevent cascading failures in distributed agents
- **Sentry**: Error tracking and monitoring for production agents
- **Rollbar**: Real-time error monitoring with debugging context

## Implementation Checklist

When implementing this principle, ensure:

- [ ] Operations save checkpoints at regular intervals (not just at the end)
- [ ] Checkpoint files include enough state to resume exactly where interrupted
- [ ] Long operations use async/await to enable cancellation and parallel execution
- [ ] Progress updates written to observable files or logs every few seconds
- [ ] Health status exposed through heartbeat files or HTTP endpoints
- [ ] Signal handlers (SIGTERM, SIGINT) implemented for graceful shutdown
- [ ] Memory usage stays bounded through streaming or batching
- [ ] Errors logged with context before saving checkpoint
- [ ] Resume logic tested by artificially interrupting operations
- [ ] Progress includes estimated completion time
- [ ] External monitoring can detect hung or deadlocked agents
- [ ] Operations are idempotent when resumed from checkpoints

## Metadata

**Category**: Technology
**Principle Number**: 24
**Related Patterns**: Saga Pattern, Event Sourcing, Checkpoint/Restart, Circuit Breaker, Bulkhead Pattern
**Prerequisites**: Understanding of async programming, file I/O, signal handling, state management
**Difficulty**: High
**Impact**: High

---

**Status**: Complete
**Last Updated**: 2025-09-30
**Version**: 1.0