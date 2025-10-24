# Progressive Canvas-Building Onboarding

## Problem
Current discovery phase feels like an interview with no tangible output. Information disappears into chat history without demonstrating value or progress.

## Solution
Transform discovery into a **collaborative workspace** where the canvas builds progressively as you chat, creating immediate tangible value.

---

## Architecture

### Layout: Split-Pane Interface

```
┌─────────────────────────────────────────────────┐
│  Studio - Discovery                             │
├──────────────────┬──────────────────────────────┤
│                  │                              │
│  Chat Panel      │  Building Canvas             │
│  (40% width)     │  (60% width)                 │
│                  │                              │
│  Conversational  │  Visual artifacts appear     │
│  guide asks      │  as you provide info:        │
│  questions       │  - Link cards                │
│                  │  - Research panels           │
│  User provides   │  - Sticky notes              │
│  information     │  - Strategy cards            │
│                  │  - Asset collections         │
└──────────────────┴──────────────────────────────┘
```

---

## Canvas Artifact Types

### 1. Link Card
**Trigger**: User mentions URL
**Behavior**:
- Auto-fetch metadata (title, description, image)
- Display preview card
- Store for later use

**Example**:
```
User: "https://redfin.com/WA/Fircrest/..."
→ Canvas spawns card with property image, title, price
```

### 2. Research Panel
**Trigger**: Entity mention (person, place, concept)
**Behavior**:
- Auto-search web for info
- Gather images, bio, articles
- Present in expandable panel

**Example**:
```
User: "Mary Lund Davis"
→ Panel spawns with:
   - Bio snippet
   - Image gallery of her work
   - Related articles
```

### 3. Sticky Note
**Trigger**: Key insight or decision in conversation
**Behavior**:
- Extract important statement
- Create color-coded sticky
- Position on canvas

**Example**:
```
User: "Mix of house history and STR marketing"
→ Sticky: "Content Strategy: Historical + Marketing"
```

### 4. Strategy Card
**Trigger**: User mentions goals/channels
**Behavior**:
- Identify distinct strategies
- Create organized cards
- Link related artifacts

**Example**:
```
User: "Dedicated site, Airbnb, social media"
→ Three cards:
   - Content Hub (dedicated site)
   - STR Optimization (Airbnb)
   - Social Distribution
```

### 5. Asset Collection
**Trigger**: Identified need for visual assets
**Behavior**:
- Search and gather images
- Organize into collection
- Make available for design phase

---

## Entity Extraction System

### Detection Patterns

```typescript
interface ExtractionRule {
  pattern: RegExp | (message: string) => boolean
  artifactType: ArtifactType
  handler: (match: string) => Promise<Artifact>
}

const extractionRules: ExtractionRule[] = [
  {
    // URL detection
    pattern: /https?:\/\/[^\s]+/g,
    artifactType: 'link-card',
    handler: async (url) => {
      const metadata = await fetchMetadata(url)
      return createLinkCard(url, metadata)
    }
  },
  {
    // Named entity (architect, designer, brand)
    pattern: (msg) => hasProperNoun(msg),
    artifactType: 'research-panel',
    handler: async (entity) => {
      const research = await searchEntity(entity)
      return createResearchPanel(entity, research)
    }
  },
  {
    // Strategy/goal mention
    pattern: /\b(strategy|goal|need to|want to)\b/i,
    artifactType: 'sticky-note',
    handler: async (statement) => {
      return createStickyNote(statement)
    }
  }
]
```

### Processing Pipeline

```
Chat message received
↓
1. Parse for entities/patterns
2. Trigger appropriate handlers
3. Create artifacts in parallel
4. Add to canvas with animation
5. Update state
```

---

## State Extensions

### New Store Fields

```typescript
interface CanvasArtifact {
  id: string
  type: 'link-card' | 'research-panel' | 'sticky-note' | 'strategy-card' | 'asset-collection'
  position: { x: number; y: number }
  data: unknown
  createdAt: number
  sourceMessageId?: string
}

interface StudioState {
  // ... existing fields

  // New canvas fields
  canvasArtifacts: CanvasArtifact[]
  addArtifact: (artifact: Omit<CanvasArtifact, 'id' | 'createdAt'>) => void
  updateArtifact: (id: string, updates: Partial<CanvasArtifact>) => void
  removeArtifact: (id: string) => void

  // Canvas layout
  canvasLayout: 'auto' | 'manual'
  setCanvasLayout: (layout: 'auto' | 'manual') => void
}
```

---

## Implementation Plan

### Phase 1: Split-Pane Layout
- [ ] Create `DiscoveryWorkspace` component
- [ ] Split into `ChatPanel` + `CanvasPanel`
- [ ] Add resize handle between panels
- [ ] Style with glassmorphism

### Phase 2: Artifact Components
- [ ] `LinkCard` - URL preview with metadata
- [ ] `ResearchPanel` - Entity info with images
- [ ] `StickyNote` - Key insights
- [ ] `StrategyCard` - Goal/channel cards
- [ ] `AssetCollection` - Image galleries

### Phase 3: Entity Extraction
- [ ] URL detection and metadata fetching
- [ ] Named entity recognition
- [ ] Strategy/goal extraction
- [ ] Image search integration

### Phase 4: Canvas System
- [ ] Auto-layout algorithm
- [ ] Manual drag-and-drop
- [ ] Artifact animations (spawn, move)
- [ ] State persistence

### Phase 5: Integration
- [ ] Connect chat API to extraction
- [ ] Trigger artifact creation from messages
- [ ] Update canvas in real-time
- [ ] Smooth transition to Expression phase

---

## User Experience Flow

### Example: Mary Lund Davis STR Site

```
1. User: "I need to brainstorm articles for my property"
   Canvas: Empty

2. Studio: "Tell me about your property"
   Canvas: Project card appears

3. User: "https://redfin.com/WA/Fircrest/137..."
   Canvas: Link card spawns with property image

4. Studio: "What's the history?"
   Canvas: (preparing for info)

5. User: "Built by Mary Lund Davis"
   Canvas: Research panel spawns
           - Searches "Mary Lund Davis architect"
           - Displays bio
           - Shows image gallery of her work

6. Studio: "Audience?"
   Canvas: (ready to capture strategy)

7. User: "Mix of STR marketing and historical storytelling"
   Canvas: Sticky note appears with strategy

8. Studio: "Where will you publish?"
   Canvas: (preparing strategy cards)

9. User: "Dedicated site, Airbnb, social media"
   Canvas: Three strategy cards appear
           - Content Hub
           - Airbnb Optimization
           - Social Distribution

10. Studio: "Let's build this..."
    Canvas: Full workspace with all artifacts
    Transition: → Expression Phase (carries all artifacts forward)
```

---

## Technical Considerations

### Performance
- Lazy load artifact components
- Debounce entity extraction
- Cache API responses
- Virtual canvas for many artifacts

### Accessibility
- Keyboard navigation for canvas
- Screen reader descriptions
- High contrast mode support

### Data Privacy
- User controls for auto-search
- Option to disable entity extraction
- Clear data attribution

---

## Success Metrics

### Qualitative
- Does discovery feel productive?
- Can users see progress being made?
- Does canvas build feel magical?

### Quantitative
- Time to first artifact: < 30 seconds
- Artifacts created per session: 5-10
- Transition to Expression: 100% with context

---

## Next Steps

1. Build split-pane layout
2. Create first artifact type (LinkCard)
3. Test with real conversation
4. Iterate on UX
5. Add remaining artifact types
6. Polish animations and transitions
