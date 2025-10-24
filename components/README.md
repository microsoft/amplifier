# Components

**Curated 9.5/10 components with locked refinement and AI-guided customization**

---

## Available Components

### [Hero Button](./hero-button-refined/)
Six meticulously crafted variants for different personalities and use cases.

**Variants**: Magnetic, Ripple, Ghost Slide, Neon Pulse, Liquid Morph, Particle Burst

**Quality Level**: 9.5/10

**Key Features**:
- Locked timing and easing for premium feel
- 6 personality-driven variants
- Full keyboard accessibility
- 60fps GPU-accelerated animations
- Reduced motion support
- WCAG AA compliant

**[View documentation →](./hero-button-refined/README.md)**

---

## Coming Soon

- **Card - Refined**: Elevated content containers with micro-interactions
- **Input - Refined**: Form inputs with delightful validation states
- **Modal - Refined**: Accessible dialogs with smooth transitions
- **Navigation - Refined**: Menu systems with natural animations

---

## Component Structure

Each component follows this pattern:

```
[component-name]/
├── README.md        - Complete documentation
├── EXAMPLES.md      - Usage patterns (optional)
├── [Component].tsx  - Implementation
├── [Component].css  - Styles with locked properties
├── variants/        - Variant demonstrations (optional)
└── tests/          - Component tests (optional)
```

---

## Using Components

### Installation

Components are designed to be copied into your project:

```bash
cp -r components/hero-button-refined ./src/components/
```

### Import

```tsx
import { HeroButton } from './components/hero-button-refined/HeroButton';

<HeroButton variant="magnetic" size="lg">
  Get Started
</HeroButton>
```

### Customization

All components support safe customization:
- **Colors**: With contrast validation
- **Sizes**: Predefined scale (sm, md, lg, xl)
- **Content**: Full flexibility

See individual component documentation for details.

---

## Quality Standards

Every component maintains:

- **9.5/10 baseline quality** - Refined, not generic
- **Locked properties** - Timing, easing, physics preserved
- **WCAG AA accessibility** - Keyboard, screen reader, contrast
- **60fps performance** - GPU-accelerated only
- **Reduced motion support** - Respects user preferences

**[Learn about our philosophy →](../PHILOSOPHY.md)**

---

## Contributing Components

Want to add a component? Follow these guidelines:

1. **Achieve 9.5/10 quality baseline** - Test extensively
2. **Define locked vs. customizable properties** - Clear boundaries
3. **Document thoroughly** - README, examples, API
4. **Create quality guardrails** - JSON schema in quality-guardrails/
5. **Follow the structure** - Match existing component patterns

**[Read contribution guide →](../CONTRIBUTING.md)**

---

## Questions?

- **Component-specific**: Check individual component README files
- **Philosophy**: See [PHILOSOPHY.md](../PHILOSOPHY.md)
- **General**: See main [README.md](../README.md)
