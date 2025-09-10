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

# Default goal
.DEFAULT_GOAL := help

# Main targets
.PHONY: help install dev test check

help: ## Show this help message
	@echo ""
	@echo "Quick Start:"
	@echo "  make install         Install all dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make check          Format, lint, and type-check all code"
	@echo "  make worktree NAME   Create git worktree with .data copy"
	@echo "  make worktree-list   List all git worktrees"
	@echo "  make worktree-rm NAME  Remove worktree and delete branch"
	@echo "  make worktree-rm-force NAME  Force remove (even with changes)"
	@echo ""
	@echo "AI Context:"
	@echo "  make ai-context-files Build AI context documentation"
	@echo ""
	@echo "Other:"
	@echo "  make clean          Clean build artifacts"
	@echo "  make clean-wsl-files Clean up WSL-related files"
	@echo ""

# Installation
install: ## Install all dependencies
	@echo "Installing workspace dependencies..."
	uv sync --group dev
	@echo ""
	@echo "Installing npm packages globally..."
	@command -v pnpm >/dev/null 2>&1 || { echo "❌ pnpm required. Install: curl -fsSL https://get.pnpm.io/install.sh | sh -"; exit 1; }
	@# Ensure pnpm global directory exists and is configured (handles non-interactive shells)
	@PNPM_HOME=$$(pnpm bin -g 2>/dev/null || echo "$$HOME/.local/share/pnpm"); \
	mkdir -p "$$PNPM_HOME" 2>/dev/null || true; \
	PATH="$$PNPM_HOME:$$PATH" pnpm add -g @anthropic-ai/claude-code@latest @mariozechner/claude-trace@latest || { \
		echo "❌ Failed to install global packages. Trying pnpm setup..."; \
		pnpm setup >/dev/null 2>&1 || true; \
		echo "❌ Could not configure pnpm global directory automatically."; \
		if [ -n "$$ZSH_VERSION" ] || [ "$$SHELL" = "/bin/zsh" ] || [ -f ~/.zshrc ]; then \
			echo "   Please run: pnpm setup && source ~/.zshrc"; \
		else \
			echo "   Please run: pnpm setup && source ~/.bashrc"; \
		fi; \
		echo "   Then run: make install"; \
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

# Git worktree management
worktree: ## Create a git worktree with .data copy. Usage: make worktree feature-name
	@if [ -z "$(filter-out $@,$(MAKECMDGOALS))" ]; then \
		echo "Error: Please provide a branch name. Usage: make worktree feature-name"; \
		exit 1; \
	fi
	@python tools/create_worktree.py "$(filter-out $@,$(MAKECMDGOALS))"

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

# Azure Automation
.PHONY: azure-create azure-create-managed azure-teardown azure-status

azure-create: ## Create Azure PostgreSQL infrastructure with password authentication
	@echo "🚀 Creating Azure PostgreSQL infrastructure (password auth)..."
	@if ! command -v az &> /dev/null; then \
		echo "❌ Azure CLI is not installed. Please install it first:"; \
		echo "  Visit: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"; \
		exit 1; \
	fi
	@bash infrastructure/azure/setup-postgresql.sh
	@echo "✅ Azure resources created! Run 'make setup-db' to initialize the database."

azure-create-managed: ## Create Azure PostgreSQL with managed identity authentication
	@echo "🚀 Creating Azure PostgreSQL infrastructure (managed identity)..."
	@if ! command -v az &> /dev/null; then \
		echo "❌ Azure CLI is not installed. Please install it first:"; \
		echo "  Visit: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"; \
		exit 1; \
	fi
	@bash infrastructure/azure/setup-postgresql-managed.sh
	@echo "✅ Azure resources created with managed identity!"
	@echo "📝 Next: Configure your app's managed identity and database user"

azure-teardown: ## Delete Azure PostgreSQL resources
	@echo "⚠️  WARNING: This will DELETE all Azure resources!"
	@bash infrastructure/azure/teardown-postgresql.sh

azure-status: ## Check Azure resource status
	@if [ -f .azure-postgresql.env ]; then \
		source .azure-postgresql.env && \
		echo "📊 Azure PostgreSQL Status:" && \
		echo "  Resource Group: $$AZURE_RESOURCE_GROUP" && \
		echo "  Server: $$AZURE_POSTGRES_SERVER" && \
		echo "  Database: $$AZURE_DATABASE_NAME" && \
		az postgres flexible-server show \
			--resource-group "$$AZURE_RESOURCE_GROUP" \
			--name "$$AZURE_POSTGRES_SERVER" \
			--query "{Status:state,Version:version,Tier:sku.tier}" \
			--output table 2>/dev/null || echo "  ❌ Server not found or not accessible"; \
	else \
		echo "❌ No Azure configuration found. Run 'make azure-create' first."; \
	fi

# Database Setup
.PHONY: setup-db validate-db reset-db db-status

setup-db: ## Setup database schema
	@echo "🚀 Setting up database schema..."
	@if [ ! -f .env ]; then \
		echo "❌ Missing .env file. Copy .env.example and add your DATABASE_URL"; \
		echo "  Or run 'make azure-create' to create Azure PostgreSQL automatically"; \
		exit 1; \
	fi
	@uv run python -m db_setup.setup
	@echo "✅ Database ready!"

validate-db: ## Validate database schema
	@echo "🔍 Validating database schema..."
	@uv run python -m db_setup.setup --validate

reset-db: ## Reset database (WARNING: deletes all data!)
	@echo "⚠️  WARNING: This will DELETE all data!"
	@uv run python -m db_setup.setup --reset

db-status: ## Show database connection status
	@uv run python -m db_setup.setup --status

# Catch-all target to handle branch names for worktree functionality
# and show error for invalid commands
%:
	@# If this is part of a worktree command, accept any branch name
	@if echo "$(MAKECMDGOALS)" | grep -qE '^(worktree|worktree-rm|worktree-rm-force)\b'; then \
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
knowledge-sync: ## Extract knowledge from all content files
	@echo "Syncing and extracting knowledge from content files..."
	uv run python -m amplifier.knowledge_synthesis.cli sync

knowledge-sync-batch: ## Extract knowledge from next N articles. Usage: make knowledge-sync-batch N=5
	@n="$${N:-5}"; \
	echo "Processing next $$n articles..."; \
	uv run python -m amplifier.knowledge_synthesis.cli sync --max-articles $$n

knowledge-search: ## Search extracted knowledge. Usage: make knowledge-search Q="AI agents"
	@if [ -z "$(Q)" ]; then \
		echo "Error: Please provide a query. Usage: make knowledge-search Q=\"your search\""; \
		exit 1; \
	fi
	@echo "Searching for: $(Q)"
	uv run python -m amplifier.knowledge_synthesis.cli search "$(Q)"

knowledge-stats: ## Show knowledge extraction statistics
	@echo "Knowledge Base Statistics:"
	uv run python -m amplifier.knowledge_synthesis.cli stats

knowledge-export: ## Export all knowledge as JSON or text. Usage: make knowledge-export [FORMAT=json|text]
	@format="$${FORMAT:-text}"; \
	echo "Exporting knowledge as $$format..."; \
	uv run python -m amplifier.knowledge_synthesis.cli export --format $$format

# Knowledge Pipeline Commands
knowledge-update: ## Full pipeline: scan content + extract knowledge + synthesize patterns
	@echo "🚀 Running full knowledge pipeline..."
	@echo "Step 1: Scanning content directories..."
	@$(MAKE) --no-print-directory content-scan
	@echo ""
	@echo "Step 3: Extracting knowledge..."
	@$(MAKE) --no-print-directory knowledge-sync
	@echo ""
	@echo "Step 4: Synthesizing patterns..."
	@$(MAKE) --no-print-directory knowledge-synthesize
	@echo ""
	@echo "✅ Knowledge pipeline complete!"

knowledge-synthesize: ## Find patterns across all extracted knowledge
	@echo "🔍 Synthesizing patterns from knowledge base..."
	@uv run python -m amplifier.knowledge_synthesis.run_synthesis
	@echo "✅ Synthesis complete! Results saved to knowledge base"

knowledge-query: ## Query the knowledge base. Usage: make knowledge-query Q="your question"
	@if [ -z "$(Q)" ]; then \
		echo "Error: Please provide a query. Usage: make knowledge-query Q=\"your question\""; \
		exit 1; \
	fi
	@echo "🔍 Querying knowledge base: $(Q)"
	@uv run python -m amplifier.knowledge_synthesis.query "$(Q)"

# Legacy command aliases (for backward compatibility)
knowledge-mine: knowledge-sync  ## DEPRECATED: Use knowledge-sync instead
knowledge-extract: knowledge-sync  ## DEPRECATED: Use knowledge-sync instead

# Knowledge Graph Commands
## Graph Core Commands
knowledge-graph-build: ## Build/rebuild graph from extractions
	@echo "🔨 Building knowledge graph from extractions..."
	@DATA_DIR=$$(python -c "from amplifier.config.paths import paths; print(paths.data_dir)"); \
	uv run python -m amplifier.knowledge.graph_builder --export-gexf "$$DATA_DIR/knowledge/graph.gexf"
	@echo "✅ Knowledge graph built successfully!"

knowledge-graph-update: ## Incremental update with new extractions
	@echo "🔄 Updating knowledge graph with new extractions..."
	@uv run python -m amplifier.knowledge.graph_updater
	@echo "✅ Knowledge graph updated successfully!"

knowledge-graph-stats: ## Show graph statistics
	@echo "📊 Knowledge Graph Statistics:"
	@uv run python -m amplifier.knowledge.graph_builder --summary --top-concepts 20

## Graph Query Commands
knowledge-graph-search: ## Semantic search in graph. Usage: make knowledge-graph-search Q="AI agents"
	@if [ -z "$(Q)" ]; then \
		echo "Error: Please provide a query. Usage: make knowledge-graph-search Q=\"your search\""; \
		exit 1; \
	fi
	@echo "🔍 Searching knowledge graph for: $(Q)"
	@uv run python -m amplifier.knowledge.graph_search "$(Q)"

knowledge-graph-path: ## Find path between concepts. Usage: make knowledge-graph-path FROM="concept1" TO="concept2"
	@if [ -z "$(FROM)" ] || [ -z "$(TO)" ]; then \
		echo "Error: Please provide FROM and TO concepts. Usage: make knowledge-graph-path FROM=\"concept1\" TO=\"concept2\""; \
		exit 1; \
	fi
	@echo "🛤️ Finding path from '$(FROM)' to '$(TO)'..."
	@uv run python -m amplifier.knowledge.graph_search path "$(FROM)" "$(TO)"

knowledge-graph-neighbors: ## Explore concept neighborhood. Usage: make knowledge-graph-neighbors CONCEPT="AI" [HOPS=2]
	@if [ -z "$(CONCEPT)" ]; then \
		echo "Error: Please provide a concept. Usage: make knowledge-graph-neighbors CONCEPT=\"your concept\""; \
		exit 1; \
	fi
	@hops="$${HOPS:-2}"; \
	echo "🔗 Exploring $$hops-hop neighborhood of '$(CONCEPT)'..."; \
	uv run python -m amplifier.knowledge.graph_search neighbors "$(CONCEPT)" --hops $$hops

## Graph Analysis Commands
knowledge-graph-tensions: ## Find productive contradictions. Usage: make knowledge-graph-tensions [TOP=10]
	@top="$${TOP:-10}"; \
	echo "⚡ Finding top $$top productive tensions..."; \
	uv run python -m amplifier.knowledge.tension_detector --top $$top

knowledge-graph-viz: ## Create interactive visualization. Usage: make knowledge-graph-viz [NODES=50]
	@nodes="$${NODES:-50}"; \
	DATA_DIR=$$(python -c "from amplifier.config.paths import paths; print(paths.data_dir)"); \
	echo "🎨 Creating interactive visualization with $$nodes nodes..."; \
	uv run python -m amplifier.knowledge.graph_visualizer --max-nodes $$nodes --output "$$DATA_DIR/knowledge/graph.html"
	@DATA_DIR=$$(python -c "from amplifier.config.paths import paths; print(paths.data_dir)"); \
	echo "✅ Visualization saved to $$DATA_DIR/knowledge/graph.html"

knowledge-graph-export: ## Export for external tools. Usage: make knowledge-graph-export [FORMAT=gexf]
	@format="$${FORMAT:-gexf}"; \
	DATA_DIR=$$(python -c "from amplifier.config.paths import paths; print(paths.data_dir)"); \
	echo "💾 Exporting knowledge graph as $$format..."; \
	FLAGS=""; \
	if [ -n "$$CLEAN" ]; then \
		FLAGS="$$FLAGS --only-predicate-edges --drop-untype-nodes"; \
	fi; \
	if [ -n "$$ALLOWED_PREDICATES" ]; then \
		FLAGS="$$FLAGS --allowed-predicates \"$$ALLOWED_PREDICATES\""; \
	fi; \
	if [ "$$format" = "gexf" ]; then \
		uv run python -m amplifier.knowledge.graph_builder $$FLAGS --export-gexf "$$DATA_DIR/knowledge/graph.gexf"; \
	elif [ "$$format" = "graphml" ]; then \
		uv run python -m amplifier.knowledge.graph_builder $$FLAGS --export-graphml "$$DATA_DIR/knowledge/graph.graphml"; \
	else \
		echo "Error: Unsupported format $$format. Use gexf or graphml."; \
		exit 1; \
	fi
	@format="$${FORMAT:-gexf}"; \
	DATA_DIR=$$(python -c "from amplifier.config.paths import paths; print(paths.data_dir)"); \
	echo "✅ Graph exported to $$DATA_DIR/knowledge/graph.$$format"

knowledge-events: ## Show recent pipeline events. Usage: make knowledge-events [N=50]
	@n="$${N:-50}"; \
	uv run python -m amplifier.knowledge_synthesis.cli events --n $$n

knowledge-events-tail: ## Follow pipeline events (like tail -f). Usage: make knowledge-events-tail [N=20]
	@n="$${N:-20}"; \
	uv run python -m amplifier.knowledge_synthesis.cli events --n $$n --follow

knowledge-events-summary: ## Summarize pipeline events. Usage: make knowledge-events-summary [SCOPE=last|all]
	@scope="$${SCOPE:-last}"; \
	uv run python -m amplifier.knowledge_synthesis.cli events-summary --scope $$scope

knowledge-graph-top-predicates: ## Show top predicates in the graph
	@n="$${N:-15}"; \
	uv run python -m amplifier.knowledge.graph_builder --top-predicates $$n --top-concepts 0

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


# Claude Trace Viewer
.PHONY: trace-viewer

trace-viewer: ## Start Claude trace viewer for .claude-trace files
	@echo "Starting Claude Trace Viewer..."
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "Access at: http://localhost:8090"
	@echo "Reading from: .claude-trace/"
	@echo "Press Ctrl+C to stop"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@python -m trace_viewer --port 8090

# AI Context
ai-context-files: ## Build AI context files
	@echo "Building AI context files..."
	uv run python tools/build_ai_context_files.py
	uv run python tools/build_git_collector_files.py
	@echo "AI context files generated"

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

# Slides Tool Commands
slides-generate: ## Generate presentation from prompt. Usage: make slides-generate PROMPT="..." [CONTEXT="..."]
	@if [ -z "$(PROMPT)" ]; then \
		echo "Error: Please provide a prompt. Usage: make slides-generate PROMPT=\"your presentation prompt\""; \
		exit 1; \
	fi
	@echo "Generating slides: $(PROMPT)"
	@OUTPUT_DIR="$${OUTPUT_DIR:-slides_output}"; \
	THEME="$${THEME:-black}"; \
	uv run python -m amplifier.slides_tool.cli generate \
		--prompt "$(PROMPT)" \
		--output-dir "$$OUTPUT_DIR" \
		--theme "$$THEME" \
		$(if $(CONTEXT),--context "$(CONTEXT)",)

slides-revise: ## Revise existing presentation. Usage: make slides-revise FILE="..." FEEDBACK="..."
	@if [ -z "$(FILE)" ] || [ -z "$(FEEDBACK)" ]; then \
		echo "Error: Please provide FILE and FEEDBACK. Usage: make slides-revise FILE=\"...\" FEEDBACK=\"...\""; \
		exit 1; \
	fi
	@echo "Revising presentation: $(FILE)"
	@OUTPUT_DIR="$${OUTPUT_DIR:-slides_output_revised}"; \
	uv run python -m amplifier.slides_tool.cli revise \
		--file "$(FILE)" \
		--feedback "$(FEEDBACK)" \
		--output-dir "$$OUTPUT_DIR"

slides-export: ## Export presentation. Usage: make slides-export FILE="..." FORMAT="pdf|png|gif" [OUTPUT="..."]
	@if [ -z "$(FILE)" ] || [ -z "$(FORMAT)" ]; then \
		echo "Error: Please provide FILE and FORMAT. Usage: make slides-export FILE=\"...\" FORMAT=\"pdf|png|gif\""; \
		exit 1; \
	fi
	@echo "Exporting $(FILE) as $(FORMAT)..."
	@OUTPUT="$${OUTPUT:-output/export_$$(date +%Y%m%d_%H%M%S).$(FORMAT)}"; \
	uv run python -m amplifier.slides_tool.cli export \
		--file "$(FILE)" \
		--format "$(FORMAT)" \
		--output "$$OUTPUT"

slides-list: ## List all saved presentations
	@echo "Saved presentations:"
	@uv run python -m amplifier.slides_tool.cli list

slides-check: ## Check slides tool dependencies
	@echo "Checking slides tool dependencies..."
	@uv run python -m amplifier.slides_tool.cli check

slides-review: ## Review slide images for truncation. Usage: make slides-review PRESENTATION="..." IMAGES="..."
	@if [ -z "$(PRESENTATION)" ] || [ -z "$(IMAGES)" ]; then \
		echo "Error: Please provide PRESENTATION and IMAGES. Usage: make slides-review PRESENTATION=\"...\" IMAGES=\"...\""; \
		exit 1; \
	fi
	@echo "Reviewing slides for truncation issues..."
	@OUTPUT="$${OUTPUT:-review_report.md}"; \
	uv run python -m amplifier.slides_tool.cli review \
		"$(PRESENTATION)" "$(IMAGES)" \
		--output "$$OUTPUT"


slides-auto-improve: ## Auto-improve presentation. Usage: make slides-auto-improve PRESENTATION="..." [MAX_ITER=3]
	@if [ -z "$(PRESENTATION)" ]; then \
		echo "Error: Please provide PRESENTATION. Usage: make slides-auto-improve PRESENTATION=\"presentation.md\""; \
		exit 1; \
	fi
	@echo "Auto-improving $(PRESENTATION)..."
	@OUTPUT_DIR="$${OUTPUT_DIR:-auto_improve_output}"; \
	MAX_ITER="$${MAX_ITER:-3}"; \
	uv run python -m amplifier.slides_tool.cli auto-improve \
		"$(PRESENTATION)" \
		--output-dir "$$OUTPUT_DIR" \
		--max-iterations "$$MAX_ITER" \
		$(if $(RESUME),--resume,)

slides-full-pipeline: ## Full pipeline: generate, export, review, improve. Usage: make slides-full-pipeline PRESENTATION="..."
	@if [ -z "$(PRESENTATION)" ]; then \
		echo "Error: Please provide PRESENTATION. Usage: make slides-full-pipeline PRESENTATION=\"presentation.md\""; \
		exit 1; \
	fi
	@echo "Running full slides pipeline for $(PRESENTATION)..."
	@OUTPUT_DIR="$${OUTPUT_DIR:-slides_full_output}"; \
	THEME="$${THEME:-default}"; \
	MAX_ITER="$${MAX_ITER:-3}"; \
	uv run python -m amplifier.slides_tool.cli full-pipeline \
		"$(PRESENTATION)" \
		--output-dir "$$OUTPUT_DIR" \
		--theme "$$THEME" \
		$(if $(AUTO_IMPROVE),--auto-improve,) \
		--max-iterations "$$MAX_ITER"
