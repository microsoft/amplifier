# Admin Dashboard - UX Specification

**Module**: 09_ADMIN_UX
**Version**: 1.0
**Last Updated**: 2025-10-21
**Status**: Modularized from monolithic files

---

## Overview

This document specifies the UX for admin dashboard features including user flows and component specifications.

## Related Documents

- **Requirements**: [../requirements/09_ADMIN_DASHBOARD.md](../requirements/09_ADMIN_DASHBOARD.md)
- **UX Overview**: [00_UX_OVERVIEW.md](./00_UX_OVERVIEW.md)
- **Core Components**: [10_CORE_COMPONENTS.md](./10_CORE_COMPONENTS.md)
- **Layout Components**: [11_LAYOUT_COMPONENTS.md](./11_LAYOUT_COMPONENTS.md)

---

## User Flows

## Admin Flows

### 1. Member Invitation Flow (Detailed)

```mermaid
graph TD
    A[Owner Dashboard] --> B[Navigate to Invitations]
    B --> C[Invitations Page]
    C --> D[View Recent Invitations List]

    D --> E[Enter New Email Address]
    E --> F{Valid Email Format?}
    F -->|No| G[Show Error: Invalid Email]
    G --> E
    F -->|Yes| H[Click Send Invitation]

    H --> I{Email Already Registered?}
    I -->|Yes| J[Show Error: User Already Exists]
    J --> E

    I -->|No| K{Pending Invitation Exists?}
    K -->|Yes| L[Show Warning: Resend Instead?]
    L --> M{Owner Confirms?}
    M -->|No| E
    M -->|Yes| N[Invalidate Old Invitation]

    K -->|No| O[Create Invitation Record]
    N --> O

    O --> P[Generate Unique Token]
    P --> Q[Set Expiration: 7 Days]
    Q --> R[Store Invitation in Database]
    R --> S[Build Registration URL]
    S --> T[Compose Email Template]

    T --> U[Include: Welcome Message]
    T --> V[Include: Property Description]
    T --> W[Include: Registration Link]
    T --> X[Include: Expiration Notice]
    T --> Y[Include: Contact Information]

    Y --> Z[Send Email via Service]
    Z --> AA{Email Sent?}

    AA -->|No| AB[Show Error: Failed to Send]
    AB --> AC[Log Error]
    AC --> AD[Keep Invitation as Draft]

    AA -->|Yes| AE[Update Status: Pending]
    AE --> AF[Log Invitation Sent]
    AF --> AG[Show Success Confirmation]
    AG --> AH[Refresh Invitations List]
    AH --> AI[New Invitation Appears at Top]
```

### 2. Member Deactivation Flow

```mermaid
graph TD
    A[Owner Views Member Directory] --> B[Select Member]
    B --> C[View Member Profile]
    C --> D[Click Deactivate Button]

    D --> E[Show Deactivation Warning]
    E --> F["Warning: User Loses Access"]
    F --> G[Show Impact: Active Bookings]

    G --> H{Active Bookings Exist?}
    H -->|Yes| I[List Active Bookings]
    I --> J[Require Booking Handling Decision]
    J --> K{Handle Bookings?}
    K -->|Cancel All| L[Confirm Booking Cancellations]
    K -->|Keep Bookings| M[Note: Bookings Preserved]
    H -->|No| N[No Active Bookings]

    L --> O{Final Confirm Deactivation?}
    M --> O
    N --> O

    O -->|No| P[Close Dialog]
    O -->|Yes| Q[Update User Status: Inactive]

    Q --> R[Invalidate User Sessions]
    R --> S[Remove from Chat Access]
    S --> T{Cancel Bookings?}
    T -->|Yes| U[Cancel All User Bookings]
    U --> V[Notify User of Cancellations]
    T -->|No| W[Preserve Bookings]

    V --> X[Log Deactivation Action]
    W --> X
    X --> Y[Show Success Message]
    Y --> Z[Refresh Member Directory]
    Z --> AA[Member Shows as Inactive]
```

### 3. Audit Log Viewing Flow

```mermaid
graph TD
    A[Owner Opens Admin] --> B[Navigate to Audit Log]
    B --> C[Load Recent Actions Last 100]
    C --> D[Display Log Table]

    D --> E[Show Filters]
    E --> F[Filter by Action Type]
    E --> G[Filter by Date Range]
    E --> H[Filter by User]

    F --> I[Select Filter Options]
    G --> I
    H --> I

    I --> J[Apply Filters]
    J --> K[Fetch Filtered Results]
    K --> L[Update Table Display]

    L --> M[Owner Clicks Row]
    M --> N[Expand Row Details]
    N --> O[Show Full Action Details]
    O --> P[Show JSON Payload if Available]

    P --> Q[Owner Clicks Export]
    Q --> R[Generate CSV of Visible Results]
    R --> S[Download File]
```

---

---

## Components

_Component specifications for admin dashboard will be added here based on component library extraction._

---

## Mobile Responsive Patterns

_Mobile-specific patterns for admin dashboard features will be documented here._

---

## Accessibility Requirements

_Accessibility specifications for admin dashboard features will be documented here._

---

## Cross-References

- All admin dashboard related flows and components are contained in this file
- For shared UI primitives, see [10_CORE_COMPONENTS.md](./10_CORE_COMPONENTS.md)
- For layout patterns, see [11_LAYOUT_COMPONENTS.md](./11_LAYOUT_COMPONENTS.md)

---

## Revision History

- **v1.0** (2025-10-21): Modularized from monolithic UX files
  - Extracted admin flows from 01_USER_FLOWS.md
  - Created feature-aligned structure matching requirements docs
