# Workspace Makefile

# Include the recursive system
repo_root = $(shell git rev-parse --show-toplevel)
include $(repo_root)/tools/makefiles/recursive.mk

# Helper function to list discovered projects
define list_projects
	@echo "Projects discovered: $(words $(MAKE_DIRS))"
	@for dir in $(MAKE_DIRS); do echo "  - $$dir"; done
	@echo ""
endef

# Default goal - shows simple list
.DEFAULT_GOAL := default

# Main targets
.PHONY: default help install dev test check

default: ## Show essential commands
	@echo ""
	@echo "Quick Start:"
	@echo "  make install         Install all dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make check          Format, lint, and type-check all code"
	@echo "  make test           Run all tests"
	@echo "  make smoke-test     Run quick smoke tests (< 2 minutes)"
	@echo "  make worktree NAME   Create git worktree with .data copy"
	@echo "  make worktree-list   List all git worktrees"
	@echo "  make worktree-stash NAME  Hide worktree (keeps directory)"
	@echo "  make worktree-adopt BRANCH  Create worktree from remote"
	@echo "  make worktree-rm NAME  Remove worktree and delete branch"
	@echo ""
	@echo "AI Context:"
	@echo "  make ai-context-files Build AI context documentation"
	@echo ""
	@echo "Blog Writing:"
	@echo "  make blog-write      Create a blog post from your ideas"
	@echo ""
	@echo "Transcription:"
	@echo "  make transcribe      Transcribe audio/video files or YouTube URLs"
	@echo "  make transcribe-index Generate index of all transcripts"
	@echo ""
	@echo "Article Illustration:"
	@echo "  make illustrate      Generate AI illustrations for article"
	@echo ""
	@echo "Web to Markdown:"
	@echo "  make web-to-md       Convert web pages to markdown"
	@echo ""
	@echo "Other:"
	@echo "  make clean          Clean build artifacts"
	@echo "  make help           Show ALL available commands"
	@echo ""

help: ## Show ALL available commands
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "                ALL AVAILABLE COMMANDS"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "QUICK START:"
	@echo "  make install         Install all dependencies"
	@echo ""
	@echo "CONTENT:"
	@echo "  make content-scan    Scan configured content directories"
	@echo "  make content-search q=\"...\"  Search content"
	@echo "  make content-status  Show content statistics"
	@echo ""
	@echo "DEVELOPMENT:"
	@echo "  make check           Format, lint, and type-check code"
	@echo "  make test            Run all tests (alias: pytest)"
	@echo "  make smoke-test      Run quick smoke tests (< 2 minutes)"
	@echo "  make worktree NAME   Create git worktree with .data copy"
	@echo "  make worktree-list   List all git worktrees"
	@echo "  make worktree-stash NAME  Hide worktree (keeps directory)"
	@echo "  make worktree-adopt BRANCH  Create worktree from remote"
	@echo "  make worktree-rm NAME  Remove worktree and delete branch"
	@echo "  make worktree-rm-force NAME  Force remove (with changes)"
	@echo "  make worktree-unstash NAME  Restore hidden worktree"
	@echo "  make worktree-list-stashed  List all hidden worktrees"
	@echo ""
	@echo "SYNTHESIS:"
	@echo "  make synthesize query=\"...\" files=\"...\"  Run synthesis"
	@echo "  make triage query=\"...\" files=\"...\"  Run triage only"
	@echo ""
	@echo "AI CONTEXT:"
	@echo "  make ai-context-files  Build AI context documentation"
	@echo ""
	@echo "BLOG WRITING:"
	@echo "  make blog-write IDEA=<file> WRITINGS=<dir> [INSTRUCTIONS=\"...\"]  Create blog"
	@echo "  make blog-resume       Resume most recent blog writing session"
	@echo ""
	@echo "ARTICLE ILLUSTRATION:"
	@echo "  make illustrate INPUT=<file> [OUTPUT=<path>] [STYLE=\"...\"] [APIS=\"...\"] [RESUME=true]  Generate illustrations"
	@echo "  make illustrate-example  Run illustrator with example article"
	@echo "  make illustrate-prompts-only INPUT=<file>  Preview prompts without generating"
	@echo ""
	@echo "WEB TO MARKDOWN:"
	@echo "  make web-to-md URL=<url> [URL2=<url>] [OUTPUT=<path>]  Convert web pages to markdown (saves to content_dirs[0]/sites/)"
	@echo ""
	@echo "UTILITIES:"
	@echo "  make clean           Clean build artifacts"
	@echo "  make clean-wsl-files Clean WSL-related files"
	@echo "  make workspace-info  Show workspace information"
	@echo "  make dot-to-mermaid INPUT=\"path\"  Convert DOT files to Mermaid"
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""

