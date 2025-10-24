#!/bin/bash

# Design System Capability - Installation Script
# This script installs the portable design intelligence into your project

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Banner
echo -e "${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║      Design System Capability - Installation                 ║
║                                                               ║
║      Portable design intelligence for AI-guided              ║
║      component customization                                  ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo -e "${RED}Error: package.json not found.${NC}"
    echo "Please run this script from your project root."
    exit 1
fi

echo -e "${BLUE}📦 Installing Design System Capability...${NC}\n"

# Determine installation directory
INSTALL_DIR="./src/design-system"
if [ -d "./app" ]; then
    # Next.js project
    INSTALL_DIR="./app/design-system"
elif [ -d "./src" ]; then
    # Standard React project
    INSTALL_DIR="./src/design-system"
else
    # Fallback
    INSTALL_DIR="./design-system"
fi

echo -e "${YELLOW}→${NC} Installation directory: ${INSTALL_DIR}"

# Create directory structure
echo -e "${YELLOW}→${NC} Creating directory structure..."
mkdir -p "$INSTALL_DIR/components"
mkdir -p "$INSTALL_DIR/knowledge-base"
mkdir -p "$INSTALL_DIR/agents"
mkdir -p "$INSTALL_DIR/quality-guardrails"

# Get the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Copy files
echo -e "${YELLOW}→${NC} Copying components..."
cp -r "$SCRIPT_DIR/components/"* "$INSTALL_DIR/components/"

echo -e "${YELLOW}→${NC} Copying knowledge base..."
cp -r "$SCRIPT_DIR/knowledge-base/"* "$INSTALL_DIR/knowledge-base/"

echo -e "${YELLOW}→${NC} Copying agent definitions..."
cp -r "$SCRIPT_DIR/agents/"* "$INSTALL_DIR/agents/"

echo -e "${YELLOW}→${NC} Copying quality guardrails..."
cp -r "$SCRIPT_DIR/quality-guardrails/"* "$INSTALL_DIR/quality-guardrails/"

echo -e "${YELLOW}→${NC} Copying documentation..."
cp "$SCRIPT_DIR/README.md" "$INSTALL_DIR/README.md"

# Create index file for easy imports
echo -e "${YELLOW}→${NC} Creating index exports..."
cat > "$INSTALL_DIR/index.ts" << 'EOF'
// Design System Capability - Main Exports

// Components
export { HeroButton } from './components/hero-button-refined/HeroButton';
export type { HeroButtonProps } from './components/hero-button-refined/HeroButton';

// Future components will be exported here
// export { Card } from './components/card-refined/Card';
// export { Input } from './components/input-refined/Input';
EOF

# Check if React and TypeScript are installed
echo -e "\n${BLUE}🔍 Checking dependencies...${NC}"

HAS_REACT=false
HAS_TYPESCRIPT=false

if grep -q '"react"' package.json; then
    HAS_REACT=true
    echo -e "${GREEN}✓${NC} React found"
else
    echo -e "${RED}✗${NC} React not found"
fi

if grep -q '"typescript"' package.json || [ -f "tsconfig.json" ]; then
    HAS_TYPESCRIPT=true
    echo -e "${GREEN}✓${NC} TypeScript found"
else
    echo -e "${YELLOW}!${NC} TypeScript not found (optional)"
fi

# Installation complete
echo -e "\n${GREEN}✅ Installation complete!${NC}\n"

# Usage instructions
echo -e "${BLUE}📚 Getting Started:${NC}\n"

echo -e "${YELLOW}1.${NC} Import the Hero Button:"
if [ "$HAS_TYPESCRIPT" = true ]; then
    echo -e "   ${BLUE}import { HeroButton } from '${INSTALL_DIR}/index';${NC}\n"
else
    echo -e "   ${BLUE}import { HeroButton } from '${INSTALL_DIR}';${NC}\n"
fi

echo -e "${YELLOW}2.${NC} Use in your component:"
cat << 'EOF'
   <HeroButton
     variant="magnetic"
     size="lg"
     onClick={() => console.log('clicked')}
   >
     Get Started
   </HeroButton>

EOF

echo -e "${YELLOW}3.${NC} Read the documentation:"
echo -e "   ${BLUE}${INSTALL_DIR}/README.md${NC}"
echo -e "   ${BLUE}${INSTALL_DIR}/components/hero-button-refined/README.md${NC}\n"

echo -e "${YELLOW}4.${NC} Explore the knowledge base:"
echo -e "   ${BLUE}${INSTALL_DIR}/knowledge-base/color-theory.md${NC}"
echo -e "   ${BLUE}${INSTALL_DIR}/knowledge-base/animation-principles.md${NC}"
echo -e "   ${BLUE}${INSTALL_DIR}/knowledge-base/accessibility.md${NC}"
echo -e "   ${BLUE}${INSTALL_DIR}/knowledge-base/typography.md${NC}\n"

echo -e "${YELLOW}5.${NC} Use AI agents for customization:"
echo -e "   Share the agent definitions with your AI assistant:"
echo -e "   ${BLUE}${INSTALL_DIR}/agents/customization-guide.md${NC}"
echo -e "   ${BLUE}${INSTALL_DIR}/agents/quality-guardian.md${NC}\n"

# Check for missing dependencies
if [ "$HAS_REACT" = false ]; then
    echo -e "${RED}⚠️  Warning:${NC} React not found. Install with:"
    echo -e "   ${BLUE}npm install react react-dom${NC}\n"
fi

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Ready to build exceptional interfaces!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}\n"

# Ask if user wants to see an example
read -p "Would you like to see a complete example? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "\n${BLUE}Example: Hero Section Button${NC}\n"
    cat << 'EOF'
import { HeroButton } from './design-system';
import { ArrowRight } from 'lucide-react'; // or your icon library

function HeroSection() {
  return (
    <section className="hero">
      <h1>Transform Your Workflow</h1>
      <p>AI-powered productivity for modern teams</p>

      <HeroButton
        variant="magnetic"
        size="lg"
        icon={<ArrowRight size={24} />}
        iconPosition="right"
        onClick={() => window.location.href = '/signup'}
      >
        Start Free Trial
      </HeroButton>
    </section>
  );
}

export default HeroSection;
EOF
    echo
fi

exit 0
