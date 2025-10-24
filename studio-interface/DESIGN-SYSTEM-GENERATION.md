# Design System Generation - Architecture & Implementation Plan

**How Studio generates complete, production-ready design systems**

---

## Philosophy

Studio generates a complete design system tailored to the user's purpose, context, and sensibility. This document outlines how we architect generative design as an Amplified Design capability, not just a Studio feature.

### Core Insight

From FRAMEWORK.md: Design is nine-dimensional (Style, Behaviors, Voice, Space, Color, Typography, Proportion, Texture, Body). A design system must express **coherent decisions** across all dimensions, not just generate random components.

From PHILOSOPHY.md: **Purpose Drives Execution**. We don't generate components first—we understand intent, then manifest it systematically.

---

## The Three-Tier System

### Tier 1: Components (Primitives)
**What**: Atomic UI elements that compose into interfaces
**Examples**: Buttons, inputs, cards, badges, avatars, toggles
**Shadcn equivalent**: https://ui.shadcn.com/docs/components

### Tier 2: Blocks (Compositions)
**What**: Pre-composed patterns combining multiple components
**Examples**: Hero sections, pricing tables, testimonial grids, feature comparisons
**Shadcn equivalent**: https://ui.shadcn.com/blocks

### Tier 3: Charts (Data Visualization)
**What**: Specialized components for displaying data
**Examples**: Area charts, bar charts, line charts, pie charts, radar charts
**Shadcn equivalent**: https://ui.shadcn.com/charts

---

## The Taxonomy: Building Blocks of a Design System

### Component Categories

#### 1. **Actions**
*Interactive elements that trigger behavior*

- **Button** - Primary, secondary, tertiary, ghost, destructive
- **IconButton** - Compact action triggers
- **LinkButton** - Navigation actions
- **FloatingActionButton** - Prominent primary actions
- **DropdownMenu** - Contextual action lists
- **ContextMenu** - Right-click/long-press actions

#### 2. **Forms & Input**
*Data entry and selection*

- **Input** - Text, email, password, search
- **Textarea** - Multi-line text input
- **Select** - Dropdown selection
- **Checkbox** - Boolean/multiple selection
- **Radio** - Single selection from options
- **Switch** - Toggle states
- **Slider** - Range selection
- **DatePicker** - Date/time selection
- **Combobox** - Searchable select

#### 3. **Display**
*Information presentation*

- **Card** - Contained content blocks
- **Badge** - Status indicators, counts
- **Avatar** - User representation
- **Tooltip** - Contextual help
- **Alert** - Feedback messages
- **Toast** - Temporary notifications
- **Progress** - Loading states
- **Skeleton** - Content placeholders
- **Separator** - Visual dividers

#### 4. **Layout**
*Structure and organization*

- **Container** - Content width constraints
- **Grid** - Multi-column layouts
- **Stack** - Vertical/horizontal spacing
- **Tabs** - Tabbed navigation
- **Accordion** - Collapsible sections
- **Collapsible** - Show/hide content
- **Drawer** - Slide-in panels
- **Dialog** - Modal overlays
- **Popover** - Floating content

#### 5. **Navigation**
*Wayfinding and hierarchy*

- **NavigationMenu** - Top-level navigation
- **Breadcrumb** - Location hierarchy
- **Pagination** - Multi-page navigation
- **CommandMenu** - Keyboard-driven actions (⌘K)
- **SideNav** - Vertical navigation

#### 6. **Data**
*Structured information display*

- **Table** - Tabular data with sorting/filtering
- **DataTable** - Advanced table with features
- **Calendar** - Date grid view
- **Timeline** - Chronological events

### Block Categories

#### 1. **Heroes**
*Landing page focal points*

- Center-aligned with CTA
- Split (text + visual)
- Video background
- Animated gradient
- Product showcase

#### 2. **Features**
*Product capability showcases*

- Icon grid (3/4/6 columns)
- Bento grid (asymmetric)
- Alternating sections
- Timeline presentation
- Comparison table

