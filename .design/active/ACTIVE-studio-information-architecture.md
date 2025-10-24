# Studio Information Architecture

**Status:** Layer 1 (Purpose & Intent) - In Progress
**Date Started:** 2025-10-15
**Designer:** Alex Lopez + Claude
**Context:** Defining IA for Studio interface based on phase structure and workflow

---

## Overview

This document defines the Information Architecture for Design Intelligence Studio - how navigation, content organization, and phase transitions work together to support the creative workflow.

---

## Layer 1: Purpose & Intent

### What Problem Does This IA Solve?

**Current State Issues:**
1. **Phase confusion:** Users don't understand what each phase does or how to move between them
2. **Navigation ambiguity:** Unclear what belongs in global navigation vs contextual menus
3. **Context loss:** Work doesn't persist or carry forward between phases
4. **Haphazard placement:** UI elements added without systematic structure
5. **Workflow interruption:** No clear sense of progression or accomplishment

**Core IA Purpose:**
Enable users to fluidly move through Studio's creative workflow (Discover → Explore → Express → Create) with clear understanding of:
- Where they are in the process
- What they're trying to accomplish in each phase
- What work has been completed
- How to access relevant tools and information
- How to transition between phases when ready

### The Four Phases (Clarified)

Based on user feedback, Studio workflow consists of:

#### 1. Discover (Learn)
**Purpose:** Gather information, understand goals, build context
**Primary Activity:** Conversational discovery, collecting inputs
**Key Question:** "What are we trying to accomplish and why?"
**Outputs:**
- Project brief/context
- Gathered links, images, inspiration
- Named entities and research
- Initial notes and strategy ideas

**Metaphor:** Initial client consultation where you learn everything

#### 2. Explore (Brainstorm)
**Purpose:** Generate possibilities, try alternatives, narrow options
**Primary Activity:** AI-assisted ideation, comparing alternatives
**Key Question:** "What are the possible ways to express this?"
**Outputs:**
- Multiple design directions
- Comparative layouts, color schemes, typography
- Mix-and-match explorations
- Narrowed preferences

**Metaphor:** Brainstorming session with sticky notes and sketches

#### 3. Express (Define)
**Purpose:** Codify decisions, establish system, create specifications
**Primary Activity:** Defining design system, documenting choices
**Key Question:** "What are the precise rules and components we're using?"
**Outputs:**
- Design system specification
- Component library
- Style guide (colors, typography, spacing)
- Implementation guidelines

**Metaphor:** Creating the blueprint and construction documents

#### 4. Create (Build)
**Purpose:** Generate tangible deliverables, export artifacts
**Primary Activity:** Producing final outputs (mockups, prototypes, code)
**Key Question:** "What are the actual deliverables we're shipping?"
**Outputs:**
- Interactive prototypes
- Visual mockups
- Generated code components
- Exportable assets
- Published designs

**Metaphor:** Construction and delivery of finished product

### Phase Relationships

**Sequential but iterative:**
- Primary flow: Discover → Explore → Express → Create
- Can return to earlier phases as needed
- Context carries forward through entire workflow
- Each phase builds on previous work

**Not strictly linear:**
- Discover new information while Exploring
- Refine Expression while Creating
- Return to Discover if fundamentals change

### Success Criteria for IA

A successful IA enables:

1. **Orientation:** User always knows where they are and what phase they're in
2. **Progression:** Clear sense of moving forward through workflow
3. **Access:** Easy access to relevant tools/information for current phase
4. **Transition:** Obvious when ready to move to next phase and how to do it
5. **Context:** Work persists and informs subsequent phases
6. **Return:** Can revisit earlier phases without losing progress
7. **Flexibility:** Can work non-linearly when needed without confusion

---

## Layer 2: Expression & Manifestation

### Global Navigation Structure

**Always Visible Elements:**

#### Top Toolbar (Persistent)
```
┌─────────────────────────────────────────────────────────────┐
│ Studio    [Project Name]                        Phase Badge │
│                                                  [Settings]  │
└─────────────────────────────────────────────────────────────┘
```

**Components:**
- **Studio wordmark** (left) - Home/reset action
- **Project name** (editable, center-left)
- **Phase badge** (right) - Shows current phase, click to see phase nav
- **Settings icon** (far right) - Global preferences

