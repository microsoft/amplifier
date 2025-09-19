#!/bin/bash
# Build self-extracting installer for Amplifier
# This script creates a single-file installer that includes the entire codebase

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_ROOT/build/installer"
OUTPUT_FILE="$BUILD_DIR/install_amplifier.sh"
ARCHIVE_NAME="amplifier_payload.tar.gz"
INSTALLER_SCRIPT="$BUILD_DIR/install_amplifier_header.sh"

# Print colored message
print_msg() {
    local color=$1
    local msg=$2
    echo -e "${color}${msg}${NC}"
}

# Clean up build directory
cleanup() {
    if [ -d "$BUILD_DIR" ]; then
        rm -rf "$BUILD_DIR"
    fi
    if [ -f "$INSTALLER_SCRIPT" ]; then
        rm -f "$INSTALLER_SCRIPT"
    fi
}

# Create the installer header script
create_installer_header() {
    cat > "$INSTALLER_SCRIPT" << 'EOF'
#!/bin/bash
# Amplifier Self-Extracting Installer
# This script will install Amplifier and all its dependencies

set -euo pipefail

# Configuration
INSTALLER_VERSION="1.1.0"
DEFAULT_INSTALL_DIR="./amplifier"
INSTALL_DIR=""
STATE_FILE=""
REQUIRED_PYTHON_VERSION="3.11"
INTERACTIVE_MODE=true
RESUME_FILE="$HOME/.amplifier_install_resume"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored message
print_msg() {
    local color=$1
    local msg=$2
    echo -e "${color}${msg}${NC}"
}

# Print error and exit
die() {
    print_msg "$RED" "ERROR: $1"
    exit 1
}

# Print header
print_header() {
    echo ""
    print_msg "$BLUE" "╔════════════════════════════════════════════╗"
    print_msg "$BLUE" "║     🚀 Amplifier Self-Extracting Installer  ║"
    print_msg "$BLUE" "║              Version $INSTALLER_VERSION              ║"
    print_msg "$BLUE" "╚════════════════════════════════════════════╝"
    echo ""
}

# Interactive prompt functions
prompt_yes_no() {
    local prompt="$1"
    local default="${2:-y}"
    local response

    if [ "$INTERACTIVE_MODE" = false ]; then
        echo "y"
        return 0
    fi

    if [ "$default" = "y" ]; then
        read -p "$(echo -e "${BLUE}$prompt [Y/n]: ${NC}")" response
    else
        read -p "$(echo -e "${BLUE}$prompt [y/N]: ${NC}")" response
    fi

    response="${response:-$default}"
    case "$response" in
        [yY][eE][sS]|[yY]) echo "y"; return 0 ;;
        [nN][oO]|[nN]) echo "n"; return 1 ;;
        *) echo "$default"; [ "$default" = "y" ] && return 0 || return 1 ;;
    esac
}

prompt_input() {
    local prompt="$1"
    local default="$2"
    local response

    if [ "$INTERACTIVE_MODE" = false ]; then
        echo "$default"
        return 0
    fi

    if [ -n "$default" ]; then
        read -p "$(echo -e "${BLUE}$prompt [$default]: ${NC}")" response
        echo "${response:-$default}"
    else
        read -p "$(echo -e "${BLUE}$prompt: ${NC}")" response
        echo "$response"
    fi
}

# Save installation preferences for resume
save_preferences() {
    cat > "$RESUME_FILE" << EOL
INSTALL_DIR="$INSTALL_DIR"
INTERACTIVE_MODE="$INTERACTIVE_MODE"
LAST_STEP="$1"
EOL
}

# Load previous preferences if available
load_preferences() {
    if [ -f "$RESUME_FILE" ]; then
        source "$RESUME_FILE"
        return 0
    fi
    return 1
}

# Detect platform
detect_platform() {
    if grep -qi microsoft /proc/version 2>/dev/null; then
        echo "wsl"
    elif [[ "$(uname -s)" == "Darwin" ]]; then
        echo "macos"
    elif [[ "$(uname -s)" == "Linux" ]]; then
        echo "linux"
    else
        echo "unknown"
    fi
}

