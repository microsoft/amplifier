#!/usr/bin/env python3
"""
Test script for the parallel pipeline executor.

Creates a test pipeline with stages that can run in parallel and demonstrates
the speedup achieved through concurrent execution.
"""

import asyncio
from pathlib import Path

from amplifier_microtask.parallel_executor import ParallelPipelineExecutor
from amplifier_microtask.stages import Stage, PipelineDefinition
from amplifier_microtask.orchestrator import Task


def create_test_pipeline() -> PipelineDefinition:
    """Create a test pipeline with parallelizable stages."""

    # Stage 1: Initial analysis (no dependencies)
    stage1 = Stage(
        id="initial_analysis",
        name="Initial Analysis",
        description="Analyze the problem space",
        tasks=[
            Task(
                id="analyze",
                prompt="Analyze this problem: How to build a simple web scraper. List 3 key requirements.",
                context_keys=[],
                save_key="initial_analysis",
                timeout=30,
            )
        ],
        depends_on=[],
        outputs=["initial_analysis"],
    )

    # Stage 2A: Technical design (depends on stage 1)
    stage2a = Stage(
        id="technical_design",
        name="Technical Design",
        description="Create technical design",
        tasks=[
            Task(
                id="design",
                prompt="Based on {initial_analysis}, create a technical design with 3 components.",
                context_keys=["initial_analysis"],
                save_key="technical_design",
                timeout=30,
            )
        ],
        depends_on=["initial_analysis"],
        outputs=["technical_design"],
    )

    # Stage 2B: Risk assessment (depends on stage 1, can run parallel with 2A)
    stage2b = Stage(
        id="risk_assessment",
        name="Risk Assessment",
        description="Identify risks",
        tasks=[
            Task(
                id="risks",
                prompt="Based on {initial_analysis}, identify 3 technical risks.",
                context_keys=["initial_analysis"],
                save_key="risk_assessment",
                timeout=30,
            )
        ],
        depends_on=["initial_analysis"],
        outputs=["risk_assessment"],
    )

    # Stage 2C: Tool selection (depends on stage 1, can run parallel with 2A and 2B)
    stage2c = Stage(
        id="tool_selection",
        name="Tool Selection",
        description="Select tools and libraries",
        tasks=[
            Task(
                id="tools",
                prompt="Based on {initial_analysis}, recommend 3 Python libraries for web scraping.",
                context_keys=["initial_analysis"],
                save_key="tool_selection",
                timeout=30,
            )
        ],
        depends_on=["initial_analysis"],
        outputs=["tool_selection"],
    )

    # Stage 3: Implementation plan (depends on stages 2A and 2B)
    stage3 = Stage(
        id="implementation_plan",
        name="Implementation Plan",
        description="Create implementation plan",
        tasks=[
            Task(
                id="plan",
                prompt="Based on {technical_design} and {risk_assessment}, create a 3-step implementation plan.",
                context_keys=["technical_design", "risk_assessment"],
                save_key="implementation_plan",
                timeout=30,
            )
        ],
        depends_on=["technical_design", "risk_assessment"],
        outputs=["implementation_plan"],
    )

    return PipelineDefinition(
        name="Parallel Test Pipeline",
        description="Test pipeline with stages that can run in parallel",
        stages=[stage1, stage2a, stage2b, stage2c, stage3],
        initial_data={},
    )


async def test_parallel_execution():
    """Test the parallel pipeline executor."""

    # Create workspace
    workspace = Path("test_workspace")
    workspace.mkdir(exist_ok=True)

    # Create executor
    executor = ParallelPipelineExecutor(workspace)

    # Create test pipeline
    pipeline = create_test_pipeline()

    print("🧪 Testing Parallel Pipeline Executor")
    print("=" * 50)

    # Find parallel groups
    groups = executor.find_parallel_stages(pipeline)

    print("\n📊 Pipeline Analysis:")
    print(f"   Total stages: {len(pipeline.stages)}")
    print(f"   Parallel groups: {len(groups)}")

    for i, group in enumerate(groups):
        stage_names = [s.name for s in group.stages]
        print(f"   Level {i}: {', '.join(stage_names)} ({len(stage_names)} stages)")

    print("\n" + "=" * 50)

    # Execute pipeline
    try:
        status = await executor.execute_pipeline_async(pipeline)

        print("\n✅ Pipeline completed successfully!")
        print(f"   Total time: {status.total_duration_seconds:.1f}s")

        # Calculate what sequential time would have been
        sequential_time = sum(r.duration_seconds for r in status.stage_results.values())
        print(f"   Sequential time (estimated): {sequential_time:.1f}s")

        if sequential_time > status.total_duration_seconds:
            speedup = sequential_time / status.total_duration_seconds
            time_saved = sequential_time - status.total_duration_seconds
            print(f"   🚀 Speedup: {speedup:.1f}x")
            print(f"   ⏱️  Time saved: {time_saved:.1f}s")

        return True

    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        return False


def main():
    """Main test entry point."""
    success = asyncio.run(test_parallel_execution())
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