**Design Rationale:**
- Minimal, clean (German car facility aesthetic)
- Always accessible essentials only
- No clutter, maximum focus on work

### Phase Navigation

**Accessed via Phase Badge:**

Click phase badge → reveals phase selector:
```
┌──────────────────────┐
│ • Discover  (Learn)  │
│   Explore   (Brainstorm) │
│   Express   (Define) │
│   Create    (Build)  │
└──────────────────────┘
```

**Visual indicators:**
- Current phase: Filled dot + bold
- Completed phases: Check mark
- Future phases: Empty dot
- Disabled phases: Grayed out (if pre-requisites not met)

**Interaction:**
- Click any accessible phase to jump there
- Hover shows tooltip: "What you'll do in this phase"
- Smooth transition animation (200-300ms)

### Contextual Navigation (Per Phase)

Each phase has its own contextual tools/panels that appear only when relevant.

#### Discover Phase
**Left Panel:** Floating Chat (draggable)
**Center:** Canvas with artifacts (links, research, notes, strategies)
**Right Panel:** None initially (contextual if needed)

**Contextual Actions:**
- Add inspiration
- Take notes
- Continue to Explore →

#### Explore Phase
**Left Panel:** Conversation + Alternatives List
**Center:** Comparison Canvas (side-by-side designs)
**Right Panel:** Properties/Refinement Controls

**Contextual Actions:**
- Generate variations
- Like/Dislike
- Mix-and-match
- Continue to Express →

#### Express Phase
**Left Panel:** Component Library Navigator
**Center:** Design System Documentation
**Right Panel:** Component Details/Properties

**Contextual Actions:**
- Edit component
- Add to library
- Generate spec
- Continue to Create →

#### Create Phase
**Left Panel:** Export Options + Format Selector
**Center:** Final Output Preview
**Right Panel:** Export Settings/Configuration

**Contextual Actions:**
- Generate prototype
- Export assets
- Publish
- Back to refine

### Information Hierarchy

**Level 1 (Always visible):**
- Project identity (name)
- Current phase
- Settings access

**Level 2 (Contextual to phase):**
- Phase-specific tools
- Primary actions
- Work canvas

**Level 3 (Revealed on demand):**
- Advanced settings
- Version history
- Help/documentation

### Layout System

