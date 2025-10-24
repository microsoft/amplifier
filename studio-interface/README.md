# Studio Interface

**Your design partner that transforms intent into expression**

An AI-powered design system generator built on the [Amplified Design](../README.md) framework. Studio guides users through discovery, generates complete design systems, and provides a beautiful showcase interface for exploring and exporting components.

---

## What Is Studio?

Studio is a design partner that:

1. **Understands Your Purpose** - Through thoughtful AI conversation
2. **Generates Your System** - Complete design systems following the 9-dimensional framework
3. **Showcases Your Components** - Beautiful documentation like shadcn/ui
4. **Exports Production Code** - Ready to use in any framework

---

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Set Up Environment

Copy the example environment file:

```bash
cp .env.local.example .env.local
```

Add your credentials:
- **Supabase URL & Key** - For database persistence
- **Anthropic API Key** - For Claude AI generation

See [SETUP.md](SETUP.md) for detailed instructions.

### 3. Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

---

## Application Flow

### 1. Empty State
Clean welcome screen inviting users to start a new project.

### 2. Discovery Phase
AI conversation to understand:
- Project purpose and goals
- Target audience
- Content and messaging
- Constraints and requirements
- Desired aesthetic and feeling

### 3. Mood Board (Coming Soon)
Explore design directions:
- Reference styles organized by 9 dimensions
- Interactive sliders to refine preferences
- Upload inspiration images for AI analysis
- Generate design profile

### 4. Expression Phase
**Current Implementation:**
- **Components Tab** - Full component showcase (like shadcn/ui)
  - Category navigation (Actions, Forms, Display, etc.)
  - Component variants with live previews
  - Code examples with copy functionality
  - Props documentation
  - Accessibility guidelines
- **Blocks Tab** - Pre-composed patterns (planned)
- **Charts Tab** - Data visualization (planned)
- **Canvas Mode** - Live design editing (planned)

### 5. Export (Coming Soon)
Export your design system in multiple formats:
- React + TypeScript
- Vue 3 + TypeScript
- Svelte + TypeScript
- Vanilla HTML/CSS
- Tailwind CSS plugin

---

## Key Features

### ✅ Implemented

- **Discovery Conversation** - AI-guided project understanding
- **Component Showcase** - Beautiful documentation interface
  - 6 component categories
  - Tabbed interface (Preview / Code / Props)
  - Live component variants
  - One-click code copying
  - Accessibility features
- **Mode Switching** - Components / Blocks / Charts / Canvas
- **Database Integration** - Supabase persistence ready
- **Claude API Integration** - Real AI conversations
- **Project Management** - Create, save, resume projects

### 🚧 In Progress

- **Mood Board Exploration** - Visual style selection
- **AI Generation** - Complete design system generation
- **Block Gallery** - Pre-composed patterns showcase
- **Chart Examples** - Data visualization library

### 📋 Planned

- **Canvas Mode** - Drag-and-drop design editing
- **Export System** - Multi-framework code generation
- **Version History** - Design iteration tracking
- **Collaboration** - Multi-user projects
- **Figma Plugin** - Design token sync

---

## Architecture

### Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS v4 + Custom CSS
- **State**: Zustand
- **Database**: Supabase (PostgreSQL)
- **AI**: Anthropic Claude (Sonnet 3.5)
- **Fonts**: Sora (headings), Geist (body)

### Project Structure

```
studio-interface/
├── app/
│   ├── api/
│   │   └── chat/          # Claude API endpoint
│   ├── globals.css        # Design system foundation
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Main router (phase switching)
├── components/
│   ├── ComponentShowcase.tsx    # Component documentation
│   ├── DiscoveryConversation.tsx # AI conversation
│   ├── EmptyState.tsx           # Initial screen
│   ├── ExpressionWorkspace.tsx  # Main workspace
│   └── icons/                   # Icon system
├── lib/
│   ├── hooks/             # Custom React hooks
│   └── supabase.ts        # Database client
├── state/
│   └── store.ts           # Zustand store
├── supabase/
│   └── schema.sql         # Database schema
└── [documentation]        # Architecture docs
```

### Key Components

- **[ComponentShowcase](components/ComponentShowcase.tsx)** - Full documentation interface
- **[ExpressionWorkspace](components/ExpressionWorkspace.tsx)** - Main workspace with mode switching
- **[DiscoveryConversation](components/DiscoveryConversation.tsx)** - AI discovery phase
- **[EmptyState](components/EmptyState.tsx)** - Welcome screen

---

## Design Philosophy

Studio is built on the **Five Pillars** from Amplified Design:

### 1. Purpose Drives Execution
Understand **why** before perfecting **how**. Discovery comes first.

