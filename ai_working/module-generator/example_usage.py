#!/usr/bin/env python3
"""
Example usage of the Module Generator CLI with Claude Code SDK integration.

This demonstrates how the module generator orchestrates subagents to transform
specifications into working code using the decomposition strategy.
"""

import asyncio
import json
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import click
import yaml

# Claude Code SDK imports (when inside Claude environment)
try:
    from claude_code_sdk import ClaudeCodeOptions
    from claude_code_sdk import ClaudeSDKClient
    from claude_code_sdk import query

    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    print("Warning: Claude Code SDK not available. Using mock mode.")


@dataclass
class GenerationState:
    """Track state of module generation for resume capability"""

    module_name: str
    phase: str
    completed_phases: list[str]
    artifacts: dict[str, Any]
    errors: list[str]
    checkpoint_file: str

    def save(self):
        """Persist state to checkpoint file"""
        Path(self.checkpoint_file).parent.mkdir(parents=True, exist_ok=True)
        with open(self.checkpoint_file, "w") as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load_or_create(cls, module_name: str) -> "GenerationState":
        """Load existing state or create new"""
        checkpoint_file = f".checkpoints/{module_name}/state.json"
        if Path(checkpoint_file).exists():
            with open(checkpoint_file) as f:
                data = json.load(f)
                return cls(**data)
        return cls(
            module_name=module_name,
            phase="validation",
            completed_phases=[],
            artifacts={},
            errors=[],
            checkpoint_file=checkpoint_file,
        )