# Installation
install: ## Install all dependencies
	@echo "Installing workspace dependencies..."
	uv sync --group dev
	@echo ""
	@echo "Installing npm packages globally..."
	@command -v pnpm >/dev/null 2>&1 || { echo "  Installing pnpm..."; npm install -g pnpm; }
	@pnpm add -g @anthropic-ai/claude-code@latest || { \
		echo "❌ Failed to install global packages."; \
		echo "   This may be a permissions issue. Try:"; \
		echo "   1. Run: pnpm setup && source ~/.bashrc (or ~/.zshrc)"; \
		echo "   2. Then run: make install"; \
		exit 1; \
	}
	@echo ""
	@echo "✅ All dependencies installed!"
	@echo ""
	@if [ -n "$$VIRTUAL_ENV" ]; then \
		echo "✓ Virtual environment already active"; \
	elif [ -f .venv/bin/activate ]; then \
		echo "→ Run this command: source .venv/bin/activate"; \
	else \
		echo "✗ No virtual environment found. Run 'make install' first."; \
	fi

# Code quality
check: ## Format, lint, and type-check all code
	@# Handle worktree virtual environment issues by unsetting mismatched VIRTUAL_ENV
	@if [ -n "$$VIRTUAL_ENV" ] && [ -d ".venv" ]; then \
		VENV_DIR=$$(cd "$$VIRTUAL_ENV" 2>/dev/null && pwd) || true; \
		LOCAL_VENV=$$(cd ".venv" 2>/dev/null && pwd) || true; \
		if [ "$$VENV_DIR" != "$$LOCAL_VENV" ]; then \
			echo "Detected virtual environment mismatch - using local .venv"; \
			export VIRTUAL_ENV=; \
		fi; \
	fi
	@echo "Formatting code with ruff..."
	@VIRTUAL_ENV= uv run ruff format .
	@echo "Linting code with ruff..."
	@VIRTUAL_ENV= uv run ruff check . --fix
	@echo "Type-checking code with pyright..."
	@VIRTUAL_ENV= uv run pyright
	@echo "Checking for stubs and placeholders..."
	@python tools/check_stubs.py
	@echo "All checks passed!"

test: ## Run all tests
	@echo "Running tests..."
	uv run pytest

smoke-test: ## Run quick smoke tests to verify basic functionality
	@echo "Running smoke tests..."
	@PYTHONPATH=. python -m amplifier.smoke_tests
	@echo "Smoke tests complete!"

# Git worktree management
worktree: ## Create a git worktree with .data copy. Usage: make worktree feature-name
	@if [ -z "$(filter-out $@,$(MAKECMDGOALS))" ]; then \
		echo "Error: Please provide a branch name. Usage: make worktree feature-name"; \
		exit 1; \
	fi
	@python tools/create_worktree.py $(filter-out $@,$(MAKECMDGOALS))


worktree-rm: ## Remove a git worktree and delete branch. Usage: make worktree-rm feature-name
	@if [ -z "$(filter-out $@,$(MAKECMDGOALS))" ]; then \
		echo "Error: Please provide a branch name. Usage: make worktree-rm feature-name"; \
		exit 1; \
	fi
	@python tools/remove_worktree.py "$(filter-out $@,$(MAKECMDGOALS))"

