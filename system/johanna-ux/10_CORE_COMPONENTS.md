# Core Components - Shared UI Primitives

**Module**: 10_CORE_COMPONENTS
**Version**: 1.0
**Last Updated**: 2025-10-21

---

## Overview

This document specifies shared UI primitives used across all feature areas. These components are based on shadcn/ui and customized for Hawks Nest.

## shadcn/ui Setup

```bash
# Initialize
npx shadcn-ui@latest init

# Install components
npx shadcn-ui@latest add button card input label textarea
npx shadcn-ui@latest add select dialog popover calendar
npx shadcn-ui@latest add badge avatar scroll-area tabs
npx shadcn-ui@latest add toast alert skeleton dropdown-menu
npx shadcn-ui@latest add toggle-group aspect-ratio table
```

## Tailwind Configuration

```typescript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#e6f2ff',
          500: '#0066cc', // Primary blue
          900: '#001429',
        },
        secondary: {
          50: '#e6f9f6',
          500: '#00a896', // Teal
          900: '#002925',
        },
      },
    },
  },
};
```

---

## Core Components

_Component specifications will be extracted from 02_COMPONENT_LIBRARY.md and organized here._

### Button
### Input
### Card
### Dialog
### Badge
### Avatar
### ...

---

## Revision History

- **v1.0** (2025-10-21): Created during documentation modularization