class SubagentOrchestrator:
    """Orchestrates subagents for module generation"""

    def __init__(self, timeout: int = 120):
        self.timeout = timeout
        self.progress = {"total": 0, "completed": 0}

    async def run_subagent(self, agent_name: str, task: dict[str, Any]) -> dict[str, Any]:
        """Execute a subagent with proper timeout and error handling"""
        if not SDK_AVAILABLE:
            return self._mock_subagent_response(agent_name, task)

        try:
            # Use Claude Code SDK to run subagent
            async with asyncio.timeout(self.timeout):
                messages = []

                # Create prompt for subagent
                prompt = f"""
                As the {agent_name} subagent, process this task:

                Input:
                {json.dumps(task, indent=2)}

                Follow your specialized instructions and return structured output.
                """

                # Query Claude through SDK
                async for message in query(
                    prompt=prompt,
                    options={
                        "subagent_type": agent_name,
                        "max_turns": 1,
                        "append_system_prompt": f"You are the {agent_name} specialist.",
                    },
                ):
                    messages.append(message)

                # Extract result from messages
                result = self._extract_result(messages)
                return {
                    "agent": agent_name,
                    "status": "success",
                    "output": result,
                    "metrics": {"duration_seconds": 0},  # Would track actual time
                }

        except TimeoutError:
            return {
                "agent": agent_name,
                "status": "timeout",
                "error": f"Subagent {agent_name} timed out after {self.timeout} seconds",
            }
        except Exception as e:
            return {"agent": agent_name, "status": "error", "error": str(e)}

    def _mock_subagent_response(self, agent_name: str, task: dict) -> dict:
        """Mock response for testing without Claude Code SDK"""
        return {
            "agent": agent_name,
            "status": "success",
            "output": {"message": f"Mock {agent_name} completed", "data": task},
            "metrics": {"duration_seconds": 1},
        }

    def _extract_result(self, messages: list) -> Any:
        """Extract structured result from Claude Code SDK messages"""
        for message in messages:
            if hasattr(message, "result"):
                return json.loads(message.result)
        return {}

    async def generate_module(self, spec_path: str, contract_path: str, resume: bool = False) -> GenerationState:
        """Orchestrate complete module generation"""

        # Load specifications
        with open(spec_path) as f:
            spec = yaml.safe_load(f)
        with open(contract_path) as f:
            contract = yaml.safe_load(f)

        module_name = contract.get("module_name", "unnamed")
        state = GenerationState.load_or_create(module_name)

        print(f"🚀 Starting generation for module: {module_name}")

        # Phase 1: Validation (Sequential)
        if "validation" not in state.completed_phases:
            print("📋 Phase 1: Validating specifications...")

            validation_result = await self.run_subagent("spec-validator", {"contract": contract, "spec": spec})

            if validation_result["status"] != "success":
                state.errors.append(f"Validation failed: {validation_result.get('error')}")
                state.save()
                raise RuntimeError(f"Validation failed: {validation_result.get('error')}")

            state.artifacts["validation"] = validation_result["output"]
            state.completed_phases.append("validation")
            state.save()
            print("✅ Validation complete")

        # Phase 2: Architecture (Sequential)
        if "architecture" not in state.completed_phases:
            print("🏗️ Phase 2: Designing architecture...")

            arch_result = await self.run_subagent(
                "code-architect",
                {"spec": spec, "contract": contract, "validation": state.artifacts.get("validation", {})},
            )

            state.artifacts["architecture"] = arch_result["output"]
            state.completed_phases.append("architecture")
            state.save()
            print("✅ Architecture complete")

        # Phase 3: Implementation (Parallel)
        if "implementation" not in state.completed_phases:
            print("⚡ Phase 3: Generating implementation (parallel)...")

            architecture = state.artifacts.get("architecture", {})

            # Run implementation tasks in parallel
            impl_tasks = [
                self.run_subagent("model-builder", {"models": architecture.get("models", {})}),
                self.run_subagent("logic-builder", {"logic": architecture.get("logic", {})}),
                self.run_subagent("interface-builder", {"interface": architecture.get("interface", {})}),
                self.run_subagent("utils-builder", {"utils": architecture.get("utils", {})}),
            ]

            impl_results = await asyncio.gather(*impl_tasks)

            state.artifacts["implementation"] = {
                "models": impl_results[0]["output"],
                "logic": impl_results[1]["output"],
                "interface": impl_results[2]["output"],
                "utils": impl_results[3]["output"],
            }
            state.completed_phases.append("implementation")
            state.save()
            print("✅ Implementation complete")

        # Phase 4: Testing (Parallel)
        if "testing" not in state.completed_phases:
            print("🧪 Phase 4: Generating tests (parallel)...")

            implementation = state.artifacts.get("implementation", {})

            test_tasks = [
                self.run_subagent("unit-test-generator", {"code": implementation, "spec": spec}),
                self.run_subagent(
                    "integration-test-generator", {"contract": contract, "implementation": implementation}
                ),
                self.run_subagent("fixture-generator", {"models": implementation.get("models", {})}),
            ]

            test_results = await asyncio.gather(*test_tasks)

            state.artifacts["tests"] = {
                "unit": test_results[0]["output"],
                "integration": test_results[1]["output"],
                "fixtures": test_results[2]["output"],
            }
            state.completed_phases.append("testing")
            state.save()
            print("✅ Tests complete")

        # Phase 5: Documentation (Parallel)
        if "documentation" not in state.completed_phases:
            print("📚 Phase 5: Generating documentation (parallel)...")

            doc_tasks = [
                self.run_subagent("api-doc-generator", {"interface": state.artifacts["implementation"]["interface"]}),
                self.run_subagent("example-generator", {"contract": contract, "tests": state.artifacts["tests"]}),
                self.run_subagent("docstring-generator", {"code": state.artifacts["implementation"]}),
            ]

            doc_results = await asyncio.gather(*doc_tasks)

            state.artifacts["documentation"] = {
                "api": doc_results[0]["output"],
                "examples": doc_results[1]["output"],
                "docstrings": doc_results[2]["output"],
            }
            state.completed_phases.append("documentation")
            state.save()
            print("✅ Documentation complete")

        # Phase 6: Validation (Sequential)
        if "final_validation" not in state.completed_phases:
            print("✔️ Phase 6: Final validation...")

            validation_result = await self.run_subagent(
                "integration-validator",
                {"module": state.artifacts["implementation"], "tests": state.artifacts["tests"], "contract": contract},
            )

            state.artifacts["final_validation"] = validation_result["output"]
            state.completed_phases.append("final_validation")
            state.save()
            print("✅ Final validation complete")

        print(f"\n🎉 Module '{module_name}' generated successfully!")
        return state


