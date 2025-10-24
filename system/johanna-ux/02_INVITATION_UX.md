# Invitation & Onboarding - UX Specification

**Module**: 02_INVITATION_UX
**Version**: 1.0
**Last Updated**: 2025-10-21
**Status**: Modularized from monolithic files

---

## Overview

This document specifies the UX for invitation & onboarding features including user flows and component specifications.

## Related Documents

- **Requirements**: [../requirements/02_INVITATION_ONBOARDING.md](../requirements/02_INVITATION_ONBOARDING.md)
- **UX Overview**: [00_UX_OVERVIEW.md](./00_UX_OVERVIEW.md)
- **Core Components**: [10_CORE_COMPONENTS.md](./10_CORE_COMPONENTS.md)
- **Layout Components**: [11_LAYOUT_COMPONENTS.md](./11_LAYOUT_COMPONENTS.md)

---

## User Flows

### 1. Invitation and Registration Flow

```mermaid
graph TD
    A[Owner Dashboard] --> B[Click 'Invite Member']
    B --> C[Enter Email Address]
    C --> D{Valid Email?}
    D -->|No| E[Show Error Message]
    E --> C
    D -->|Yes| F[Submit Invitation]
    F --> G[System Creates Invitation Record]
    G --> H[System Sends Email]
    H --> I[Owner Sees Success Confirmation]

    J[Invitee Receives Email] --> K[Clicks Registration Link]
    K --> L{Link Valid?}
    L -->|Expired| M[Show Error: Link Expired]
    L -->|Already Used| N[Show Error: Already Registered]
    L -->|Valid| O[Show Registration Form]

    O --> P[Email Pre-filled Read-only]
    P --> Q[Enter: Name, Phone, Password]
    Q --> R[Select Contact Preference]
    R --> S{Form Valid?}
    S -->|No| T[Show Validation Errors]
    T --> Q
    S -->|Yes| U[Submit Registration]

    U --> V[Create User Account]
    V --> W[Auto-Login User]
    W --> X[Add to Group Chat]
    X --> Y[Show Welcome Screen]
    Y --> Z{Take Tour?}
    Z -->|Yes| AA[Show Product Tour]
    Z -->|No| AB[Redirect to Calendar]
    AA --> AB

    AB --> AC[Send Welcome Notification]
    AC --> AD[Announce New Member in Chat]
```



---

## Components

_Component specifications for invitation & onboarding will be added here based on component library extraction._

---

## Mobile Responsive Patterns

_Mobile-specific patterns for invitation & onboarding features will be documented here._

---

## Accessibility Requirements

_Accessibility specifications for invitation & onboarding features will be documented here._

---

## Cross-References

- All invitation & onboarding related flows and components are contained in this file
- For shared UI primitives, see [10_CORE_COMPONENTS.md](./10_CORE_COMPONENTS.md)
- For layout patterns, see [11_LAYOUT_COMPONENTS.md](./11_LAYOUT_COMPONENTS.md)

---

## Revision History

- **v1.0** (2025-10-21): Modularized from monolithic UX files
  - Extracted invitation flows from 01_USER_FLOWS.md
  - Created feature-aligned structure matching requirements docs