#### 3. **Testimonials**
*Social proof and reviews*

- Carousel
- Grid layout
- Featured quote + grid
- Video testimonials
- Star ratings + quotes

#### 4. **Pricing**
*Monetization presentation*

- Tiered cards (3-column)
- Comparison table
- Toggle (monthly/annual)
- Feature breakdown
- Usage-based calculator

#### 5. **Content**
*Blog, articles, documentation*

- Article grid
- Feature callout
- Code example
- FAQ accordion
- Table of contents

#### 6. **Conversion**
*Lead capture and action*

- Newsletter signup
- Contact form
- Waitlist
- Early access
- Demo request

### Chart Categories

Based on data type and purpose:

#### 1. **Trend Analysis**
- **Line Chart** - Time-series data
- **Area Chart** - Cumulative values
- **Stacked Area** - Multiple series composition

#### 2. **Comparison**
- **Bar Chart** - Category comparison
- **Column Chart** - Vertical comparison
- **Grouped Bar** - Multi-series comparison
- **Radar Chart** - Multi-axis comparison

#### 3. **Composition**
- **Pie Chart** - Part-to-whole
- **Donut Chart** - Part-to-whole with center space
- **Stacked Bar** - Category composition

#### 4. **Distribution**
- **Histogram** - Frequency distribution
- **Scatter Plot** - Correlation/clustering

---

## The Discovery-to-Generation Flow

### Phase 1: Discovery (What We Already Have)
**Component**: `DiscoveryConversation.tsx`

Claude asks questions to understand:
- **Purpose**: What should this serve?
- **Audience**: Who will use it?
- **Content**: What needs to be communicated?
- **Context**: Where/how will it be used?
- **Constraints**: Technical, budget, timeline

**Output**: Project context object with intent

### Phase 2: Mood Board & Samples (NEW)
**Component**: `MoodBoardExploration.tsx` (to be built)

User explores design directions through:

#### A. Reference Styles
Present curated examples organized by **9-dimensional profile**:

```typescript
interface DesignProfile {
  // The 9 dimensions from FRAMEWORK.md
  style: 'minimalist' | 'humanist' | 'maximalist' | 'brutalist'
  motion: 'instant' | 'responsive' | 'deliberate' | 'expressive'
  voice: 'professional' | 'conversational' | 'playful' | 'authoritative'
  space: 'compact' | 'balanced' | 'generous' | 'dramatic'
  color: 'muted' | 'vibrant' | 'monochrome' | 'gradient'
  typography: 'traditional' | 'modern' | 'display' | 'technical'
  proportion: 'golden-ratio' | 'modular-scale' | 'fibonacci' | 'custom'
  texture: 'flat' | 'subtle-depth' | 'glassmorphism' | 'neumorphism'
  body: 'mobile-first' | 'desktop-first' | 'responsive' | 'adaptive'
}
```

Show 6-8 sample "styles" as full component examples:

**Example 1: "German Car Facility" (Current Studio aesthetic)**
- Style: Minimalist
- Motion: Responsive (250-300ms)
- Voice: Professional
- Space: Generous
- Color: Muted with precise accents
- Typography: Geometric sans (Sora/Geist)
- Proportion: 8px grid
- Texture: Glassmorphism
- Body: Responsive

**Example 2: "SaaS Professional"**
- Style: Humanist
- Motion: Responsive
- Voice: Conversational
- Space: Balanced
- Color: Vibrant blue accent
- Typography: Modern sans
- Proportion: Modular scale
- Texture: Subtle shadows
- Body: Desktop-first

**Example 3: "Creative Studio"**
- Style: Maximalist
- Motion: Expressive (longer, spring-based)
- Voice: Playful
- Space: Dramatic
- Color: Bold gradients
- Typography: Display mixed with modern
- Proportion: Custom asymmetry
- Texture: Rich depth
- Body: Adaptive

#### B. Interactive Refinement
User can adjust each dimension independently:

