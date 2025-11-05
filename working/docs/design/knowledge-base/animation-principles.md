# Animation Principles for Design Systems

## Phenomenological Foundations

### Ready-to-Hand Motion

**Heidegger's Insight**: When tools work well, they become "ready-to-hand"—invisible extensions of our intentions. We focus on the task, not the tool. Digital animations achieve this when they feel natural.

**The Goal**: Motion that becomes **transparent**—users don't think "that animated," they just experience smooth progression toward their goal.

**When Animation Breaks**: If timing is off, easing feels wrong, or duration is too long/short, the interface becomes "present-at-hand"—an object of conscious attention, breaking flow. This is why our locked timing functions matter: they preserve phenomenological transparency.

**Practical Application**:
- 300ms button press = felt but not noticed (ready-to-hand)
- 1000ms button press = "why is this slow?" (present-at-hand, flow broken)
- Perfect timing disappears into the user's intentional action

### Embodied Interaction

**Merleau-Ponty's Insight**: We understand the world through bodily action. Physical objects have weight, momentum, elasticity—our bodies know this.

**Digital Physics**: Animations that mirror physical properties feel "right" because they align with embodied knowledge:
- **Spring bounce**: Objects overshoot then settle (like real springs)
- **Inertia**: Heavy objects move slowly, light objects move quickly
- **Friction**: Movement decelerates (doesn't stop instantly)

**Why Cubic Bezier Curves Matter**:
```css
cubic-bezier(0.34, 1.56, 0.64, 1)  /* Spring: overshoots >1, settles to 1 */
```
This isn't arbitrary—it models **physical spring behavior** that our bodies recognize.

## Human Time Perception

### Perceptual Thresholds

**The Science**: Human time perception operates on specific thresholds backed by empirical research:

**~100ms**: "Instant"
- Below this, actions feel immediate
- User perceives direct cause-and-effect
- Use for: Hover states, initial feedback

**100-300ms**: "Responsive"
- Perceptibly delayed but still feels connected to action
- Sweet spot for most UI animations
- Use for: Button presses, toggles, micro-interactions

**300-1000ms**: "Deliberate"
- Noticeable duration, conveys importance/weight
- Requires purpose (modal opening, major transition)
- Use for: Modals, sidebars, page transitions

**>1000ms**: "Slow"
- Feels like waiting
- Requires explicit progress indication
- Use sparingly: Loading states only

**Why 300ms Is Locked**: It sits at the boundary between "responsive" and "deliberate"—fast enough to feel immediate, slow enough to perceive the motion. This isn't aesthetic preference; it's **calibrated to human time perception thresholds**.

### 60fps Threshold

**The Science**: Human vision perceives smooth motion at 60fps (16.67ms per frame). Below 30fps, motion appears "janky"—we consciously notice the stutter.

**Why This Matters**:
- 60fps = **below conscious perception** (smooth)
- 30fps = **consciously perceptible** (choppy)
- 24fps = cinematic but only works with motion blur

**Practical Application**:
```css
/* GPU-accelerated = 60fps guaranteed */
transform: translateX(100px);
opacity: 0.5;

/* CPU-rendered = often <60fps = janky */
width: 100px;
margin-left: 50px;
```

This is why we lock `transform` and `opacity` usage—they're the only properties guaranteed to maintain perceptual smoothness.

## The 12 Principles of Animation (Disney)

### 1. Squash and Stretch
**Purpose**: Convey weight, flexibility, and impact

**Application in UI**:
- Buttons squash slightly on press (scale: 0.95-0.98)
- Loading spinners stretch/squash for organic feel
- Card expansions use elastic easing

**DO**: Use subtle scale changes (2-5%)
**DON'T**: Over-exaggerate (breaks realism in UI)

### 2. Anticipation
**Purpose**: Prepare viewer for action

**Application in UI**:
- Buttons scale up slightly before click animation
- Modals darken background before opening
- Dropdowns show shadow before expanding

**DO**: Add 50-100ms anticipation phase
**DON'T**: Make anticipation longer than main action

### 3. Staging
**Purpose**: Direct attention to most important element

**Application in UI**:
- Fade background when modal opens
- Highlight active form field
- Dim inactive navigation items

**DO**: Use z-index, opacity, blur strategically
**DON'T**: Animate everything at once

### 4. Straight Ahead vs Pose-to-Pose
**Purpose**: Control vs spontaneity

**Application in UI**:
- **Straight Ahead**: Particle effects, confetti
- **Pose-to-Pose**: Keyframe animations, transitions

**DO**: Use pose-to-pose for predictable UI transitions
**DON'T**: Use straight ahead for critical interactions

### 5. Follow Through and Overlapping Action
**Purpose**: Simulate physics and weight

**Application in UI**:
- Side panels slide in, then header animates
- Cards move, then shadows/content animate
- Toast notifications slide + fade sequentially

**DO**: Stagger child animations 50-100ms apart
**DON'T**: Synchronize everything (feels robotic)

### 6. Slow In and Slow Out
**Purpose**: Natural acceleration and deceleration

**Application in UI**:
```css
/* Standard easing curves */
ease-in-out: cubic-bezier(0.4, 0.0, 0.2, 1)
ease-out: cubic-bezier(0.0, 0.0, 0.2, 1)
ease-in: cubic-bezier(0.4, 0.0, 1, 1)
```

**DO**: Use ease-out for entrances (starts fast, ends slow)
**DON'T**: Use linear easing (feels mechanical)

### 7. Arc
**Purpose**: Natural movement follows curved paths

**Application in UI**:
- Menu items fan out in arc pattern
- Floating action buttons expand in circular path
- Page transitions slide diagonally (not just horizontal)

**DO**: Combine transforms (translate + rotate)
**DON'T**: Use straight-line movement for organic elements

### 8. Secondary Action
**Purpose**: Support main action without dominating

**Application in UI**:
- Icon rotates while button changes color
- Badge bounces while notification arrives
- Ripple effect while button press happens

**DO**: Keep secondary actions subtle (50% duration/distance)
**DON'T**: Let secondary actions steal focus

### 9. Timing
**Purpose**: Create personality and weight

**Application in UI**:
- Fast interactions: 150-250ms (buttons, hovers)
- Medium: 250-400ms (dropdowns, tooltips)
- Slow: 400-600ms (modals, page transitions)

**DO**: Match timing to element size/importance
**DON'T**: Use same duration for everything

### 10. Exaggeration
**Purpose**: Make actions clear and impactful

**Application in UI**:
- Error shake animation (more than natural)
- Success checkmark grows then settles
- Delete swipe action shows preview

**DO**: Exaggerate important feedback (errors, success)
**DON'T**: Exaggerate subtle interactions (hover states)

### 11. Solid Drawing
**Purpose**: Maintain volume and form

**Application in UI**:
- Preserve aspect ratios during scale
- Maintain border radius proportions
- Keep shadows consistent with light source

**DO**: Use `transform` (GPU-accelerated)
**DON'T**: Animate `width`/`height` (causes reflow)

### 12. Appeal
**Purpose**: Create engaging, delightful experiences

**Application in UI**:
- Smooth transitions that feel "right"
- Consistent timing across similar elements
- Subtle micro-interactions (like button hover lift)

**DO**: Polish details (bounce, spring effects)
**DON'T**: Sacrifice usability for "cool" effects

## Performance Principles

### 1. Optimize for 60fps
**Target**: 16.67ms per frame
- Limit DOM changes during animation
- Use `transform` and `opacity` (composited properties)
- Avoid `width`, `height`, `top`, `left` (trigger reflow)

### 2. GPU Acceleration
```css
/* Force GPU acceleration */
transform: translateZ(0);
will-change: transform;
```

**DO**: Use for animations you know will happen
**DON'T**: Apply to everything (wastes GPU memory)

### 3. Reduce Complexity
- Limit simultaneous animations (3-5 max)
- Simplify paths/shapes
- Use CSS animations over JavaScript when possible

### 4. Prefers-Reduced-Motion
```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

## Easing Functions (The Secret Sauce)

### Standard Curves

#### Ease-Out (Most Common)
**Use**: Entrances, user-initiated actions
```
cubic-bezier(0.0, 0.0, 0.2, 1)
```
Starts fast, ends slow → feels responsive

#### Ease-In
**Use**: Exits, dismissals
```
cubic-bezier(0.4, 0.0, 1, 1)
```
Starts slow, ends fast → elements leave quickly

#### Ease-In-Out
**Use**: Continuous loops, attention-grabbing
```
cubic-bezier(0.4, 0.0, 0.2, 1)
```
Slow start and end → smooth, cinematic

### Industry-Standard Curves

#### Standard Ease
```
cubic-bezier(0.4, 0.0, 0.2, 1) // 300ms
```

#### Deceleration
```
cubic-bezier(0.0, 0.0, 0.2, 1) // 225ms
```

#### Acceleration
```
cubic-bezier(0.4, 0.0, 1, 1) // 195ms
```

#### Sharp
```
cubic-bezier(0.4, 0.0, 0.6, 1) // 200ms
```

### Custom Physics-Based

#### Spring (iOS-like)
```
cubic-bezier(0.175, 0.885, 0.32, 1.275)
```
Overshoots slightly → playful, energetic

#### Bounce
```
cubic-bezier(0.68, -0.55, 0.265, 1.55)
```
Bounces past endpoint → fun, attention-grabbing

## Timing Guidelines

### Micro-Interactions
- **Hover**: 100-150ms
- **Click**: 150-200ms
- **Toggle**: 200-250ms

### Transitions
- **Dropdown**: 200-250ms
- **Tooltip**: 150-200ms
- **Sidebar**: 300-350ms
- **Modal**: 300-400ms

### Page-Level
- **Route Change**: 400-600ms
- **Tab Switch**: 300-400ms
- **Accordion**: 250-350ms

### Feedback
- **Success**: 400-500ms (celebrate!)
- **Error**: 300ms + 200ms shake
- **Loading**: Infinite (but show after 300ms delay)

## Common Patterns

### 1. Fade In
```css
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
/* Duration: 200-300ms, Easing: ease-out */
```

### 2. Slide Up
```css
@keyframes slideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}
/* Duration: 300-400ms, Easing: ease-out */
```

### 3. Scale In
```css
@keyframes scaleIn {
  from {
    transform: scale(0.9);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}
/* Duration: 250-350ms, Easing: ease-out */
```

### 4. Shake (Error)
```css
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
  20%, 40%, 60%, 80% { transform: translateX(5px); }
}
/* Duration: 500ms, Easing: ease-in-out */
```

### 5. Skeleton Loading
```css
@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
/* Duration: 1500ms, Easing: linear, Infinite */
```

## Quality Guardrails

### LOCKED (Never Change)
1. **Easing curves**: Maintain consistency across system
2. **Performance**: Must maintain 60fps
3. **Accessibility**: Respect prefers-reduced-motion

### CUSTOMIZABLE (With Guardrails)
1. **Duration**: Within 50ms of guideline
2. **Scale amounts**: Within 10% of recommendation
3. **Colors**: Any, but maintain opacity changes

### FULLY FLEXIBLE
1. **Trigger conditions**: When animation starts
2. **Animation targets**: What elements animate
3. **Sequence order**: Order of staggered animations

## Testing Checklist

- [ ] Runs at 60fps on mid-range devices
- [ ] Respects prefers-reduced-motion
- [ ] Keyboard navigation feels responsive
- [ ] Works in all supported browsers
- [ ] No layout shift (CLS = 0)
- [ ] Clear start/end states
- [ ] Interruptible (can be canceled mid-animation)

## Best Practices Summary

1. **Keep it subtle**: Less is more (5-10% scale changes)
2. **Be consistent**: Same timing for similar elements
3. **Optimize performance**: Use transform/opacity only
4. **Respect preferences**: Honor reduced-motion settings
5. **Test on devices**: Animation feels different on 60Hz vs 120Hz
6. **Add personality**: Use spring/bounce for delightful moments
7. **Make it meaningful**: Every animation should serve a purpose

---

**Key Takeaway**: Animation is about **timing and easing**, not flashy effects. Master these, and everything feels polished.
