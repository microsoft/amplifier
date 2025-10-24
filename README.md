# Amplified Design

> **A complete design intelligence system that amplifies human creativity through purpose-driven methodology, AI guidance, and quality guardrails.**

---

## What Is Amplified Design?

Amplified Design is not just a design system or component library—it's a complete **design intelligence framework** that changes how we think about and create digital experiences.

We're solving a fundamental problem: **AI-generated designs are generic (5/10 quality). Customization breaks the few good parts. Every output looks the same.**

**Amplified Design's approach:**
- Start with exceptional quality (9.5/10 baseline)
- Guide through purpose-first design methodology
- Provide AI agents for validation and guidance
- Enforce quality through intelligent guardrails
- Generate working prototypes, not just mockups
- Learn and adapt to your design sensibility over time

---

## The System

Amplified Design consists of six interconnected parts:

### 1. The Framework
A proven 4-layer methodology with 9 dimensions of expression:
- **Layer 1**: Purpose & Intent (What and Why)
- **Layer 2**: Expression & Manifestation (How)
- **Layer 3**: Context & Appropriateness (For Whom)
- **Layer 4**: Contextual Adaptation (Across Modalities)

**[Learn the complete framework →](./FRAMEWORK.md)**

### 2. The Philosophy
Five foundational pillars that guide every decision:
- Purpose Drives Execution
- Craft Embeds Care
- Constraints Enable Creativity
- Intentional Incompleteness
- Design for Humans

**[Deep dive into philosophy →](./PHILOSOPHY.md)**

### 3. Studio Interface
The interactive design partner that implements the methodology:
- Progressive discovery system
- Interactive prototype generation
- AI-guided customization
- Content-aware recommendations
- Currently in active development

**[View Studio development →](./studio-interface/)**

### 4. Knowledge Base
Comprehensive design theory and research:
- Color systems and psychology
- Typography principles
- Animation and motion design
- Accessibility standards
- Interaction patterns

**[Browse knowledge base →](./knowledge-base/)**

### 5. AI Agents
Intelligent validation and guidance:
- Quality Guardian (validates 9.5/10 standard)
- Customization Guide (recommends safe modifications)
- Requirements Architect (clarifies purpose)
- UX Wireframe Designer (visualizes concepts)

**[See agent system →](./agents/)**

### 6. Quality Guardrails
Automated validation and standards enforcement:
- CSS token validation
- TypeScript type checking
- Accessibility compliance
- Performance benchmarks
- Design system consistency

**[Review guardrails →](./quality-guardrails/)**

---

## Current State

Amplified Design is in **active development** using its own methodology. We're practicing what we're building.

**What exists now:**
- Complete framework documentation (4 layers, 9 dimensions)
- Five Pillars philosophy and principles
- Studio interface foundation (Next.js, TypeScript)
- AI agent system (4 specialized agents)
- Quality validation tools
- Comprehensive knowledge base
- Discovery workspace implementation

**What we're building:**
- Full Studio interface with progressive discovery
- Component library with 9.5/10 baseline quality
- Interactive prototype generation
- AI-guided design customization
- Real-time quality validation

**[View the design discovery process →](./DISCOVERY.md)**

---

## The Philosophy: Beyond the Artifact

**Remember:** The code is just the container, not the product.

When you ship a button component, you're shipping:
- How someone **feels** when they click it
- What **values** your team embodies
- What **culture** you're creating
- What **impact** you have on the world

### Three Levels of Experience

1. **Individual Experience**: Do they feel heard, confirmed, respected, trust?
2. **Social Experience**: Do teams feel empowered, confident, collaborative, proud?
3. **Cultural Experience**: Does it shift expectations, demand accessibility, question mediocrity?

**[Read the complete vision →](./VISION.md)**

---

## Quick Start (For Developers)

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/amplified-design.git
cd amplified-design

# Install dependencies
npm install

# Start Studio interface in development
cd studio-interface
npm run dev
```

### Development Commands

```bash
# Validate design tokens
npm run validate:tokens

# TypeScript type checking
npx tsc --noEmit

# Build Studio interface
npm run build

