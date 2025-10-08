# Super-Planner Performance Benchmarks

Performance requirements and benchmarks for the super-planner system, ensuring it scales appropriately for real-world usage.

## Performance Requirements

### Core Performance Targets

| Operation | Target Time | Scalability | Memory Limit |
|-----------|-------------|-------------|--------------|
| Project Load (1000 tasks) | < 30s | Linear O(n) | < 1GB |
| Task Assignment Batch | < 5s | Constant O(1) | < 100MB |
| State Transition | < 100ms | Constant O(1) | < 10MB |
| Dependency Analysis | < 10s | O(n log n) | < 500MB |
| Git Operations | < 5s | Linear O(changes) | < 50MB |
| Agent Spawning | < 30s | Linear O(agents) | < 200MB |

### Concurrent Performance

| Scenario | Target | Limit |
|----------|--------|-------|
| Concurrent Agents | 20 agents | No deadlocks |
| Concurrent File Ops | 100 ops/sec | < 1% failures |
| State Modifications | 50/sec | Zero corruption |
| Git Commits | 10/min | No conflicts |

### Throughput Requirements

- **Planning Mode**: Break down 500 tasks in < 5 minutes
- **Working Mode**: Process 1000 state changes in < 2 minutes
- **Multi-Agent**: Coordinate 10 agents on 200 tasks in < 30 minutes
- **File I/O**: Handle 1000 file operations in < 1 minute

## Benchmark Test Scenarios

### BENCH-001: Large Project Loading

**Scenario**: Load projects of increasing size to measure scalability

**Test Configuration**:
```python
project_sizes = [10, 50, 100, 500, 1000, 2000]
max_depth = 5
dependency_density = 0.3  # 30% of tasks have dependencies
```

**Measurement Points**:
- Initial project file parsing time
- Task dependency graph construction
- Memory usage at peak
- Time to first agent assignment

**Success Criteria**:
- Linear scaling with task count
- Memory usage < 1MB per task
- No performance degradation for repeated loads
- Consistent performance regardless of dependency complexity

**Benchmark Implementation**:
```python
@pytest.mark.performance
@pytest.mark.parametrize("task_count", [10, 50, 100, 500, 1000, 2000])
async def test_project_loading_performance(task_count, performance_tracker):
    """Benchmark project loading performance across different sizes"""

    # Generate test project
    project = generate_complex_project(
        task_count=task_count,
        max_depth=5,
        dependency_density=0.3
    )

    # Measure loading performance
    performance_tracker.start_timer("project_load")

    planner = SuperPlanner()
    await planner.load_project(project)

    performance_tracker.end_timer("project_load")

    # Assert performance requirements
    max_time = task_count * 0.03  # 30ms per task max
    performance_tracker.assert_performance("project_load", max_time)

    # Memory usage check
    memory_usage = get_memory_usage()
    max_memory = task_count * 1024 * 1024  # 1MB per task
    assert memory_usage < max_memory
```

### BENCH-002: Concurrent Agent Coordination

**Scenario**: Test coordination performance with increasing agent counts

**Test Configuration**:
```python
agent_counts = [2, 5, 10, 15, 20]
tasks_per_agent = 10
coordination_complexity = "high"  # Complex task dependencies
```

**Measurement Points**:
- Agent registration time
- Task assignment latency
- Conflict resolution time
- Overall coordination overhead

**Success Criteria**:
- Support 20 concurrent agents without deadlock
- Agent assignment time < 2s regardless of agent count
- No performance degradation under load
- Fair task distribution maintained

**Benchmark Implementation**:
```python
@pytest.mark.performance
@pytest.mark.parametrize("agent_count", [2, 5, 10, 15, 20])
async def test_concurrent_agent_coordination(agent_count, performance_tracker):
    """Benchmark multi-agent coordination performance"""

    # Setup project with tasks for all agents
    project = generate_multi_agent_project(
        agent_count=agent_count,
        tasks_per_agent=10
    )

    # Create agents
    agents = create_test_agents(agent_count)

    # Measure coordination performance
    performance_tracker.start_timer("agent_coordination")

    coordinator = AgentCoordinator()
    await coordinator.register_agents(agents)
    assignments = await coordinator.assign_all_tasks(project.tasks)

    performance_tracker.end_timer("agent_coordination")

    # Assert performance requirements
    performance_tracker.assert_performance("agent_coordination", 30.0)

    # Verify load balancing
    assert_load_balanced(assignments, tolerance=0.15)
```

