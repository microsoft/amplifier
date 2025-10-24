# Chat System - UX Specification

**Module**: 06_CHAT_UX
**Version**: 1.0
**Last Updated**: 2025-10-21
**Status**: Modularized from monolithic files

---

## Overview

This document specifies the UX for chat system features including user flows and component specifications.

## Related Documents

- **Requirements**: [../requirements/06_CHAT_SYSTEM.md](../requirements/06_CHAT_SYSTEM.md)
- **UX Overview**: [00_UX_OVERVIEW.md](./00_UX_OVERVIEW.md)
- **Core Components**: [10_CORE_COMPONENTS.md](./10_CORE_COMPONENTS.md)
- **Layout Components**: [11_LAYOUT_COMPONENTS.md](./11_LAYOUT_COMPONENTS.md)

---

## User Flows

## Chat Flows

### 1. Sending and Receiving Messages

```mermaid
graph TD
    A[User Opens Chat] --> B[Load Recent Messages Last 50]
    B --> C[Establish WebSocket Connection]
    C --> D[Display Message List]
    D --> E[Auto-scroll to Bottom]

    E --> F[User Types in Input Field]
    F --> G{Text Length > 0?}
    G -->|No| H[Disable Send Button]
    G -->|Yes| I[Enable Send Button]
    I --> J[Broadcast Typing Indicator]

    J --> K{User Action?}
    K -->|Stop Typing 3sec| L[Stop Typing Indicator]
    K -->|Press Enter| M[Trigger Send]
    K -->|Click Send Button| M

    M --> N{Text Length <= 2000?}
    N -->|No| O[Show Error: Message Too Long]
    N -->|Yes| P[Send Message]

    P --> Q[Optimistic UI: Add Message Immediately]
    Q --> R[Show Sending Indicator]
    R --> S[Send via WebSocket]

    S --> T{Send Success?}
    T -->|No| U[Show Error State on Message]
    U --> V[Offer Retry Option]
    T -->|Yes| W[Update Message: Sent Status]

    W --> X[Server Broadcasts to All Clients]
    X --> Y[Other Users Receive Message]
    Y --> Z{User Viewing Chat?}

    Z -->|Yes| AA[Append Message to List]
    AA --> AB{User Near Bottom?}
    AB -->|Yes| AC[Auto-scroll to New Message]
    AB -->|No| AD[Show 'New Messages' Badge]

    Z -->|No| AE{User Online?}
    AE -->|Yes| AF[Show In-App Notification]
    AF --> AG[Update Chat Badge Count]
    AE -->|No| AH{Notifications Enabled?}
    AH -->|Yes| AI[Send Email Notification]
    AH -->|No| AJ[No Notification Sent]
```

### 2. Loading Chat History

```mermaid
graph TD
    A[User Viewing Chat] --> B[Scroll to Top of List]
    B --> C{More History Available?}

    C -->|No| D[Show 'Beginning of Chat' Message]
    C -->|Yes| E[Trigger Load More]

    E --> F[Show Loading Indicator]
    F --> G[Fetch Previous 50 Messages]
    G --> H{Fetch Success?}

    H -->|No| I[Show Error: Could Not Load]
    I --> J[Offer Retry Button]
    J --> E

    H -->|Yes| K[Prepend Messages to List]
    K --> L[Maintain Scroll Position]
    L --> M[Remove Loading Indicator]
    M --> N[Update 'More Available' Flag]
```

### 3. Chat Moderation (Owner)

```mermaid
graph TD
    A[Owner Views Chat Message] --> B[Hover/Long-press Message]
    B --> C[Show Action Menu]
    C --> D{Owner Action?}

    D -->|Delete| E[Show Delete Confirmation]
    E --> F["Warning: Message Removed for Everyone"]
    F --> G{Confirm Delete?}

    G -->|No| H[Close Menu]
    G -->|Yes| I[Soft Delete Message]

    I --> J[Update Message Status: Deleted]
    J --> K[Preserve in Audit Log]
    K --> L[Broadcast Deletion to All Clients]
    L --> M[Message Replaced with 'Message Deleted']
    M --> N[Log Moderation Action]
    N --> O[Show Success Message]
```

### 4. Online Status Updates

```mermaid
graph TD
    A[User Opens App] --> B[Establish WebSocket Connection]
    B --> C[Send 'User Online' Event]
    C --> D[Server Updates User Status: Online]
    D --> E[Broadcast Status to All Connected Users]

    E --> F[Update Online Status Indicator]
    F --> G[Show Green Dot Next to User]

    H[User Closes App/Loses Connection] --> I[WebSocket Disconnects]
    I --> J[Server Detects Disconnect]
    J --> K[Wait 30 Seconds Grace Period]
    K --> L{Reconnected?}

    L -->|Yes| M[Keep Status: Online]
    L -->|No| N[Update User Status: Offline]
    N --> O[Broadcast Status to All Connected Users]
    O --> P[Update Online Status Indicator]
    P --> Q[Show Gray Dot Next to User]

    R[User Inactive 15min] --> S[Send 'User Away' Event]
    S --> T[Update User Status: Away]
    T --> U[Show Yellow Dot Next to User]
```

---

---

## Components

_Component specifications for chat system will be added here based on component library extraction._

---

## Mobile Responsive Patterns

_Mobile-specific patterns for chat system features will be documented here._

---

## Accessibility Requirements

_Accessibility specifications for chat system features will be documented here._

---

## Cross-References

- All chat system related flows and components are contained in this file
- For shared UI primitives, see [10_CORE_COMPONENTS.md](./10_CORE_COMPONENTS.md)
- For layout patterns, see [11_LAYOUT_COMPONENTS.md](./11_LAYOUT_COMPONENTS.md)

---

## Revision History

- **v1.0** (2025-10-21): Modularized from monolithic UX files
  - Extracted chat flows from 01_USER_FLOWS.md
  - Created feature-aligned structure matching requirements docs
