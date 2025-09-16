"""Exemplar library of AI-integrated code patterns for Tool Builder.

This module provides working examples of Claude Code SDK integration patterns
that the Tool Builder can reference when generating new AI-powered tools.
"""

# Pattern 1: Basic AI text processing
AI_TEXT_PROCESSOR = '''
async def process_with_ai(text: str, operation: str) -> str:
    """Process text using Claude Code SDK.

    Args:
        text: Input text to process
        operation: The operation to perform (summarize, expand, analyze, etc.)

    Returns:
        Processed text result
    """
    try:
        from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions
    except ImportError:
        raise RuntimeError("Claude Code SDK not available. Install with: pip install claude-code-sdk")

    prompt = f"""Please {operation} the following text:

    {text}

    Provide only the {operation}d result, no additional commentary."""

    try:
        async with ClaudeSDKClient(
            options=ClaudeCodeOptions(
                system_prompt=f"You are a helpful assistant that performs text {operation}.",
                max_turns=1,
            )
        ) as client:
            await client.query(prompt)

            response = ""
            async for message in client.receive_response():
                if hasattr(message, "content"):
                    content = getattr(message, "content", [])
                    if isinstance(content, list):
                        for block in content:
                            if hasattr(block, "text"):
                                response += getattr(block, "text", "")

            return response.strip()
    except Exception as e:
        raise RuntimeError(f"AI processing failed: {e}")
'''

# Pattern 2: AI analysis with structured output
AI_STRUCTURED_ANALYZER = '''
async def analyze_with_structure(content: str, schema: dict) -> dict:
    """Analyze content and return structured data using AI.

    Args:
        content: Content to analyze
        schema: Expected output schema

    Returns:
        Structured analysis results
    """
    try:
        from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions
        import json
    except ImportError:
        raise RuntimeError("Required packages not available")

    schema_str = json.dumps(schema, indent=2)

    prompt = f"""Analyze the following content and provide results in JSON format matching this schema:

    Schema:
    {schema_str}

    Content:
    {content}

    Return ONLY valid JSON matching the schema, no additional text."""

    try:
        async with ClaudeSDKClient(
            options=ClaudeCodeOptions(
                system_prompt="You are an expert analyst that returns structured JSON data.",
                max_turns=1,
            )
        ) as client:
            await client.query(prompt)

            response = ""
            async for message in client.receive_response():
                if hasattr(message, "content"):
                    content = getattr(message, "content", [])
                    if isinstance(content, list):
                        for block in content:
                            if hasattr(block, "text"):
                                response += getattr(block, "text", "")

            # Clean markdown formatting if present
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]

            return json.loads(cleaned.strip())
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse AI response as JSON: {e}")
    except Exception as e:
        raise RuntimeError(f"AI analysis failed: {e}")
'''

# Pattern 3: Multi-stage AI pipeline
AI_PIPELINE_PROCESSOR = '''
class AIProcessingPipeline:
    """Multi-stage AI processing pipeline."""

    def __init__(self, stages: list[str]):
        """Initialize pipeline with processing stages.

        Args:
            stages: List of processing stage names
        """
        self.stages = stages
        self.results = {}

    async def run(self, input_data: str) -> dict:
        """Run all pipeline stages.

        Args:
            input_data: Initial input data

        Returns:
            Dictionary of results from all stages
        """
        current_input = input_data

        for stage in self.stages:
            print(f"Running stage: {stage}")
            result = await self._run_stage(stage, current_input)
            self.results[stage] = result
            current_input = result  # Feed forward to next stage

        return self.results

    async def _run_stage(self, stage_name: str, input_data: str) -> str:
        """Run a single pipeline stage.

        Args:
            stage_name: Name of the stage to run
            input_data: Input for this stage

        Returns:
            Output from the stage
        """
        try:
            from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions
        except ImportError:
            raise RuntimeError("Claude Code SDK not available")

        # Map stage names to specific prompts
        stage_prompts = {
            "summarize": "Create a concise summary of the following content:",
            "analyze": "Analyze the key themes and insights from:",
            "synthesize": "Synthesize the main points and create a coherent narrative from:",
            "expand": "Expand on the key ideas with additional context and examples from:",
            "extract": "Extract the most important information and key takeaways from:",
        }

        prompt_prefix = stage_prompts.get(stage_name, f"Process the following for {stage_name}:")
        prompt = f"""{prompt_prefix}

        {input_data}

        Provide only the {stage_name} result."""

        try:
            async with ClaudeSDKClient(
                options=ClaudeCodeOptions(
                    system_prompt=f"You are an expert at {stage_name} operations.",
                    max_turns=1,
                )
            ) as client:
                await client.query(prompt)

                response = ""
                async for message in client.receive_response():
                    if hasattr(message, "content"):
                        content = getattr(message, "content", [])
                        if isinstance(content, list):
                            for block in content:
                                if hasattr(block, "text"):
                                    response += getattr(block, "text", "")

                return response.strip()
        except Exception as e:
            raise RuntimeError(f"Stage '{stage_name}' failed: {e}")
'''

