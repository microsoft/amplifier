# Studio Interface - AI Execution Specification

**Status:** Ready for implementation (pending user approval of brief)
**Source:** [ACTIVE-studio-discovery.md](./ACTIVE-studio-discovery.md)
**For:** AI implementation (Claude as designer + developer)
**Connected to:** [TODO-studio-brief-user.md](./TODO-studio-brief-user.md) (User review)

---

## Implementation Overview

**What:** Build `studio-interface/` directory with web application
**How:** Use discovery answers to guide every implementation decision
**Quality:** Match the 9.5/10 baseline we're building the system to enable

---

## Technical Foundation

### Stack Recommendations (TBD - Next Phase)

**Will determine based on requirements:**
- Framework (React/Next.js, Vue/Nuxt, Svelte/SvelteKit)
- Styling (Tailwind, vanilla CSS, CSS-in-JS)
- State management (Context, Zustand, Redux)
- AI integration (Anthropic Claude, OpenAI, custom)
- Storage (Supabase, Firebase, custom)
- Preview system (iframe, separate server, both)

**Decision criteria:**
- Matches "German car facility" aesthetic (clean, precise)
- Supports real-time updates (responsive feel)
- Enables version history (time-travel state)
- Handles multimodal input (text, images, files)
- Allows device preview (simulated + live)

---

## Design Token System

### Colors

```typescript
const colors = {
  // Foundation
  ghostWhite: '#FAFAFF',      // Background
  antiFlashWhite: '#EEF0F2',  // Clean white
  alabaster: '#ECEBE4',        // Warm light gray
  platinum: '#DADDD8',         // Warm mid gray
  eerieBlack: '#1C1C1C',       // Darkest

  // Functional
  aiThinking: 'hsl(217, 90%, 60%)',  // Pulsing blue
  success: 'hsl(142, 70%, 45%)',      // Green
  attention: 'hsl(38, 90%, 50%)',     // Amber
  userMessage: 'hsl(217, 90%, 60%)',  // Blue
  aiMessage: 'hsl(270, 60%, 65%)',    // Purple
}
```

### Typography

```typescript
const typography = {
  fonts: {
    heading: "'Sora', sans-serif",
    body: "'Geist', sans-serif",
    code: "'Source Code Pro', monospace",
  },

  // 1.5× scale for clear hierarchy
  scale: {
    xs: '0.75rem',    // 12px
    sm: '0.875rem',   // 14px
    base: '1rem',     // 16px
    lg: '1.5rem',     // 24px (1.5×)
    xl: '2.25rem',    // 36px (1.5×)
    '2xl': '3.375rem', // 54px (1.5×)
  },

  weights: {
    regular: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  }
}
```

### Behaviors (Motion + Interaction)

```typescript
const behaviors = {
  // Motion timing
  motion: {
    // Instant (<100ms) - UI interactions
    instant: {
      duration: '50ms',
      easing: 'linear',
    },

    // Responsive (200-300ms) - Transitions
    responsive: {
      duration: '250ms',
      easing: 'cubic-bezier(0.4, 0, 0.2, 1)', // ease-in-out
    },

    // Deliberate (400-600ms) - AI generation
    deliberate: {
      duration: '500ms',
      easing: 'cubic-bezier(0.34, 1.56, 0.64, 1)', // spring
    },
  },

  // Interaction patterns
  interactions: {
    hover: {
      timing: 'instant',
      feedback: 'subtle', // Color change, underline
    },
    click: {
      timing: 'responsive',
      feedback: 'medium', // Scale, shadow
    },
    drag: {
      timing: 'instant',
      feedback: 'strong', // Elevation, cursor
    },
    focus: {
      timing: 'instant',
      feedback: 'accessible', // Visible outline
    },
  }
}
```

### Spacing & Proportion

```typescript
const spacing = {
  // 8px base unit
  base: 8,
  scale: [0, 4, 8, 12, 16, 24, 32, 48, 64, 96, 128],

  // Touch targets
  touchMin: 48,        // Minimum
  touchPrimary: 52,    // Primary actions

  // Breakpoints (desktop-first)
  breakpoints: {
    mobile: 640,
    tablet: 768,
    desktop: 1024,
    wide: 1280,
  }
}
```

### Effects (Frosted Glass)