**Core Layout Pattern:**
```
┌─────────────────────────────────────────────────────────────┐
│ Global Toolbar                                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [Context Panel]        [Main Canvas]      [Detail Panel]  │
│   (Left/Floating)        (Center)           (Right/Hidden)  │
│                                                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Flexibility:**
- Panels can be collapsed/expanded
- Left panel can be floating (like current chat)
- Right panel appears only when needed
- Canvas always dominant and central

---

## Layer 3: Context & Appropriateness

### Navigation Patterns by User Type

#### Phase 1: Alex (Designer validating methodology)
**Needs:**
- Quick phase switching (testing full workflow)
- Access to technical details
- Ability to inspect system reasoning
- Version comparison

**Optimizations:**
- Keyboard shortcuts for phase switching
- Developer mode toggle
- Full access to all phases immediately

#### Phase 2: Team (Testing scenarios)
**Needs:**
- Clear workflow guidance
- Ability to save/share work
- Commenting and feedback tools
- Understanding system decisions

**Optimizations:**
- Onboarding tooltips
- "Why did Studio choose this?" explanations
- Collaboration features
- Shareable project links

#### Phase 3: End Users (Non-designers with goals)
**Needs:**
- Hand-holding through process
- Clear next steps
- Confidence building
- Simplified vocabulary

**Optimizations:**
- Guided workflow (linear initially)
- Plain language (no jargon)
- Progress indicators
- Celebration of milestones

### State Persistence

**What Carries Forward:**

Discover → Explore:
- All gathered context (links, images, notes)
- Research and entities
- Strategy cards and goals
- Conversation history

Explore → Express:
- Selected design direction
- Approved alternatives
- User preferences (colors, typography)
- Rejected options (learn from nos)

Express → Create:
- Complete design system spec
- Component library
- Style guide definitions
- Implementation rules

**Technical Implementation:**
- Zustand store maintains full state
- Supabase persists state on changes
- Each phase reads from shared context
- Additions/edits available to all phases

### Accessibility Considerations

**Keyboard Navigation:**
- `⌘/Ctrl + 1-4`: Jump to phase 1-4
- `⌘/Ctrl + K`: Command palette
- `Tab`: Navigate through focusable elements
- `Escape`: Close panels/modals
- `⌘/Ctrl + S`: Save project
- `⌘/Ctrl + Z/Y`: Undo/Redo

**Screen Reader:**
- ARIA landmarks for regions
- Live region for AI responses
- Clear focus indicators
- Descriptive button labels

**Visual:**
- High contrast mode support
- Respect reduced motion preferences
- Minimum 48px touch targets
- Clear visual phase indicators

---

## Layer 4: Contextual Adaptation

### Desktop (Primary)
**Full IA as designed above**
- All panels accessible
- Full keyboard shortcuts
- Maximum workspace
- Multi-panel layouts

### Tablet (Secondary - Phase 2)
**Simplified IA:**
- Single-panel focus
- Bottom sheet for phase switching
- Touch-optimized interactions
- Review/feedback mode prioritized

**Adaptations:**
- Phase nav becomes bottom drawer
- Panels become full-screen views
- Simplified toolbar (just phase + settings)
- Swipe gestures for navigation

### Mobile (Tertiary - Phase 3)
**Minimal IA:**
- Capture mode (inspiration, photos, notes)
- Quick view mode (check generated work)
- No complex editing

**Adaptations:**
- Phase nav becomes full-screen menu
- Single view at a time
- Bottom navigation for primary actions
- Focus on input gathering

---

## Implementation Priorities

### Phase 1 (Current - Desktop Only)

**Immediate:**
1. ✅ Fix global toolbar structure (Studio | Project Name | Phase Badge | Settings)
2. Implement phase badge with dropdown navigation
3. Create phase transition system
4. Ensure context persists between phases
5. Define contextual navigation for each phase

**Can Wait:**
- Tablet/mobile layouts
- Advanced keyboard shortcuts
- Collaboration features
- Version history UI

### Phase 2 (Team Testing)

**Add:**
- Save/share functionality
- Commenting system
- Onboarding tooltips
- Progress indicators

### Phase 3 (End Users)

**Add:**
- Guided workflow mode
- Simplified language toggle
- Celebration moments
- Mobile/tablet support

---

## Resolved Questions (2025-10-15)

### 1. Phase Transitions - ANSWERED
**Answer:** Progressive unlock with intelligent thresholds
- System tracks context gathered and communicates readiness to user
- Phases unlock as prerequisites are met
- User sees visual indication when next phase is available
- Prevents premature advancement but empowers user choice

### 2. Phase Switcher Location - ANSWERED
**Answer:** Main canvas area navigation
- Location: `body > div.flex.h-screen.w-screen.flex-col.studio-canvas > div.flex-1.relative.overflow-hidden`
- Reuse existing component architecture
- Integrated into workspace, not separate toolbar

### 3. Express Phase Purpose - ANSWERED
**Answer:** Design system creator
- Uses context gathered from Discover and Explore phases
- Defines and reviews design system end result
- Creates component library, style guide, specifications
- Interactive editor for design system elements

### 4. Settings Content - ANSWERED
**Answer:** Modal with sidebar layout (reference: ChatGPT settings pattern)
- **Location:** Icon-only button in global toolbar (right side)
- **Interaction:** Opens modal overlay
- **Content:**
  - Theme (light/dark)
  - Voice preferences (verbosity, tone)
  - Account/project management
  - Language preferences
- **Excluded:** AI model selection (not needed for Phase 1)

---

## Next Steps

Once Layer 1 is approved:
1. Move to Layer 2 detailed design (specific component specs)
2. Design phase transition animations
3. Create component hierarchy for each phase
4. Build implementation plan
5. Update existing components to match IA

---

## References

- [Studio Discovery Document](.design/ACTIVE-studio-discovery.md) - Full methodology and 9-dimension design
- [Design Principles](../PRINCIPLES.md) - Core design philosophy
- [Current Implementation](../studio-interface/) - Existing codebase
