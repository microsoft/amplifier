# Studio Interface - Design Brief (User Review)

**Status:** Ready for review
**Source:** [ACTIVE-studio-discovery.md](./ACTIVE-studio-discovery.md)
**For:** User verification and feedback
**Connected to:** [TODO-studio-spec-ai.md](./TODO-studio-spec-ai.md) (AI execution)

---

## What We're Building

**Studio Interface** - The workspace where you interact with Studio's design intelligence.

**Purpose:**
Your design partner that transforms intent into expression—working with you to create bespoke solutions that serve your purpose.

**For whom:**
- **Phase 1:** You (validating methodology)
- **Phase 2:** Team (testing with scenarios)
- **Phase 3:** Non-designers trying to make things happen

---

## Design Vision

### The Aesthetic: "German Car Facility"

**Clean, precise, but beautiful.**

Like a Porsche design studio or Braun workshop:
- Precision and craftsmanship over decoration
- Functional beauty (every element serves purpose)
- Quality through subtle refinement
- Not cold/sterile - warm precision

### Color Palette

**Foundation (Light Mode):**
```
#FAFAFF - Ghost White (background)
#EEF0F2 - Anti-flash White (clean white)
#ECEBE4 - Alabaster (warm light gray)
#DADDD8 - Platinum (warm mid gray)
#1C1C1C - Eerie Black (darkest elements)
```

**Functional Colors:**
- AI thinking: Pulsing blue
- Success: Green check
- Needs attention: Amber
- You vs AI: Distinct colors in conversation

**Philosophy:** Colors serve function, not decoration. Tidy and thoughtful.

### Typography