# State management functions
init_state() {
    mkdir -p "$(dirname "$STATE_FILE")"
    if [ ! -f "$STATE_FILE" ]; then
        echo "# Amplifier Installation State" > "$STATE_FILE"
        echo "# Generated: $(date -Iseconds)" >> "$STATE_FILE"
    fi
}

mark_completed() {
    local step=$1
    local timestamp=$(date -Iseconds)
    echo "${step}:completed:${timestamp}" >> "$STATE_FILE"
}

is_completed() {
    local step=$1
    grep -q "^${step}:completed:" "$STATE_FILE" 2>/dev/null
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Version comparison
version_ge() {
    # Returns 0 if $1 >= $2
    [ "$(printf '%s\n' "$2" "$1" | sort -V | head -n1)" = "$2" ]
}

# Check Python version
check_python_version() {
    if command_exists python3; then
        local version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        if version_ge "$version" "$REQUIRED_PYTHON_VERSION"; then
            return 0
        fi
    fi
    return 1
}

# Install Python based on platform
install_python() {
    local platform=$1

    if is_completed "python"; then
        print_msg "$GREEN" "✓ Python already installed"
        return 0
    fi

    print_msg "$YELLOW" "🐍 Installing Python ${REQUIRED_PYTHON_VERSION}+..."

    case $platform in
        wsl|linux)
            if command_exists apt-get; then
                sudo apt-get update
                sudo apt-get install -y python3.11 python3.11-venv python3-pip
            elif command_exists yum; then
                sudo yum install -y python311 python311-pip
            else
                die "Unsupported Linux distribution. Please install Python ${REQUIRED_PYTHON_VERSION}+ manually."
            fi
            ;;
        macos)
            if ! command_exists brew; then
                print_msg "$YELLOW" "Installing Homebrew first..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            brew install python@3.11
            ;;
        *)
            die "Unsupported platform: $platform"
            ;;
    esac

    if check_python_version; then
        mark_completed "python"
        print_msg "$GREEN" "✓ Python installed successfully"
    else
        die "Failed to install Python ${REQUIRED_PYTHON_VERSION}+"
    fi
}

# Install UV package manager
install_uv() {
    if is_completed "uv"; then
        print_msg "$GREEN" "✓ UV already installed"
        return 0
    fi

    print_msg "$YELLOW" "📦 Installing UV package manager..."

    if command_exists curl; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
    elif command_exists wget; then
        wget -qO- https://astral.sh/uv/install.sh | sh
    else
        die "Neither curl nor wget found. Please install one of them."
    fi

    # Source the UV environment
    if [ -f "$HOME/.cargo/env" ]; then
        source "$HOME/.cargo/env"
    fi

    # Add UV to PATH for current session
    export PATH="$HOME/.cargo/bin:$PATH"

    if command_exists uv; then
        mark_completed "uv"
        print_msg "$GREEN" "✓ UV installed successfully"
    else
        die "Failed to install UV"
    fi
}

# Install Node.js and npm
install_node() {
    local platform=$1

    if is_completed "node"; then
        print_msg "$GREEN" "✓ Node.js already installed"
        return 0
    fi

    print_msg "$YELLOW" "🟢 Installing Node.js..."

    case $platform in
        wsl|linux)
            # Install Node.js via NodeSource repository
            curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
            sudo apt-get install -y nodejs
            ;;
        macos)
            if command_exists brew; then
                brew install node
            else
                die "Homebrew not found. Please install it first."
            fi
            ;;
        *)
            die "Unsupported platform: $platform"
            ;;
    esac

    if command_exists node && command_exists npm; then
        mark_completed "node"
        print_msg "$GREEN" "✓ Node.js installed successfully ($(node --version))"
    else
        die "Failed to install Node.js"
    fi
}

