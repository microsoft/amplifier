# Amplifier Usage Guide

This guide covers installation, configuration, and usage of the Amplifier framework.

## Command Line Usage

### Three Ways to Run Tools

#### 1. Mode + Tool + Input (RECOMMENDED)
```bash
amplifier run mymode ultra_think "Explain quantum physics"
amplifier run demo blog_generator "The Future of AI"
```

#### 2. Direct Tool Invocation (if tool is a mode)
```bash
# This only works if "ultra_think" is registered as a mode
amplifier run ultra_think "Explain something"
```

#### 3. Interactive Mode
```bash
amplifier interactive --mode demo
amp> !ultra_think "Explain quantum physics"
amp> !blog_generator "The Future of AI"
amp> list-tools
amp> help
amp> exit
```

## Setting Up API Keys

The tools make real API calls. You need valid API keys:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Creating Custom Modes

### Option 1: Multiple --modules flags
```bash
amplifier init --name mymode \
  --modules amplifier_mod_llm_openai \
  --modules amplifier_mod_tool_ultra_think
```

### Option 2: Comma-separated
```bash
amplifier init --name mymode \
  --modules amplifier_mod_llm_openai,amplifier_mod_tool_ultra_think
```

## Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `amplifier list-modes` | Show all configured modes | `amplifier list-modes` |
| `amplifier list-modules` | Show available modules | `amplifier list-modules` |
| `amplifier init` | Create a new mode | `amplifier init --name test --modules ...` |
| `amplifier run <mode>` | Load a mode and show tools | `amplifier run demo` |
| `amplifier run <mode> <tool> <input>` | Run a specific tool | `amplifier run demo ultra_think "test"` |
| `amplifier interactive` | Start interactive shell | `amplifier interactive --mode demo` |

## How It Works

1. **Mode Loading**: `amplifier run demo`
   - Loads all modules configured for that mode
   - Registers tools and model providers with the kernel
   - Shows what's available

2. **Tool Execution**: `amplifier run demo ultra_think "question"`
   - Loads the demo mode
   - Finds the ultra_think tool
   - Passes your input to the tool
   - Tool makes API calls to AI providers
   - Returns and displays the result

3. **Interactive Mode**: `amplifier interactive --mode demo`
   - Loads the mode
   - Starts a shell where you can run tools with `!tool_name "input"`
   - Type `help` for commands

## Troubleshooting

### Tools hang or timeout
- **Cause**: Making real API calls
- **Fix**: Ensure API keys are set and valid
- **Test**: Try with a very simple query first

### "Warning: 'tool_name' is not a known mode or tool"
- **Cause**: Trying to run tool without loading a mode first
- **Fix**: Use `amplifier run <mode> <tool> <input>` format

### Module not found errors
- **Cause**: Module not installed in the environment
- **Fix**: Ensure all required modules are installed

## Available Tools

| Tool | Purpose | Example |
|------|---------|---------|
| `ultra_think` | Multi-perspective analysis | `amplifier run demo ultra_think "Explain AI ethics"` |
| `blog_generator` | Generate blog posts | `amplifier run demo blog_generator "Future of Technology"` |

## Available Model Providers

| Provider | Module | API Key Required |
|----------|--------|------------------|
| `openai` | amplifier_mod_llm_openai | OPENAI_API_KEY |
| `claude` | amplifier_mod_llm_claude | ANTHROPIC_API_KEY |

## Full Example Session

```bash
# 1. Set your API key
export OPENAI_API_KEY="your-key-here"

# 2. Create a custom mode
amplifier init --name myai \
  --modules amplifier_mod_llm_openai \
  --modules amplifier_mod_tool_ultra_think

# 3. Run a tool
amplifier run myai ultra_think "What is consciousness?"

# 4. Or use interactive mode
amplifier interactive --mode myai
amp> !ultra_think "Explain quantum computing"
amp> exit
```

## Next Steps

- Install the required modules for your use case
- Set up your API keys for the model providers you plan to use
- Create a mode with your preferred configuration
- Start building and running AI-powered tools