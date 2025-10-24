# Examples

**Real-world usage patterns showing components in context**

---

## Available Examples

### [Hero Section Example](./hero-section-example.tsx)
Comprehensive example demonstrating multiple button variants in a landing page context.

**Demonstrates**:
- Visual hierarchy using different variants
- Size differentiation for importance (lg primary, md secondary)
- Icon usage for affordance (arrows, play buttons)
- Responsive full-width patterns for mobile
- Multiple use case scenarios

**Use cases shown**:
1. **SaaS Landing Page** - Magnetic (primary) + Ghost Slide (secondary)
2. **Product Page** - E-commerce with Ripple confirmation
3. **Gaming Interface** - Neon Pulse for energetic feel
4. **Creative Portfolio** - Liquid Morph for artistic expression
5. **Form Submission** - Proper validation and disabled states
6. **Component Showcase** - All variants, sizes, states

**[View code →](./hero-section-example.tsx)**

---

## Coming Soon

As the system grows, we'll add examples for:

### E-commerce
- Product pages with multiple CTAs
- Checkout flows with confirmation
- Cart actions (add, remove, update)

### Forms
- Multi-step forms
- Validation patterns
- Success/error states

### Dashboards
- Admin actions
- Bulk operations
- Status indicators

### Marketing
- Landing page patterns
- Email CTAs
- Promotional campaigns

---

## Running Examples

These examples are React/TypeScript components.

### To use in your project:

1. **Copy the example file**
   ```bash
   cp examples/hero-section-example.tsx ./src/examples/
   ```

2. **Ensure components are available**
   ```bash
   cp -r components/hero-button-refined ./src/components/
   ```

3. **Import and use**
   ```tsx
   import { HeroSectionExample } from './examples/hero-section-example';

   <HeroSectionExample />
   ```

4. **Customize for your needs**
   - Change content
   - Adjust colors
   - Modify layout
   - Add your brand

---

## Example Structure

Each example includes:

### Complete Implementation
- Full component code
- All necessary imports
- Styled structure

### Real Content
- Authentic copy (not Lorem Ipsum)
- Realistic use cases
- Production-ready patterns

### Comments
- Explaining decisions
- Noting variant choices
- Highlighting patterns

### Multiple Scenarios
- Different contexts
- Various configurations
- Edge cases handled

---

## Creating Examples

Good examples show:

**✅ Do**:
- Real-world use cases
- Multiple component variants
- Responsive patterns
- Accessibility considerations
- Comments explaining decisions
- Complete, runnable code

**❌ Don't**:
- Contrived scenarios
- Single component in isolation
- Placeholder content
- Missing imports
- Unexplained choices

---

## Example Patterns

### Visual Hierarchy
```tsx
{/* Primary action - most prominent */}
<HeroButton variant="magnetic" size="lg">
  Get Started
</HeroButton>

{/* Secondary action - less prominent */}
<HeroButton variant="ghost-slide" size="md">
  Learn More
</HeroButton>
```

### Contextual Variants
```tsx
{/* E-commerce checkout - needs confirmation */}
<HeroButton variant="ripple" size="md">
  Complete Purchase
</HeroButton>

{/* Gaming interface - energetic feel */}
<HeroButton variant="neon-pulse" size="lg">
  Play Now
</HeroButton>
```

### Responsive Design
```tsx
{/* Full-width on mobile, fixed on desktop */}
<HeroButton
  variant="magnetic"
  size="lg"
  fullWidth={isMobile}
>
  Sign Up
</HeroButton>
```

### Icon Usage
```tsx
import { ArrowRight, Play, Check } from 'lucide-react';

{/* Forward movement */}
<HeroButton icon={<ArrowRight />} iconPosition="right">
  Continue
</HeroButton>

{/* Play action */}
<HeroButton icon={<Play />} iconPosition="left">
  Watch Demo
</HeroButton>

{/* Confirmation */}
<HeroButton icon={<Check />}>
  Confirm
</HeroButton>
```

---

## Contributing Examples

Want to add an example?

**Follow these steps**:

1. **Identify a real use case** - Not contrived scenarios
2. **Show multiple components** - Demonstrate composition
3. **Include comments** - Explain your decisions
4. **Use realistic content** - No Lorem Ipsum
5. **Test thoroughly** - Ensure it works
6. **Add to this README** - Document what it shows

**Structure**:
```tsx
/**
 * Example: [Name]
 *
 * This example demonstrates:
 * 1. [Key concept]
 * 2. [Pattern shown]
 * 3. [Integration approach]
 */

const ExampleComponent: React.FC = () => {
  // Implementation with comments explaining decisions
};
```

**[Read contribution guide →](../CONTRIBUTING.md)**

---

## Questions?

- **Component usage**: See [components](../components/)
- **Customization**: See [agents](../agents/)
- **Philosophy**: See [PHILOSOPHY.md](../PHILOSOPHY.md)
- **General**: See main [README.md](../README.md)
