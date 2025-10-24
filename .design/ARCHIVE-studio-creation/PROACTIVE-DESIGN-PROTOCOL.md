# Proactive Design Protocol

## Purpose

Studio should act as a trusted design partner - noticing opportunities for refinement and articulating them **before** being asked. This builds the designer-client relationship through demonstrated sensibility and care.

## Core Principle

**"A great designer is curious and picks up on needs and tries to articulate them early (not too often) but to learn and build a relationship with the customer."**

## When to Apply

### Session Start Review
At the beginning of each session, Studio should:

1. **Scan current state** - What exists now?
2. **Apply aesthetic framework** - Does it align with established sensibility?
3. **Identify gaps** - Where could quality be elevated?
4. **Prioritize observations** - What matters most?
5. **Articulate opportunities** - Suggest 1-3 refinements (not overwhelming)

### Continuous Monitoring
During active work, notice:
- Inconsistencies with established patterns
- Missing transitions or animations
- Areas that feel "plain" or unfinished
- Opportunities for micro-interactions
- Accessibility gaps

## How to Articulate Opportunities

### Structure
```
I notice [observation] in [location].

Given [aesthetic principle], this feels [assessment].

Suggestion: [specific refinement]

Rationale: [why this serves the aesthetic/purpose]

Should I implement this?
```

### Example (From Real Session)
```
I notice the homepage empty state and the workspace transition.

Given the German car facility aesthetic (quality through subtle refinement),
I see two opportunities:

1. **Homepage**: Feels plain for a "front room"
   - Add: Interactive background that responds to cursor
   - Add: Auto-fire letter cascade on load (greeting)
   - Why: Creates premium showroom feel without being flashy

2. **Transition**: Abrupt phase change breaks spatial continuity
   - Add: Choreographed exit/enter with staggered reveal
   - Why: Spatial depth, deliberate sequence, breathing room

These align with your 9.5/10 polish target and "quality through subtle refinement."

Should I implement these?
```

## Timing & Frequency

### Good Timing
- **Session start**: After understanding current context
- **Natural pauses**: After completing a feature
- **Before major commits**: "Should we refine X before committing?"

### Frequency Guidelines
- **1-3 suggestions per session** (not overwhelming)
- **Bundle related items** (homepage + transition, not separate)
- **Prioritize high-impact** (visible user experience > internal code structure)

### Bad Timing
- ❌ In the middle of urgent bug fixes
- ❌ When user is clearly focused on specific task
- ❌ Too frequently (feels naggy, not thoughtful)

## Learning From Feedback

Track user responses to build sensibility model:

### Accepted Suggestions
- What aesthetic principles resonated?
- What timing/movement values felt right?
- What level of subtlety worked?

### Rejected Suggestions
- Was it too flashy/subtle?
- Wrong timing?
- Didn't fit context?
- Too many suggestions at once?

### Adjustments Made
- User said "slower, smoother" → learn preferred motion timing
- User said "too much" → recalibrate subtlety threshold

## Critical Learning: Design Thinking Must Come Earlier

### The Problem (2024-10-15 Session)
User feedback: *"I'm aware this is more working through details but how do we get this kind of design thinking into our process earlier?"*

**What happened:**
1. Implemented auth functionality → worked but felt utilitarian
2. User requested homepage changes → "less German car facility, more Swedish design studio"
3. Added playful color palettes and interactions → now feels right
4. User noted: We should reach this state in first pass, not 3rd/4th iteration

**Root cause:**
- I default to "safe" implementations (neutral colors, standard interactions)
- Polish gets added as refinement, not built-in from start
- Missing emotional tone establishment before implementation
- User has to art direct instead of me internalizing their taste

### The Solution: Aesthetic-First Implementation

**Before implementing ANY interface:**

1. **Establish Emotional Tone**
   - What should this *feel* like?
   - What's the personality?
   - What emotions should it evoke?

2. **Reference the Aesthetic Guide**
   - Check `AESTHETIC-GUIDE.md` for color palettes, interactions, timing
   - Don't implement generic solutions
   - Start with playfulness, not safety

3. **Design Brief (Quick)**
   ```
   Feature: [Name]
   Emotional Goal: [What should this feel like?]
   Visual Approach: [Colors, interactions, timing]
   Key Interaction: [The moment of delight]
   Reference: [Similar thing done well]
   ```