### BENCH-003: High-Frequency State Transitions

**Scenario**: Stress test state transition performance

**Test Configuration**:
```python
transition_rates = [10, 50, 100, 200, 500]  # transitions per second
duration = 60  # seconds
concurrent_agents = 8
```

**Measurement Points**:
- Individual state transition time
- Throughput under load
- Error rate during high-frequency updates
- File system contention effects

**Success Criteria**:
- Handle 200 transitions/sec with < 1% errors
- Individual transitions < 100ms
- No data corruption under any load
- Graceful degradation when limits exceeded

### BENCH-004: Git Operations Under Load

**Scenario**: Test git integration performance with frequent commits

**Test Configuration**:
```python
commit_frequencies = [1, 5, 10, 20]  # commits per minute
concurrent_operations = [1, 4, 8, 12]  # simultaneous git ops
project_sizes = [100, 500, 1000]  # tasks generating commits
```

**Measurement Points**:
- Individual commit latency
- Git conflict resolution time
- Repository growth rate
- Branch switching performance

**Success Criteria**:
- Commits complete < 5s each
- No git corruption under concurrent access
- Conflict resolution < 10s
- Repository size grows linearly with changes

### BENCH-005: Memory Usage and Garbage Collection

**Scenario**: Long-running memory usage and leak detection

**Test Configuration**:
```python
duration = 30  # minutes
operation_frequency = 5  # operations per second
project_size = 1000  # tasks
agent_count = 10
```

**Measurement Points**:
- Baseline memory usage
- Peak memory during operations
- Memory growth over time
- Garbage collection frequency

**Success Criteria**:
- No memory leaks (stable after GC)
- Peak memory < 2x baseline
- GC pauses < 100ms
- Stable performance over long runs

## Performance Test Implementation

### Test Infrastructure

```python
class PerformanceBenchmark:
    """Base class for performance benchmark tests"""

    def __init__(self):
        self.metrics = PerformanceMetrics()
        self.resource_monitor = ResourceMonitor()
        self.test_config = BenchmarkConfig()

    async def setup_benchmark(self, scenario: str):
        """Setup benchmark environment"""
        self.resource_monitor.start()
        self.metrics.reset()

        # Configure test environment for performance
        os.environ["PLANNER_PERFORMANCE_MODE"] = "true"
        os.environ["PLANNER_LOG_LEVEL"] = "WARNING"  # Reduce logging overhead

    async def teardown_benchmark(self):
        """Cleanup and collect final metrics"""
        self.resource_monitor.stop()

        # Generate performance report
        report = self.metrics.generate_report()
        self.save_benchmark_results(report)

    def assert_performance_requirements(self, operation: str, max_time: float):
        """Assert operation meets performance requirements"""
        actual_time = self.metrics.get_average_time(operation)
        assert actual_time <= max_time, (
            f"Performance requirement failed: {operation} "
            f"took {actual_time:.2f}s, max allowed {max_time}s"
        )

    def assert_memory_requirements(self, max_memory_mb: int):
        """Assert memory usage within limits"""
        peak_memory = self.resource_monitor.get_peak_memory()
        assert peak_memory <= max_memory_mb * 1024 * 1024, (
            f"Memory requirement failed: used {peak_memory / 1024 / 1024:.1f}MB, "
            f"max allowed {max_memory_mb}MB"
        )
```

### Benchmark Data Generation

```python
class BenchmarkDataGenerator:
    """Generate realistic test data for performance benchmarks"""

    @staticmethod
    def generate_large_project(task_count: int, complexity: str) -> TestProject:
        """Generate project data for performance testing"""

        if complexity == "simple":
            # Linear dependency chain, minimal metadata
            return generate_linear_project(task_count)

        elif complexity == "complex":
            # Realistic microservices with cross-dependencies
            return generate_microservices_project(
                service_count=task_count // 50,
                avg_tasks_per_service=50,
                cross_dependencies=0.2
            )

        elif complexity == "extreme":
            # Maximum complexity scenario
            return generate_extreme_project(
                task_count=task_count,
                max_depth=8,
                dependency_density=0.4,
                metadata_richness="high"
            )

    @staticmethod
    def generate_high_frequency_operations(rate: int, duration: int) -> list[Operation]:
        """Generate operations for high-frequency testing"""
        operations = []

        operation_types = [
            "state_transition",
            "task_assignment",
            "agent_status_update",
            "dependency_modification"
        ]

        for i in range(rate * duration):
            op = Operation(
                type=random.choice(operation_types),
                timestamp=i / rate,
                data=generate_operation_data()
            )
            operations.append(op)

        return operations
```

