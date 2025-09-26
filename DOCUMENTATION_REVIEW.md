# Amplifier Documentation Review

## Executive Summary

After reviewing the Amplifier documentation following the unified CLI implementation, I've identified several areas that need improvement for clarity, completeness, and user-friendliness. The documentation has some inconsistencies and outdated information that should be addressed.

## Key Issues Found

### 1. **Installation Documentation Confusion** ⚠️

#### README.md Issues:
- **Line 54**: States "Global `amplifier` command for use anywhere on your system" but the actual installation process doesn't automatically install it globally
- **Line 84-94**: The examples show `amplifier` being used directly, but users need to run `make install-global` separately (not mentioned in main install steps)
- **Line 177-195**: Troubleshooting section for global access appears, but users won't know they need it until they hit the problem

#### Recommended Fix:
The README should clarify that `make install` sets up the environment but `make install-global` is needed for the global command. Or better yet, `make install` should include the global installation automatically.

### 2. **Outdated Transition Documentation** 📝

#### docs/INSTALLATION_TRANSITION.md Issues:
- **Line 43-53**: Documents `amplifier claude` command which doesn't exist in current implementation
- **Line 17**: References `make install` doing everything, but it doesn't install global command
- **Lines 99-115**: Migration steps reference old files that may not exist anymore

### 3. **Missing Core Documentation** ❌

#### What's Missing:
1. **API Documentation**: No docstrings in key modules:
   - `amplifier/cli.py` - Commands lack detailed docstrings
   - `amplifier/claude_launcher.py` - Functions documented but not comprehensive

2. **Architecture Documentation**: No explanation of how the unified CLI works internally

3. **Developer Guide**: No guide for extending the CLI with new commands

4. **Changelog**: No CHANGELOG.md to track version changes

### 4. **Inconsistent Usage Examples** 🔄

#### README.md Inconsistencies:
- **Lines 104-113**: Shows simple `amplifier` usage
- **Lines 129-145**: Shows alternative methods that may confuse users
- No clear explanation of when to use which method

### 5. **Incomplete Command Documentation** 📚

#### CLI Help Text Issues:
- Commands like `extract`, `synthesize`, `run` have stub implementations but are shown in help
- No indication which commands are fully functional vs. planned
- Missing detailed examples for each command

## Recommended Improvements

### Priority 1: Fix Installation Process & Documentation

**Option A: Make `make install` complete**
```makefile
install: ## Install everything including global command
	@echo "📦 Installing Python dependencies..."
	uv sync --group dev
	@echo "🌐 Installing Claude CLI globally..."
	# ... existing Claude CLI installation ...
	@echo "🔧 Installing global amplifier command..."
	@$(MAKE) install-global
```

**Option B: Update README to be explicit**
```markdown
2. **Install Amplifier**:
   ```bash
   make install          # Install dependencies
   make install-global   # Install global command (recommended)
   ```
```

### Priority 2: Create Missing Documentation

#### 1. Add CHANGELOG.md:
```markdown
# Changelog

## [0.2.0] - 2025-01-25

### Added
- Unified `amplifier` CLI command for all functionality
- Automatic project detection (Amplifier vs external)
- Global installation via `make install-global`

### Changed
- Simplified installation process
- Removed need for separate wrapper scripts

### Deprecated
- `amplifier-unified` command (use `amplifier` instead)
```

#### 2. Improve CLI Docstrings:
```python
@cli.command()
def extract(...):
    """Extract knowledge from documents.

    This command processes documents to extract concepts, relationships,
    and insights for the knowledge base.

    Examples:
        amplifier extract                  # Process default content directories
        amplifier extract ~/docs           # Process specific directory
        amplifier extract --force ~/docs  # Reprocess all documents

    Note: Requires Claude CLI to be installed for full functionality.
    """
```

#### 3. Add Developer Documentation:
Create `docs/CLI_DEVELOPMENT.md`:
```markdown
# Amplifier CLI Development Guide

## Architecture
The Amplifier CLI is built using Click framework...

## Adding New Commands
1. Create a new function in `amplifier/cli.py`
2. Decorate with `@cli.command()`
3. Add comprehensive docstring
4. Implement functionality or delegate to modules
```

### Priority 3: Update Existing Documentation

#### README.md Updates:

1. **Clarify Installation** (Line 45-56):
```markdown
2. **Run the installer**:

   ```bash
   make install          # Core installation
   make install-global   # Global command (recommended)
   ```

   The first command installs:
   - Python dependencies and virtual environment
   - Claude CLI globally via pnpm

   The second command adds:
   - Global `amplifier` command accessible from anywhere
```

2. **Simplify Usage Section** (Lines 98-145):
```markdown
## 📖 How to Use Amplifier

### Quick Start

After installation, use Amplifier from anywhere:

```bash
amplifier                    # Launch in current directory
amplifier ~/my-project       # Launch in specific project
amplifier --help            # See all available commands
```

### Common Commands

**Launch Claude with AI agents:**
```bash
amplifier               # Current directory
amplifier ~/project     # Specific project
```

**Check your setup:**
```bash
amplifier doctor        # Diagnose environment
amplifier smoke         # Run validation tests
```

**Knowledge extraction (in development):**
```bash
amplifier extract       # Extract from documents
amplifier synthesize    # Generate insights
```
```

3. **Update Troubleshooting** (Lines 173-195):
```markdown
### Troubleshooting

**"Command not found: amplifier"**

Run the global installation:
```bash
cd ~/dev/amplifier
make install-global
```

Then add ~/bin to PATH if needed:
```bash
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc  # or ~/.bashrc
source ~/.zshrc
```
```

### Priority 4: Remove Outdated Documentation

1. **Update or remove** `docs/INSTALLATION_TRANSITION.md` - it references non-existent `amplifier claude` command
2. **Clean up** alternative installation methods that may confuse users
3. **Remove or mark** non-functional commands in CLI help

### Priority 5: Add User-Friendly Features

#### 1. Add First-Run Experience:
```python
def first_run_check():
    """Check if this is first run and provide guidance."""
    if not Path("~/.amplifier/config").exists():
        click.echo("Welcome to Amplifier! 🚀")
        click.echo("Run 'amplifier doctor' to check your setup.")
```

#### 2. Add Command Status Indicators:
```python
@cli.command()
def extract():
    """Extract knowledge from documents. [BETA]"""
    click.echo("⚠️  This command is in beta...")
```

#### 3. Improve Error Messages:
```python
if not claude_path:
    raise RuntimeError(
        "❌ Claude CLI not found!\n\n"
        "To fix this, run:\n"
        "  npm install -g @anthropic-ai/claude-code\n\n"
        "Or check your installation with:\n"
        "  amplifier doctor"
    )
```

## Testing Recommendations

### Documentation Validation Tests:
1. Test each command example in README works
2. Verify installation steps on fresh system
3. Check all links and references are valid
4. Ensure help text matches actual functionality

### User Journey Tests:
1. New user installation flow
2. First-time usage experience
3. Troubleshooting common issues
4. Upgrade from old installation

## Summary

The documentation needs updates to reflect the current unified CLI implementation. Key priorities are:

1. **Fix installation confusion** - Either make `make install` complete or clearly document two-step process
2. **Remove outdated content** - Update transition guide and remove references to old commands
3. **Add missing docs** - Changelog, API docs, developer guide
4. **Improve clarity** - Simplify usage examples, add status indicators for beta features
5. **Enhance user experience** - Better error messages, first-run guidance

These improvements will significantly reduce user friction and support tickets while making Amplifier more approachable for new users.