```typescript
const effects = {
  frosted: {
    panel: {
      backdropFilter: 'blur(12px)',
      background: 'rgba(255, 255, 255, 0.8)',
      border: '1px solid rgba(255, 255, 255, 0.2)',
    },

    modal: {
      backdropFilter: 'blur(16px)',
      background: 'rgba(255, 255, 255, 0.9)',
    },
  },

  shadows: {
    subtle: '0 1px 3px rgba(0, 0, 0, 0.05)',
    panel: '0 4px 6px rgba(0, 0, 0, 0.07)',
    elevated: '0 10px 15px rgba(0, 0, 0, 0.1)',
  }
}
```

---

## Nine Dimensions Framework

**Studio's design understanding is structured around nine dimensions:**

1. **Style** - Visual language, aesthetic approach
2. **Behaviors** - Motion timing + interaction patterns (consolidated)
3. **Voice** - Language personality, communication tone
4. **Space** - Layout, hierarchy, spatial relationships
5. **Color** - Meaning, emotion, accessibility
6. **Typography** - Attention direction, content hierarchy
7. **Proportion** - Scale relationships, visual balance
8. **Texture** - Surface quality, depth, materiality
9. **Body** - Physical ergonomics, touch interaction

**Implementation implications:**

```typescript
interface DesignDimensions {
  style: {
    approach: 'minimal' | 'decorative' | 'functional' | 'expressive'
    influences: string[]  // "Brutalism", "Swiss design", etc.
  }

  behaviors: {
    motion: {
      speed: 'instant' | 'responsive' | 'deliberate'
      character: 'linear' | 'spring' | 'custom'
    }
    interactions: {
      hover: InteractionSpec
      click: InteractionSpec
      drag: InteractionSpec
    }
  }

  voice: {
    tone: 'formal' | 'casual' | 'technical' | 'warm'
    vocabulary: string[]
    personality: string
  }

  space: {
    density: 'compact' | 'comfortable' | 'spacious'
    rhythm: number[]  // Spacing scale
    hierarchy: 'flat' | 'layered' | 'deep'
  }

  color: {
    palette: ColorPalette
    contrast: 'AA' | 'AAA'
    meaning: Record<string, string>  // "blue = trust"
  }

  typography: {
    scale: TypographyScale
    families: FontFamilies
    hierarchy: HierarchyRules
  }

  proportion: {
    ratio: number  // 1.5, 1.618, etc.
    balance: 'symmetrical' | 'asymmetrical'
    scale: 'uniform' | 'varied'
  }

  texture: {
    surfaces: 'flat' | 'frosted' | 'gradient' | 'material'
    depth: 'shallow' | 'medium' | 'deep'
    effects: SurfaceEffects
  }

  body: {
    touchTargets: number  // Minimum size
    gestures: string[]    // Supported gestures
    ergonomics: ErgonomicRules
  }
}
```

**Learning system:**
- Each dimension has confidence score (0-1)
- Past projects build sensibility profile
- High confidence → applies without asking
- Low confidence → asks clarifying questions
- User feedback updates dimension understanding

---

## Component Architecture

### Layout Structure

```
studio-interface/
├── Canvas (center, flexible)
│   ├── Preview area
│   ├── Device frame simulation
│   └── Interactive prototype render
│
├── Conversation (right sidebar, collapsible)
│   ├── Message history
│   ├── Input field
│   └── Suggested questions
│
├── Properties (contextual, right panel)
│   ├── Direct manipulation controls
│   ├── Sliders, inputs, pickers
│   └── Apply/reset actions
│
├── History (bottom timeline, collapsible)
│   ├── Version thumbnails
│   ├── Timeline scrubber
│   └── Compare mode
│
└── Inspiration (separate tab/modal)
    ├── Uploaded images
    ├── Reference links
    └── Mood board
```

### Core Components Needed

**1. Canvas Component**
- Renders generated designs (iframe or direct)
- Handles device frame overlay
- Supports zoom/pan
- Click-to-select elements
- Shows loading states (deliberate motion)

**2. Conversation Component**
- Message bubbles (user vs AI colors)
- Typing indicators
- Suggested questions/options
- Collapsible for focus
- Auto-scroll to latest

**3. Properties Panel**
- Contextual (shows based on selection)
- Sliders with live preview
- Color pickers
- Dropdown selectors
- Apply button (responsive motion)

**4. Version History**
- Timeline visualization
- Thumbnail previews
- Hover for quick view
- Click to restore
- Compare mode (side-by-side)

**5. Content Input Modal**
- Large text area (paste scenarios)
- File upload (drag-drop)
- URL input (fetch content)
- Start generation button