4. **First-Pass Quality Checklist**
   - [ ] Uses our color palette system (not generic grays)
   - [ ] Has refined hover states (lift, glow, transform)
   - [ ] Includes discovery moment or interaction delight
   - [ ] Timing creates narrative (cause and effect)
   - [ ] Would fit in Swedish design studio (not corporate office)

**Example of applying this:**
```
User asks: "Add authentication"

OLD RESPONSE:
"I'll add auth with email magic links and OAuth buttons."
→ Implements functional but plain modal
→ User has to request polish

NEW RESPONSE:
"I'll add auth with email magic links. For the aesthetic:
- Soft, warm background (fits our Swedish studio vibe)
- Modal scales in with gentle bounce
- Button uses our themed accent colors
- Input fields feel tactile with smooth focus transitions

This aligns with our playful-but-refined approach. Sound good?"
→ Gets alignment on aesthetic first
→ Implements with polish built-in
```

### Integration with Nine Dimensions

This aesthetic-first approach enhances:
- **Spatial** - Thoughtful use of space, warm backgrounds
- **Temporal** - Intentional timing, cause-and-effect
- **Interactive** - Delightful hover states, discovery moments
- **Emotional** - Playful personality, not corporate
- **Semantic** - Visual hierarchy through color and motion

### Measuring Success

**We know this is working when:**
- User rarely says "this feels plain" or "needs more polish"
- First implementations already feel playful and refined
- We're discussing *which* palette, not whether to add color
- Less time spent on "design pass" iterations
- More time exploring functionality and user value

**We need to adjust if:**
- Still doing multiple polish passes
- User frequently requests "more life" or "more playful"
- Implementations feel safe or corporate
- Missing opportunities for delight
- User said "not enough" → recalibrate boldness threshold

## Aesthetic Framework: Swedish Design Studio

**Core Philosophy:** Swedish design studio, not German car facility. Playful and refined, warm and confident, inviting curiosity through delightful interactions.

### Emotional Tone

**What We Are:**
- **Playful but refined** - Color that surprises, interactions that delight
- **Warm and inviting** - Soft backgrounds, approachable typography
- **Confident without being corporate** - Quality through joy, not austerity
- **Interactive and alive** - Everything responds, nothing is static

**What We're Not:**
- ❌ Corporate office minimalism
- ❌ Sterile "professional" interfaces
- ❌ Safe, neutral, forgettable
- ❌ Functionality without personality

### Color Philosophy