```tsx
<DimensionSlider
  dimension="motion"
  values={['instant', 'responsive', 'deliberate', 'expressive']}
  onChange={(value) => updateProfile({ motion: value })}
/>
```

Real-time preview shows components updating.

#### C. Inspiration Board
User can upload reference images, and AI analyzes them:

```typescript
interface ImageAnalysis {
  detectedProfile: DesignProfile
  confidence: number
  notes: string[]
  suggestions: string[]
}
```

**Output**: Refined DesignProfile with user preferences

### Phase 3: Component Generation (Enhanced Expression Phase)
**Component**: Enhanced `ExpressionWorkspace.tsx`

#### A. System Foundation Generation

Generate base design tokens:

```typescript
interface DesignTokens {
  colors: {
    primary: ColorScale      // 50-900
    neutral: ColorScale
    accent: ColorScale
    semantic: SemanticColors // success, warning, error, info
  }
  typography: {
    families: {
      heading: string
      body: string
      mono: string
    }
    scale: TypeScale        // xs to 4xl
    weights: number[]
    lineHeights: Record<string, number>
  }
  spacing: {
    unit: number            // Base (usually 4 or 8px)
    scale: number[]         // 0.5x to 20x
  }
  motion: {
    durations: {
      instant: string       // <100ms
      fast: string          // 100-300ms
      normal: string        // 300-500ms
      slow: string          // 500-1000ms
    }
    easings: {
      linear: string
      easeIn: string
      easeOut: string
      spring: string
    }
  }
  radius: {
    none: string
    sm: string
    md: string
    lg: string
    full: string
  }
  shadows: {
    sm: string
    md: string
    lg: string
    xl: string
  }
}
```

#### B. Component Library Generation

For each component category, generate:

1. **Base Component** (TypeScript + React)
2. **Variants** (different styles/sizes)
3. **Documentation** (usage + examples)
4. **Types** (full TypeScript definitions)

Example structure:

```
/design-system
  /tokens
    colors.ts
    typography.ts
    spacing.ts
    motion.ts
  /components
    /button
      Button.tsx
      Button.stories.tsx
      Button.test.tsx
      README.md
    /input
      ...
  /blocks
    /hero
      HeroCenter.tsx
      HeroSplit.tsx
      ...
  /charts
    /area
      AreaChart.tsx
      ...
  globals.css
  package.json
```

#### C. Showcase Interface

Live documentation site showing:

**Component Pages** (like shadcn/ui):
- Interactive examples
- Code snippets
- Prop tables
- Accessibility notes
- Usage guidelines

**Block Gallery**:
- Full-screen previews
- Hover to see code
- One-click copy
- Category filters

**Chart Examples**:
- Live data demos
- Configuration options
- Responsive behavior
- Theme variants

### Phase 4: Export & Delivery
**Component**: `ExportPanel.tsx` (to be built)

User can export:

1. **Full Package** - Complete npm-ready design system
2. **Individual Components** - Cherry-pick specific components
3. **Theme Only** - Just tokens/globals.css
4. **Documentation Site** - Standalone docs (Storybook or custom)
5. **Figma Plugin** - Design tokens → Figma variables

Export formats:
- React + TypeScript
- React + JavaScript
- Vue 3 + TypeScript
- Svelte + TypeScript
- Vanilla HTML/CSS
- Tailwind CSS plugin

---

## Technical Architecture

### Database Schema Addition

```sql
-- Design system versions
create table design_systems (
  id uuid primary key default uuid_generate_v4(),
  project_id uuid references projects(id) on delete cascade,
  version_number integer not null,

  -- The 9-dimensional profile
  profile jsonb not null,

  -- Generated tokens
  tokens jsonb not null,

  -- Component manifest (what was generated)
  components jsonb not null,
  blocks jsonb not null,
  charts jsonb not null,

  -- Export artifacts
  package_json jsonb,
  readme text,

  created_at timestamp with time zone default now(),

  unique(project_id, version_number)
);

-- User-saved mood boards
create table mood_boards (
  id uuid primary key default uuid_generate_v4(),
  project_id uuid references projects(id) on delete cascade,

  -- Reference images (URLs or base64)
  images jsonb not null,

  -- AI analysis of each image
  analyses jsonb not null,

  -- User notes
  notes text,

  created_at timestamp with time zone default now()
);

-- Component customizations
create table component_customizations (
  id uuid primary key default uuid_generate_v4(),
  design_system_id uuid references design_systems(id) on delete cascade,

  component_type text not null,
  component_name text not null,

  -- User modifications
  overrides jsonb not null,

  -- Original generated version (for diffing)
  original jsonb not null,

  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now()
);
```

