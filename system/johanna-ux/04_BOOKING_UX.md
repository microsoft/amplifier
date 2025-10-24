# Booking Management - UX Specification

**Module**: 04_BOOKING_UX
**Version**: 1.0
**Last Updated**: 2025-10-21
**Status**: Modularized from monolithic files

---

## Overview

This document specifies the UX for booking management features including user flows and component specifications.

## Related Documents

- **Requirements**: [../requirements/04_BOOKING_MANAGEMENT.md](../requirements/04_BOOKING_MANAGEMENT.md)
- **UX Overview**: [00_UX_OVERVIEW.md](./00_UX_OVERVIEW.md)
- **Core Components**: [10_CORE_COMPONENTS.md](./10_CORE_COMPONENTS.md)
- **Layout Components**: [11_LAYOUT_COMPONENTS.md](./11_LAYOUT_COMPONENTS.md)

---

## User Flows

## Booking Flows

### 1. Guest Booking Request Flow (Complete)

```mermaid
graph TD
    A[Calendar View] --> B[Select Check-in Date]
    B --> C[Select Check-out Date]
    C --> D{Valid Date Range?}

    D -->|No: Past Dates| E[Show Error: Cannot Book Past Dates]
    D -->|No: Too Long| F[Show Error: Max 14 Nights]
    D -->|No: Too Soon| G[Show Error: Min 48hr Lead Time]
    E --> B
    F --> B
    G --> B

    D -->|Yes| H[Show Room Selection Screen]

    H --> I[Display Room 1 Card]
    H --> J[Display Room 2 Card]
    H --> K[Display Room 3 Card]

    I --> L{Room 1 Available?}
    L -->|No| M[Show Unavailable Badge]
    L -->|Yes| N[Enable Room 1 Checkbox]

    J --> O{Room 2 Available?}
    O -->|No| P[Show Unavailable Badge]
    O -->|Yes| Q[Enable Room 2 Checkbox]

    K --> R{Room 3 Available?}
    R -->|No| S[Show Unavailable Badge]
    R -->|Yes| T[Enable Room 3 Checkbox]

    N --> U[User Selects Room 1]
    Q --> V[User Selects Room 2]
    T --> W[User Selects Room 3]

    U --> X{Any Room Selected?}
    V --> X
    W --> X

    X -->|No| Y[Disable Next Button]
    X -->|Yes| Z[Enable Next Button]

    Z --> AA[Click Next: Guest Count]

    AA --> AB[Show Guest Count Screen]
    AB --> AC{For Each Selected Room}
    AC --> AD[Show Room Name]
    AD --> AE[Show Guest Count Stepper]
    AE --> AF[Default: 1 Guest]

    AF --> AG[User Adjusts Count]
    AG --> AH{Count Valid? 1-2}
    AH -->|No| AI[Prevent Invalid Count]
    AH -->|Yes| AJ[Accept Count]

    AJ --> AK[Click Next: Review]

    AK --> AL[Show Review Screen]
    AL --> AM[Display Date Summary]
    AM --> AN[Display Room List with Counts]
    AN --> AO[Show Notes Textarea Optional]

    AO --> AP[User Reviews Details]
    AP --> AQ{Make Changes?}
    AQ -->|Yes| AR[Click Back to Edit]
    AR --> B
    AQ -->|No| AS[Click Submit Request]

    AS --> AT{User Has Overlapping Booking?}
    AT -->|Yes| AU[Show Error: Overlapping Booking]
    AT -->|No| AV[Create Booking Record]

    AV --> AW[Set Status: Pending]
    AW --> AX[Record Timestamp]
    AX --> AY[Send Notification to Owners]
    AY --> AZ[Show Success Screen]

    AZ --> BA[Display Confirmation Message]
    BA --> BB[Show Request Details]
    BB --> BC[Offer: View My Bookings]
    BC --> BD[Offer: Return to Calendar]
```

### 2. Owner Booking Approval Flow