# Install pnpm
install_pnpm() {
    if is_completed "pnpm"; then
        print_msg "$GREEN" "✓ pnpm already installed"
        return 0
    fi

    print_msg "$YELLOW" "🎯 Installing pnpm package manager..."

    if command_exists npm; then
        npm install -g pnpm
    else
        # Alternative installation method
        curl -fsSL https://get.pnpm.io/install.sh | sh -
    fi

    # Add pnpm to PATH for current session
    export PNPM_HOME="$HOME/.local/share/pnpm"
    export PATH="$PNPM_HOME:$PATH"

    if command_exists pnpm; then
        mark_completed "pnpm"
        print_msg "$GREEN" "✓ pnpm installed successfully"
    else
        die "Failed to install pnpm"
    fi
}

# Install Claude CLI
install_claude_cli() {
    if is_completed "claude-cli"; then
        print_msg "$GREEN" "✓ Claude CLI already installed"
        return 0
    fi

    print_msg "$YELLOW" "🤖 Installing Claude CLI..."

    # Ensure pnpm global directory exists and is configured
    PNPM_HOME="${PNPM_HOME:-$HOME/.local/share/pnpm}"
    mkdir -p "$PNPM_HOME"
    export PATH="$PNPM_HOME:$PATH"

    # Install claude-code globally
    if command_exists pnpm; then
        pnpm add -g @anthropic-ai/claude-code@latest
    elif command_exists npm; then
        npm install -g @anthropic-ai/claude-code@latest
    else
        die "Neither pnpm nor npm found. Cannot install Claude CLI."
    fi

    if command_exists claude; then
        mark_completed "claude-cli"
        print_msg "$GREEN" "✓ Claude CLI installed successfully"
    else
        # Check if it's in the pnpm global directory
        if [ -f "$PNPM_HOME/claude" ]; then
            mark_completed "claude-cli"
            print_msg "$GREEN" "✓ Claude CLI installed (may require shell restart to be in PATH)"
        else
            die "Failed to install Claude CLI"
        fi
    fi
}

# Extract the embedded archive
extract_payload() {
    print_msg "$YELLOW" "📂 Extracting Amplifier codebase..."

    # Find where the archive starts
    ARCHIVE_LINE=$(awk '/^__ARCHIVE_BELOW__/ {print NR + 1; exit}' "$0")

    # Create installation directory
    mkdir -p "$INSTALL_DIR"

    # Extract the archive with progress indication
    if [ "$INTERACTIVE_MODE" = true ]; then
        print_msg "$YELLOW" "   This may take a moment..."
    fi

    tail -n +"$ARCHIVE_LINE" "$0" | tar xzf - -C "$INSTALL_DIR"

    print_msg "$GREEN" "✓ Codebase extracted to $INSTALL_DIR"
}

# Setup Python environment and dependencies
setup_python_env() {
    if is_completed "python-deps"; then
        print_msg "$GREEN" "✓ Python dependencies already installed"
        return 0
    fi

    print_msg "$YELLOW" "🔧 Setting up Python environment and dependencies..."

    cd "$INSTALL_DIR"

    # Ensure UV is in PATH
    export PATH="$HOME/.cargo/bin:$PATH"

    # Run make install which uses UV
    if [ -f "Makefile" ]; then
        make install
        mark_completed "python-deps"
        print_msg "$GREEN" "✓ Python dependencies installed"
    else
        die "Makefile not found in $INSTALL_DIR"
    fi
}

# Update shell configuration
update_shell_config() {
    local shell_config=""

    # Determine shell configuration file
    if [ -n "${ZSH_VERSION:-}" ] || [ -f "$HOME/.zshrc" ]; then
        shell_config="$HOME/.zshrc"
    elif [ -n "${BASH_VERSION:-}" ] || [ -f "$HOME/.bashrc" ]; then
        shell_config="$HOME/.bashrc"
    else
        shell_config="$HOME/.profile"
    fi

    print_msg "$YELLOW" "🐚 Updating shell configuration ($shell_config)..."

    # Add PATH updates if not already present
    if ! grep -q "# Amplifier paths" "$shell_config" 2>/dev/null; then
        cat >> "$shell_config" << EOL

# Amplifier paths
export AMPLIFIER_HOME="$INSTALL_DIR"
export PATH="\$HOME/.cargo/bin:\$PATH"  # UV
export PNPM_HOME="\$HOME/.local/share/pnpm"
export PATH="\$PNPM_HOME:\$PATH"  # pnpm global
EOL
        print_msg "$GREEN" "✓ Shell configuration updated"
        print_msg "$YELLOW" "  Note: Run 'source $shell_config' or restart your shell"
    fi
}