### AI Integration Points

#### 1. Mood Board Analysis (Vision + Claude)

```typescript
async function analyzeReferenceImage(imageUrl: string): Promise<ImageAnalysis> {
  // Use Claude with vision to analyze
  const analysis = await anthropic.messages.create({
    model: 'claude-3-5-sonnet-20241022',
    messages: [{
      role: 'user',
      content: [
        {
          type: 'image',
          source: { type: 'url', url: imageUrl }
        },
        {
          type: 'text',
          text: `Analyze this design across the 9 dimensions:
          Style, Motion, Voice, Space, Color, Typography, Proportion, Texture, Body.

          For each dimension, identify:
          - Where it falls on the spectrum
          - Specific evidence from the image
          - Suggestions for similar expressions

          Return structured JSON.`
        }
      ]
    }]
  })

  return parseAnalysis(analysis)
}
```

#### 2. Design System Generation (Claude)

```typescript
async function generateDesignSystem(
  profile: DesignProfile,
  context: ProjectContext
): Promise<DesignSystemCode> {
  const prompt = `Generate a complete design system in React + TypeScript.

Design Profile:
${JSON.stringify(profile, null, 2)}

Project Context:
${JSON.stringify(context, null, 2)}

Generate:
1. Design tokens (colors, typography, spacing, motion)
2. Base components (Button, Input, Card, etc.)
3. Component variants based on profile
4. Full TypeScript types
5. CSS-in-JS or Tailwind configuration
6. Accessibility compliance (WCAG AA minimum)

Follow these principles:
- Purpose-driven: Every component serves the project's goals
- Craft: 9.5/10 quality, refined details
- Constraints: Lock critical properties (motion timing, accessibility)
- Incompleteness: Allow user customization where appropriate
- Humans: Full accessibility, diverse context support

Output as structured code with explanatory comments.`

  const response = await anthropic.messages.create({
    model: 'claude-3-5-sonnet-20241022',
    max_tokens: 16000,
    messages: [{ role: 'user', content: prompt }]
  })

  return parseGeneratedCode(response)
}
```

#### 3. Component Refinement (Iterative)

```typescript
async function refineComponent(
  component: GeneratedComponent,
  userFeedback: string
): Promise<GeneratedComponent> {
  // Iterative refinement with context of design profile
  // Similar to discovery conversation but for refinement
}
```

---

## UI/UX Flow

### Visual Design

#### MoodBoardExploration Interface

```
┌─────────────────────────────────────────────────────────┐
│  Studio / Discovery / Mood Board                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Explore design directions                              │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━                            │
│                                                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐               │
│  │ German   │ │ SaaS     │ │ Creative │    [6-8 cards] │
│  │ Car      │ │ Pro      │ │ Studio   │               │
│  │ Facility │ │          │ │          │               │
│  │ [Preview]│ │ [Preview]│ │ [Preview]│               │
│  │ ○ Select │ │ ○ Select │ │ ○ Select │               │
│  └──────────┘ └──────────┘ └──────────┘               │
│                                                          │
│  Refine your selection                                  │
│  ━━━━━━━━━━━━━━━━━━━━━━                                │
│                                                          │
│  Style:      Minimalist ●───────────○ Maximalist       │
│  Motion:     Instant ○────●─────────○ Expressive       │
│  Voice:      Professional ●─────────○ Playful          │
│  Space:      Compact ○──────────●───○ Dramatic         │
│  ...                                                     │
│                                                          │
│  Upload inspiration                                     │
│  ━━━━━━━━━━━━━━━━━━━                                   │
│                                                          │
│  [Drag images or click to upload]                      │
│                                                          │
│  ┌───────────────────────────────────────┐             │
│  │ [Continue to Generation] →            │             │
│  └───────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────┘
```

