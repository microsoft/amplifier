# Microtask Patterns: Reusable Code Examples

## Introduction

This document provides concrete, copy-paste ready patterns for implementing microtask-driven AI operations using the Claude Code SDK. Each pattern is battle-tested and follows the Amplifier principles.

## Core Patterns

### 1. Basic Microtask Executor

**Purpose**: Execute a single focused AI task with timeout and error handling

```python
import asyncio
import json
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions
from typing import Dict, Any, Optional

class MicrotaskExecutor:
    """Execute focused AI tasks with 5-10 second timeout"""

    def __init__(self, task_type: str, timeout_seconds: int = 10):
        self.task_type = task_type
        self.timeout = timeout_seconds

    async def execute(self,
                     system_prompt: str,
                     user_prompt: str,
                     input_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute a single microtask with proper timeout and error handling

        Args:
            system_prompt: Defines the agent's role and expertise
            user_prompt: The specific task to perform
            input_data: Optional structured data to include

        Returns:
            Dict containing the result or error information
        """
        try:
            # Always use timeout to prevent hanging
            async with asyncio.timeout(self.timeout):
                async with ClaudeSDKClient(
                    options=ClaudeCodeOptions(
                        system_prompt=system_prompt,
                        max_turns=1,  # Single focused operation
                    )
                ) as client:
                    # Build prompt with optional data
                    full_prompt = user_prompt
                    if input_data:
                        full_prompt += f"\n\nData:\n{json.dumps(input_data, indent=2)}"

                    await client.query(full_prompt)

                    # Collect response
                    response_text = ""
                    async for message in client.receive_response():
                        if hasattr(message, 'content'):
                            for block in getattr(message, 'content', []):
                                if hasattr(block, 'text'):
                                    response_text += getattr(block, 'text', '')

                    return {
                        "success": True,
                        "task_type": self.task_type,
                        "result": response_text,
                        "duration": self.timeout
                    }

        except asyncio.TimeoutError:
            return {
                "success": False,
                "task_type": self.task_type,
                "error": f"Microtask timed out after {self.timeout} seconds",
                "fallback": self._get_fallback_result(input_data)
            }
        except Exception as e:
            return {
                "success": False,
                "task_type": self.task_type,
                "error": str(e),
                "fallback": self._get_fallback_result(input_data)
            }

    def _get_fallback_result(self, input_data: Optional[Dict]) -> Any:
        """Provide a degraded but useful result on failure"""
        # Override in subclasses for specific fallback logic
        return {"message": "Using fallback result due to AI unavailability"}

# Usage Example
async def analyze_code_quality():
    executor = MicrotaskExecutor("code_quality_check")

    result = await executor.execute(
        system_prompt="You are a code quality analyzer. Identify issues concisely.",
        user_prompt="Analyze this Python function for quality issues",
        input_data={"code": "def calc(x,y): return x+y"}
    )

    if result["success"]:
        print(f"Analysis: {result['result']}")
    else:
        print(f"Failed: {result['error']}")
        print(f"Fallback: {result['fallback']}")
```

### 2. Incremental Save Pattern

**Purpose**: Save progress after every atomic operation to enable recovery