worktree-rm-force: ## Force remove a git worktree (even with changes). Usage: make worktree-rm-force feature-name
	@if [ -z "$(filter-out $@,$(MAKECMDGOALS))" ]; then \
		echo "Error: Please provide a branch name. Usage: make worktree-rm-force feature-name"; \
		exit 1; \
	fi
	@python tools/remove_worktree.py "$(filter-out $@,$(MAKECMDGOALS))" --force

worktree-list: ## List all git worktrees
	@git worktree list

worktree-stash: ## Hide a worktree from git (keeps directory). Usage: make worktree-stash feature-name
	@if [ -z "$(filter-out $@,$(MAKECMDGOALS))" ]; then \
		echo "Error: Please provide a worktree name. Usage: make worktree-stash feature-name"; \
		exit 1; \
	fi
	@python tools/worktree_manager.py stash-by-name "$(filter-out $@,$(MAKECMDGOALS))"

worktree-unstash: ## Restore a hidden worktree. Usage: make worktree-unstash feature-name
	@if [ -z "$(filter-out $@,$(MAKECMDGOALS))" ]; then \
		echo "Error: Please provide a worktree name. Usage: make worktree-unstash feature-name"; \
		exit 1; \
	fi
	@python tools/worktree_manager.py unstash-by-name "$(filter-out $@,$(MAKECMDGOALS))"

worktree-adopt: ## Create worktree from remote branch. Usage: make worktree-adopt branch-name
	@if [ -z "$(filter-out $@,$(MAKECMDGOALS))" ]; then \
		echo "Error: Please provide a branch name. Usage: make worktree-adopt branch-name"; \
		exit 1; \
	fi
	@python tools/worktree_manager.py adopt "$(filter-out $@,$(MAKECMDGOALS))"

worktree-list-stashed: ## List all hidden worktrees
	@python tools/worktree_manager.py list-stashed

# Catch-all target to handle branch names for worktree functionality
# and show error for invalid commands
%:
	@# If this is part of a worktree command, accept any branch name
	@if echo "$(MAKECMDGOALS)" | grep -qE '^(worktree|worktree-rm|worktree-rm-force|worktree-stash|worktree-unstash|worktree-adopt)\b'; then \
		: ; \
	else \
		echo "Error: Unknown command '$@'. Run 'make help' to see available commands."; \
		exit 1; \
	fi

# Content Processing
content-scan: ## Scan configured content directories for files
	@echo "Scanning content directories..."
	uv run python -m amplifier.content_loader scan

content-search: ## Search content. Usage: make content-search q="your query"
	@if [ -z "$(q)" ]; then \
		echo "Error: Please provide a query. Usage: make content-search q=\"your search query\""; \
		exit 1; \
	fi
	@echo "Searching: $(q)"
	uv run python -m amplifier.content_loader search "$(q)"

content-status: ## Show content statistics
	@echo "Content status:"
	uv run python -m amplifier.content_loader status

# Knowledge Synthesis (Simplified)
# Transcript Management
transcript-list: ## List available conversation transcripts. Usage: make transcript-list [LAST=10]
	@last="$${LAST:-10}"; \
	python tools/transcript_manager.py list --last $$last

transcript-load: ## Load a specific transcript. Usage: make transcript-load SESSION=id
	@if [ -z "$(SESSION)" ]; then \
		echo "Error: Please provide a session ID. Usage: make transcript-load SESSION=abc123"; \
		exit 1; \
	fi
	@python tools/transcript_manager.py load $(SESSION)

transcript-search: ## Search transcripts for a term. Usage: make transcript-search TERM="your search"
	@if [ -z "$(TERM)" ]; then \
		echo "Error: Please provide a search term. Usage: make transcript-search TERM=\"API\""; \
		exit 1; \
	fi
	@python tools/transcript_manager.py search "$(TERM)"