**6. Device Preview**
- Device frame overlays (mobile, tablet, watch)
- Simulated view (fast)
- QR code generator (live device)
- Quick device switcher

---

## State Management Architecture

### Core State

```typescript
interface StudioState {
  // Current project
  project: {
    id: string
    name: string
    content: string
    context: DiscoveryContext
  }

  // Design state
  design: {
    current: DesignVersion
    history: DesignVersion[]
    selected: ElementSelection | null
  }

  // Conversation
  conversation: {
    messages: Message[]
    isGenerating: boolean
    suggestedQuestions: string[]
  }

  // UI state
  ui: {
    panels: {
      conversation: boolean
      properties: boolean
      history: boolean
    }
    device: 'desktop' | 'mobile' | 'tablet' | 'watch'
    previewMode: 'simulated' | 'live'
  }

  // User sensibility (learned)
  sensibility: {
    preferences: DesignPreferences
    pastProjects: ProjectSummary[]
    confidence: ConfidenceLevel
  }
}
```

### Version History Implementation

**Requirements:**
- Every change creates version
- Auto-save (no manual save button)
- Efficient storage (delta-based, not full copies)
- Fast restore (responsive motion)
- Visual diff (compare versions)

**Implementation approach:**
- Store as event sourcing (commands applied)
- Reconstruct any version by replaying
- Thumbnail generation for timeline
- Metadata: timestamp, user action, AI confidence

---

## AI Integration Architecture

### Agent Communication

**Customization Guide Agent:**
- Takes: User input + context
- Returns: Design recommendations + questions
- Mode: Progressive discovery (vague → specific)

**Quality Guardian Agent:**
- Takes: Generated design
- Returns: Validation results + suggestions
- Mode: Automated quality checks

**Content Analysis Agent:**
- Takes: Blog post, scenario, etc.
- Returns: Semantic understanding (tone, structure, requirements)
- Mode: Content-first design enablement

### API Integration Points

```typescript
interface AIService {
  // Discovery conversation
  discover(
    userInput: string,
    context: DiscoveryContext
  ): Promise<{
    questions: string[]
    suggestions: DesignOption[]
    confidence: number
  }>

  // Generate design
  generate(
    intent: DesignIntent,
    context: FullContext
  ): Promise<{
    prototype: InteractivePrototype
    spec: DesignSpecification
    components: ComponentLibrary
  }>

  // Refine design
  refine(
    current: Design,
    feedback: UserFeedback
  ): Promise<Design>

  // Analyze content
  analyzeContent(
    content: string
  ): Promise<ContentAnalysis>
}
```

---

## Preview System Architecture

### Simulated Preview (Fast)

**Approach:**
- Render in iframe with device frame CSS
- Apply viewport constraints
- Simulate touch events
- Fast switching (<100ms)

**Device Frames:**
- Mobile: 375×667 (iPhone SE)
- Tablet: 768×1024 (iPad)
- Watch: 184×224 (Apple Watch)
- Desktop: Responsive

### Live Device Preview (Accurate)

**Approach:**
- Generate unique session URL
- QR code for device scanning
- WebSocket for live updates
- Synced state (changes reflect immediately)

**Implementation:**
- Separate preview server route
- Session management (expires after X hours)
- Real-time sync via WebSocket
- Supports multiple devices simultaneously

---

## File Structure

```
studio-interface/
├── src/
│   ├── components/
│   │   ├── Canvas/
│   │   │   ├── Canvas.tsx
│   │   │   ├── DeviceFrame.tsx
│   │   │   └── PreviewRenderer.tsx
│   │   ├── Conversation/
│   │   │   ├── Conversation.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   └── InputField.tsx
│   │   ├── Properties/
│   │   │   ├── PropertiesPanel.tsx
│   │   │   ├── Slider.tsx
│   │   │   └── ColorPicker.tsx
│   │   ├── History/
│   │   │   ├── Timeline.tsx
│   │   │   ├── VersionThumbnail.tsx
│   │   │   └── CompareView.tsx
│   │   └── Inspiration/
│   │       ├── InspirationBoard.tsx
│   │       └── ImageUpload.tsx
│   ├── services/
│   │   ├── ai.ts              # AI agent communication
│   │   ├── storage.ts         # State persistence
│   │   ├── preview.ts         # Preview system
│   │   └── export.ts          # Export specs/code
│   ├── state/
│   │   ├── store.ts           # State management
│   │   ├── history.ts         # Version history
│   │   └── sensibility.ts     # Learning system
│   ├── design-tokens/
│   │   ├── colors.ts
│   │   ├── typography.ts
│   │   ├── motion.ts
│   │   └── spacing.ts
│   └── utils/
│       ├── device-detection.ts
│       ├── content-analysis.ts
│       └── validation.ts
├── public/
│   └── fonts/
│       ├── Sora/
│       ├── Geist/
│       └── SourceCodePro/
└── package.json
```