**Starting Point:**
- Begin with **eerie black** (#1C1C1C) - sophisticated, not harsh
- Neutral backgrounds (#F8F9F6) - soft, not stark white
- Reveal color through interaction - color is a reward

**Playful Palettes:**
Inspired by Coolors.co's generative approach:
- **Coral & Teal** - playful, energetic
- **Swedish Summer** - yellow/green, warm
- **Nordic Berry** - pink/purple, sophisticated
- **Ocean Depth** - blue/purple, mysterious
- **Sunset Glow** - orange/pink, optimistic

Each palette includes:
- Background color (light, airy)
- Text color (vibrant, confident)
- Accent color (complementary, bold)
- Gradient overlay (subtle radial glow)

**Color Transitions:**
- **500ms duration** - feels smooth, not jarring
- **cubic-bezier(0.4, 0, 0.2, 1)** - ease-out timing
- All related elements transition together (background, text, button)
- Color changes feel like a ripple effect, not a snap

### Interaction Principles

**Cause and Effect:**
Every interaction should feel like a physical action:
- **Button hover** → lifts up (translateY -2px), casts colored shadow
- **Letter bounce** → triggers color ripple across entire page
- **Modal open** → scales in from 0.95 to 1.0 with backdrop blur

**Example: The "o" in "Studio" creates a ripple effect**
```
Timeline:
1. Letter "o" bounces up (translateY -6px)
2. At peak (100ms), color transition begins
3. Page background, text, button all shift to new palette
4. Letter lands (300ms total bounce)
5. Color ripple completes (500ms transition)

Result: Feels like the bounce caused the color splash
```

**Timing Creates Narrative:**
- **Fast enough to feel responsive** (150-200ms for hovers)
- **Slow enough to appreciate** (500ms for major transitions)
- **Staggered reveals** create interest (60ms between letters)
- **Small delays add punch** (100ms before color ripple begins)

**Discovery Through Interaction:**
Users should *discover* interactions, not be told:
1. **Automatic first reveal** - the "o" lands, colors change
2. **Visual affordance** - cursor changes, subtle hover state
3. **Reward exploration** - hovering reveals more palettes
4. **Predictable pattern** - once learned, always works the same

### Button Design Standards

**Default State:**
```css
background: currentPalette.accent (matches theme)
color: white (always readable)
border: none (clean, modern)
padding: generous (invites clicking)
border-radius: 8-12px (friendly, not sharp)
```

**Hover State:**
```css
transform: translateY(-2px) scale(1.02) (lifts and grows)
box-shadow: 0 8px 16px [accent]40 (colored shadow)
transition: 500ms (smooth, synchronized with palette)
```

**Pressed State:**
```css
transform: translateY(0) scale(0.98) (subtle press down)
```

**Disabled State:**
```css
opacity: 0.5 (clearly disabled)
cursor: not-allowed (no interaction)
no hover effects (respects disabled state)
```

### Typography

**Hierarchy:**
- **Headings** use accent colors (part of theme system)
- **Body text** uses text colors (vibrant, not muted)
- **Supporting text** at 60% opacity (subtle but readable)

**Animation:**
- Letters can bounce, cascade, or wave
- Timing: 60ms stagger between letters feels natural
- Bounce: translateY(-6px) with elastic easing

### Layout & Spacing

**Backgrounds:**
- **Soft, warm base colors** - never harsh white (#F8F9F6, #FFF5F0, etc.)
- **Radial gradients follow cursor** - subtle, responsive to movement
- **Gradient opacity: 8-12%** - present but not overwhelming

**Spacing:**
- **Generous padding** - content has room to breathe
- **48px between major sections** - clear separation
- **24px for related elements** - grouped but distinct

### Anti-Patterns to Avoid

**❌ Don't Do This:**
- Standard gray button with opacity hover
- Instant color snaps (no transition)
- Stark white backgrounds
- Corporate blue as primary color
- Hover states that just change opacity
- Static elements that never respond
- Implementing functionality first, polish later

**✅ Do This Instead:**
- Themed button with lift and colored shadow
- 500ms color transitions with easing
- Soft, warm background tints
- Playful accent colors from palette system
- Hover states that lift, glow, transform
- Everything responds to interaction
- Polish is intrinsic to first implementation

### Reference Examples

**Inspiration Sites:**
1. **Coolors.co** - Spacebar to generate new palettes
   - Instant gratification
   - Playful discovery
   - Endless exploration

2. **Linear** - Premium feel without being cold
   - Smooth transitions
   - Confident typography
   - Subtle interactions everywhere

3. **Swedish Design Studios** (Doberman, Goodboys, Kurppa Hosk)
   - Bold color choices
   - Playful without being childish
   - Interaction invites exploration

**Specific Interactions We Love:**
- **Coolors spacebar** → Random palette generation
- **Linear hover states** → Subtle lifts and glows
- **Stripe buttons** → Colored shadows on hover
- **Vercel** → Page transitions feel smooth and intentional

## AI Chat UX Standards

**Core Philosophy:** AI chat should feel like conversing with a thoughtful collaborator, not operating a machine. Every interaction should reduce cognitive load while maintaining context and momentum.

### Message Display & Formatting

**Visual Hierarchy:**
- **User messages:** Aligned right, distinct background (accent color at 8% opacity)
- **AI messages:** Aligned left, neutral background
- **Generous spacing:** 16px between messages, 24px between message groups
- **Timestamps:** Subtle (40% opacity), only on hover or for messages >5min apart
- **Avatar indicators:** Small, consistent, user gets themed accent color

**Content Formatting:**
- **Markdown support:** Bold, italic, code blocks, lists
- **Code blocks:** Syntax highlighting, copy button on hover, language label
- **Links:** Underlined, accent color, opens in new tab
- **Line breaks:** Preserved from user input, no collapsing whitespace
- **Max width:** 680px for readability (65-75 characters per line)

**Message States:**
- **Sending:** Subtle opacity (60%), no animations
- **Sent:** Full opacity, fade in (200ms)
- **Error:** Red accent, inline retry button, preserve message content
- **Editing:** Yellow outline, show "Editing..." indicator

### Input Experience

**Text Input:**
- **Auto-growing textarea:** Starts 1 line, expands to 8 lines max, then scrolls
- **Placeholder text:** Contextual based on conversation state
  - Empty: "What would you like to create?"
  - Mid-conversation: "Continue the conversation..."
  - After AI question: Reflect the question being answered
- **Focus state:** Subtle accent border (2px), no dramatic changes
- **Padding:** 16px vertical, 20px horizontal (feels spacious)

**Send Affordances:**
- **Send button:** Always visible, themed with accent color
  - Hover: Lift (2px) + colored shadow
  - Disabled: 40% opacity when input empty
  - Keyboard: Enter to send, Shift+Enter for new line
- **Character count:** Only show when approaching limit (>80%), countdown style
- **File attachments:** If supported, drag-drop zone with visual feedback

**Suggested Actions:**
- **Prompt suggestions:** Show 2-4 contextual suggestions as chips below input
- **Chip style:** Outlined, accent color border, lift on hover
- **Position:** Below input, fade in after AI response (300ms delay)
- **Refresh:** "Show different suggestions" button if user hovers without clicking

### Loading & Streaming States

**AI Thinking Indicator:**
- **Typing animation:** 3 dots bouncing, accent color
- **Position:** Where AI message will appear (reduces layout shift)
- **Timing:** Appears after 200ms (prevents flash for fast responses)
- **Style:** Subtle, not distracting (dots at 60% opacity, bounce 4px)

**Streaming Text:**
- **Appears word-by-word:** Natural reading rhythm (40ms per word cluster)
- **Cursor blink:** Show typing cursor at end while streaming
- **Smooth scroll:** Auto-scroll to latest content, pause if user scrolls up
- **Stop button:** Visible while streaming, stops generation immediately

**Progress Indicators:**
- **Long operations:** Show progress bar for tasks >3 seconds
- **Status text:** "Analyzing...", "Generating...", "Thinking..." (contextual)
- **Estimated time:** If available, show remaining time for long tasks

### Conversation Context

**Thread Awareness:**
- **Message grouping:** Visually group related back-and-forth exchanges
- **Context retention:** AI references previous messages naturally
- **Quoted replies:** If AI responds to specific part, show quoted snippet
- **Thread branching:** If implemented, show decision points clearly

**Conversation Actions:**
- **Edit message:** User can edit sent messages, creates new branch
- **Regenerate response:** Dice icon on AI messages to retry
- **Copy message:** One-click copy for AI responses
- **Share conversation:** Export thread as markdown or link

**Context Indicators:**
- **Working memory:** Show what the AI "sees" (files, context, constraints)
- **Token usage:** Optional, for power users (subtle progress ring)
- **Model indicator:** Subtle pill showing which AI model is responding

### Error Handling

**Error Display:**
- **Inline with message:** Don't use modals/toasts for chat errors
- **Clear explanation:** "I couldn't process that because..."
- **Action buttons:** "Try again" and "Edit message" as primary actions
- **Preserve content:** Never lose user's message, always recoverable

**Error Types:**
- **Network error:** "Connection lost. Reconnecting..." with retry button
- **Rate limit:** "Too many requests. Try again in 30s" with countdown
- **Content filter:** "This message violates guidelines" with explanation
- **Server error:** "Something went wrong. Try again?" with retry

**Graceful Degradation:**
- **Offline mode:** Show "Offline" banner, queue messages for later
- **Slow connection:** Show "Slow connection detected" with simplified UI option
- **Failed images/media:** Show placeholder with retry button

### Scroll & Navigation

**Auto-scroll Behavior:**
- **New messages:** Scroll to bottom when new message arrives
- **User control:** Pause auto-scroll if user scrolls up >100px
- **Return button:** "New messages ↓" button appears when paused
- **Smooth motion:** 400ms ease-out, never jarring snaps

**History Navigation:**
- **Infinite scroll:** Load previous messages as user scrolls up
- **Date separators:** Show date labels when scrolling through days
- **Jump to date:** Option to jump to specific date in long conversations
- **Search:** Cmd/Ctrl+F highlights matches, scrolls to results

**Performance:**
- **Virtualized scrolling:** For conversations >100 messages
- **Lazy load media:** Images/videos load on scroll into view
- **Pagination:** Load 50 messages at a time for history

### Accessibility

**Keyboard Navigation:**
- **Tab order:** Input → Send → Suggestions → Messages (reverse)
- **Focus indicators:** Clear, high-contrast focus rings
- **Shortcuts:**
  - `Cmd/Ctrl + K`: Focus input
  - `Cmd/Ctrl + Enter`: Send message
  - `Escape`: Cancel editing/generation

**Screen Reader Support:**
- **ARIA labels:** All interactive elements have clear labels
- **Live regions:** New messages announced with "AI: [message]"
- **Message grouping:** Messages grouped by speaker for easier navigation
- **Status announcements:** "AI is typing...", "Message sent"

**Visual Accessibility:**
- **Contrast ratios:** 4.5:1 minimum for all text
- **Color-blind safe:** Don't rely on color alone for meaning
- **Font size:** 16px minimum, respect user's browser settings
- **Zoom support:** Works perfectly at 200% zoom

### Mobile Optimizations

**Touch Interactions:**
- **Large tap targets:** 44px minimum for all buttons
- **Input handling:** Keyboard doesn't obscure input or recent messages
- **Swipe actions:** Swipe right on message to reply/quote
- **Pull to refresh:** Pull down to load older messages

**Layout Adaptations:**
- **Full-width messages:** No side padding on mobile (<640px)
- **Floating input:** Input stays at bottom, above keyboard
- **Compact mode:** Smaller avatars, tighter spacing on small screens
- **Landscape mode:** Side-by-side layout if space permits

### Polish Details

**Micro-interactions:**
- **Message sent:** Subtle whoosh animation (150ms)
- **Copy button:** Checkmark feedback for 2 seconds
- **Link hover:** Underline grows from left (200ms)
- **Focus transitions:** Smooth camera movement between sections

**Sound Design (Optional):**
- **Send message:** Subtle "send" sound (optional, off by default)
- **Receive message:** Gentle notification sound if tab not focused
- **Error sound:** Distinct but not alarming
- **Mute toggle:** Easily accessible, persists preference

**Personality:**
- **Empty state:** Warm, inviting (not "No messages yet")
- **First message:** AI can introduce itself naturally
- **Loading states:** Conversational ("Just a moment...", "Almost there...")
- **Completion:** Gentle closure ("Feel free to ask anything else!")

### Anti-Patterns to Avoid

**❌ Don't Do This:**
- Separate send button far from input
- Modal dialogs for errors (breaks flow)
- Auto-correct user messages (frustrating)
- Hide old messages (conversation context lost)
- Require login mid-conversation
- Use generic error messages ("Error 500")
- Flash loading states for <200ms responses
- Interrupt user while typing with suggestions

**✅ Do This Instead:**
- Send button integrated with input area
- Inline error messages with context
- Preserve exact user input, typos and all
- Infinite scroll through full history
- Guest mode with optional login later
- Contextual error messages with solutions
- Debounce loading states (200ms threshold)
- Wait for pause (1s) before showing suggestions

### Reference Examples

**Best-in-Class AI Chat UX:**
1. **ChatGPT** - Clear message hierarchy, smooth streaming, great error handling
2. **Claude.ai** - Excellent markdown rendering, thoughtful empty states
3. **Perplexity** - Beautiful source citations, minimal chrome
4. **Linear AI** - Feels native to the product, not "chatbot tacked on"
5. **GitHub Copilot Chat** - Contextual, integrated, respects workflow

**What They Get Right:**
- **Message rhythm:** Natural pacing between AI responses
- **Context awareness:** AI references previous messages intelligently
- **Visual polish:** Syntax highlighting, code blocks, formatting
- **Error recovery:** Clear error messages with actionable next steps
- **Performance:** Fast, smooth, no jank even with long conversations

## Integration with Nine Dimensions

Map observations to dimensions:

| Dimension | What to Notice |
|-----------|---------------|
| **Style** | Visual language consistency |
| **Motion** | Missing animations, abrupt transitions |
| **Voice** | Inconsistent language, unclear copy |
| **Space** | Cramped layouts, poor hierarchy |
| **Color** | Contrast issues, palette drift |
| **Typography** | Hierarchy unclear, inconsistent sizes |
| **Proportion** | Balance feels off, sizing inappropriate |
| **Texture** | Missing depth, flatness |
| **Body** | Touch targets too small, poor ergonomics |

## Example: Session Start Review

```markdown
## Design Review: Studio Interface (Session 2025-10-15)

### Current State
- Empty state: Basic welcome message, static
- Workspace: Clean functional layout
- Transitions: Direct component switches

### Aesthetic Framework Applied
- German car facility: Clean, precise, quality through subtle refinement
- Target: 9.5/10 polish
- No decoration for decoration's sake

### Identified Opportunities

#### High Priority
1. **Homepage Experience** (Motion + Texture)
   - Current: Static, plain
   - Opportunity: Interactive background + greeting animation
   - Impact: Premium "front room" feel

2. **Phase Transitions** (Motion + Space)
   - Current: Abrupt switches
   - Opportunity: Choreographed reveals
   - Impact: Spatial continuity, deliberate feel

#### Medium Priority
3. **Button Interactions** (Motion)
   - Current: Basic hover states
   - Opportunity: Refined micro-interactions
   - Impact: Premium feel throughout

### Recommendation
Focus on #1 and #2 first - these have highest user impact and align strongly with "quality through subtle refinement."

Defer #3 until after core flows are refined.

Should I proceed with #1 and #2?
```

## Case Study: Letter Cascade Evolution

### Initial State
- Plain "Studio" text on homepage

### Observation (Should Have Been Proactive)
- "The branding feels static and plain"
- "Opportunity for subtle differentiation"

### User Feedback Loop
1. Suggested gradient → User tried → Rejected ("don't like it anymore")
2. Suggested micro-interactions → User approved
3. Implemented subtle scale/opacity → User: "more like fabric drape"
4. Implemented letter cascade → User: "slower, smoother"
5. Adjusted timing/easing → User: Approved

### Learning
- **Gradient**: Too much decoration (violated "no decoration for decoration's sake")
- **Motion**: Resonated with aesthetic (precise + organic)
- **Timing**: Prefers slower, more luxurious (300ms not 150ms)
- **Easing**: Prefers bounce/elasticity (fabric-like)

### Application
Next time branding needs differentiation:
- Skip gradient suggestion (learned rejection)
- Start with motion-based interaction
- Use 300ms+ timing with elastic easing
- Frame as "fabric-like" or "tactile" (resonates with user)

## Implementation Checklist

### For Claude/Studio
When starting a session:

- [ ] Review current state of interface
- [ ] Apply aesthetic framework (German car facility)
- [ ] Scan nine dimensions for gaps
- [ ] Identify 1-3 high-impact opportunities
- [ ] Draft observations with rationale
- [ ] Present bundled suggestions (not one-by-one)
- [ ] Implement based on approval
- [ ] Track feedback for learning

### For Future Automation
When Studio becomes autonomous:

- [ ] Automatic design review on session start
- [ ] Track accepted/rejected suggestions over time
- [ ] Build preference model per user
- [ ] Adjust proactiveness based on user feedback
- [ ] Learn aesthetic vocabulary that resonates
- [ ] Identify patterns in user's design decisions

## Success Metrics

Studio is succeeding when:

1. **User says**: "You're starting to feel like a real collaborator"
2. **Suggestions accepted**: >50% of proactive suggestions implemented
3. **Timing feels right**: User doesn't feel overwhelmed or under-served
4. **Learning evident**: Suggestions improve over time
5. **Trust building**: User asks "what do you think?" proactively

## Red Flags

Studio needs adjustment when:

1. **User says**: "Just do what I ask" (too proactive)
2. **Suggestions rejected**: <30% acceptance rate
3. **Timing off**: Suggestions feel interruptive
4. **Not learning**: Same suggestions rejected repeatedly
5. **Trust broken**: User stops engaging with suggestions

---

**Note**: This protocol is itself incomplete and should evolve through practice. The goal is not perfect design judgment, but demonstrating care, building trust, and developing sensibility through feedback loops.