```python
import json
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime

class IncrementalProcessor:
    """Process items with immediate saving after each operation"""

    def __init__(self, session_id: str, checkpoint_dir: str = ".amplifier/checkpoints"):
        self.session_id = session_id
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_file = self.checkpoint_dir / f"{session_id}.json"
        self.state = self._load_checkpoint()

    def _load_checkpoint(self) -> Dict:
        """Load existing checkpoint or create new one"""
        if self.checkpoint_file.exists():
            with open(self.checkpoint_file, 'r') as f:
                return json.load(f)

        return {
            "session_id": self.session_id,
            "created_at": datetime.now().isoformat(),
            "processed_items": {},
            "failed_items": {},
            "metadata": {}
        }

    def _save_checkpoint(self):
        """Save current state immediately"""
        self.state["updated_at"] = datetime.now().isoformat()

        # Atomic write with temporary file
        temp_file = self.checkpoint_file.with_suffix('.tmp')
        with open(temp_file, 'w') as f:
            json.dump(self.state, f, indent=2)

        # Atomic rename
        temp_file.rename(self.checkpoint_file)

    async def process_items(self, items: List[Any], processor_func) -> Dict:
        """Process items with immediate checkpoint after each"""
        results = {
            "processed": 0,
            "skipped": 0,
            "failed": 0,
            "results": []
        }

        for item_id, item in enumerate(items):
            # Skip already processed items
            if str(item_id) in self.state["processed_items"]:
                results["skipped"] += 1
                results["results"].append(self.state["processed_items"][str(item_id)])
                continue

            try:
                # Process the item
                result = await processor_func(item)

                # Save immediately - NEVER lose work
                self.state["processed_items"][str(item_id)] = result
                self._save_checkpoint()

                results["processed"] += 1
                results["results"].append(result)

            except Exception as e:
                # Save failure information
                self.state["failed_items"][str(item_id)] = {
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                self._save_checkpoint()

                results["failed"] += 1
                results["results"].append({"error": str(e)})

        return results

    def get_progress(self) -> Dict:
        """Get current processing progress"""
        return {
            "session_id": self.session_id,
            "processed": len(self.state["processed_items"]),
            "failed": len(self.state["failed_items"]),
            "last_update": self.state.get("updated_at", "never")
        }

# Usage Example
async def process_documents_with_recovery():
    processor = IncrementalProcessor("doc-analysis-001")

    documents = ["doc1.txt", "doc2.txt", "doc3.txt"]

    async def analyze_document(doc):
        # Your AI processing here
        executor = MicrotaskExecutor("document_analysis")
        result = await executor.execute(
            system_prompt="Analyze this document",
            user_prompt=f"Extract key points from {doc}"
        )
        return result

    # Process with automatic recovery
    results = await processor.process_items(documents, analyze_document)

    print(f"Processed: {results['processed']}")
    print(f"Skipped (already done): {results['skipped']}")
    print(f"Failed: {results['failed']}")

    # If interrupted, just run again - it will resume where it left off
```

### 3. Feedback Loop Pattern

**Purpose**: Iteratively improve results through verification and revision

```python
class FeedbackLoopProcessor:
    """Process with verification and improvement loops"""

    def __init__(self, max_iterations: int = 3, quality_threshold: float = 0.8):
        self.max_iterations = max_iterations
        self.quality_threshold = quality_threshold
        self.executor = MicrotaskExecutor("feedback_processor")

    async def process_with_feedback(self,
                                   item: Any,
                                   generator_prompt: str,
                                   verifier_prompt: str) -> Dict:
        """Process item with feedback loop until quality threshold met"""

        history = []

        for iteration in range(self.max_iterations):
            # Generate or improve
            if iteration == 0:
                prompt = generator_prompt
            else:
                # Include previous attempt and feedback
                prompt = f"""
                Previous attempt: {history[-1]['result']}
                Feedback: {history[-1]['feedback']}

                Please improve based on the feedback.
                """

            # Generate result
            generation = await self.executor.execute(
                system_prompt="You are a content generator",
                user_prompt=prompt,
                input_data={"item": item}
            )

            if not generation["success"]:
                return generation  # Return error

            # Verify quality
            verification = await self.executor.execute(
                system_prompt="You are a quality verifier. Rate quality 0-1 and provide feedback.",
                user_prompt=verifier_prompt,
                input_data={"content": generation["result"]}
            )

            # Parse quality score (simple extraction)
            quality_score = self._extract_score(verification.get("result", ""))

            history.append({
                "iteration": iteration,
                "result": generation["result"],
                "quality_score": quality_score,
                "feedback": verification.get("result", "")
            })

            # Check if quality threshold met
            if quality_score >= self.quality_threshold:
                return {
                    "success": True,
                    "final_result": generation["result"],
                    "iterations": iteration + 1,
                    "final_score": quality_score,
                    "history": history
                }

        # Max iterations reached
        best_result = max(history, key=lambda x: x["quality_score"])
        return {
            "success": True,
            "final_result": best_result["result"],
            "iterations": self.max_iterations,
            "final_score": best_result["quality_score"],
            "history": history,
            "note": "Max iterations reached"
        }

    def _extract_score(self, text: str) -> float:
        """Extract quality score from verifier response"""
        # Simple pattern matching - improve as needed
        import re
        match = re.search(r'(?:score|quality)[:=\s]*([0-9.]+)', text.lower())
        if match:
            try:
                return float(match.group(1))
            except:
                pass
        return 0.5  # Default middle score

# Usage Example
async def improve_slide_content():
    processor = FeedbackLoopProcessor(max_iterations=3, quality_threshold=0.85)

    slide = {"title": "Intro", "content": "stuff about things"}

    result = await processor.process_with_feedback(
        item=slide,
        generator_prompt="Improve this slide to be professional and engaging",
        verifier_prompt="Rate this slide 0-1 for quality. Check: clarity, engagement, professionalism"
    )

    print(f"Final result after {result['iterations']} iterations")
    print(f"Quality score: {result['final_score']}")
    print(f"Content: {result['final_result']}")
```