**Headings:** [Sora](https://fonts.google.com/specimen/Sora) - Geometric, modern, clean
**UI + Body:** [Geist](https://www.fontpair.co/fonts/google/geist) - Clean, readable
**Code:** [Source Code Pro](https://fonts.google.com/specimen/Source+Code+Pro) - Professional monospace

### Motion & Feel

**Speed communicates intent:**
- **Instant (<100ms):** UI interactions (tabs, menus) - respectful of your time
- **Deliberate (400-600ms):** AI generation - emphasizes thoughtful work, not instant slop
- **Responsive (200-300ms):** Transitions, refinements - premium, polished feel

### Materials & Texture

**Frosted aesthetic:**
- Subtle backdrop-blur for panels
- Soft shadows for elevation
- Quality through restraint
- Depth for focus, not distraction

---

## How It Works

### Spatial Organization

**Canvas-dominant layout:**
- Large central canvas (your work is prominent)
- Clean collapsible sidebars (tools when needed)
- Adaptive density (starts spacious, adds panels as context builds)

**Functional Areas:**
- **Canvas/Preview:** Center stage - generated designs appear here
- **Conversation:** Sidebar - AI partner dialogue
- **Properties:** Contextual panels - direct manipulation controls
- **History:** Timeline - version navigation
- **Inspiration:** Separate area - uploaded references
- **Content Input:** Starting modal - paste scenarios, blog posts, etc.

### The Studio Experience

**Two phases working together:**

**1. Design Thinking (Discovery):**
- You describe what you're trying to achieve
- Studio asks thoughtful questions
- Progressive narrowing through alternatives
- Builds understanding of your intent

**2. Design Expression (Manifestation):**
- Studio generates interactive prototypes
- You refine through conversation + direct manipulation
- Real-time updates, auto-saved versions
- Export specs, components, prototypes

### Multi-Modal Refinement

**All supported:**
- **Conversation:** "Make headlines bigger"
- **Direct manipulation:** Click, adjust sliders, see updates
- **Inspiration feeding:** Upload reference images, "more like this"
- **Alternatives:** Compare 3 approaches side-by-side
- **Mix-and-match:** "Typography from A + layout from B"

### Intelligence That Learns

**Studio adapts over time:**
- **First session:** Asks foundational questions
- **Repeat user:** Leverages past learnings
- **Similar project:** "Like your last project?"
- **Mastered workflow:** Assumes confidently, confirms when uncertain

**Critical balance:**
- Never overbearing (too many questions)
- Never reckless (guessing high-stakes decisions)
- Calibrated confidence based on signals
- You can adjust: "Ask more" or "You know me, go ahead"

---

## Device Support

### Phase 1: Desktop First

**Primary creation:** Desktop (full workflow, complex work)

**But multi-device aware:**
- Simulated preview (fast iteration across devices)
- Live device preview (QR code → test on real hardware)
- Both approaches for speed + accuracy

### Future Phases

**Phase 2 (Tablet):**
- Review generated designs
- Light edits/refinement
- Brainstorming sessions

**Phase 3 (Mobile):**
- Capture inspiration (photos while out)
- Quick checks
- Voice notes/observations

**Workflow extends beyond desk:**
- Capture (mobile) → Generate (desktop) → Validate (all devices)

---

## What Makes Studio Different

### Not Another AI Design Tool

**Others generate 5/10 from scratch.**
Studio guides you to 9.5/10 from refined baselines.

**Others execute prompts.**
Studio discovers purpose → guides expression.

**Others are one-shot.**
Studio learns your sensibility over time.

**Others make designers faster.**
Studio enables non-designers to achieve quality.

### The Unique Combination

No one else has:
- Purpose-first methodology (not prompt → generate)
- 9.5/10 quality baseline (refined components, not scratch)
- Progressive discovery (vague ideas → specific designs)
- Nine-dimensional design framework (see below)
- Intelligent curiosity (calibrated confidence, never guessing)

**Result:** Design Intelligence System (new category)

### Nine Dimensions of Design Expression

Studio understands design through nine interconnected dimensions:

1. **Style** - Visual language and aesthetic approach
2. **Behaviors** - Motion timing and interaction patterns (how things move and respond)
3. **Voice** - Language personality and communication tone
4. **Space** - Layout, hierarchy, and spatial relationships
5. **Color** - Meaning, emotion, and accessibility
6. **Typography** - Attention direction and content hierarchy
7. **Proportion** - Scale relationships and visual balance
8. **Texture** - Surface quality, depth, and materiality
9. **Body** - Physical ergonomics and touch interaction

**Why nine dimensions matter:**
- Gives Studio comprehensive understanding of your aesthetic intent
- Enables learning beyond "make it blue" to understanding your sensibility
- Allows precise refinement (adjust motion timing vs color vs voice separately)
- Ensures quality across all aspects of design, not just visuals

---

## Success Looks Like

**For you (Phase 1) - Community Event Scenario:**

**Input:** "I'm running our local youth arts program's annual fundraiser. We need everything for the event—website, social posts, printed programs, signage, thank you materials. It needs to feel professional but warm, appeal to donors and families, and work across all these formats."

**Studio's Process:**
1. **Discovery conversation:**
   - What's the program's mission? (empowering youth through arts)
   - Who's the audience? (donors, families, community members)
   - What's the event atmosphere? (celebratory, inspiring, accessible)
   - Budget constraints? (modest, printed materials need to be cost-effective)

2. **Expression development:**
   - Generates cohesive visual system across all touchpoints
   - Website: Event info, donation flow, program showcase
   - Social: Pre-event hype, event day coverage, thank you posts
   - Print: Programs (8.5×11 folded), signage (poster sizes), name tags
   - Thank you materials: Donor cards, sponsor recognition

3. **Refinement through conversation:**
   - "Make the youth artwork more prominent"
   - "Can we simplify the donation form?"
   - "The poster needs to work in black and white for budget printing"

4. **Outputs:**
   - Interactive website prototype
   - Social media templates (editable)
   - Print-ready PDFs (with bleed, CMYK)
   - Design system specs (colors, typography, spacing)
   - Component library for future events

**Success metrics:**
- Complete event identity from single conversation
- All materials feel cohesive (not disconnected pieces)
- Budget constraints respected (print optimization)
- User could execute without design knowledge
- 9.5/10 quality across all deliverables

**For users (Future):**
- Same workflow for any scenario (rental property, small business, personal project)
- Studio guides discovery → generates bespoke designs → refines through conversation
- Quality maintained without design expertise

**Metrics:**
- User rarely says "that's not what I wanted"
- User rarely feels interrogated
- System learns without being overbearing
- Costly mistakes avoided through smart questions
- 9.5/10 quality maintained across all outputs

---

## What You're Reviewing

**Does this vision match your intent?**

Specifically:
1. **Aesthetic:** German car facility feel (clean, precise, beautiful)?
2. **Intelligence:** Calibrated confidence, intelligent curiosity?
3. **Workflow:** Canvas-dominant, multi-modal refinement?
4. **Phasing:** Desktop-first, expand to tablet/mobile?
5. **Positioning:** Design Intelligence System (guide vs generate)?

**Any misalignments or missing pieces?**

Once approved, this becomes the specification for AI implementation.

**Next:** Technical architecture + build studio-interface/

---

**Source:** All decisions from 4-layer discovery process
**Connected:** [AI Execution Spec](./TODO-studio-spec-ai.md) (what to build)
**Discovery:** [Full process](./ACTIVE-studio-discovery.md) (800+ lines of context)
