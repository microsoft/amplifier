# Authentication & Access - UX Specification

**Module**: 01_AUTH_UX
**Version**: 1.0
**Last Updated**: 2025-10-21
**Status**: Modularized from monolithic files

---

## Overview

This document specifies the UX for authentication & access features including user flows and component specifications.

## Related Documents

- **Requirements**: [../requirements/01_AUTH_AND_ACCESS.md](../requirements/01_AUTH_AND_ACCESS.md)
- **UX Overview**: [00_UX_OVERVIEW.md](./00_UX_OVERVIEW.md)
- **Core Components**: [10_CORE_COMPONENTS.md](./10_CORE_COMPONENTS.md)
- **Layout Components**: [11_LAYOUT_COMPONENTS.md](./11_LAYOUT_COMPONENTS.md)

---

## User Flows

## Authentication Flows

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

### 2. Login Flow

```mermaid
graph TD
    A[Login Page] --> B[Enter Email]
    B --> C[Enter Password]
    C --> D[Click 'Log In']
    D --> E{Credentials Valid?}

    E -->|No| F[Show Error: Invalid Email/Password]
    F --> B

    E -->|Yes| G{Account Active?}
    G -->|No| H[Show Error: Account Deactivated]
    G -->|Yes| I[Create Session]

    I --> J[Load User Data]
    J --> K{User Role?}
    K -->|Owner| L[Redirect to Owner Dashboard]
    K -->|Guest| M[Redirect to Guest Home]

    L --> N[Show Pending Actions Badge]
    M --> O[Show Upcoming Bookings]
```

### 3. Password Reset Flow

```mermaid
graph TD
    A[Login Page] --> B[Click 'Forgot Password?']
    B --> C[Enter Email]
    C --> D[Submit Request]
    D --> E{Email Exists?}

    E -->|No| F[Show Generic Success for Security]
    E -->|Yes| G[Generate Reset Token]
    G --> H[Send Reset Email]
    H --> F

    F --> I[Show: Check Your Email]

    J[User Receives Email] --> K[Click Reset Link]
    K --> L{Link Valid?}
    L -->|Expired| M[Show Error: Link Expired]
    L -->|Invalid| N[Show Error: Invalid Link]
    L -->|Valid| O[Show Reset Form]

    O --> P[Enter New Password]
    P --> Q[Confirm New Password]
    Q --> R{Passwords Match?}
    R -->|No| S[Show Error: Passwords Don't Match]
    S --> P
    R -->|Yes| T{Password Strong Enough?}
    T -->|No| U[Show Error: Password Requirements]
    U --> P
    T -->|Yes| V[Update Password]

    V --> W[Show Success Message]
    W --> X[Redirect to Login]
```

---

---

## Components

_Component specifications for authentication & access will be added here based on component library extraction._

---

## Mobile Responsive Patterns

_Mobile-specific patterns for authentication & access features will be documented here._

---

## Accessibility Requirements

_Accessibility specifications for authentication & access features will be documented here._

---

## Cross-References

- All authentication & access related flows and components are contained in this file
- For shared UI primitives, see [10_CORE_COMPONENTS.md](./10_CORE_COMPONENTS.md)
- For layout patterns, see [11_LAYOUT_COMPONENTS.md](./11_LAYOUT_COMPONENTS.md)

---

## Revision History

- **v1.0** (2025-10-21): Modularized from monolithic UX files
  - Extracted auth flows from 01_USER_FLOWS.md
  - Created feature-aligned structure matching requirements docs
