#!/usr/bin/env python3
"""
Demo script for UltraThink Tool

Shows how to use the UltraThink workflow for deep analysis.
"""

import asyncio
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock

# For demonstration, we'll mock the kernel and model
# In real usage, you'd have an actual AmplifierKernel instance


class MockModel:
    """Mock model for demonstration."""

    async def generate(self, prompt: str) -> str:
        """Simulate LLM response based on prompt content."""
        await asyncio.sleep(0.5)  # Simulate API delay

        if "philosophical" in prompt.lower():
            return (
                "From a philosophical standpoint, this represents a fundamental "
                "shift in how we understand human-machine collaboration. The implications "
                "touch on questions of agency, creativity, and the nature of intelligence itself."
            )
        elif "practical" in prompt.lower():
            return (
                "Practically speaking, implementation requires robust infrastructure, "
                "clear governance frameworks, and careful consideration of resource allocation. "
                "Success metrics should focus on measurable outcomes and user adoption rates."
            )
        elif "critique" in prompt.lower():
            return (
                "Critical analysis reveals several potential risks: dependency on technology, "
                "loss of human skills, privacy concerns, and the possibility of reinforcing "
                "existing biases. Mitigation strategies must be proactive rather than reactive."
            )
        elif "creative" in prompt.lower():
            return (
                "From a creative perspective, this opens unprecedented opportunities for "
                "hybrid intelligence systems, novel forms of expression, and breakthrough "
                "innovations at the intersection of human intuition and machine processing."
            )
        elif "systems" in prompt.lower():
            return (
                "Systems analysis shows cascading effects across multiple domains: "
                "economic restructuring, educational transformation, social dynamics shifts, "
                "and emergent behaviors that may be difficult to predict but crucial to monitor."
            )
        elif "Given these multiple perspectives" in prompt:
            return (
                "## Synthesis: The Future of AI Assistants\n\n"
                "### Key Insights\n"
                "- AI assistants represent a paradigm shift in human-machine collaboration\n"
                "- Success requires balancing innovation with risk mitigation\n"
                "- Implementation must consider technical, social, and ethical dimensions\n\n"
                "### Tensions and Trade-offs\n"
                "- Efficiency gains vs. human skill preservation\n"
                "- Automation benefits vs. privacy concerns\n"
                "- Innovation speed vs. governance frameworks\n\n"
                "### Recommendations\n"
                "1. Develop adaptive governance that evolves with the technology\n"
                "2. Invest in human-AI collaboration training programs\n"
                "3. Create transparent metrics for measuring impact\n"
                "4. Build in ethical considerations from the ground up\n\n"
                "### Critical Takeaway\n"
                "The future of AI assistants isn't about replacement but augmentation. "
                "Success lies in designing systems that amplify human capabilities while "
                "preserving human agency and values."
            )
        else:
            return f"Analysis complete for: {prompt[:50]}..."


async def demo_ultra_think():
    """Demonstrate the UltraThink workflow."""
    print("=" * 60)
    print("UltraThink Workflow Demonstration")
    print("=" * 60)
    print()

    # Import after the mock setup
    import sys
    import os

    # Add parent directory to path to import our module
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from amplifier_mod_tool_ultra_think import UltraThinkTool

    # Create mock kernel
    mock_kernel = Mock()
    mock_model = MockModel()
    mock_kernel.model_providers = {"openai": mock_model}
    mock_kernel.logger = Mock()

    # Initialize the tool
    tool = UltraThinkTool(mock_kernel)

    # Example 1: Basic usage
    print("Example 1: Analyzing 'The Future of AI Assistants'")
    print("-" * 40)

    start_time = asyncio.get_event_loop().time()
    result = await tool.run("The Future of AI Assistants")
    end_time = asyncio.get_event_loop().time()

    print(result)
    print()
    print(f"⏱️  Analysis completed in {end_time - start_time:.2f} seconds")
    print("   (Note: 5 perspectives ran in parallel, not sequentially)")
    print()

    # Example 2: Custom perspectives
    print("Example 2: Using Custom Perspectives")
    print("-" * 40)

    custom_result = await tool.execute(
        topic="Sustainable Software Development",
        perspectives=[
            "Environmental impact of computing resources",
            "Long-term maintainability and technical debt",
            "Developer well-being and work-life balance",
        ],
    )

    if custom_result["success"]:
        print(f"✅ Analysis complete for: {custom_result['topic']}")
        print(f"📊 Perspectives analyzed: {custom_result['perspectives_used']}")
        print("\nResult preview:")
        print(custom_result["result"][:500] + "...")
    else:
        print(f"❌ Analysis failed: {custom_result['error']}")

    print()
    print("=" * 60)
    print("Demo Complete")
    print("=" * 60)


async def demo_parallel_performance():
    """Demonstrate the performance benefits of parallel execution."""
    print("\n" + "=" * 60)
    print("Parallel Performance Demonstration")
    print("=" * 60)
    print()

    import sys
    import os

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from amplifier_mod_tool_ultra_think import UltraThinkTool

    # Create mock kernel with timing
    mock_kernel = Mock()

    call_log = []

    async def timed_generate(prompt: str) -> str:
        """Track when each call happens."""
        start = asyncio.get_event_loop().time()
        call_log.append(("start", start, prompt[:30]))
        await asyncio.sleep(1)  # Simulate 1 second API call
        end = asyncio.get_event_loop().time()
        call_log.append(("end", end, prompt[:30]))
        return f"Response for: {prompt[:30]}..."

    mock_model = Mock()
    mock_model.generate = timed_generate
    mock_kernel.model_providers = {"openai": mock_model}

    tool = UltraThinkTool(mock_kernel)

    print("Running 5 perspectives + 1 synthesis...")
    print("Each API call takes ~1 second")
    print()

    overall_start = asyncio.get_event_loop().time()
    await tool.run("Performance test topic")
    overall_end = asyncio.get_event_loop().time()

    print("Timeline of API calls:")
    print("-" * 40)

    base_time = call_log[0][1]
    for event_type, timestamp, prompt_preview in call_log:
        relative_time = timestamp - base_time
        marker = "▶" if event_type == "start" else "■"
        print(f"{marker} {relative_time:5.2f}s - {event_type:5} - {prompt_preview}...")

    print("-" * 40)
    print(f"\n📊 Total execution time: {overall_end - overall_start:.2f} seconds")
    print(f"   Sequential would take: ~6.0 seconds")
    print(f"   Parallel speedup: ~{6.0/(overall_end - overall_start):.1f}x faster")


if __name__ == "__main__":
    # Run the demos
    asyncio.run(demo_ultra_think())
    asyncio.run(demo_parallel_performance())