```mermaid
graph TD
    A[Owner Receives Notification] --> B[Open Dashboard]
    B --> C[See Pending Requests Badge]
    C --> D[Click Pending Requests]

    D --> E[View Requests List]
    E --> F[Sorted by Timestamp First-Come-First-Served]

    F --> G[Select Request to Review]
    G --> H[View Request Details Screen]

    H --> I[Display Guest Information]
    H --> J[Display Dates]
    H --> K[Display Rooms Requested]
    H --> L[Display Guest Counts]
    H --> M[Display Notes from Guest]
    H --> N[Display Timestamp Priority]

    N --> O{Conflicts Exist?}
    O -->|Yes| P[Show Warning: Other Requests Exist]
    P --> Q[List Conflicting Requests]
    O -->|No| R[No Conflicts Message]

    Q --> S[Owner Decides]
    R --> S

    S --> T{Decision?}

    T -->|Approve| U[Click Approve Button]
    U --> V[Show Confirmation Dialog]
    V --> W{Confirm Approval?}
    W -->|No| S
    W -->|Yes| X[Update Booking Status: Confirmed]

    X --> Y[Record Approval Timestamp]
    Y --> Z[Record Approver User ID]
    Z --> AA[Update Calendar]
    AA --> AB{Conflicting Requests?}

    AB -->|Yes| AC[Auto-Deny Conflicting Requests]
    AC --> AD[Send Denial Notifications]
    AB -->|No| AE[Skip Auto-Denial]

    AD --> AF[Send Approval Notification to Guest]
    AE --> AF
    AF --> AG[Log Approval Action]
    AG --> AH[Show Success Message]
    AH --> AI[Return to Dashboard]

    T -->|Deny| AJ[Click Deny Button]
    AJ --> AK[Show Denial Reason Modal]
    AK --> AL[Enter Reason Required]
    AL --> AM{Reason Provided?}
    AM -->|No| AN[Show Error: Reason Required]
    AN --> AL
    AM -->|Yes| AO[Submit Denial]

    AO --> AP[Update Booking Status: Denied]
    AP --> AQ[Store Denial Reason]
    AQ --> AR[Record Denial Timestamp]
    AR --> AS[Send Denial Notification with Reason]
    AS --> AT[Log Denial Action]
    AT --> AU[Show Success Message]
    AU --> AI

    T -->|Request Info| AV[Click Request More Info]
    AV --> AW[Open Message Compose Modal]
    AW --> AX[Enter Message to Guest]
    AX --> AY[Send Message]
    AY --> AZ[Notify Guest]
    AZ --> BA[Keep Status: Pending]
    BA --> AI
```

### 3. Guest Booking Cancellation Flow

```mermaid
graph TD
    A[My Bookings Page] --> B[View Confirmed Booking]
    B --> C[Click Cancel Button]
    C --> D{Check Cancellation Policy}

    D --> E{Days Until Check-in?}
    E -->|>= 7 Days| F[Show Standard Cancellation Dialog]
    E -->|< 7 Days| G[Show Warning: Requires Owner Approval]

    F --> H["Confirm: 'Are you sure?'"]
    H --> I{User Confirms?}
    I -->|No| J[Close Dialog, Return to Bookings]
    I -->|Yes| K[Update Status: Cancelled]

    K --> L[Record Cancellation Timestamp]
    L --> M[Record Cancelled By User]
    M --> N[Notify Owner of Cancellation]
    N --> O[Update Calendar: Dates Available]
    O --> P[Log Cancellation Action]
    P --> Q[Show Success: Booking Cancelled]
    Q --> R[Redirect to My Bookings]

    G --> S["Dialog: 'Owner approval required'"]
    S --> T[Show Reason Input Optional]
    T --> U{User Confirms?}
    U -->|No| J
    U -->|Yes| V[Create Cancellation Request]

    V --> W[Set Status: Pending Cancellation]
    W --> X[Notify Owner of Request]
    X --> Y[Log Cancellation Request]
    Y --> Z[Show: Request Sent to Owner]
    Z --> R

    AA[Owner Reviews Cancellation] --> AB{Approve Cancellation?}
    AB -->|Yes| K
    AB -->|No| AC[Update Status: Remains Confirmed]
    AC --> AD[Notify Guest: Cancellation Denied]
    AD --> AE[Log Decision]
```

### 4. Owner Booking Cancellation Flow

```mermaid
graph TD
    A[Owner Views Any Booking] --> B[Click Cancel Booking]
    B --> C[Show Cancellation Dialog]
    C --> D["Enter Reason Required"]
    D --> E{Reason Provided?}

    E -->|No| F[Show Error: Reason Required]
    F --> D
    E -->|Yes| G{Confirm Cancellation?}

    G -->|No| H[Close Dialog]
    G -->|Yes| I[Update Status: Cancelled]

    I --> J[Store Cancellation Reason]
    J --> K[Record Cancelled By Owner]
    K --> L[Record Cancellation Timestamp]
    L --> M[Notify Guest with Reason]
    M --> N[Update Calendar: Dates Available]
    N --> O[Log Cancellation Action]
    O --> P[Show Success Message]
    P --> Q[Return to Bookings or Dashboard]
```

---

---

## Components

_Component specifications for booking management will be added here based on component library extraction._

---

## Mobile Responsive Patterns

_Mobile-specific patterns for booking management features will be documented here._

---

## Accessibility Requirements

_Accessibility specifications for booking management features will be documented here._

---

## Cross-References

- All booking management related flows and components are contained in this file
- For shared UI primitives, see [10_CORE_COMPONENTS.md](./10_CORE_COMPONENTS.md)
- For layout patterns, see [11_LAYOUT_COMPONENTS.md](./11_LAYOUT_COMPONENTS.md)

---

## Revision History

- **v1.0** (2025-10-21): Modularized from monolithic UX files
  - Extracted booking flows from 01_USER_FLOWS.md
  - Created feature-aligned structure matching requirements docs