### 4. Parallel Microtask Pattern

**Purpose**: Execute independent microtasks in parallel for efficiency

```python
import asyncio
from typing import List, Dict, Any

class ParallelMicrotaskProcessor:
    """Execute multiple independent microtasks in parallel"""

    async def execute_parallel(self,
                              tasks: List[Dict[str, Any]],
                              max_concurrent: int = 5) -> List[Dict]:
        """
        Execute multiple microtasks in parallel with concurrency limit

        Args:
            tasks: List of task definitions with prompts and data
            max_concurrent: Maximum concurrent executions

        Returns:
            List of results in same order as tasks
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_with_semaphore(task_def: Dict) -> Dict:
            async with semaphore:
                executor = MicrotaskExecutor(task_def.get("task_type", "parallel_task"))
                return await executor.execute(
                    system_prompt=task_def["system_prompt"],
                    user_prompt=task_def["user_prompt"],
                    input_data=task_def.get("input_data")
                )

        # Execute all tasks in parallel
        results = await asyncio.gather(
            *[execute_with_semaphore(task) for task in tasks],
            return_exceptions=True
        )

        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "task_index": i,
                    "error": str(result)
                })
            else:
                result["task_index"] = i
                processed_results.append(result)

        return processed_results

# Usage Example
async def analyze_code_modules():
    processor = ParallelMicrotaskProcessor()

    # Define independent analysis tasks
    tasks = [
        {
            "task_type": "security_check",
            "system_prompt": "You are a security analyzer",
            "user_prompt": "Check for security issues",
            "input_data": {"code": "module1.py content"}
        },
        {
            "task_type": "performance_check",
            "system_prompt": "You are a performance analyzer",
            "user_prompt": "Check for performance issues",
            "input_data": {"code": "module2.py content"}
        },
        {
            "task_type": "style_check",
            "system_prompt": "You are a style analyzer",
            "user_prompt": "Check for style issues",
            "input_data": {"code": "module3.py content"}
        }
    ]

    # Execute in parallel
    results = await processor.execute_parallel(tasks, max_concurrent=3)

    for result in results:
        if result["success"]:
            print(f"Task {result['task_index']}: {result['result']}")
        else:
            print(f"Task {result['task_index']} failed: {result['error']}")
```

### 5. Metacognitive Analysis Pattern

**Purpose**: Analyze failures and improve strategy

```python
class MetacognitiveAnalyzer:
    """Analyze failures and suggest improvements"""

    def __init__(self):
        self.executor = MicrotaskExecutor("metacognitive_analysis")
        self.failure_history = []

    async def analyze_failure(self,
                             attempt: Dict,
                             result: Dict,
                             context: Dict) -> Dict:
        """Analyze why an attempt failed and suggest improvements"""

        # Add to history
        self.failure_history.append({
            "attempt": attempt,
            "result": result,
            "context": context,
            "timestamp": datetime.now().isoformat()
        })

        # Analyze with focused prompt
        analysis_prompt = f"""
        Analyze this failure and suggest improvements:

        Attempt: {json.dumps(attempt, indent=2)}
        Result: {json.dumps(result, indent=2)}
        Context: {json.dumps(context, indent=2)}
        Previous failures: {len(self.failure_history)}

        Identify:
        1. Root cause of failure
        2. Pattern in failures (if any)
        3. Specific improvement strategy
        4. Should we retry with adjustments or escalate?

        Respond in JSON format.
        """

        analysis = await self.executor.execute(
            system_prompt="""You are a metacognitive analyzer.
            Analyze failures and suggest strategic improvements.
            Always respond in valid JSON format.""",
            user_prompt=analysis_prompt
        )

        if analysis["success"]:
            try:
                strategy = json.loads(analysis["result"])
                return {
                    "success": True,
                    "strategy": strategy,
                    "should_retry": strategy.get("retry", False),
                    "adjustments": strategy.get("adjustments", {})
                }
            except json.JSONDecodeError:
                pass

        # Fallback strategy
        return {
            "success": False,
            "strategy": {"message": "Unable to analyze, using fallback"},
            "should_retry": len(self.failure_history) < 3,
            "adjustments": {}
        }

    async def execute_with_learning(self,
                                   operation,
                                   max_attempts: int = 3) -> Dict:
        """Execute operation with metacognitive learning"""

        for attempt_num in range(max_attempts):
            try:
                result = await operation()

                if result.get("success"):
                    return result

                # Analyze failure
                analysis = await self.analyze_failure(
                    attempt={"number": attempt_num, "operation": "task"},
                    result=result,
                    context={"max_attempts": max_attempts}
                )

                if not analysis["should_retry"]:
                    return {
                        "success": False,
                        "final_attempt": attempt_num,
                        "reason": "Metacognitive analysis suggests stopping",
                        "analysis": analysis
                    }

                # Apply adjustments for next attempt
                if analysis["adjustments"]:
                    operation = self._apply_adjustments(operation, analysis["adjustments"])

            except Exception as e:
                if attempt_num == max_attempts - 1:
                    raise

                # Analyze exception
                await self.analyze_failure(
                    attempt={"number": attempt_num},
                    result={"error": str(e)},
                    context={"exception": True}
                )

        return {
            "success": False,
            "reason": "Max attempts reached",
            "attempts": max_attempts
        }

    def _apply_adjustments(self, operation, adjustments: Dict):
        """Apply strategic adjustments to operation"""
        # This would be customized based on your specific needs
        # For example, modifying prompts, changing parameters, etc.
        return operation

# Usage Example
async def generate_with_learning():
    analyzer = MetacognitiveAnalyzer()

    async def generate_content():
        executor = MicrotaskExecutor("content_generation")
        return await executor.execute(
            system_prompt="Generate technical documentation",
            user_prompt="Create API documentation for a REST endpoint"
        )

    result = await analyzer.execute_with_learning(
        operation=generate_content,
        max_attempts=3
    )

    if result["success"]:
        print("Successfully generated content")
    else:
        print(f"Failed after learning: {result['reason']}")
```