# Development server (Studio)
npm run dev
```

### Working with the System

Before creating or modifying any component:

```
□ Can articulate WHY in one sentence?
□ All tokens defined in globals.css?
□ Follows 8px spacing system?
□ Meets contrast requirements?
□ Touch targets 44x44px+?
□ Motion timing follows protocol?
□ Keyboard accessible?
```

**[Read complete development guide →](./CLAUDE.md)**

---

## The Four-Layer Methodology

### Layer 1: Purpose & Intent
**What should exist and why?**
- Should this exist? (Necessity)
- What problem does this solve? (Function)
- For whom? (Audience)
- Why now? (Timing and context)
- What values does this embody? (Ethics)

### Layer 2: Expression & Manifestation
**How should it look, feel, and behave?**

**Nine Dimensions:**
1. Style - Visual language
2. Motion - Timing and choreography
3. Voice - Language and tone
4. Space - Layout and hierarchy
5. Color - Meaning and accessibility
6. Typography - Hierarchy and readability
7. Proportion - Scale and balance
8. Texture - Depth and materiality
9. Body - Physical ergonomics

### Layer 3: Context & Appropriateness
**Where and when does this work?**
- Cultural context
- Audience expectations
- Industry conventions
- Pattern recognition

### Layer 4: Contextual Adaptation
**How does it adapt across modalities?**
- Desktop (precision, rich information)
- Mobile (thumb zones, simplified)
- Voice (conversational, sequential)
- Emerging platforms (AR/VR, spatial)

---

## Quality Standards

Every component and system maintains:
- **9.5/10 quality baseline** - Refined, not generic
- **WCAG AA accessibility** - Works for everyone
- **60fps performance** - GPU-accelerated animations
- **Full keyboard support** - Navigate without a mouse
- **Reduced motion support** - Respects user preferences

---

## Project Structure

```
amplified-design/
├── studio-interface/          # Studio interface (Next.js app)
│   ├── app/                  # Pages and routes
│   ├── components/           # React components
│   ├── state/                # Zustand state management
│   └── public/               # Static assets
├── packages/                  # Modular packages
│   └── interactions/         # Interaction patterns
├── components/               # Design components library
├── agents/                   # AI agents for guidance
├── quality-guardrails/       # Validation rules
├── knowledge-base/           # Design theory documentation
├── .design/                  # Design documentation
│   ├── AESTHETIC-GUIDE.md
│   └── COMPONENT-CREATION-PROTOCOL.md
├── FRAMEWORK.md             # Complete methodology
├── PHILOSOPHY.md            # Five Pillars deep dive
├── PRINCIPLES.md            # Quick reference guide
├── VISION.md                # Beyond the artifact
├── DISCOVERY.md             # Current development process
├── PROGRESS.md              # Development timeline
└── CONTRIBUTING.md          # Contribution guidelines
```

---

## Technology Stack

- **Framework**: Next.js 14+ (React 18+)
- **Language**: TypeScript
- **Styling**: CSS3 with CSS Variables
- **State Management**: Zustand
- **Icons**: Custom Icon component (24x24 grid, 2px stroke)
- **Fonts**: Sora (headings), Geist Sans (body), Geist Mono (code)
- **Validation**: Custom token validator, TypeScript compiler

---

## Amplifier Integration

This repository includes **Amplifier** - a complementary system for AI-amplified development workflows. Amplifier provides:
- Knowledge synthesis
- Parallel exploration tools
- Automation utilities
- Development workflow optimization

**[Learn about Amplifier →](./amplifier/AMPLIFIER_VISION.md)**

---

## Contributing

We welcome contributions that maintain:
- The 9.5/10 quality baseline
- Accessibility standards (WCAG AA minimum)
- Design system consistency
- Purpose-first methodology
- The Five Pillars principles

**Before contributing:**
1. Read [CLAUDE.md](./CLAUDE.md) for development guidelines
2. Review [CONTRIBUTING.md](./CONTRIBUTING.md) for process
3. Check [.design/COMPONENT-CREATION-PROTOCOL.md](./.design/COMPONENT-CREATION-PROTOCOL.md)
4. Understand the [FRAMEWORK.md](./FRAMEWORK.md) methodology

---

## Documentation

### Core Philosophy
- [VISION.md](./VISION.md) - Beyond the artifact: designing for experience
- [PHILOSOPHY.md](./PHILOSOPHY.md) - The Five Pillars explained
- [PRINCIPLES.md](./PRINCIPLES.md) - Quick reference for daily practice

### Methodology
- [FRAMEWORK.md](./FRAMEWORK.md) - Complete 4-layer, 9-dimension framework

### Development
- [CLAUDE.md](./CLAUDE.md) - AI assistant guide and development protocols
- [CONTRIBUTING.md](./CONTRIBUTING.md) - Contribution guidelines
- [DISCOVERY.md](./DISCOVERY.md) - Current design discovery process
- [PROGRESS.md](./PROGRESS.md) - Development timeline and milestones

### Design Standards
- [.design/AESTHETIC-GUIDE.md](./.design/AESTHETIC-GUIDE.md) - Visual language guide
- [.design/COMPONENT-CREATION-PROTOCOL.md](./.design/COMPONENT-CREATION-PROTOCOL.md) - Component standards

---

## Built With Care

Amplified Design is built on established research and best practices:
- Human-centered design thinking (IDEO, Norman, Cooper)
- Accessibility standards (WCAG 2.1 AA, ARIA)
- Motion design research (Disney, Issara Willenskomer)
- Design systems patterns (Atomic Design, Design Tokens)
- Interaction design principles (Fitts's Law, Hick's Law)

---

## License

MIT License - See [LICENSE](./LICENSE) for details

---

## Questions & Support

- **Documentation**: Start with [FRAMEWORK.md](./FRAMEWORK.md) and [CLAUDE.md](./CLAUDE.md)
- **Philosophy**: Read [VISION.md](./VISION.md) for the deeper "why"
- **Development**: Check [DISCOVERY.md](./DISCOVERY.md) for current state
- **Issues**: Open a GitHub issue for bugs or questions
- **Contributing**: See [CONTRIBUTING.md](./CONTRIBUTING.md)

---

## The Goal

**Quality at creation beats debugging later.**

Every decision compounds:
- Thousands of micro-decisions across nine dimensions
- Each guided by the Five Pillars
- All serving a clear purpose
- Validated against technical standards
- Tested with real humans

**This is what creates 9.5/10 quality.**

---

**The artifact is the container. The experience is the product. The values are the legacy. The impact is what matters.**

Design accordingly.