transcript-restore: ## Restore entire conversation lineage. Usage: make transcript-restore
	@python tools/transcript_manager.py restore

transcript-export: ## Export transcript to file. Usage: make transcript-export SESSION=id [FORMAT=text]
	@if [ -z "$(SESSION)" ]; then \
		echo "Error: Please provide a session ID. Usage: make transcript-export SESSION=abc123"; \
		exit 1; \
	fi
	@format="$${FORMAT:-text}"; \
	python tools/transcript_manager.py export --session-id $(SESSION) --format $$format


# Knowledge Graph Commands
## Graph Core Commands
# Synthesis Pipeline
synthesize: ## Run the synthesis pipeline. Usage: make synthesize query="..." files="..." [args="..."]
	@if [ -z "$(query)" ] || [ -z "$(files)" ]; then \
		echo "Error: Please provide 'query' and 'files'. Usage: make synthesize query=\"…\" files=\"…\""; \
		exit 1; \
	fi
	uv run python -m amplifier.synthesis.main --query "$(query)" --files "$(files)" $(args)

triage: ## Run only the triage step of the pipeline. Usage: make triage query="..." files="..."
	@if [ -z "$(query)" ] || [ -z "$(files)" ]; then \
		echo "Error: Please provide 'query' and 'files'. Usage: make triage query=\"…\" files=\"…\""; \
		exit 1; \
	fi
	uv run python -m amplifier.synthesis.main --query "$(query)" --files "$(files)" --use-triage



# AI Context
ai-context-files: ## Build AI context files
	@echo "Building AI context files..."
	uv run python tools/build_ai_context_files.py
	uv run python tools/build_git_collector_files.py
	@echo "AI context files generated"

# Blog Writing
blog-write: ## Create a blog post from your ideas. Usage: make blog-write IDEA=ideas.md WRITINGS=my_writings/ [INSTRUCTIONS="..."]
	@if [ -z "$(IDEA)" ]; then \
		echo "Error: Please provide an idea file. Usage: make blog-write IDEA=ideas.md WRITINGS=my_writings/"; \
		exit 1; \
	fi
	@if [ -z "$(WRITINGS)" ]; then \
		echo "Error: Please provide a writings directory. Usage: make blog-write IDEA=ideas.md WRITINGS=my_writings/"; \
		exit 1; \
	fi
	@echo "🚀 Starting blog post writer..."; \
	echo "  Idea: $(IDEA)"; \
	echo "  Writings: $(WRITINGS)"; \
	if [ -n "$(INSTRUCTIONS)" ]; then echo "  Instructions: $(INSTRUCTIONS)"; fi; \
	echo "  Output: Auto-generated from title in session directory"; \
	if [ -n "$(INSTRUCTIONS)" ]; then \
		uv run python -m scenarios.blog_writer \
			--idea "$(IDEA)" \
			--writings-dir "$(WRITINGS)" \
			--instructions "$(INSTRUCTIONS)"; \
	else \
		uv run python -m scenarios.blog_writer \
			--idea "$(IDEA)" \
			--writings-dir "$(WRITINGS)"; \
	fi

blog-resume: ## Resume an interrupted blog writing session
	@echo "📝 Resuming blog post writer..."
	@uv run python -m scenarios.blog_writer --resume

blog-write-example: ## Run blog writer with example data
	@echo "📝 Running blog writer with example data..."
	@uv run python -m scenarios.blog_writer \
		--idea scenarios/blog_writer/tests/sample_brain_dump.md \
		--writings-dir scenarios/blog_writer/tests/sample_writings/

