# Calendar & Availability - UX Specification

**Module**: 05_CALENDAR_UX
**Version**: 1.0
**Last Updated**: 2025-10-21
**Status**: Modularized from monolithic files

---

## Overview

This document specifies the UX for calendar & availability features including user flows and component specifications.

## Related Documents

- **Requirements**: [../requirements/05_CALENDAR_AVAILABILITY.md](../requirements/05_CALENDAR_AVAILABILITY.md)
- **UX Overview**: [00_UX_OVERVIEW.md](./00_UX_OVERVIEW.md)
- **Core Components**: [10_CORE_COMPONENTS.md](./10_CORE_COMPONENTS.md)
- **Layout Components**: [11_LAYOUT_COMPONENTS.md](./11_LAYOUT_COMPONENTS.md)

---

## User Flows

## Calendar Flows

### 1. Calendar Viewing and Navigation

```mermaid
graph TD
    A[User Opens Calendar] --> B[Display Current Month]
    B --> C[Load Next 12 Months Data]
    C --> D[Show Room Filter Chips]

    D --> E[All Rooms Selected by Default]
    E --> F[Render Calendar Grid]

    F --> G{For Each Date Cell}
    G --> H[Check Room Availability]
    H --> I{All Filtered Rooms Available?}

    I -->|Yes| J[Show Available Badge Green]
    I -->|No| K{Some Rooms Available?}
    K -->|Yes| L[Show Partial Badge Yellow]
    K -->|No| M{Owner Blocked?}
    M -->|Yes| N[Show Blocked Badge Red]
    M -->|No| O{All Booked?}
    O -->|Yes| P[Show Booked Badge Gray]

    J --> Q[Render Date Cell]
    L --> Q
    N --> Q
    P --> Q

    Q --> R[User Interacts]

    R --> S{Interaction Type?}

    S -->|Tap/Click Date| T{User Type?}
    T -->|Guest| U[Start Booking Flow]
    T -->|Owner| V[Show Date Details & Block Option]

    S -->|Toggle Room Filter| W[Deselect/Select Room Chip]
    W --> X[Re-render Calendar with Filter]
    X --> F

    S -->|Navigate Month| Y[Click Previous/Next]
    Y --> Z[Load New Month Data]
    Z --> F

    S -->|Change View| AA[Select Month/Week/List]
    AA --> AB{View Type?}
    AB -->|Month| F
    AB -->|Week| AC[Render Week View]
    AB -->|List| AD[Render List View]
```

### 2. Owner Date Blocking Flow

```mermaid
graph TD
    A[Owner Clicks Date on Calendar] --> B[Date Details Popover Appears]
    B --> C[Show Current Status]
    C --> D[Show 'Block Dates' Button]

    D --> E[Click Block Dates]
    E --> F[Open Block Dates Modal]

    F --> G[Display Date Range Picker]
    G --> H[User Selects Start Date]
    H --> I[User Selects End Date]
    I --> J{Valid Range?}

    J -->|No| K[Show Error: Invalid Range]
    K --> H
    J -->|Yes| L[Enter Block Reason Required]

    L --> M{Reason Provided?}
    M -->|No| N[Show Error: Reason Required]
    N --> L
    M -->|Yes| O[Preview Impact]

    O --> P{Check for Conflicts}
    P --> Q{Existing Bookings in Range?}

    Q -->|Yes| R[Show Warning List]
    R --> S["Affected Bookings: Dates, Guests"]
    S --> T[Show Override Confirmation]
    T --> U{Owner Confirms Override?}
    U -->|No| H

    Q -->|No| V[No Conflicts Message]
    U -->|Yes| W[Create Calendar Block]
    V --> W

    W --> X[Store Block Reason]
    X --> Y[Store Date Range]
    Y --> Z[Record Created By Owner]
    Z --> AA[Update Calendar Display]
    AA --> AB{Conflicting Bookings?}

    AB -->|Yes| AC[Cancel Conflicting Bookings]
    AC --> AD[Notify Affected Guests]
    AB -->|No| AE[Skip Notifications]

    AD --> AF[Log Block Action]
    AE --> AF
    AF --> AG[Show Success Message]
    AG --> AH[Close Modal, Refresh Calendar]
```

### 3. Calendar Date Selection for Booking

```mermaid
graph TD
    A[Guest Views Calendar] --> B[Clicks First Date]
    B --> C[Store as Check-in Date]
    C --> D[Highlight Selected Date]
    D --> E[Enable Range Selection Mode]

    E --> F[User Hovers Over Dates]
    F --> G[Show Preview Range]

    G --> H[User Clicks Second Date]
    H --> I{Second Date After First?}

    I -->|No| J[Reset Selection]
    J --> B
    I -->|Yes| K[Store as Check-out Date]

    K --> L[Highlight Date Range]
    L --> M[Calculate Night Count]
    M --> N{Range Valid?}

    N -->|Too Long >14| O[Show Error: Max 14 Nights]
    O --> B
    N -->|Too Soon <48hr| P[Show Error: Min 48hr Notice]
    P --> B
    N -->|Valid| Q[Show Booking Summary Banner]

    Q --> R["Display: Check-in, Check-out, Nights"]
    R --> S[Show 'Continue to Room Selection' Button]
    S --> T[User Clicks Continue]
    T --> U[Start Booking Request Flow]
```

---

---

## Components

_Component specifications for calendar & availability will be added here based on component library extraction._

---

## Mobile Responsive Patterns

_Mobile-specific patterns for calendar & availability features will be documented here._

---

## Accessibility Requirements

_Accessibility specifications for calendar & availability features will be documented here._

---

## Cross-References

- All calendar & availability related flows and components are contained in this file
- For shared UI primitives, see [10_CORE_COMPONENTS.md](./10_CORE_COMPONENTS.md)
- For layout patterns, see [11_LAYOUT_COMPONENTS.md](./11_LAYOUT_COMPONENTS.md)

---

## Revision History

- **v1.0** (2025-10-21): Modularized from monolithic UX files
  - Extracted calendar flows from 01_USER_FLOWS.md
  - Created feature-aligned structure matching requirements docs
