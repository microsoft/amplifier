# Notifications - UX Specification

**Module**: 07_NOTIFICATIONS_UX
**Version**: 1.0
**Last Updated**: 2025-10-21
**Status**: Modularized from monolithic files

---

## Overview

This document specifies the UX for notifications features including user flows and component specifications.

## Related Documents

- **Requirements**: [../requirements/07_NOTIFICATIONS.md](../requirements/07_NOTIFICATIONS.md)
- **UX Overview**: [00_UX_OVERVIEW.md](./00_UX_OVERVIEW.md)
- **Core Components**: [10_CORE_COMPONENTS.md](./10_CORE_COMPONENTS.md)
- **Layout Components**: [11_LAYOUT_COMPONENTS.md](./11_LAYOUT_COMPONENTS.md)

---

## User Flows

## Notification Flows

### 1. In-App Notification Flow

```mermaid
graph TD
    A[System Event Occurs] --> B{Event Type?}

    B -->|Booking Request| C[New Booking Request Event]
    B -->|Booking Approved| D[Booking Approved Event]
    B -->|Booking Denied| E[Booking Denied Event]
    B -->|Booking Cancelled| F[Booking Cancelled Event]
    B -->|Chat Message| G[New Chat Message Event]
    B -->|Member Joined| H[New Member Event]

    C --> I[Determine Recipients: Owners]
    D --> J[Determine Recipients: Requesting Guest]
    E --> J
    F --> K[Determine Recipients: Guest + Owners]
    G --> L[Determine Recipients: All Members Offline]
    H --> M[Determine Recipients: All Members]

    I --> N[Create Notification Records]
    J --> N
    K --> N
    L --> N
    M --> N

    N --> O[For Each Recipient]
    O --> P{User Online?}

    P -->|Yes| Q[Send via WebSocket]
    Q --> R[Client Receives Notification]
    R --> S[Show Toast Notification]
    S --> T[Update Notification Badge Count]
    T --> U[Play Sound if Enabled]

    P -->|No| V[Store for Next Login]
    V --> W[Check Email Notification Settings]

    U --> X[User Clicks Notification]
    X --> Y[Mark as Read]
    Y --> Z[Navigate to Related Content]

    AA[User Opens App While Offline Notifications Exist] --> AB[Fetch Unread Notifications]
    AB --> AC[Display Badge Count]
    AC --> AD[User Opens Notification Panel]
    AD --> AE[Display Notification List]
    AE --> AF[User Clicks Notification]
    AF --> Y
```

### 2. Email Notification Flow

```mermaid
graph TD
    A[System Event Requires Email] --> B{User Email Prefs?}
    B -->|Disabled| C[Skip Email]
    B -->|Enabled| D[Build Email Template]

    D --> E{Notification Type?}
    E -->|Booking Request| F[Template: Booking Request]
    E -->|Booking Approved| G[Template: Booking Approved]
    E -->|Booking Denied| H[Template: Booking Denied]
    E -->|Invitation| I[Template: Invitation]
    E -->|Password Reset| J[Template: Password Reset]

    F --> K[Populate Template Data]
    G --> K
    H --> K
    I --> K
    J --> K

    K --> L[Include: Recipient Name]
    L --> M[Include: Event Details]
    M --> N[Include: Action Link]
    N --> O[Include: Contact Information]

    O --> P[Queue Email for Sending]
    P --> Q[Email Service Processes Queue]
    Q --> R{Send Success?}

    R -->|No| S[Retry Up to 3 Times]
    S --> T{Retry Success?}
    T -->|No| U[Log Failed Email]
    U --> V[Alert Admin]
    T -->|Yes| W[Log Successful Send]

    R -->|Yes| W
    W --> X[Mark Notification as Sent]
```

### 3. Notification Preference Management

```mermaid
graph TD
    A[User Opens Profile] --> B[Navigate to Notifications Section]
    B --> C[Display Notification Preferences]

    C --> D[Show In-App Toggle]
    C --> E[Show Email Toggle]
    C --> F[Show Notification Types]

    F --> G[Booking Updates]
    F --> H[Chat Messages]
    F --> I[New Members]
    F --> J[System Announcements]

    G --> K[Toggle In-App for This Type]
    G --> L[Toggle Email for This Type]
    H --> K
    H --> L
    I --> K
    I --> L
    J --> K
    J --> L

    K --> M[Update Preferences]
    L --> M

    M --> N[Save to Database]
    N --> O[Show Success Message]
    O --> P[Preferences Apply Immediately]
```

---

---

## Components

_Component specifications for notifications will be added here based on component library extraction._

---

## Mobile Responsive Patterns

_Mobile-specific patterns for notifications features will be documented here._

---

## Accessibility Requirements

_Accessibility specifications for notifications features will be documented here._

---

## Cross-References

- All notifications related flows and components are contained in this file
- For shared UI primitives, see [10_CORE_COMPONENTS.md](./10_CORE_COMPONENTS.md)
- For layout patterns, see [11_LAYOUT_COMPONENTS.md](./11_LAYOUT_COMPONENTS.md)

---

## Revision History

- **v1.0** (2025-10-21): Modularized from monolithic UX files
  - Extracted notifications flows from 01_USER_FLOWS.md
  - Created feature-aligned structure matching requirements docs