### 6. Progressive Specialization Pattern

**Purpose**: Start with general solutions, progressively specialize based on needs

```python
class ProgressiveSpecializer:
    """Apply progressive specialization based on complexity"""

    def __init__(self):
        self.levels = {
            0: self._level_0_code_only,
            1: self._level_1_general_ai,
            2: self._level_2_specialized_ai,
            3: self._level_3_metacognitive
        }

    async def process_with_specialization(self, item: Any) -> Dict:
        """Process item with progressive specialization"""

        # Start with simplest approach
        for level in range(4):
            result = await self.levels[level](item)

            if result["success"] and result.get("quality", 0) >= 0.8:
                return {
                    "success": True,
                    "level": level,
                    "result": result["result"],
                    "quality": result.get("quality")
                }

        # All levels tried
        return {
            "success": False,
            "message": "All specialization levels exhausted",
            "last_result": result
        }

    async def _level_0_code_only(self, item: Any) -> Dict:
        """Pure code solution - instant, deterministic"""
        try:
            # Example: Simple pattern matching
            if isinstance(item, dict) and "title" in item:
                if item["title"].startswith("##"):
                    item["title"] = item["title"][2:].strip()
                    return {
                        "success": True,
                        "result": item,
                        "quality": 0.6  # Good enough for simple cases
                    }
        except:
            pass

        return {"success": False}

    async def _level_1_general_ai(self, item: Any) -> Dict:
        """General AI assistance"""
        executor = MicrotaskExecutor("general_ai")
        result = await executor.execute(
            system_prompt="You are a general assistant",
            user_prompt="Improve this content",
            input_data={"item": item}
        )

        if result["success"]:
            return {
                "success": True,
                "result": result["result"],
                "quality": 0.7
            }
        return {"success": False}

    async def _level_2_specialized_ai(self, item: Any) -> Dict:
        """Domain-specialized AI"""
        executor = MicrotaskExecutor("specialized_ai")
        result = await executor.execute(
            system_prompt="You are a specialized expert in this domain",
            user_prompt="Apply domain expertise to improve this",
            input_data={"item": item}
        )

        if result["success"]:
            return {
                "success": True,
                "result": result["result"],
                "quality": 0.85
            }
        return {"success": False}

    async def _level_3_metacognitive(self, item: Any) -> Dict:
        """Metacognitive approach"""
        analyzer = MetacognitiveAnalyzer()

        async def specialized_operation():
            return await self._level_2_specialized_ai(item)

        result = await analyzer.execute_with_learning(
            operation=specialized_operation,
            max_attempts=2
        )

        if result.get("success"):
            return {
                "success": True,
                "result": result,
                "quality": 0.95
            }
        return {"success": False}

# Usage Example
async def process_content_progressively():
    processor = ProgressiveSpecializer()

    items = [
        {"title": "## Simple Title", "content": "Basic content"},
        {"title": "Complex Analysis Required", "content": "..."},
        {"title": "Extremely nuanced case", "content": "..."}
    ]

    for item in items:
        result = await processor.process_with_specialization(item)
        print(f"Processed at level {result.get('level', 'failed')}")
        print(f"Quality: {result.get('quality', 0)}")
```