### Performance Monitoring

```python
class ResourceMonitor:
    """Monitor system resources during benchmarks"""

    def __init__(self):
        self.start_time = None
        self.memory_samples = []
        self.cpu_samples = []
        self.io_samples = []

    def start(self):
        """Start resource monitoring"""
        self.start_time = time.time()
        self.monitoring_task = asyncio.create_task(self._monitor_loop())

    async def _monitor_loop(self):
        """Continuous monitoring loop"""
        while True:
            # Sample memory usage
            memory_info = psutil.Process().memory_info()
            self.memory_samples.append({
                'timestamp': time.time() - self.start_time,
                'rss': memory_info.rss,
                'vms': memory_info.vms
            })

            # Sample CPU usage
            cpu_percent = psutil.Process().cpu_percent()
            self.cpu_samples.append({
                'timestamp': time.time() - self.start_time,
                'cpu_percent': cpu_percent
            })

            await asyncio.sleep(0.1)  # Sample every 100ms

    def get_peak_memory(self) -> int:
        """Get peak RSS memory usage in bytes"""
        if not self.memory_samples:
            return 0
        return max(sample['rss'] for sample in self.memory_samples)

    def get_average_cpu(self) -> float:
        """Get average CPU usage percentage"""
        if not self.cpu_samples:
            return 0.0
        return sum(sample['cpu_percent'] for sample in self.cpu_samples) / len(self.cpu_samples)
```

## Continuous Performance Testing

### CI Integration

```yaml
# .github/workflows/performance.yml
name: Performance Tests

on:
  pull_request:
    paths:
    - 'amplifier/planner/**'
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  performance:
    runs-on: ubuntu-latest-8-cores  # Consistent hardware

    steps:
    - uses: actions/checkout@v3

    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -e .[dev]
        pip install pytest-benchmark

    - name: Run performance benchmarks
      run: |
        pytest tests/planner/performance/ \
          --benchmark-json=benchmark_results.json \
          --benchmark-only

    - name: Compare with baseline
      run: |
        python tools/compare_benchmarks.py \
          --current benchmark_results.json \
          --baseline performance_baseline.json \
          --threshold 0.1  # 10% regression threshold

    - name: Upload results
      uses: actions/upload-artifact@v3
      with:
        name: performance-results
        path: benchmark_results.json
```

### Performance Regression Detection

```python
def detect_performance_regressions(current_results: dict, baseline_results: dict,
                                 threshold: float = 0.1) -> list[str]:
    """Detect performance regressions compared to baseline"""
    regressions = []

    for benchmark_name, current_metrics in current_results.items():
        if benchmark_name not in baseline_results:
            continue

        baseline_metrics = baseline_results[benchmark_name]

        # Check if performance regressed beyond threshold
        current_time = current_metrics['mean']
        baseline_time = baseline_metrics['mean']

        regression_ratio = (current_time - baseline_time) / baseline_time

        if regression_ratio > threshold:
            regressions.append(
                f"{benchmark_name}: {regression_ratio:.1%} slower "
                f"({current_time:.3f}s vs {baseline_time:.3f}s baseline)"
            )

    return regressions
```

## Performance Optimization Targets

### Phase 1: Foundation Performance
- ✅ Basic operations meet target times
- ✅ Memory usage within reasonable bounds
- ✅ No obvious performance bottlenecks

### Phase 2: Scale Performance
- ✅ Linear scaling to 1000+ tasks
- ✅ Support for 10+ concurrent agents
- ✅ Stable performance under sustained load

### Phase 3: Production Performance
- ✅ Enterprise-scale projects (5000+ tasks)
- ✅ High-availability coordination (20+ agents)
- ✅ Sub-second response times for interactive operations

These performance benchmarks ensure the super-planner system will perform well in real-world scenarios while maintaining reliability and user experience quality.