#### ComponentShowcase Interface

```
┌─────────────────────────────────────────────────────────┐
│  Studio / Your Design System                            │
├─────────┬───────────────────────────────────────────────┤
│         │  Components / Blocks / Charts / Export        │
│ Button  │                                                │
│ Input   │  Button                                        │
│ Card    │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━     │
│ Badge   │                                                │
│ Avatar  │  [Preview with all variants]                  │
│ ...     │                                                │
│         │  Primary  Secondary  Ghost  Destructive       │
│         │                                                │
│         │  Props                                         │
│         │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━     │
│         │  variant: 'primary' | 'secondary' | ...       │
│         │  size: 'sm' | 'md' | 'lg'                     │
│         │  disabled: boolean                            │
│         │  ...                                           │
│         │                                                │
│         │  Code                                          │
│         │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━     │
│         │  ```tsx                                        │
│         │  <Button variant="primary">               │
│         │    Click me                                   │
│         │  </Button>                                    │
│         │  ```                                           │
│         │  [Copy]                                        │
└─────────┴───────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Design MoodBoardExploration component
- [ ] Build dimension slider components
- [ ] Create 6-8 reference style profiles
- [ ] Implement profile selection UI

### Phase 2: AI Integration (Week 2-3)
- [ ] Build image upload + analysis
- [ ] Integrate Claude Vision API
- [ ] Create profile inference from images
- [ ] Build refinement conversation

### Phase 3: Token Generation (Week 3-4)
- [ ] Design token generation logic
- [ ] Build DesignProfile → DesignTokens transformer
- [ ] Create token preview UI
- [ ] Implement token editing

### Phase 4: Component Generation (Week 4-6)
- [ ] Build component template system
- [ ] Create generation prompts for each component type
- [ ] Implement code generation pipeline
- [ ] Add component preview renderer

### Phase 5: Showcase (Week 6-7)
- [ ] Build ComponentShowcase interface
- [ ] Create block gallery
- [ ] Add chart examples
- [ ] Implement code copy/export

### Phase 6: Export (Week 7-8)
- [ ] Build package.json generator
- [ ] Create npm package bundler
- [ ] Add documentation generator
- [ ] Implement export formats

---

## Success Metrics

### Quality Metrics
- Generated components pass WCAG AA (100%)
- Code follows best practices (linted, typed)
- Design coherence across 9 dimensions
- User satisfaction with generation

### Usage Metrics
- Time from discovery to generated system
- Components customized vs. used as-is
- Export format distribution
- User retention (return for new projects)

### Impact Metrics
- Design systems created per month
- Components in production use
- Accessibility improvements (vs. hand-coded)
- Developer time saved

---

## Open Questions

1. **Component Library Size**: Start with 20 core components or 50+?
2. **AI Model**: Use Claude for all generation or specialized models for different tasks?
3. **Versioning**: How do users iterate on generated systems?
4. **Collaboration**: Multi-user editing of design systems?
5. **Figma Integration**: Priority for Figma plugin?

---

## Related Documents

- [FRAMEWORK.md](../FRAMEWORK.md) - 9-dimensional design framework
- [PHILOSOPHY.md](../PHILOSOPHY.md) - Five pillars guiding decisions
- [PRINCIPLES.md](../PRINCIPLES.md) - Quick reference for daily practice
- [FLOW.md](./FLOW.md) - Application phase architecture
- [IMPLEMENTATION-SPEC.md](./IMPLEMENTATION-SPEC.md) - Studio design details

---

**Next Steps**: Review this architecture, validate with user feedback, begin Phase 1 implementation.