# Validate installation
validate_installation() {
    print_msg "$YELLOW" "🔍 Validating installation..."

    local all_good=true

    # Check Python
    if check_python_version; then
        print_msg "$GREEN" "  ✓ Python ${REQUIRED_PYTHON_VERSION}+"
    else
        print_msg "$RED" "  ✗ Python ${REQUIRED_PYTHON_VERSION}+ not found"
        all_good=false
    fi

    # Check UV
    if command_exists uv || [ -f "$HOME/.cargo/bin/uv" ]; then
        print_msg "$GREEN" "  ✓ UV package manager"
    else
        print_msg "$RED" "  ✗ UV not found"
        all_good=false
    fi

    # Check Node.js
    if command_exists node; then
        print_msg "$GREEN" "  ✓ Node.js $(node --version)"
    else
        print_msg "$RED" "  ✗ Node.js not found"
        all_good=false
    fi

    # Check pnpm
    if command_exists pnpm || [ -f "$PNPM_HOME/pnpm" ]; then
        print_msg "$GREEN" "  ✓ pnpm package manager"
    else
        print_msg "$RED" "  ✗ pnpm not found"
        all_good=false
    fi

    # Check Claude CLI
    if command_exists claude || [ -f "$PNPM_HOME/claude" ]; then
        print_msg "$GREEN" "  ✓ Claude CLI"
    else
        print_msg "$RED" "  ✗ Claude CLI not found"
        all_good=false
    fi

    # Check Amplifier installation
    if [ -f "$INSTALL_DIR/Makefile" ] && [ -d "$INSTALL_DIR/amplifier" ]; then
        print_msg "$GREEN" "  ✓ Amplifier codebase"
    else
        print_msg "$RED" "  ✗ Amplifier codebase not found"
        all_good=false
    fi

    if [ "$all_good" = true ]; then
        print_msg "$GREEN" "\n✅ Installation validated successfully!"
        return 0
    else
        print_msg "$RED" "\n❌ Installation validation failed"
        return 1
    fi
}

# Launch Claude Code
launch_claude() {
    print_msg "$BLUE" "\n🚀 Launching Claude Code..."
    print_msg "$YELLOW" "   Please wait while we start the AI assistant...\n"

    cd "$INSTALL_DIR"

    # Ensure paths are set
    export PATH="$HOME/.cargo/bin:$PATH"
    export PNPM_HOME="${PNPM_HOME:-$HOME/.local/share/pnpm}"
    export PATH="$PNPM_HOME:$PATH"

    # Activate virtual environment if it exists
    if [ -f "$INSTALL_DIR/.venv/bin/activate" ]; then
        source "$INSTALL_DIR/.venv/bin/activate"
    fi

    # Launch Claude Code
    if command_exists claude; then
        exec claude
    elif [ -f "$PNPM_HOME/claude" ]; then
        exec "$PNPM_HOME/claude"
    else
        print_msg "$YELLOW" "Claude CLI not in PATH. Try running:"
        print_msg "$YELLOW" "  cd $INSTALL_DIR && claude"
        print_msg "$YELLOW" "Or restart your shell and run 'claude' from the amplifier directory"
    fi
}

# Check for existing installation
check_existing_installation() {
    local dirs_to_check=(
        "./amplifier"
        "$HOME/amplifier"
        "${AMPLIFIER_HOME:-}"
    )

    for dir in "${dirs_to_check[@]}"; do
        if [ -n "$dir" ] && [ -d "$dir" ] && [ -f "$dir/Makefile" ]; then
            echo "$dir"
            return 0
        fi
    done
    return 1
}