### 7. Re-entrant Pipeline Pattern

**Purpose**: Allow tools to process their own output iteratively

```python
class ReentrantPipeline:
    """Pipeline that can process its own output for improvement"""

    def __init__(self, max_revisions: int = 3):
        self.max_revisions = max_revisions
        self.executor = MicrotaskExecutor("reentrant_processor")
        self.processor = IncrementalProcessor("reentrant_session")

    async def process_with_revisions(self,
                                    initial_input: Any,
                                    process_prompt: str,
                                    review_prompt: str) -> Dict:
        """Process input with potential multiple revision passes"""

        current_version = initial_input
        revision_history = []

        for revision in range(self.max_revisions):
            # Process current version
            if revision == 0:
                prompt = process_prompt
            else:
                prompt = f"""
                Improve this based on the review feedback:
                Current version: {current_version}
                Feedback: {revision_history[-1]['feedback']}
                """

            processed = await self.executor.execute(
                system_prompt="You are a content processor",
                user_prompt=prompt,
                input_data={"input": current_version}
            )

            if not processed["success"]:
                break

            # Review the processed version
            review = await self.executor.execute(
                system_prompt="You are a quality reviewer",
                user_prompt=review_prompt,
                input_data={"content": processed["result"]}
            )

            # Save revision
            revision_data = {
                "revision": revision,
                "input": current_version,
                "output": processed["result"],
                "feedback": review.get("result", ""),
                "timestamp": datetime.now().isoformat()
            }
            revision_history.append(revision_data)

            # Check if good enough
            if "approved" in review.get("result", "").lower():
                return {
                    "success": True,
                    "final_output": processed["result"],
                    "revisions": revision + 1,
                    "history": revision_history
                }

            # Use output as input for next revision
            current_version = processed["result"]

        # Return best effort
        return {
            "success": True,
            "final_output": current_version,
            "revisions": self.max_revisions,
            "history": revision_history,
            "note": "Max revisions reached"
        }

# Usage Example
async def refine_documentation():
    pipeline = ReentrantPipeline(max_revisions=3)

    initial_doc = """
    API Documentation
    This API does things with stuff.
    """

    result = await pipeline.process_with_revisions(
        initial_input=initial_doc,
        process_prompt="Improve this API documentation to be professional and complete",
        review_prompt="Review this documentation. Is it clear, complete, and professional? Say 'approved' if yes."
    )

    print(f"Final version after {result['revisions']} revisions:")
    print(result['final_output'])
```

## Integration Patterns

### Complete Tool Builder Example

```python
class AmplifierToolBuilder:
    """Example integration of all patterns for tool building"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.incremental = IncrementalProcessor(session_id)
        self.parallel = ParallelMicrotaskProcessor()
        self.feedback = FeedbackLoopProcessor()
        self.metacognitive = MetacognitiveAnalyzer()
        self.progressive = ProgressiveSpecializer()
        self.reentrant = ReentrantPipeline()

    async def build_tool(self, specification: Dict) -> Dict:
        """Build a complete tool using all patterns"""

        # Phase 1: Analyze requirements (parallel microtasks)
        analysis_tasks = [
            {
                "task_type": "problem_analysis",
                "system_prompt": "Identify the core problem",
                "user_prompt": "What problem does this tool solve?",
                "input_data": specification
            },
            {
                "task_type": "architecture_design",
                "system_prompt": "Design the architecture",
                "user_prompt": "What architecture is needed?",
                "input_data": specification
            },
            {
                "task_type": "ai_split_analysis",
                "system_prompt": "Determine code vs AI split",
                "user_prompt": "What should code handle vs AI?",
                "input_data": specification
            }
        ]

        analysis_results = await self.parallel.execute_parallel(analysis_tasks)

        # Phase 2: Generate code with feedback loops
        modules = []
        for module_spec in specification.get("modules", []):
            module_code = await self.feedback.process_with_feedback(
                item=module_spec,
                generator_prompt="Generate Python code for this module",
                verifier_prompt="Rate code quality 0-1. Check: syntax, patterns, clarity"
            )
            modules.append(module_code)

        # Phase 3: Progressive improvement
        for i, module in enumerate(modules):
            improved = await self.progressive.process_with_specialization(module)
            modules[i] = improved

        # Phase 4: Re-entrant refinement
        final_tool = await self.reentrant.process_with_revisions(
            initial_input={"modules": modules},
            process_prompt="Integrate these modules into a complete tool",
            review_prompt="Is this a complete, working tool? Say 'approved' if yes."
        )

        # Phase 5: Metacognitive analysis if needed
        if not final_tool.get("success"):
            strategy = await self.metacognitive.analyze_failure(
                attempt={"specification": specification},
                result=final_tool,
                context={"phases_completed": 4}
            )

            if strategy["should_retry"]:
                # Apply learned adjustments and retry
                pass

        return final_tool

# Usage
async def create_new_tool():
    builder = AmplifierToolBuilder("tool-builder-session-001")

    specification = {
        "name": "api-tester",
        "description": "Test REST APIs automatically",
        "modules": [
            {"name": "auth", "purpose": "Handle authentication"},
            {"name": "requests", "purpose": "Make API calls"},
            {"name": "validator", "purpose": "Validate responses"}
        ]
    }

    tool = await builder.build_tool(specification)
    print(f"Tool built successfully: {tool.get('success')}")
```

