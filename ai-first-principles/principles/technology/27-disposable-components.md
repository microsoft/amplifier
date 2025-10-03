# Principle #27 - Disposable Components Everywhere

## Plain-Language Definition

Disposable components can be created, destroyed, and replaced at will without loss of data or functionality. They're designed to be thrown away and recreated rather than carefully maintained and updated over time.

## Why This Matters for AI-First Development

When AI agents build and modify systems, they need the freedom to experiment without fear of breaking things permanently. Disposable components enable rapid iteration because an agent can spin up a new version, test it, and throw it away if it doesn't work—all without manual recovery procedures or data loss.

Disposable components provide three critical benefits for AI-driven development:

1. **Fearless experimentation**: AI agents can try multiple approaches in parallel, spinning up containers or services to test different implementations. If an experiment fails, simply destroy the component and try again. No complex rollback procedures, no lingering state to clean up.

2. **Simplified recovery**: When something goes wrong, the solution is straightforward: destroy the broken component and create a fresh one. AI agents don't need to diagnose complex state corruption or apply careful surgical fixes—they can regenerate from known-good configurations.

3. **Rapid iteration cycles**: Disposable components dramatically reduce the cost of change. An AI agent can modify a component specification, regenerate it completely, deploy the new version, and roll back instantly if needed. This enables the kind of rapid experimentation that AI-first development requires.

Without disposability, AI systems become fragile and slow. Agents spend more time managing state, performing careful updates, and recovering from failures than they do building new functionality. Components accumulate technical debt as patches layer upon patches. The system becomes increasingly difficult to modify because every change must account for historical state and potential side effects.

## Implementation Approaches

### 1. **Containerization with Immutable Images**

Package components as Docker containers with all dependencies included. Never modify running containers—always deploy new images:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

When you need to change the component, build a new image and replace the container. The old container is destroyed, taking all its state with it.

**When to use**: Services, workers, background jobs, any component that doesn't need to persist state locally.

**Success looks like**: Being able to destroy and recreate any component in seconds without loss of functionality.

### 2. **Immutable Infrastructure**

Treat infrastructure as disposable. Use infrastructure-as-code to define components declaratively, then destroy and recreate entire environments:

```python
# Terraform-like configuration
resource "aws_instance" "web_server" {
    ami           = "ami-0c55b159cbfafe1f0"
    instance_type = "t2.micro"
    user_data     = file("setup.sh")
}
```

Never SSH into servers to make changes. Instead, update the configuration and deploy fresh infrastructure.

**When to use**: Cloud infrastructure, databases, networking, any infrastructure component.

**Success looks like**: Destroying and recreating your entire infrastructure from code in minutes.

### 3. **Stateless Services**

Design services that store no local state. All state lives in external storage (databases, object stores, caches):

```python
class OrderService:
    def __init__(self, db_connection, cache_connection):
        self.db = db_connection
        self.cache = cache_connection
        # No local state stored here

    def create_order(self, order_data):
        order = Order(**order_data)
        self.db.save(order)  # State goes to database
        self.cache.set(f"order:{order.id}", order)  # Cached externally
        return order
```

Any instance of the service can handle any request because there's no local state to synchronize.

**When to use**: Web services, APIs, microservices, any component that handles requests.

**Success looks like**: Being able to kill any service instance without affecting system behavior.

### 4. **Fast Startup and Shutdown**

Design components to start quickly and shut down cleanly:

```python
class Worker:
    def __init__(self):
        self.running = False

    async def start(self):
        self.running = True
        # Fast initialization—no complex setup
        logger.info("Worker started")
        while self.running:
            await self.process_next_job()

    async def shutdown(self):
        # Clean shutdown—finish current job, release resources
        logger.info("Worker shutting down")
        self.running = False
        await self.cleanup()
```

Components that start quickly can be recreated rapidly. Components that shut down cleanly don't leave resources locked or operations incomplete.

**When to use**: All components, but especially critical for frequently restarted services.

**Success looks like**: Start time under 5 seconds, clean shutdown under 10 seconds.

### 5. **No Local State or Configuration**

Avoid storing state in local files, environment variables, or configuration files on the filesystem:

```python
# Good: Configuration from environment or config service
config = {
    "database_url": os.getenv("DATABASE_URL"),
    "api_key": config_service.get("api_key"),
    "feature_flags": feature_service.get_flags()
}

# Bad: Configuration from local files
with open("/etc/myapp/config.ini") as f:
    config = parse_config(f)  # Tied to this specific filesystem
```

External configuration means any new instance automatically has the right settings.