class ModuleGeneratorCLI:
    """CLI interface for module generation"""

    def __init__(self):
        self.orchestrator = SubagentOrchestrator()

    async def generate(self, spec: str, contract: str, output: str = "./generated"):
        """Generate a module from specifications"""
        state = await self.orchestrator.generate_module(spec, contract)

        # Write generated files
        output_dir = Path(output) / state.module_name
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save all artifacts to files
        self._write_artifacts(output_dir, state.artifacts)

        print(f"\n📁 Module saved to: {output_dir}")
        return state

    async def generate_parallel(self, specs: list[str], contracts: list[str], output: str = "./generated"):
        """Generate multiple modules in parallel"""
        print(f"🚀 Generating {len(specs)} modules in parallel...")

        tasks = []
        for spec, contract in zip(specs, contracts, strict=False):
            tasks.append(self.orchestrator.generate_module(spec, contract))

        results = await asyncio.gather(*tasks)

        for state in results:
            output_dir = Path(output) / state.module_name
            output_dir.mkdir(parents=True, exist_ok=True)
            self._write_artifacts(output_dir, state.artifacts)

        print(f"\n🎉 Generated {len(results)} modules successfully!")
        return results

    def _write_artifacts(self, output_dir: Path, artifacts: dict):
        """Write generated artifacts to files"""
        # Implementation files
        if "implementation" in artifacts:
            impl = artifacts["implementation"]

            if "models" in impl:
                (output_dir / "models.py").write_text(impl["models"].get("code", "# Generated models"))

            if "logic" in impl:
                (output_dir / "core.py").write_text(impl["logic"].get("code", "# Generated logic"))

            if "interface" in impl:
                (output_dir / "__init__.py").write_text(impl["interface"].get("code", "# Generated interface"))

        # Test files
        if "tests" in artifacts:
            test_dir = output_dir / "tests"
            test_dir.mkdir(exist_ok=True)

            tests = artifacts["tests"]
            if "unit" in tests:
                (test_dir / "test_unit.py").write_text(tests["unit"].get("code", "# Generated unit tests"))

        # Documentation
        if "documentation" in artifacts:
            docs = artifacts["documentation"]
            if "api" in docs:
                (output_dir / "API.md").write_text(docs["api"].get("content", "# API Documentation"))


@click.group()
def cli():
    """Module Generator CLI - Transform specs into code using AI subagents"""
    pass


@cli.command()
@click.option("--spec", required=True, help="Path to implementation spec YAML")
@click.option("--contract", required=True, help="Path to contract YAML")
@click.option("--output", default="./generated", help="Output directory")
@click.option("--resume", is_flag=True, help="Resume from checkpoint")
def generate(spec, contract, output, resume):
    """Generate a single module from specifications"""
    generator = ModuleGeneratorCLI()
    asyncio.run(generator.generate(spec, contract, output))


@cli.command()
@click.option("--specs", multiple=True, required=True, help="Spec files")
@click.option("--contracts", multiple=True, required=True, help="Contract files")
@click.option("--output", default="./generated", help="Output directory")
def parallel(specs, contracts, output):
    """Generate multiple modules in parallel"""
    generator = ModuleGeneratorCLI()
    asyncio.run(generator.generate_parallel(list(specs), list(contracts), output))


@cli.command()
@click.option("--spec", required=True, help="Path to spec YAML to validate")
@click.option("--contract", required=True, help="Path to contract YAML to validate")
def validate(spec, contract):
    """Validate specifications without generating"""
    orchestrator = SubagentOrchestrator()

    async def run_validation():
        result = await orchestrator.run_subagent("spec-validator", {"spec_path": spec, "contract_path": contract})

        if result["status"] == "success":
            print("✅ Validation passed!")
            print(yaml.dump(result["output"], default_flow_style=False))
        else:
            print(f"❌ Validation failed: {result.get('error')}")

    asyncio.run(run_validation())


if __name__ == "__main__":
    cli()