## Best Practices

### 1. Always Use Timeouts
```python
# Good: Explicit timeout prevents hanging
async with asyncio.timeout(10):
    result = await client.query(prompt)

# Bad: Can hang indefinitely
result = await client.query(prompt)
```

### 2. Save Immediately
```python
# Good: Save after each operation
result = process(item)
save(result)

# Bad: Save only at end
results = []
for item in items:
    results.append(process(item))
save(results)  # Lose everything if crash here
```

### 3. Provide Fallbacks
```python
# Good: Graceful degradation
try:
    result = await ai_process(item)
except:
    result = simple_code_process(item)

# Bad: Complete failure
result = await ai_process(item)  # Fails completely if AI unavailable
```

### 4. Focus Microtasks
```python
# Good: Single, focused task
"Extract the main topic from this paragraph"

# Bad: Multiple tasks in one
"Extract the topic, summarize, translate, and rate quality"
```

### 5. Structure Responses
```python
# Good: Request structured output
"Respond with JSON: {score: 0-1, feedback: string}"

# Bad: Parse unstructured text
"Tell me what you think about this"
```

## Common Pitfalls

1. **Timeout Too Short**: Some operations need more than 5 seconds
2. **Not Saving State**: Losing work on interruption
3. **No Fallback Strategy**: Complete failure when AI unavailable
4. **Overly Complex Prompts**: Trying to do too much in one microtask
5. **Ignoring Failures**: Not learning from what doesn't work

## Testing Patterns

```python
import pytest
import asyncio

@pytest.mark.asyncio
async def test_microtask_timeout():
    """Test that microtasks respect timeout"""
    executor = MicrotaskExecutor("test", timeout_seconds=1)

    # This should timeout
    result = await executor.execute(
        system_prompt="Test",
        user_prompt="Count to 1000000 slowly"
    )

    assert not result["success"]
    assert "timeout" in result["error"].lower()

@pytest.mark.asyncio
async def test_incremental_recovery():
    """Test that processing resumes correctly"""
    processor = IncrementalProcessor("test-session")

    items = [1, 2, 3]
    processed = []

    async def process_item(item):
        if item == 2:
            raise Exception("Simulated failure")
        return {"processed": item}

    # First run - will fail on item 2
    result1 = await processor.process_items(items, process_item)
    assert result1["failed"] == 1

    # Second run - should skip item 1, retry item 2
    result2 = await processor.process_items(items, lambda x: {"processed": x})
    assert result2["skipped"] >= 1
```

## Conclusion

These patterns form the foundation of the Amplifier CLI Tool Builder. By combining them appropriately, you can build sophisticated tools that are:

- **Resilient**: Never lose work, recover from failures
- **Efficient**: Parallel execution, focused microtasks
- **Intelligent**: Progressive specialization, metacognitive learning
- **Reliable**: Timeouts, fallbacks, verification loops

Remember: Each pattern solves a specific problem. Use them individually or combine them as needed for your specific use case.

## Next Steps

Continue to [Developer Onboarding](05-DEVELOPER-ONBOARDING.md) for setup instructions.