**When to use**: All components that need configuration or state.

**Success looks like**: New instances work correctly without copying files or setup scripts.

### 6. **Idempotent Deployment**

Deploy components using idempotent operations (see Principle #31). Running deployment twice produces the same result:

```python
def deploy_component(component_spec):
    # Check if component exists
    existing = kubernetes_api.get_deployment(component_spec.name)

    if existing and existing.spec == component_spec:
        return existing  # Already deployed with this spec

    if existing:
        # Update existing deployment
        kubernetes_api.update_deployment(component_spec)
    else:
        # Create new deployment
        kubernetes_api.create_deployment(component_spec)
```

Idempotency makes components safely disposable—you can redeploy without fear.

**When to use**: All deployment operations, especially in automated systems.

**Success looks like**: Deployment scripts that can run multiple times safely.

## Good Examples vs Bad Examples

### Example 1: Web Service Container

**Good:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app

# Copy dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# No local state, no volumes
# Configuration from environment variables
ENV PYTHONUNBUFFERED=1

# Fast startup
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```python
# Service is stateless
app = FastAPI()

@app.get("/api/users/{user_id}")
async def get_user(user_id: str, db: Database = Depends(get_db)):
    # All state in database
    return await db.users.find_one({"id": user_id})
```

**Bad:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

# BAD: Storing state in local volume
VOLUME /app/data

# BAD: Configuration file baked into image
COPY config.ini /etc/myapp/config.ini

# BAD: Slow startup with database migrations
CMD ["sh", "-c", "python migrate.py && uvicorn main:app"]
```

```python
# BAD: Service stores state locally
app = FastAPI()
local_cache = {}  # Lost when container restarts

@app.get("/api/users/{user_id}")
async def get_user(user_id: str):
    # BAD: State in local memory
    if user_id in local_cache:
        return local_cache[user_id]

    user = await db.users.find_one({"id": user_id})
    local_cache[user_id] = user  # Won't survive restart
    return user
```

**Why It Matters:** The good example can be destroyed and recreated in seconds without data loss. The bad example stores state locally, has slow startup due to migrations, and loses cached data on restart. AI agents can't safely experiment with the bad version because restarting it loses data and takes too long.

### Example 2: Worker Process

**Good:**
```python
import signal
import asyncio
from dataclasses import dataclass

@dataclass
class JobResult:
    job_id: str
    status: str
    result: dict

class DisposableWorker:
    def __init__(self, queue_url: str, results_db: Database):
        self.queue = Queue(queue_url)
        self.results_db = results_db
        self.running = False

    async def start(self):
        # Fast startup—just connect to queue
        await self.queue.connect()
        self.running = True

        # Handle graceful shutdown
        signal.signal(signal.SIGTERM, self._handle_shutdown)

        logger.info("Worker started, processing jobs")

        while self.running:
            job = await self.queue.receive()
            if job:
                await self._process_job(job)

    async def _process_job(self, job):
        try:
            result = await process(job)
            # Store result externally
            await self.results_db.save(JobResult(
                job_id=job.id,
                status="completed",
                result=result
            ))
            await self.queue.delete(job)
        except Exception as e:
            logger.error(f"Job {job.id} failed: {e}")
            # Put back in queue for retry
            await self.queue.return_job(job)

    def _handle_shutdown(self, signum, frame):
        logger.info("Shutdown signal received")
        self.running = False

    async def shutdown(self):
        # Clean shutdown—finish current job
        logger.info("Worker shutting down gracefully")
        await self.queue.disconnect()
```

**Bad:**
```python
class StatefulWorker:
    def __init__(self, queue_url: str):
        self.queue = Queue(queue_url)
        self.running = False
        # BAD: Local state
        self.processed_jobs = []
        self.job_cache = {}

    async def start(self):
        # BAD: Slow startup with setup
        await self.queue.connect()
        await self._load_state_from_disk()  # Reading local files
        await self._initialize_cache()  # Building local cache
        await self._run_health_checks()  # Slow checks
        self.running = True

        # BAD: No shutdown handling
        while self.running:
            job = await self.queue.receive()
            await self._process_job(job)

    async def _process_job(self, job):
        # BAD: Storing results locally
        result = await process(job)
        self.processed_jobs.append(job.id)  # Lost on restart
        self.job_cache[job.id] = result  # Lost on restart

        # BAD: Writing to local file
        with open("/var/worker/results.json", "a") as f:
            f.write(json.dumps(result))

    async def _load_state_from_disk(self):
        # BAD: Dependent on local filesystem state
        if os.path.exists("/var/worker/state.json"):
            with open("/var/worker/state.json") as f:
                state = json.load(f)
                self.processed_jobs = state.get("processed", [])
```

**Why It Matters:** The good example can be killed at any time and restarted immediately. Jobs in progress return to the queue automatically. Results are stored externally. The bad example maintains local state that's lost on restart, has slow startup, and doesn't handle shutdown gracefully. Killing it loses work and requires manual recovery.

### Example 3: Database Schema Migration

**Good:**
```python
import hashlib
from datetime import datetime

class MigrationRunner:
    def __init__(self, db: Database):
        self.db = db

    async def run_migrations(self, migration_dir: str):
        # Create migrations table if needed (idempotent)
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id SERIAL PRIMARY KEY,
                version VARCHAR(255) UNIQUE NOT NULL,
                checksum VARCHAR(64) NOT NULL,
                applied_at TIMESTAMP NOT NULL
            )
        """)

        # Load all migration files
        migrations = self._load_migrations(migration_dir)

        for migration in sorted(migrations):
            await self._apply_migration(migration)

    async def _apply_migration(self, migration):
        # Check if already applied (idempotent)
        existing = await self.db.fetch_one(
            "SELECT * FROM schema_migrations WHERE version = $1",
            migration.version
        )

        if existing:
            # Verify checksum matches
            if existing.checksum != migration.checksum:
                raise MigrationError(
                    f"Migration {migration.version} checksum mismatch. "
                    "Database may have been manually modified."
                )
            logger.info(f"Migration {migration.version} already applied")
            return

        # Apply migration in transaction
        async with self.db.transaction():
            await self.db.execute(migration.sql)
            await self.db.execute(
                """
                INSERT INTO schema_migrations (version, checksum, applied_at)
                VALUES ($1, $2, $3)
                """,
                migration.version,
                migration.checksum,
                datetime.utcnow()
            )

        logger.info(f"Applied migration {migration.version}")

    def _load_migrations(self, migration_dir: str):
        migrations = []
        for file_path in sorted(Path(migration_dir).glob("*.sql")):
            sql = file_path.read_text()
            migrations.append(Migration(
                version=file_path.stem,
                sql=sql,
                checksum=hashlib.sha256(sql.encode()).hexdigest()
            ))
        return migrations
```

**Bad:**
```python
class MigrationRunner:
    def __init__(self, db: Database):
        self.db = db
        # BAD: Tracking state locally
        self.applied_migrations = []

    async def run_migrations(self, migration_dir: str):
        # BAD: Assumes clean database
        migrations = self._load_migrations(migration_dir)

        for migration in migrations:
            # BAD: No idempotency check
            await self.db.execute(migration.sql)
            self.applied_migrations.append(migration.version)

        # BAD: Writing state to local file
        with open("/var/migrations.log", "w") as f:
            json.dump(self.applied_migrations, f)

    def _load_migrations(self, migration_dir: str):
        # BAD: No checksums, no verification
        return [
            Migration(version=f.stem, sql=f.read_text())
            for f in Path(migration_dir).glob("*.sql")
        ]
```

**Why It Matters:** The good example can be run multiple times safely—it checks what's already applied and only runs new migrations. If a container restarts mid-migration, it can resume safely. The bad example fails if run twice, doesn't track what's been applied in the database, and stores state locally. You can't safely destroy and recreate components that depend on it.

### Example 4: Configuration Management

**Good:**
```python
from dataclasses import dataclass
import os

@dataclass
class Config:
    database_url: str
    redis_url: str
    api_key: str
    feature_flags: dict

class ConfigLoader:
    """Load configuration from external sources only"""

    @staticmethod
    def load() -> Config:
        return Config(
            # From environment variables
            database_url=os.environ["DATABASE_URL"],
            redis_url=os.environ["REDIS_URL"],
            api_key=os.environ["API_KEY"],

            # From remote config service
            feature_flags=ConfigLoader._load_feature_flags()
        )

    @staticmethod
    def _load_feature_flags() -> dict:
        # Fetch from config service
        import requests
        config_service_url = os.environ["CONFIG_SERVICE_URL"]
        response = requests.get(f"{config_service_url}/flags")
        return response.json()

# Usage: any new instance automatically gets correct config
config = ConfigLoader.load()
app = create_app(config)
```

**Bad:**
```python
import configparser

class Config:
    """BAD: Load configuration from local files"""

    def __init__(self, config_file="/etc/myapp/config.ini"):
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self):
        # BAD: Reading from local filesystem
        parser = configparser.ConfigParser()
        parser.read(self.config_file)
        return parser

    def get(self, section, key):
        return self.config[section][key]

    def update(self, section, key, value):
        # BAD: Writing to local filesystem
        self.config[section][key] = value
        with open(self.config_file, "w") as f:
            self.config.write(f)

# BAD: New instances need the config file copied to them
config = Config()
database_url = config.get("database", "url")
```

**Why It Matters:** The good example requires no local files—any new instance works immediately. Configuration changes propagate to all instances automatically. The bad example requires copying config files to each instance, manual updates, and careful coordination. You can't spin up new instances quickly because they need the right files in place.

### Example 5: Kubernetes Deployment

**Good:**
```yaml
# deployment.yaml - Disposable pods with external state
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-api
  template:
    metadata:
      labels:
        app: web-api
    spec:
      containers:
      - name: web-api
        image: myregistry/web-api:v1.2.3
        ports:
        - containerPort: 8000

        # Configuration from ConfigMap and Secrets
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: redis_url

        # No local storage
        volumeMounts: []

        # Fast startup
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10

        # Clean shutdown
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 10"]

        # Resource limits for predictable behavior
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

```python
# main.py - Application designed for disposability
from fastapi import FastAPI
import signal

app = FastAPI()

# Graceful shutdown handling
@app.on_event("startup")
async def startup():
    logger.info("Service starting")
    signal.signal(signal.SIGTERM, handle_shutdown)

@app.on_event("shutdown")
async def shutdown():
    logger.info("Service shutting down")
    # Clean up connections
    await db.disconnect()
    await redis.disconnect()

def handle_shutdown(signum, frame):
    logger.info("SIGTERM received, shutting down gracefully")
    # FastAPI handles the actual shutdown
```

**Bad:**
```yaml
# deployment.yaml - Stateful pods with local storage
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-api
spec:
  replicas: 1  # BAD: Single replica due to local state
  selector:
    matchLabels:
      app: web-api
  template:
    metadata:
      labels:
        app: web-api
    spec:
      containers:
      - name: web-api
        image: myregistry/web-api:latest  # BAD: Using 'latest' tag

        # BAD: Configuration file mounted from host
        volumeMounts:
        - name: config
          mountPath: /etc/myapp
        - name: data
          mountPath: /var/data  # BAD: Local state storage

        # BAD: No health checks
        # BAD: No shutdown handling

        # BAD: No resource limits

      volumes:
      - name: config
        hostPath:
          path: /opt/myapp/config  # BAD: Tied to specific host
      - name: data
        hostPath:
          path: /var/myapp/data  # BAD: Data on host filesystem
```

```python
# main.py - Application with local state
from fastapi import FastAPI
import json

app = FastAPI()

# BAD: Local state
cache = {}

@app.on_event("startup")
async def startup():
    # BAD: Loading state from local file
    with open("/var/data/cache.json") as f:
        cache.update(json.load(f))

@app.on_event("shutdown")
async def shutdown():
    # BAD: Saving state to local file
    with open("/var/data/cache.json", "w") as f:
        json.dump(cache, f)

# BAD: No graceful shutdown handling
```

**Why It Matters:** The good example can scale to any number of replicas, pods can be killed and recreated instantly, and Kubernetes can roll out updates with zero downtime. The bad example is tied to specific hosts, stores state locally, can't scale horizontally, and loses data when pods are destroyed. You can't treat pods as disposable because they contain important state.

## Related Principles

- **[Principle #7 - Regenerate, Don't Edit](../process/07-regenerate-dont-edit.md)** - Disposable components enable regeneration because you can destroy and recreate them without fear of data loss

- **[Principle #31 - Idempotency by Design](31-idempotency-by-design.md)** - Idempotent operations make components safely disposable; you can redeploy without worrying about partial state

- **[Principle #26 - Stateless by Default](26-stateless-by-default.md)** - Stateless components are naturally disposable because they store no local state

- **[Principle #24 - Long-Running Agent Processes](24-everything-in-containers.md)** - Containers are inherently disposable, making this principle practical to implement

- **[Principle #28 - CLI-First Design](28-infrastructure-as-code.md)** - IaC enables disposable infrastructure by making it easy to destroy and recreate components

- **[Principle #33 - Graceful Degradation by Design](33-declarative-configuration.md)** - Declarative config describes desired state, making components disposable because they can be recreated from specifications

## Common Pitfalls

1. **Storing State in Local Volumes**: Mounting local directories or using Docker volumes for application state makes components non-disposable.
   - Example: Storing user uploads in `/var/uploads` on the container filesystem instead of object storage.
   - Impact: Can't destroy containers without losing data. Can't scale horizontally. Manual backup procedures required.

2. **Slow Startup Times**: Components that take minutes to start can't be rapidly recreated.
   - Example: Application that rebuilds ML models or runs database migrations on startup.
   - Impact: Long recovery times after failures. Can't quickly spin up new instances for scaling.

3. **Manual Configuration Steps**: Components that require SSH access or manual setup aren't disposable.
   - Example: "After deploying, SSH in and run these commands to configure the service."
   - Impact: Can't automate deployment. New instances require manual intervention. AI agents can't manage the system.

4. **Persistent Connections or Locks**: Components that hold long-lived connections or locks can't be safely destroyed.
   - Example: Worker that acquires a file lock on startup and holds it indefinitely.
   - Impact: Killing the component leaves resources locked. Other components can't proceed.

5. **Cleanup Dependencies**: Components that must run cleanup on shutdown aren't truly disposable.
   - Example: Service that must gracefully drain all connections and flush buffers before shutdown.
   - Impact: Can't forcefully kill components. Shutdown takes too long. Recovery is complex.

6. **Configuration Drift**: Manually updating configuration on running components creates inconsistency.
   - Example: SSH into production server to change a config value instead of redeploying.
   - Impact: New instances don't have the change. Configuration becomes inconsistent. Can't reliably recreate the component.

7. **Local Caching Without Invalidation**: Building up local caches that don't handle invalidation makes components non-disposable.
   - Example: In-memory cache that never expires, growing until the component runs out of memory.
   - Impact: Long-running components accumulate state. Restarting them causes performance degradation until cache rebuilds.

## Tools & Frameworks

### Containerization Platforms
- **Docker**: Build disposable containers with all dependencies included. Destroy and recreate in seconds.
- **Podman**: Daemonless container runtime, even more suitable for disposable components.
- **containerd**: Lightweight container runtime for Kubernetes, optimized for fast startup.

### Orchestration Platforms
- **Kubernetes**: Treats pods as disposable by design. Automatically recreates failed pods.
- **Docker Swarm**: Simple orchestration with rolling updates and service discovery.
- **Nomad**: Flexible scheduler that treats all workloads as disposable.

### Infrastructure as Code
- **Terraform**: Declaratively define infrastructure, destroy and recreate entire environments.
- **Pulumi**: IaC with programming languages, making infrastructure disposable through code.
- **AWS CDK**: Define cloud infrastructure as code, enabling disposable infrastructure.

### Configuration Management
- **Consul**: Service discovery and configuration, no local config files needed.
- **etcd**: Distributed key-value store for configuration, separates config from components.
- **Vault**: Secrets management, components fetch credentials at runtime rather than storing locally.

### Cloud Services
- **AWS Lambda**: Functions are inherently disposable, destroyed after execution.
- **Google Cloud Run**: Fully managed container platform, instances are disposable.
- **Azure Container Instances**: On-demand containers, no persistent state.

### Message Queues
- **RabbitMQ**: Durable queues survive worker restarts, making workers disposable.
- **Kafka**: Persistent message log, consumers can be destroyed and recreated without data loss.
- **AWS SQS**: Managed queues, workers are disposable because messages persist in the queue.

## Implementation Checklist

When implementing this principle, ensure:

- [ ] Components store no state on local filesystem or in memory
- [ ] All configuration comes from environment variables or external config services
- [ ] Startup time is under 10 seconds for most components
- [ ] Shutdown completes in under 30 seconds, gracefully finishing current work
- [ ] Deployment is idempotent—can be run multiple times safely
- [ ] Components can be destroyed and recreated without data loss
- [ ] Multiple instances of a component can run simultaneously without conflict
- [ ] No manual steps required to deploy or configure components
- [ ] Health checks enable orchestrators to automatically restart failed components
- [ ] Logs and metrics are sent to external systems, not stored locally
- [ ] Secrets and credentials are fetched at runtime, not baked into images
- [ ] Documentation includes commands to destroy and recreate components quickly

## Metadata

**Category**: Technology
**Principle Number**: 27
**Related Patterns**: Immutable Infrastructure, Cattle Not Pets, Blue-Green Deployment, Canary Releases, Circuit Breaker
**Prerequisites**: Containerization, external state storage, configuration management, orchestration platform
**Difficulty**: Medium
**Impact**: High

---

**Status**: Complete
**Last Updated**: 2025-09-30
**Version**: 1.0