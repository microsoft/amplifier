# Studio Interface - User Flow

**The journey from empty state to creation**

---

## State Machine

Studio operates in distinct phases, each with its own UI:

```
Empty → Discovery → Expression → Export
  ↓         ↓           ↓          ↓
 No UI   Conversation  Full IDE   Output
```

---

## Phase 1: Empty State

**When:** First open, no project exists
**UI Elements:**
- Clean canvas with centered welcome
- Single "Start New Project" button
- NO toolbar, NO device switcher, NO panels

**Visual:**
```
┌──────────────────────────────────────┐
│                                      │
│                                      │
│          Welcome to Studio           │
│                                      │
│   Your design partner that trans-    │
│   forms intent into expression       │
│                                      │
│      [Start New Project]             │
│                                      │
│                                      │
└──────────────────────────────────────┘
```

**Interaction:**
- Click "Start New Project" → Transitions to Discovery Phase

---

## Phase 2: Discovery Phase

**When:** User starts project, discovery conversation active
**Purpose:** Understand what they're trying to create

**UI Elements:**
- Minimal toolbar (just "Studio" branding)
- Full-screen conversation interface
- AI asks thoughtful questions
- User responds
- NO canvas yet, NO device switcher, NO history

**Visual:**
```
┌─────────────────────────────────────────┐
│ Studio                                  │
├─────────────────────────────────────────┤
│                                         │
│  [AI]: What would you like to create?   │
│                                         │
│  [User]: I need a website for...        │
│                                         │
│  [AI]: Who is your audience?            │
│                                         │
│  [User]: Donors and families...         │
│                                         │
│  ┌────────────────────────────────┐    │
│  │ Tell me more...                │    │
│  └────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

**Conversation Flow:**
1. **Initial prompt:** "What would you like to create today?"
2. **Discovery questions:**
   - What's the purpose?
   - Who's the audience?
   - What content do you have?
   - Any constraints? (budget, timeline, technical)
3. **Refinement:** Progressive narrowing through follow-ups
4. **Confirmation:** "Based on what you've told me, I'll create..."

**Transition:**
- When AI has enough context → "I'm ready to generate some options for you" → Expression Phase

---

## Phase 3: Expression Phase

**When:** AI has generated initial designs
**Purpose:** Refine through conversation and direct manipulation

**UI Elements:** (What we just built!)
- Full toolbar with device switcher
- Canvas with generated design preview
- Conversation sidebar (for refinement)
- History timeline (version control)
- Properties panel (direct manipulation)

**Visual:**
```
┌─────────────────────────────────────────────────────┐
│ Studio     [Desktop][Tablet][Mobile][Watch]  [⋮][⊕] │
├─────────────────────────────────────────────────────┤
│                                                      │
│              [Generated Design Preview]              │
│                                                      │
│                                                      │
│                                                      │
├─────────────────────────────────────────────────────┤
│ Version 1     Version 2     Version 3                │
└─────────────────────────────────────────────────────┘
```

**Interactions:**
- **Device switcher:** Preview across devices
- **Conversation:** "Make headlines bigger", "Use warmer colors"
- **Direct manipulation:** Click elements, adjust properties
- **History:** Compare versions, restore previous
- **Alternatives:** "Show me 3 different layouts"

**Sub-states:**
- Generating: AI is creating/updating
- Idle: Ready for input
- Refining: Processing user feedback

---

## Phase 4: Export Phase

**When:** User is satisfied with design
**Purpose:** Output deliverables

**UI Elements:**
- Export modal overlay
- Format selection (Figma, HTML, PDF, etc.)
- Download/share options

**Not built yet - future phase**

---

## Implementation Strategy

### Current State
We built **Expression Phase UI** but didn't implement the **Empty** or **Discovery** phases.

### What We Need

**1. Add state management:**
```typescript
type StudioPhase = 'empty' | 'discovery' | 'expression' | 'export'

interface StudioState {
  phase: StudioPhase
  // ... existing state
}
```

**2. Conditional rendering based on phase:**
```tsx
export default function Studio() {
  const { phase } = useStudioStore()

  if (phase === 'empty') return <EmptyState />
  if (phase === 'discovery') return <DiscoveryConversation />
  if (phase === 'expression') return <ExpressionWorkspace />
  if (phase === 'export') return <ExportFlow />
}
```

**3. Build missing phases:**
- EmptyState component
- DiscoveryConversation component
- (ExpressionWorkspace already exists - current page.tsx)

---

## Design Principles for Each Phase

### Empty State
- **Minimal:** No distractions
- **Inviting:** "Let's create something"
- **Clear:** Single obvious action

### Discovery
- **Conversational:** Not a form, a dialogue
- **Progressive:** One question at a time
- **Patient:** No rush, build understanding
- **Transparent:** Show what you're asking and why

### Expression
- **Canvas-dominant:** Work takes center stage
- **Multi-modal:** Conversation + direct manipulation
- **Real-time:** Instant feedback
- **Non-destructive:** History and versions

---

## Next Actions

To implement proper flow:

1. **Add phase state to store**
2. **Build EmptyState component**
   - Clean welcome
   - "Start New Project" button
   - Transition to discovery
3. **Build DiscoveryConversation component**
   - Full-screen conversation UI
   - Question/answer flow
   - "Generating..." state when transitioning
4. **Update current page.tsx to ExpressionWorkspace**
   - Rename/refactor
   - Only renders when phase === 'expression'
5. **Wire up transitions**
   - Empty → Discovery (on button click)
   - Discovery → Expression (when AI ready)
   - Expression → Export (when user satisfied)

---

## Questions for You

1. Should we build all three phases now?
2. Or start with Empty + Discovery and connect to current Expression phase?
3. Any specific details about the Discovery conversation flow you want to nail down first?
