# SpaceApp Marketing

Marketing website for SpaceApp.

## Getting Started

First, install dependencies:

```bash
npm install
```

Then, run the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Project Structure

```
spaceapp-marketing/
├── app/              # Next.js app directory
├── components/       # React components
├── public/          # Static assets
├── state/           # Zustand state management
└── utils/           # Utility functions
```

## Design System

This project follows the Amplified Design system principles:

- **Spacing**: 8px system (4, 8, 12, 16, 24, 32, 48, 64, 96, 128)
- **Typography**: Sora (headings), Geist Sans (body), Geist Mono (code)
- **Motion**: <100ms instant, 100-300ms responsive, 300-1000ms deliberate
- **Accessibility**: WCAG AA minimum, 44x44px touch targets

## Validation

Validate design tokens:

```bash
npm run validate:tokens
```

Type check:

```bash
npx tsc --noEmit
```

## Learn More

See the main [Amplified Design](../) repository for design principles and guidelines.