# Tips Synthesis
tips-synthesizer: ## Synthesize tips from markdown files into cohesive document. Usage: make tips-synthesizer INPUT=tips_dir/ OUTPUT=guide.md [RESUME=true] [VERBOSE=true]
	@if [ -z "$(INPUT)" ]; then \
		echo "Error: Please provide an input directory. Usage: make tips-synthesizer INPUT=tips_dir/ OUTPUT=guide.md"; \
		exit 1; \
	fi
	@if [ -z "$(OUTPUT)" ]; then \
		echo "Error: Please provide an output file. Usage: make tips-synthesizer INPUT=tips_dir/ OUTPUT=guide.md"; \
		exit 1; \
	fi
	@echo "📚 Synthesizing tips from $(INPUT) to $(OUTPUT)"
	@uv run python -m scenarios.tips_synthesizer \
		--input-dir "$(INPUT)" \
		--output-file "$(OUTPUT)" \
		$(if $(RESUME),--resume) \
		$(if $(VERBOSE),--verbose)

tips-synthesizer-example: ## Run tips synthesizer with example data
	@echo "📚 Running tips synthesizer with example data..."
	@uv run python -m scenarios.tips_synthesizer \
		--input-dir scenarios/tips_synthesizer/tests/sample_tips/ \
		--output-file synthesized_tips_example.md \
		--verbose

# Transcription
transcribe: ## Transcribe audio/video files or YouTube URLs. Usage: make transcribe SOURCE="url or file" [NO_ENHANCE=true]
	@if [ -z "$(SOURCE)" ]; then \
		echo "Error: Please provide a source. Usage: make transcribe SOURCE=\"https://youtube.com/watch?v=...\""; \
		echo "   Or: make transcribe SOURCE=\"video.mp4\""; \
		exit 1; \
	fi
	@echo "🎙️ Starting transcription..."; \
	echo "  Source: $(SOURCE)"; \
	if [ "$(NO_ENHANCE)" = "true" ]; then \
		echo "  Enhancement: Disabled"; \
		uv run python -m scenarios.transcribe transcribe "$(SOURCE)" --no-enhance; \
	else \
		echo "  Enhancement: Enabled (summaries and quotes)"; \
		uv run python -m scenarios.transcribe transcribe "$(SOURCE)"; \
	fi

transcribe-batch: ## Transcribe multiple files. Usage: make transcribe-batch SOURCES="file1.mp4 file2.mp4" [NO_ENHANCE=true]
	@if [ -z "$(SOURCES)" ]; then \
		echo "Error: Please provide sources. Usage: make transcribe-batch SOURCES=\"video1.mp4 video2.mp4\""; \
		exit 1; \
	fi
	@echo "🎙️ Starting batch transcription..."; \
	echo "  Sources: $(SOURCES)"; \
	if [ "$(NO_ENHANCE)" = "true" ]; then \
		echo "  Enhancement: Disabled"; \
		uv run python -m scenarios.transcribe transcribe $(SOURCES) --no-enhance; \
	else \
		echo "  Enhancement: Enabled"; \
		uv run python -m scenarios.transcribe transcribe $(SOURCES); \
	fi

transcribe-resume: ## Resume interrupted transcription session
	@echo "🎙️ Resuming transcription..."
	@uv run python -m scenarios.transcribe transcribe --resume

transcribe-index: ## Generate index of all transcripts
	@echo "📑 Generating transcript index..."
	@uv run python -m scenarios.transcribe index