# Prompt for installation directory
prompt_install_directory() {
    print_msg "$YELLOW" "\n📁 Where would you like to install Amplifier?"
    print_msg "$YELLOW" "   (This will create an 'amplifier' directory at the location)"

    local default_dir="$DEFAULT_INSTALL_DIR"
    local existing_dir

    if existing_dir=$(check_existing_installation); then
        print_msg "$YELLOW" "\n   ⚠️  Found existing installation at: $existing_dir"
        if prompt_yes_no "   Use existing location?"; then
            echo "$existing_dir"
            return 0
        fi
    fi

    local install_path
    install_path=$(prompt_input "Installation path" "$default_dir")

    # Expand path and ensure it's absolute or relative to current directory
    if [[ "$install_path" == /* ]]; then
        # Absolute path
        echo "$install_path"
    elif [[ "$install_path" == ~* ]]; then
        # Home directory relative
        echo "${install_path/#\~/$HOME}"
    else
        # Relative to current directory
        echo "$(pwd)/$install_path"
    fi
}

# Check prerequisites interactively
check_prerequisites_interactive() {
    print_msg "$BLUE" "\n🔍 Checking prerequisites..."
    echo ""

    local all_good=true
    local missing_items=()

    # Check Python
    if check_python_version; then
        print_msg "$GREEN" "  ✓ Python ${REQUIRED_PYTHON_VERSION}+ found"
    else
        print_msg "$YELLOW" "  ⚠ Python ${REQUIRED_PYTHON_VERSION}+ not found (will install)"
        missing_items+=("Python ${REQUIRED_PYTHON_VERSION}+")
        all_good=false
    fi

    # Check UV
    if command_exists uv || [ -f "$HOME/.cargo/bin/uv" ]; then
        print_msg "$GREEN" "  ✓ UV package manager found"
    else
        print_msg "$YELLOW" "  ⚠ UV not found (will install)"
        missing_items+=("UV package manager")
        all_good=false
    fi

    # Check Node.js
    if command_exists node; then
        print_msg "$GREEN" "  ✓ Node.js found ($(node --version))"
    else
        print_msg "$YELLOW" "  ⚠ Node.js not found (will install)"
        missing_items+=("Node.js")
        all_good=false
    fi

    # Check pnpm
    if command_exists pnpm || [ -f "$HOME/.local/share/pnpm/pnpm" ]; then
        print_msg "$GREEN" "  ✓ pnpm found"
    else
        print_msg "$YELLOW" "  ⚠ pnpm not found (will install)"
        missing_items+=("pnpm")
        all_good=false
    fi

    # Check Claude CLI
    if command_exists claude || [ -f "$HOME/.local/share/pnpm/claude" ]; then
        print_msg "$GREEN" "  ✓ Claude CLI found"
    else
        print_msg "$YELLOW" "  ⚠ Claude CLI not found (will install)"
        missing_items+=("Claude CLI")
        all_good=false
    fi

    echo ""

    if [ "$all_good" = false ]; then
        print_msg "$YELLOW" "The installer will automatically install:"
        for item in "${missing_items[@]}"; do
            print_msg "$YELLOW" "  • $item"
        done
        echo ""

        if ! prompt_yes_no "Continue with installation?"; then
            print_msg "$YELLOW" "\nInstallation cancelled. You can run this installer again anytime."
            exit 0
        fi
    else
        print_msg "$GREEN" "All prerequisites are already installed! 🎉"
    fi
}

# Main installation flow
main() {
    print_header

    # Parse arguments
    local force_install=false
    local skip_launch=false
    local auto_launch=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --force)
                force_install=true
                shift
                ;;
            --no-launch)
                skip_launch=true
                shift
                ;;
            --yes|-y)
                INTERACTIVE_MODE=false
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  -y, --yes     Run in non-interactive mode with defaults"
                echo "  --force       Force reinstall even if already installed"
                echo "  --no-launch   Don't launch Claude Code after installation"
                echo "  --help        Show this help message"
                echo ""
                echo "Environment variables:"
                echo "  AMPLIFIER_HOME  Override default installation directory"
                exit 0
                ;;
            *)
                die "Unknown option: $1"
                ;;
        esac
    done

    # Welcome message for interactive mode
    if [ "$INTERACTIVE_MODE" = true ]; then
        print_msg "$GREEN" "Welcome to the Amplifier installer!"
        print_msg "$YELLOW" "This installer will set up everything you need to run Amplifier."
        print_msg "$YELLOW" "Press ENTER to accept defaults at any prompt.\n"

        # Check if we can resume a previous installation
        if load_preferences; then
            print_msg "$YELLOW" "Found previous installation attempt."
            if prompt_yes_no "Resume from where you left off?"; then
                print_msg "$GREEN" "Resuming installation...\n"
            else
                rm -f "$RESUME_FILE"
                INSTALL_DIR=""
            fi
        fi
    fi

    # Detect platform
    PLATFORM=$(detect_platform)
    print_msg "$BLUE" "🖥️  Detected platform: $PLATFORM"

    if [ "$PLATFORM" = "unknown" ]; then
        die "Unsupported platform"
    fi

    # Get installation directory
    if [ -z "$INSTALL_DIR" ]; then
        if [ -n "${AMPLIFIER_HOME:-}" ]; then
            INSTALL_DIR="$AMPLIFIER_HOME"
            print_msg "$BLUE" "Using AMPLIFIER_HOME: $INSTALL_DIR"
        else
            INSTALL_DIR=$(prompt_install_directory)
        fi
    fi

    # Make path absolute if relative
    if [[ "$INSTALL_DIR" != /* ]]; then
        INSTALL_DIR="$(cd "$(dirname "$INSTALL_DIR")" 2>/dev/null && pwd)/$(basename "$INSTALL_DIR")"
    fi

    # Set state file path
    STATE_FILE="$INSTALL_DIR/.install_state"

    print_msg "$BLUE" "\n📍 Installation directory: $INSTALL_DIR"

    # Check if already installed
    if [ -f "$STATE_FILE" ] && [ "$force_install" = false ]; then
        print_msg "$YELLOW" "\nAmplifier appears to be already installed at this location."

        if [ "$INTERACTIVE_MODE" = true ]; then
            if prompt_yes_no "Would you like to launch Claude Code now?"; then
                launch_claude
                exit 0
            else
                print_msg "$YELLOW" "Use --force to reinstall or just run 'claude' from $INSTALL_DIR"
                exit 0
            fi
        else
            # Still try to launch if not skipped
            if [ "$skip_launch" = false ]; then
                launch_claude
            fi
            exit 0
        fi
    fi

    # Check prerequisites
    check_prerequisites_interactive

    # Initialize state tracking
    init_state
    save_preferences "init"

    # Installation steps
    print_msg "$BLUE" "\n📦 Starting installation...\n"

    extract_payload
    save_preferences "extract"

    install_python "$PLATFORM"
    save_preferences "python"

    install_uv
    save_preferences "uv"

    install_node "$PLATFORM"
    save_preferences "node"

    install_pnpm
    save_preferences "pnpm"

    install_claude_cli
    save_preferences "claude_cli"

    setup_python_env
    save_preferences "python_env"

    # Shell configuration with interactive prompt
    if [ "$INTERACTIVE_MODE" = true ]; then
        print_msg "$YELLOW" "\n🐚 Shell configuration"
        print_msg "$YELLOW" "   The installer can update your shell configuration to add:"
        print_msg "$YELLOW" "   • UV package manager to PATH"
        print_msg "$YELLOW" "   • pnpm global packages to PATH"
        print_msg "$YELLOW" "   • AMPLIFIER_HOME environment variable"

        if prompt_yes_no "\n   Update shell configuration?"; then
            update_shell_config
        else
            print_msg "$YELLOW" "   Skipping shell configuration."
            print_msg "$YELLOW" "   You may need to manually add paths to your shell config."
        fi
    else
        update_shell_config
    fi

    save_preferences "shell_config"

    # Validate installation
    if validate_installation; then
        mark_completed "installation"

        # Clean up resume file on success
        rm -f "$RESUME_FILE"

        print_msg "$GREEN" "\n🎉 Amplifier installed successfully!"
        print_msg "$BLUE" "Installation directory: $INSTALL_DIR"

        # Interactive launch prompt
        if [ "$INTERACTIVE_MODE" = true ] && [ "$skip_launch" = false ]; then
            echo ""
            print_msg "$GREEN" "🚀 Ready to launch Claude Code!"
            print_msg "$YELLOW" "   Claude Code is the AI assistant that will help you use Amplifier."

            if prompt_yes_no "\n   Launch Claude Code now?"; then
                auto_launch=true
            else
                print_msg "$BLUE" "\n   To launch Claude Code later:"
                print_msg "$BLUE" "   1. Navigate to: cd $INSTALL_DIR"
                print_msg "$BLUE" "   2. Run: claude"
            fi
        fi

        # Launch Claude Code if requested
        if [ "$auto_launch" = true ] || ([ "$INTERACTIVE_MODE" = false ] && [ "$skip_launch" = false ]); then
            launch_claude
        fi
    else
        print_msg "$RED" "\n❌ Installation completed with errors."
        print_msg "$YELLOW" "   You can resume the installation by running this installer again."
        die "Please check the output above for error details."
    fi
}

# Trap errors and cleanup
trap 'echo "Installation failed. Please check the error messages above."' ERR

# Run main function
main "$@"

exit 0

__ARCHIVE_BELOW__
EOF
}

# Main build process
main() {
    print_msg "$BLUE" "Building Amplifier self-extracting installer..."

    # Clean up any previous builds
    cleanup
    mkdir -p "$BUILD_DIR"

    # Create the installer header script
    print_msg "$YELLOW" "Creating installer script header..."
    create_installer_header

    # Create the archive with exclusions
    print_msg "$YELLOW" "Creating compressed archive..."
    cd "$PROJECT_ROOT"

    # Build exclusion arguments for tar
    local exclude_args=""
    if [ -f ".tarignore" ]; then
        while IFS= read -r pattern; do
            # Skip comments and empty lines
            [[ "$pattern" =~ ^#.*$ ]] && continue
            [[ -z "$pattern" ]] && continue
            exclude_args="$exclude_args --exclude=$pattern"
        done < .tarignore
    fi

    # Create archive with progress indication
    print_msg "$YELLOW" "Creating archive (this may take a moment)..."

    # Create the archive
    tar czf "$BUILD_DIR/$ARCHIVE_NAME" \
        $exclude_args \
        --transform 's,^,amplifier/,' \
        --exclude="./build" \
        --exclude="build" \
        --exclude="install_amplifier.sh" \
        --exclude="install_amplifier_header.sh" \
        --exclude="./.venv" \
        --exclude=".venv" \
        --exclude="./.git" \
        --exclude=".git" \
        .

    # Get archive size
    ARCHIVE_SIZE=$(du -h "$BUILD_DIR/$ARCHIVE_NAME" | cut -f1)
    print_msg "$GREEN" "Archive created: $ARCHIVE_SIZE"

    # Combine script and archive
    print_msg "$YELLOW" "Creating self-extracting installer..."
    cp "$INSTALLER_SCRIPT" "$OUTPUT_FILE"
    cat "$BUILD_DIR/$ARCHIVE_NAME" >> "$OUTPUT_FILE"
    chmod +x "$OUTPUT_FILE"

    # Get final size
    FINAL_SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)

    # Clean up
    cleanup

    # Success message
    print_msg "$GREEN" "✅ Installer built successfully!"
    print_msg "$GREEN" "   File: $OUTPUT_FILE"
    print_msg "$GREEN" "   Size: $FINAL_SIZE"
    print_msg "$BLUE" "\nTo use the installer:"
    print_msg "$BLUE" "  1. Share the file: $OUTPUT_FILE"
    print_msg "$BLUE" "  2. Run: bash $OUTPUT_FILE"
    print_msg "$BLUE" "  3. Or make executable: chmod +x $OUTPUT_FILE && $OUTPUT_FILE"
}

# Run main function
main "$@"