### 2. Craft Embeds Care
9.5/10 quality in every detail. Refinement shows respect.

### 3. Constraints Enable Creativity
Strategic limitations unlock better solutions. Lock what matters.

### 4. Intentional Incompleteness
Complete what requires expertise, leave room for expression.

### 5. Design for Humans
Real people with diverse abilities. Accessibility is non-negotiable.

See [PHILOSOPHY.md](../PHILOSOPHY.md) for deep dive.

---

## The 9-Dimensional Framework

Every design decision considers:

1. **Style** - Visual language and personality
2. **Behaviors (Motion)** - Timing, easing, choreography
3. **Voice** - Language and tone
4. **Space** - Layout and hierarchy
5. **Color** - Palette and meaning
6. **Typography** - Fonts and hierarchy
7. **Proportion** - Scale relationships
8. **Texture** - Materiality and depth
9. **Body** - Ergonomics and context

See [FRAMEWORK.md](../FRAMEWORK.md) for complete guide.

---

## Documentation

### Setup & Configuration
- **[SETUP.md](SETUP.md)** - Installation and configuration
- **[.env.local.example](.env.local.example)** - Environment variables

### Architecture & Planning
- **[DESIGN-SYSTEM-GENERATION.md](DESIGN-SYSTEM-GENERATION.md)** - Complete architecture plan
- **[FLOW.md](FLOW.md)** - Application phase flow
- **[IMPLEMENTATION-SPEC.md](IMPLEMENTATION-SPEC.md)** - Design implementation details

### Implementation Details
- **[SHOWCASE-IMPLEMENTATION.md](SHOWCASE-IMPLEMENTATION.md)** - Component showcase summary

### Design Philosophy
- **[FRAMEWORK.md](../FRAMEWORK.md)** - 9-dimensional design framework
- **[PHILOSOPHY.md](../PHILOSOPHY.md)** - Five Pillars guiding principles
- **[PRINCIPLES.md](../PRINCIPLES.md)** - Quick reference guide
- **[VISION.md](../VISION.md)** - Beyond the artifact

---

## Current Status

### ✅ Phase 1: Foundation (Complete)
- Application structure
- Phase-based routing
- Design system CSS
- Component foundation

### ✅ Phase 2: Database & AI (Complete)
- Supabase integration
- Claude API integration
- Project persistence
- Real-time conversations

### ✅ Phase 3: Showcase Interface (Complete)
- ComponentShowcase component
- Mode switching
- Category navigation
- Code display and copy
- Props documentation

### 🚧 Phase 4: Generation (In Progress)
- Mood board exploration
- Design profile creation
- AI-powered generation
- Component library creation

### 📋 Phase 5: Export (Planned)
- Multi-framework support
- Package generation
- Documentation site
- Figma plugin

---

## Running the Application

### Development Mode

```bash
npm run dev
```

Server runs on [http://localhost:3000](http://localhost:3000)

### Build for Production

```bash
npm run build
npm start
```

### Run Tests

```bash
npm test
```

---

## Environment Variables

Required environment variables (see [SETUP.md](SETUP.md)):

```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=your-project-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# Anthropic Claude
ANTHROPIC_API_KEY=your-api-key
```

---

## Contributing

Studio is part of the Amplified Design project. Contributions should:

1. Follow the Five Pillars
2. Consider all 9 dimensions
3. Maintain 9.5/10 quality
4. Include accessibility
5. Document the "why"

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

---

## Roadmap

### Q1 2025
- ✅ Core application structure
- ✅ Discovery conversation
- ✅ Component showcase
- 🚧 Mood board exploration
- 🚧 AI generation pipeline

### Q2 2025
- Block gallery
- Chart library
- Canvas mode
- Version history

### Q3 2025
- Export system
- Multi-framework support
- Collaboration features
- Figma plugin

### Q4 2025
- Advanced customization
- Template library
- Community showcase
- Enterprise features

---

## License

See [LICENSE](../LICENSE) in the main repository.

---

## Support

- **Documentation**: This README and linked docs
- **Issues**: [GitHub Issues](https://github.com/your-org/amplified-design/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/amplified-design/discussions)

---

## Acknowledgments

Studio is built on decades of design research and practice:

- Human-centered design principles
- Accessibility standards (WCAG, ARIA)
- Motion design research
- Design systems best practices
- Open source community

We stand on the shoulders of giants.

---

Studio transforms intent into expression. Your design partner, powered by AI. Built on principled sensibility.

🚀 [Get Started](SETUP.md) | 📖 [Documentation](DESIGN-SYSTEM-GENERATION.md) | 🎨 [Philosophy](../PHILOSOPHY.md)
