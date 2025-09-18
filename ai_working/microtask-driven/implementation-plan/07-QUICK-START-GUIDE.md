# Quick Start Guide - Start Building in 10 Minutes

## 🚀 Zero to Building in 5 Steps

### Step 1: Prerequisites Check (1 minute)
```bash
# Check Python
python --version  # Need 3.10+

# Check Node
node --version   # Need v18+

# Check/Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Step 2: Clone and Install (2 minutes)
```bash
# Clone repository
git clone <repository-url>
cd amplifier-tool-builder

# Install everything
uv sync
npm install -g @anthropic-ai/claude-code

# Set API key
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Step 3: Verify Setup (1 minute)
```bash
# Quick test
python -c "from claude_code_sdk import ClaudeSDKClient; print('✅ SDK ready')"
which claude && echo "✅ CLI ready"
```

### Step 4: Create Project Structure (3 minutes)
```bash
# Create the package structure
mkdir -p amplifier_tool_builder/{agents,stages,patterns,metacognitive}
touch amplifier_tool_builder/__init__.py

# Create the CLI entry point
cat > amplifier_tool_builder/cli.py << 'EOF'
import click
import asyncio

@click.command()
@click.argument('name')
def create(name):
    """Create a new Amplifier CLI Tool"""
    click.echo(f"Creating tool: {name}")
    # Your implementation here

if __name__ == "__main__":
    create()
EOF

# Test the CLI
python amplifier_tool_builder/cli.py test-tool
```

### Step 5: Run Your First Microtask (3 minutes)
```python
# Create test_microtask.py
cat > test_microtask.py << 'EOF'
import asyncio
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions

async def run_microtask():
    async with ClaudeSDKClient(
        options=ClaudeCodeOptions(
            system_prompt="You are a helpful assistant",
            max_turns=1
        )
    ) as client:
        await client.query("Say 'Hello, Amplifier!'")

        async for message in client.receive_response():
            if hasattr(message, 'content'):
                for block in message.content:
                    if hasattr(block, 'text'):
                        print(block.text, end='', flush=True)

asyncio.run(run_microtask())
EOF

# Run it
python test_microtask.py
```

**🎉 If you see "Hello, Amplifier!" - you're ready to build!**

---

## 📦 Building Your First Agent (10 minutes)

### 1. Create Base Agent Class
```python
# amplifier_tool_builder/agents/base.py
import asyncio
import json
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions

class MicrotaskAgent:
    def __init__(self, task_type: str, timeout: int = 10):
        self.task_type = task_type
        self.timeout = timeout

    async def execute(self, input_data: dict) -> dict:
        try:
            async with asyncio.timeout(self.timeout):
                async with ClaudeSDKClient(
                    options=ClaudeCodeOptions(
                        system_prompt=self._get_system_prompt(),
                        max_turns=1
                    )
                ) as client:
                    await client.query(self._build_prompt(input_data))

                    response = ""
                    async for message in client.receive_response():
                        if hasattr(message, 'content'):
                            for block in message.content:
                                if hasattr(block, 'text'):
                                    response += block.text

                    return {
                        "success": True,
                        "result": self._parse_response(response)
                    }
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"Timeout after {self.timeout} seconds"
            }

    def _get_system_prompt(self) -> str:
        return "You are a helpful assistant"

    def _build_prompt(self, input_data: dict) -> str:
        return json.dumps(input_data)

    def _parse_response(self, response: str) -> any:
        return response
```

### 2. Create Your First Specific Agent
```python
# amplifier_tool_builder/agents/requirements.py
from .base import MicrotaskAgent

class ProblemIdentifier(MicrotaskAgent):
    """Identifies the core problem a tool should solve"""

    def __init__(self):
        super().__init__("problem_identification", timeout=8)

    def _get_system_prompt(self) -> str:
        return """You are an expert at identifying core problems.
        Be concise and specific."""

    def _build_prompt(self, input_data: dict) -> str:
        return f"""
        Tool Description: {input_data.get('description', '')}

        Identify the CORE PROBLEM this tool solves in 1-2 sentences.
        """

    def _parse_response(self, response: str) -> dict:
        return {
            "core_problem": response.strip()
        }
```

### 3. Test Your Agent
```python
# test_agent.py
import asyncio
from amplifier_tool_builder.agents.requirements import ProblemIdentifier

async def test():
    agent = ProblemIdentifier()
    result = await agent.execute({
        "description": "A tool that tests REST APIs automatically"
    })

    if result["success"]:
        print(f"✅ Core problem: {result['result']['core_problem']}")
    else:
        print(f"❌ Error: {result['error']}")

asyncio.run(test())
```

---

## 🔧 Essential Patterns Copy-Paste

### Pattern 1: Incremental Save
```python
# Never lose work!
import json
from pathlib import Path

def save_progress(session_id: str, data: any):
    """Save immediately after every operation"""
    checkpoint_dir = Path(".amplifier/checkpoints")
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    checkpoint_file = checkpoint_dir / f"{session_id}.json"
    with open(checkpoint_file, 'w') as f:
        json.dump(data, f, indent=2)

# Usage
result = process_something()
save_progress("session-001", result)  # IMMEDIATELY!
```

### Pattern 2: Recovery on Startup
```python
def load_checkpoint(session_id: str) -> dict:
    """Load previous progress if it exists"""
    checkpoint_file = Path(f".amplifier/checkpoints/{session_id}.json")

    if checkpoint_file.exists():
        with open(checkpoint_file) as f:
            return json.load(f)

    return {}  # Start fresh

# Usage
previous_work = load_checkpoint("session-001")
if previous_work:
    print(f"Resuming from checkpoint...")
```