# Pattern 4: Batch AI processing with progress
AI_BATCH_PROCESSOR = '''
async def process_batch_with_ai(items: list, operation: str, callback=None) -> list:
    """Process multiple items with AI, reporting progress.

    Args:
        items: List of items to process
        operation: The AI operation to perform on each item
        callback: Optional progress callback function

    Returns:
        List of processed results
    """
    try:
        from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions
        import asyncio
    except ImportError:
        raise RuntimeError("Required packages not available")

    results = []
    total = len(items)

    for i, item in enumerate(items, 1):
        if callback:
            callback(f"Processing item {i}/{total}")

        # Process with rate limiting to avoid overwhelming the API
        if i > 1:
            await asyncio.sleep(1)  # Simple rate limiting

        prompt = f"""Please {operation} the following:

        {item}

        Provide only the result."""

        try:
            async with ClaudeSDKClient(
                options=ClaudeCodeOptions(
                    system_prompt=f"You perform {operation} operations concisely.",
                    max_turns=1,
                )
            ) as client:
                await client.query(prompt)

                response = ""
                async for message in client.receive_response():
                    if hasattr(message, "content"):
                        content = getattr(message, "content", [])
                        if isinstance(content, list):
                            for block in content:
                                if hasattr(block, "text"):
                                    response += getattr(block, "text", "")

                results.append(response.strip())
        except Exception as e:
            if callback:
                callback(f"Warning: Failed to process item {i}: {e}")
            results.append(None)  # Mark failed items

    if callback:
        callback(f"Completed processing {total} items")

    return results
'''

# Pattern 5: AI with retry and error handling
AI_ROBUST_PROCESSOR = '''
async def process_with_retry(text: str, operation: str, max_attempts: int = 3) -> str:
    """Process text with AI, including retry logic for failures.

    Args:
        text: Input text
        operation: Operation to perform
        max_attempts: Maximum retry attempts

    Returns:
        Processed result
    """
    try:
        from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions
        import asyncio
    except ImportError:
        raise RuntimeError("Required packages not available")

    last_error = None

    for attempt in range(max_attempts):
        try:
            if attempt > 0:
                print(f"Retry attempt {attempt + 1}/{max_attempts}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

            prompt = f"""{operation} the following text:

            {text}

            Provide a clear, well-formatted result."""

            if last_error:
                prompt += f"\n\nPrevious attempt failed with: {last_error}\nPlease correct and try again."

            async with ClaudeSDKClient(
                options=ClaudeCodeOptions(
                    system_prompt=f"You are an expert at {operation}.",
                    max_turns=1,
                )
            ) as client:
                await client.query(prompt)

                response = ""
                async for message in client.receive_response():
                    if hasattr(message, "content"):
                        content = getattr(message, "content", [])
                        if isinstance(content, list):
                            for block in content:
                                if hasattr(block, "text"):
                                    response += getattr(block, "text", "")

                result = response.strip()

                # Validate result
                if not result:
                    raise ValueError("Empty response from AI")

                return result

        except Exception as e:
            last_error = str(e)
            if attempt == max_attempts - 1:
                raise RuntimeError(f"Failed after {max_attempts} attempts: {last_error}")
'''

# Map of exemplar patterns
EXEMPLARS = {
    "text_processor": AI_TEXT_PROCESSOR,
    "structured_analyzer": AI_STRUCTURED_ANALYZER,
    "pipeline": AI_PIPELINE_PROCESSOR,
    "batch_processor": AI_BATCH_PROCESSOR,
    "robust_processor": AI_ROBUST_PROCESSOR,
}


def get_exemplar(pattern_type: str) -> str:
    """Get an exemplar pattern by type.

    Args:
        pattern_type: Type of pattern to retrieve

    Returns:
        The exemplar code pattern
    """
    return EXEMPLARS.get(pattern_type, "")


def get_best_exemplar_for_requirements(requirements: str) -> tuple[str, str]:
    """Determine the best exemplar pattern based on requirements.

    Args:
        requirements: Tool requirements text

    Returns:
        Tuple of (pattern_type, exemplar_code)
    """
    requirements_lower = requirements.lower()

    # Match requirements to patterns
    if "pipeline" in requirements_lower or "stages" in requirements_lower:
        return "pipeline", EXEMPLARS["pipeline"]
    if "batch" in requirements_lower or "multiple" in requirements_lower:
        return "batch_processor", EXEMPLARS["batch_processor"]
    if "json" in requirements_lower or "structured" in requirements_lower:
        return "structured_analyzer", EXEMPLARS["structured_analyzer"]
    if "retry" in requirements_lower or "robust" in requirements_lower:
        return "robust_processor", EXEMPLARS["robust_processor"]
    return "text_processor", EXEMPLARS["text_processor"]
