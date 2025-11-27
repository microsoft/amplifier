# Amplifier Benchmarks

## Running Terminal-Bench

Run the terminal-bench benchmark suite with amplifier or baseline agent:

```bash
uv run --with terminal-bench tests/terminal_bench/run_terminal_bench.py --agent baseline
```

## Analyzing Benchmark Results

Generate failure analysis reports for a terminal-bench run:

```bash
uv run tests/terminal_bench/generate_benchmark_report.py --run-dir "ai_working/tmp/2025-10-14__09-39-16"
```


## Common Issues

### Docker Compose Network Pool Exhaustion

**Error Message:**
```
Command '['docker', 'compose', '-p', 'task-name', '-f', '/path/to/docker-compose.yaml', 'up', '-d']' returned non-zero exit status 1.
```

**Root Cause:**
This error can occur when Docker runs out of available network address pools. Terminal-bench creates a new Docker network for each task run, and if these aren't cleaned up properly, Docker eventually exhausts its predefined address pools with the error:
```
failed to create network: Error response from daemon: all predefined address pools have been fully subnetted
```

**Solution:**
Clean up unused Docker networks:
```bash
# Remove all unused networks
docker network prune -f

# Check how many networks exist (should be < 30)
docker network ls | wc -l
```