### Pattern 3: Parallel Execution
```python
async def run_parallel_tasks(tasks: list):
    """Run multiple independent tasks in parallel"""
    results = await asyncio.gather(
        *[task.execute() for task in tasks],
        return_exceptions=True
    )

    # Handle any failures
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"Task {i} failed: {result}")

    return results

# Usage
agents = [ProblemIdentifier(), ArchitectureDesigner(), FlowAnalyzer()]
results = await run_parallel_tasks(agents)
```

---

## 🏃 Speed Run: Complete Mini Tool Builder (15 minutes)

```python
# mini_tool_builder.py - A working tool builder in <100 lines
import asyncio
import json
from pathlib import Path
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions

class MiniToolBuilder:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.checkpoint_file = Path(f".amplifier/{session_id}.json")
        self.checkpoint_file.parent.mkdir(exist_ok=True)

    async def analyze_requirements(self, description: str) -> dict:
        """Step 1: Analyze what the tool needs"""
        async with ClaudeSDKClient(
            options=ClaudeCodeOptions(
                system_prompt="You are a requirements analyst",
                max_turns=1
            )
        ) as client:
            await client.query(f"What does this tool need: {description}")

            response = ""
            async for msg in client.receive_response():
                if hasattr(msg, 'content'):
                    for block in msg.content:
                        if hasattr(block, 'text'):
                            response += block.text

            return {"requirements": response}

    async def generate_code(self, requirements: dict) -> dict:
        """Step 2: Generate the code"""
        async with ClaudeSDKClient(
            options=ClaudeCodeOptions(
                system_prompt="You are a Python code generator",
                max_turns=1
            )
        ) as client:
            prompt = f"Generate Python code for: {requirements}"
            await client.query(prompt)

            code = ""
            async for msg in client.receive_response():
                if hasattr(msg, 'content'):
                    for block in msg.content:
                        if hasattr(block, 'text'):
                            code += block.text

            return {"code": code}

    def save_checkpoint(self, data: dict):
        """Save progress immediately"""
        with open(self.checkpoint_file, 'w') as f:
            json.dump(data, f, indent=2)

    def load_checkpoint(self) -> dict:
        """Load previous progress"""
        if self.checkpoint_file.exists():
            with open(self.checkpoint_file) as f:
                return json.load(f)
        return {}

    async def build_tool(self, name: str, description: str):
        """Build a complete tool"""
        # Load any previous progress
        state = self.load_checkpoint()

        # Step 1: Requirements (if not done)
        if "requirements" not in state:
            print("🔍 Analyzing requirements...")
            state["requirements"] = await self.analyze_requirements(description)
            self.save_checkpoint(state)
            print("✅ Requirements analyzed")

        # Step 2: Generate code (if not done)
        if "code" not in state:
            print("🔨 Generating code...")
            state["code"] = await self.generate_code(state["requirements"])
            self.save_checkpoint(state)
            print("✅ Code generated")

        # Step 3: Save the tool
        tool_file = Path(f"{name}.py")
        with open(tool_file, 'w') as f:
            f.write(state["code"]["code"])

        print(f"🎉 Tool created: {tool_file}")
        return state

# Run it!
async def main():
    builder = MiniToolBuilder("quick-build-001")
    await builder.build_tool(
        name="my_tool",
        description="A tool that formats JSON files"
    )

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🎯 Next Immediate Actions

### Right Now (Next 30 minutes)
1. Run the mini tool builder above
2. Examine the generated tool
3. Modify it to generate a different type of tool

### Today
1. Implement 2-3 more agents
2. Add proper error handling
3. Test interruption/recovery

### Tomorrow
1. Build a complete stage (requirements or architecture)
2. Add parallel execution
3. Implement quality verification

---

## 🚨 Common Gotchas & Fixes

### "Claude CLI not found"
```bash
# Fix: Install globally
npm install -g @anthropic-ai/claude-code

# Verify
which claude
```

### "Timeout after 10 seconds"
```python
# Fix: Some operations need more time
MicrotaskAgent.__init__(self, timeout=30)  # Increase timeout
```

### "No module named claude_code_sdk"
```bash
# Fix: Install the SDK
pip install claude-code-sdk
# or
uv add claude-code-sdk
```

### "API key not set"
```bash
# Fix: Export the key
export ANTHROPIC_API_KEY="sk-ant-..."

# Or in Python
import os
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-..."
```

---

## 📚 Minimal Required Reading

If you read nothing else, read these sections:
1. [Microtask Patterns - Basic Executor](04-MICROTASK-PATTERNS.md#1-basic-microtask-executor)
2. [Incremental Save Pattern](04-MICROTASK-PATTERNS.md#2-incremental-save-pattern)
3. [Technical Architecture - Microtask Agent](02-TECHNICAL-ARCHITECTURE.md#3-microtask-agent-architecture)

---

## 💪 Challenge: Build Something Real

### 15-Minute Challenge
Build an agent that:
1. Takes a Python function as input
2. Generates unit tests for it
3. Saves the tests to a file

### 30-Minute Challenge
Build a mini-tool that:
1. Analyzes a README file
2. Generates a CLI tool based on it
3. Includes error handling

### 60-Minute Challenge
Build a complete stage that:
1. Has 3+ microtask agents
2. Saves progress incrementally
3. Can resume from interruption
4. Includes verification

---

## 🎉 You're Ready!

You now have:
- ✅ Working environment
- ✅ First microtask running
- ✅ Basic agent created
- ✅ Essential patterns understood
- ✅ Mini tool builder working

**Start building! The best way to learn is by doing.**

Remember:
- Keep microtasks under 10 seconds
- Save after every operation
- Test frequently
- Ask for help when stuck

Happy building! 🚀