# Article Illustration
illustrate: ## Generate AI illustrations for markdown article. Usage: make illustrate INPUT=article.md [OUTPUT=path] [STYLE="..."] [APIS="..."] [RESUME=true]
	@if [ -z "$(INPUT)" ]; then \
		echo "Error: Please provide an input file. Usage: make illustrate INPUT=article.md"; \
		exit 1; \
	fi
	@echo "🎨 Generating illustrations for article..."
	@echo "  Input: $(INPUT)"
	@if [ -n "$(OUTPUT)" ]; then echo "  Output: $(OUTPUT)"; fi
	@if [ -n "$(STYLE)" ]; then echo "  Style: $(STYLE)"; fi
	@if [ -n "$(APIS)" ]; then echo "  APIs: $(APIS)"; fi
	@if [ -n "$(RESUME)" ]; then echo "  Mode: Resume"; fi
	@echo ""
	@CMD="uv run python -m scenarios.article_illustrator \"$(INPUT)\""; \
	if [ -n "$(OUTPUT)" ]; then CMD="$$CMD --output-dir \"$(OUTPUT)\""; fi; \
	if [ -n "$(STYLE)" ]; then CMD="$$CMD --style \"$(STYLE)\""; fi; \
	if [ -n "$(APIS)" ]; then \
		for api in $(APIS); do \
			CMD="$$CMD --apis $$api"; \
		done; \
	fi; \
	if [ -n "$(RESUME)" ]; then CMD="$$CMD --resume"; fi; \
	eval $$CMD

illustrate-example: ## Run article illustrator with example article
	@echo "🎨 Running article illustrator with example..."
	@uv run python -m scenarios.article_illustrator \
		scenarios/article_illustrator/tests/sample_article.md \
		--max-images 3

illustrate-prompts-only: ## Preview prompts without generating images. Usage: make illustrate-prompts-only INPUT=article.md
	@if [ -z "$(INPUT)" ]; then \
		echo "Error: Please provide an input file. Usage: make illustrate-prompts-only INPUT=article.md"; \
		exit 1; \
	fi
	@echo "🎨 Generating prompts (no images)..."
	@uv run python -m scenarios.article_illustrator "$(INPUT)" --prompts-only

# Web to Markdown
web-to-md: ## Convert web pages to markdown. Usage: make web-to-md URL=https://example.com [URL2=https://another.com] [OUTPUT=path]
	@if [ -z "$(URL)" ]; then \
		echo "Error: Please provide at least one URL. Usage: make web-to-md URL=https://example.com"; \
		exit 1; \
	fi
	@echo "🌐 Converting web page(s) to markdown..."
	@CMD="uv run python -m scenarios.web_to_md --url \"$(URL)\""; \
	if [ -n "$(URL2)" ]; then CMD="$$CMD --url \"$(URL2)\""; fi; \
	if [ -n "$(URL3)" ]; then CMD="$$CMD --url \"$(URL3)\""; fi; \
	if [ -n "$(URL4)" ]; then CMD="$$CMD --url \"$(URL4)\""; fi; \
	if [ -n "$(URL5)" ]; then CMD="$$CMD --url \"$(URL5)\""; fi; \
	if [ -n "$(OUTPUT)" ]; then CMD="$$CMD --output \"$(OUTPUT)\""; fi; \
	eval $$CMD

# Clean WSL Files
clean-wsl-files: ## Clean up WSL-related files (Zone.Identifier, sec.endpointdlp)
	@echo "Cleaning WSL-related files..."
	@uv run python tools/clean_wsl_files.py

# Workspace info
workspace-info: ## Show workspace information
	@echo ""
	@echo "Workspace"
	@echo "==============="
	@echo ""
	$(call list_projects)
	@echo ""

# DOT to Mermaid Converter
dot-to-mermaid: ## Convert DOT files to Mermaid format. Usage: make dot-to-mermaid INPUT="path/to/dot/files"
	@if [ -z "$(INPUT)" ]; then \
		echo "Error: Please provide an input path. Usage: make dot-to-mermaid INPUT=\"path/to/dot/files\""; \
		exit 1; \
	fi
	@DATA_DIR=$$(python -c "from amplifier.config.paths import paths; print(paths.data_dir)"); \
	SESSION_DIR="$$DATA_DIR/dot_to_mermaid"; \
	mkdir -p "$$SESSION_DIR"; \
	echo "Converting DOT files to Mermaid format..."; \
	uv run python -m ai_working.dot_to_mermaid.cli "$(INPUT)" --session-file "$$SESSION_DIR/session.json"
