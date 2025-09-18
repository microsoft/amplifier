# Core Improvement: Settings Pass-through

> **Source Branch**: `generator-from-code-cdx`
> **Created**: 2025-09-18
> **Status**: Phase 1 COMPLETED ✅ (items 1-3) - Phase 2+ specification
> **Context**: Core toolkit improvement specifications from module_generator analysis


## Priority: 🟢 Valuable (P3)

## Problem Statement

The toolkit doesn't support passing custom settings to the Claude SDK, limiting advanced configuration options. The module generator allows settings pass-through for fine-tuning behavior.

## Current Implementation

```python
# No settings parameter exposed
ClaudeCodeOptions(
    system_prompt=self.options.system_prompt,
    max_turns=self.options.max_turns,
    # No settings parameter
)
```

## Proposed Solution

### Add Settings Support

```python
# ccsdk_toolkit/core/models.py
class SessionOptions(BaseModel):
    # Existing fields...

    settings: dict[str, Any] | None = Field(
        default=None,
        description="Custom settings to pass to Claude SDK"
    )

    # Convenience settings that map to common settings
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    top_p: float | None = Field(default=None, ge=0.0, le=1.0)
    top_k: int | None = Field(default=None, ge=1)

    def get_effective_settings(self) -> dict[str, Any] | None:
        """Combine explicit settings with convenience fields."""
        if not any([self.settings, self.temperature, self.top_p, self.top_k]):
            return None

        effective = self.settings.copy() if self.settings else {}

        # Add convenience settings if not already in settings
        if self.temperature is not None and "temperature" not in effective:
            effective["temperature"] = self.temperature
        if self.top_p is not None and "top_p" not in effective:
            effective["top_p"] = self.top_p
        if self.top_k is not None and "top_k" not in effective:
            effective["top_k"] = self.top_k

        return effective if effective else None
```

### Pass Settings to SDK

```python
# ccsdk_toolkit/core/session.py
async def __aenter__(self):
    options_dict = {
        "system_prompt": self.options.system_prompt,
        "max_turns": self.options.max_turns,
    }

    # Add settings if provided
    effective_settings = self.options.get_effective_settings()
    if effective_settings:
        options_dict["settings"] = effective_settings

    self.client = ClaudeSDKClient(
        options=ClaudeCodeOptions(**options_dict)
    )
```

## Usage Patterns

### Pattern 1: Temperature Control

```python
# High temperature for creative tasks
creative_options = SessionOptions(
    system_prompt="Generate creative solutions...",
    temperature=1.5,  # More randomness
    max_turns=10
)

# Low temperature for precise tasks
precise_options = SessionOptions(
    system_prompt="Implement exactly as specified...",
    temperature=0.2,  # More deterministic
    max_turns=40
)
```

### Pattern 2: Advanced Settings

```python
# Custom settings for specific behavior
options = SessionOptions(
    settings={
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 50,
        "frequency_penalty": 0.5,
        "presence_penalty": 0.3,
        "stop_sequences": ["END", "DONE"],
        # Any other SDK-supported settings
    }
)
```

### Pattern 3: Settings Presets

```python
class SettingsPresets:
    """Common settings configurations."""

    CREATIVE = {
        "temperature": 1.2,
        "top_p": 0.95,
        "frequency_penalty": 0.8
    }

    PRECISE = {
        "temperature": 0.3,
        "top_p": 0.85,
        "frequency_penalty": 0.0
    }

    BALANCED = {
        "temperature": 0.7,
        "top_p": 0.9,
        "frequency_penalty": 0.3
    }

    CODE_GENERATION = {
        "temperature": 0.4,
        "top_p": 0.9,
        "stop_sequences": ["```\n", "# End"]
    }

# Use preset
options = SessionOptions(
    settings=SettingsPresets.CODE_GENERATION,
    system_prompt="Generate Python code..."
)
```

### Pattern 4: Dynamic Settings

```python
def get_settings_for_complexity(complexity: int) -> dict[str, Any]:
    """Adjust settings based on task complexity."""
    if complexity < 3:
        return SettingsPresets.PRECISE
    elif complexity < 7:
        return SettingsPresets.BALANCED
    else:
        return SettingsPresets.CREATIVE

# Adapt to task
task_complexity = analyze_task_complexity(prompt)
options = SessionOptions(
    settings=get_settings_for_complexity(task_complexity)
)
```

## Module Generator Pattern

```python
# sdk_client.py
async with ClaudeSDKClient(
    options=ClaudeCodeOptions(
        system_prompt=_default_system_prompt(),
        cwd=cwd,
        add_dirs=effective_add_dirs,
        settings=settings,  # Pass-through parameter
        # ...
    )
) as client:
```

## Testing Requirements

- Test settings are passed correctly to SDK
- Verify convenience fields override settings
- Test that invalid settings are handled gracefully
- Ensure settings affect behavior appropriately

## Migration Impact

- No settings by default (current behavior)
- Opt-in configuration for advanced users
- Examples should demonstrate common patterns

## Success Criteria

- Advanced users can fine-tune behavior
- Common settings easily accessible
- Presets simplify configuration
- Settings documented clearly

## Philosophy Note

Settings provide fine-grained control without complicating the simple use case. Most users won't need settings, but power users can access the full capability of the underlying SDK.