---

## Implementation Phases

### Phase 1: Core Desktop Experience
**Goal:** Validate methodology with community fundraiser event scenario

**Test scenario:**
"I'm running our local youth arts program's annual fundraiser. We need everything for the event—website, social posts, printed programs, signage, thank you materials. It needs to feel professional but warm, appeal to donors and families, and work across all these formats."

**Build:**
- ✅ Canvas with simulated preview
- ✅ Conversation interface
- ✅ Basic properties panel
- ✅ Version history timeline
- ✅ Content input modal
- ✅ AI integration (discovery + generation)

**Success deliverables:**
- Cohesive event identity across all touchpoints
- Website: Event info, donation flow, program showcase
- Social: Pre-event hype, event day, thank you posts
- Print: Programs (8.5×11 folded), signage (posters), name tags
- Thank you materials: Donor cards, sponsor recognition
- Design system specs + component library
- All materials feel unified, budget-conscious (print optimization)

### Phase 2: Refinement & Polish
**Goal:** Multi-modal refinement, quality polish

**Build:**
- ✅ Direct manipulation (click elements, adjust properties)
- ✅ Inspiration board (upload images, references)
- ✅ Comparison mode (side-by-side alternatives)
- ✅ Live device preview (QR code)
- ✅ Export system (specs, components, code)

**Success:** You can refine through all interaction modes, preview on real device, export outputs

### Phase 3: Tablet Support
**Goal:** Review + light work on tablet

**Build:**
- ✅ Responsive layout for tablet
- ✅ Touch-optimized controls
- ✅ Brainstorming mode
- ✅ Image capture integration

**Success:** You can review/refine work on iPad

### Phase 4: Mobile Support
**Goal:** Capture inspiration, quick checks

**Build:**
- ✅ Mobile-optimized interface
- ✅ Camera integration
- ✅ Voice notes
- ✅ Quick preview mode

**Success:** You can capture inspiration on phone, check designs

---

## Quality Standards

**Every component must:**
- Match German car facility aesthetic (clean, precise, beautiful)
- Use design tokens (no magic numbers)
- Support keyboard navigation (accessibility)
- Have 48px+ touch targets
- Animate with appropriate timing (instant/responsive/deliberate)
- Work with frosted glass aesthetic
- Be responsive (at least desktop + tablet in Phase 1-2)

**Every interaction must:**
- Feel intentional (not accidental)
- Provide feedback (visual, not silent)
- Be reversible (undo/version history)
- Be documented (why this choice?)

**Every AI response must:**
- State confidence level when uncertain
- Ask before expensive operations
- Confirm high-stakes decisions
- Learn from user feedback
- Adapt to user's sensibility

---

## Testing Strategy

### Manual Testing (You provide feedback)

**Test scenarios:**
1. **Community fundraiser event** (comprehensive multi-format scenario)
   - Input: Event description, requirements, constraints
   - Expected: Cohesive identity across web, social, print
   - Validates: Full scope thinking, budget constraints, format optimization

2. [Additional scenarios from Amplifier/scenarios/]
3. Edge cases (vague input, conflicting feedback)

**Validation criteria:**
- Output matches intent
- Has unique fingerprint (not generic templates)
- 9.5/10 quality maintained across all formats
- Process feels collaborative (not interrogative)
- Never overbearing, never reckless
- Budget/practical constraints respected

### Automated Testing

**Unit tests:**
- Design token calculations
- Version history event sourcing
- Content analysis parsing

**Integration tests:**
- AI agent communication
- State management
- Export generation

**Visual regression:**
- Component screenshots
- Motion timing validation

---

## Next Steps

1. **User approval** of [TODO-studio-brief-user.md](./TODO-studio-brief-user.md)
2. **Technical architecture** decision (framework, stack)
3. **Phase 1 implementation** (core desktop experience)
4. **Testing with publishing house scenario**
5. **Iterate based on feedback**

---

**This spec guides AI implementation.**
**Any questions or ambiguities → reference [ACTIVE-studio-discovery.md](./ACTIVE-studio-discovery.md) for full context.**
**Design decisions → justified by Layer 1-4 methodology.**
