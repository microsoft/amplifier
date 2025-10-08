# Amplifier: AI Development Supercharged

## 🎯 What is Amplifier

Amplifier transforms AI coding assistants into force multipliers through specialized expertise and proven patterns. It is a supercharged AI development environment for your AI-first needs. Get immediate access to 20+ specialized agents, pre-loaded context, and workflows that deliver complex solutions with minimal guidance. 

### 📊 Feature Comparison Chart

| Traditional AI Setup | Amplifier Environment |
|----------------------|----------------------|
| ❌ Generic responses | ✅ **20+ Specialized agents** |
| ❌ Lost context each session | ✅ **Accumulated knowledge** |  
| ❌ Single solution path | ✅ **Parallel exploration** |
| ❌ Manual processes | ✅ **Automated workflows** |
| ❌ Surprise bills | ✅ **Real-time cost tracking** |


**[See how it can benefit you →](https://microsoft.github.io/amplifier)**

---

## 🚀 QuickStart 

### Prerequisites

```bash
python3 --version  # Need 3.11+
uv --version       # Need any version
node --version     # Need any version
pnpm --version     # Need any version
git --version      # Need any version
claude --version   # For now. To be removed in the future.
```

Missing something? [→ Quick Install Guide](#quick-install-guide)


### Setup

```bash
git clone https://github.com/microsoft/amplifier.git
cd amplifier
make configure
make install
source .venv/bin/activate  # Linux/Mac/WSL
```
> **Windows PowerShell:** `.venv\Scripts\Activate.ps1`

> **Verify installation:** `make check` and `make test`


### Start Claude Code


- **Option 1** - Work within the Amplifier project
    ```bash
    mkdir ai_working/quickstart-demo
    claude
    ```

    ```
    > I'm working in ai_working/quickstart-demo, and using the capabilities from amplifier.
    ```
    
- **Option 2** - Connect to a new project
    ```bash
    mkdir ~/quickstart-demo
    claude --add-dir ~/quickstart-demo
    ```

    ```
    > I'm working in ~/quickstart-demo, and using the capabilities from amplifier.
    ```

---

## ✨  Explore Features

**[View the complete guide →](https://microsoft.github.io/amplifier)**

Expand the different sections below to learn more about Amplifier feature capabilities. *Recommended to progress in order.*

<details>
<summary> Deploy Specialists</summary>

> ### 💡 Deploy Specialists
>*Amplifier includes 20+ specialized AI agents, each trained for specific tasks like architecture design, bug hunting, test coverage analysis, and modular code generation. These specialists work with expert-level precision, delivering focused results without the context confusion of general-purpose AI assistants.*
>
> **[Learn more about Specialists →](https://microsoft.github.io/amplifier)**
> 
> ### Try It Out
>```
>>  Use zen-architect to design a CLI tool that analyzes markdown files and reports: word 
>   count, heading count, link count, and reading time estimate
>```
> **What you'll see**: A clean design spec for the modular-builder to use.
> <br>
>```
>>  Use modular-builder to implement the markdown analyzer
>```
> **What you'll experience**: An automated workflow that implements the design.

</details>

<details>
<summary>Create a Scenario Tool</summary>

> ### 🎨 Create A Scenario Tool
>*Scenario tools are reusable CLI applications that combine Python code structure with AI intelligence for reliable, repeatable workflows. Create custom tools once, then run them anytime with simple make commands - perfect for standardizing complex multi-step processes.*
>
> **[Learn more about Scenario Tools →](https://microsoft.github.io/amplifier)**
>
> ### Try It Out
>```
>>  I need a @scenarios/ tool that creates multiple text-based files such as notes, specs,
>   decisions, etc., all based on the current material in the demo directory. These files will 
>   be used to showcase Amplifier's knowledge base capabilities. The files should be diverse 
>   enough to demonstrate what the knowledge commands can do, but small enough that knowledge-
>   update can complete within 2 minutes. Because this tool is for a demo, please keep the 
>   design compact enough that it can be implemented within 2 minutes.
>```
> **What you'll discover**: How simple it is to create a dependable tool
> <br>
>```
>>  Run the scenario tool to create content for the ~/quickstart-demo.
>```
> **What you'll see**: Content generated for the demo using the newly created Scenario.

</details>

<details>
<summary>Build a Knowledge Base</summary>

> ### 📚 Build a Knowledge Base
>*Amplifier's knowledge system automatically extracts concepts, relationships, and insights from your documents, organizing them into a queryable knowledge graph. This enables powerful semantic search, pattern recognition, and context-aware assistance across your entire project documentation.*
>
> **[Learn more about the Knowledge Base →](https://microsoft.github.io/amplifier)**
>
> ### Try It Out
>```
>>  make knowledge-update for AMPLIFIER_CONTENT_DIRS="~/quickstart-demo"
>```
> **What you'll experience**: Knowledge classification and extraction at work on the new content. *This step can take ~10-15 minutes.*
> <br>
>```
>>  make knowledge-stats
>
>>  make knowledge-graph-viz
>```
> **What you'll see**: Statistics and a visualization of the content.

</details>

<details>
<summary>Context Management</summary>

> ### 🧠 Context Management
>*Amplifier's context management intelligently compresses long conversation sessions, reducing token usage while preserving the essential information you need. All conversation history is automatically saved as searchable transcripts that you can restore anytime, ensuring no valuable context is ever lost.*
>
>**[Learn more about Context Management →](https://microsoft.github.io/amplifier)**
> 
> ### Try It Out
>```
>>  /compact
>```
> **What you'll see**: A summary is saved but the full history is cleared.
> <br>
>```
>>  What are the available transcripts?
>
>>  /transcript
>```
> **What you'll discover**: Even compacted conversations can be restored for context.
>
</details>

---

## Quick Install Guide

<details>
<summary>Click to expand installation instructions</summary>

### Mac

```bash
brew install python3 node git pnpm uv
npm install -g @anthropic-ai/claude-cli
```

### Ubuntu/Debian/WSL

```bash
# System packages
sudo apt update && sudo apt install -y python3 python3-pip nodejs npm git

# pnpm
npm install -g pnpm
pnpm setup && source ~/.bashrc

# uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Claude Code CLI
npm install -g @anthropic-ai/claude-cli
```

### Windows

1. Install [WSL2](https://learn.microsoft.com/windows/wsl/install)
2. Run Ubuntu commands above inside WSL

### Manual Downloads

- [Python](https://python.org/downloads) (3.11 or newer)
- [Node.js](https://nodejs.org) (any recent version)
- [pnpm](https://pnpm.io/installation) (package manager)
- [Git](https://git-scm.com) (any version)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python package manager)
- [Claude Code CLI](https://github.com/anthropics/claude-code) (AI assistant)

</details>

---

*Experience the interactive documentation at [microsoft.github.io/amplifier](https://microsoft.github.io/amplifier)*