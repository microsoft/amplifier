# Photo Gallery - UX Specification

**Module**: 08_GALLERY_UX
**Version**: 1.0
**Last Updated**: 2025-10-21
**Status**: Modularized from monolithic files

---

## Overview

This document specifies the UX for photo gallery features including user flows and component specifications.

## Related Documents

- **Requirements**: [../requirements/08_PHOTO_GALLERY.md](../requirements/08_PHOTO_GALLERY.md)
- **UX Overview**: [00_UX_OVERVIEW.md](./00_UX_OVERVIEW.md)
- **Core Components**: [10_CORE_COMPONENTS.md](./10_CORE_COMPONENTS.md)
- **Layout Components**: [11_LAYOUT_COMPONENTS.md](./11_LAYOUT_COMPONENTS.md)

---

## User Flows

## Photo Gallery Flows

### 1. Guest Photo Browsing Flow

```mermaid
graph TD
    A[User Opens Photos] --> B[Load Category List]
    B --> C[Display Category Cards]
    C --> D[Show Primary Photo per Category]
    D --> E[Show Photo Count per Category]

    E --> F[User Selects Category]
    F --> G[Load Category Photos]
    G --> H[Display Thumbnail Grid]
    H --> I[Lazy Load Visible Thumbnails]

    I --> J[User Scrolls Down]
    J --> K[Load More Thumbnails]
    K --> I

    I --> L[User Taps/Clicks Photo]
    L --> M[Open Lightbox]
    M --> N[Display Full Resolution Image]
    N --> O[Show Caption/Description]
    O --> P[Show Photo Counter 'X of Y']

    P --> Q{User Interaction?}

    Q -->|Swipe Right/Click Prev| R[Load Previous Photo]
    R --> N

    Q -->|Swipe Left/Click Next| S[Load Next Photo]
    S --> N

    Q -->|Tap/Click Close| T[Close Lightbox]
    T --> H

    Q -->|Press Escape Key| T
    Q -->|Press Arrow Left Key| R
    Q -->|Press Arrow Right Key| S
```

### 2. Owner Photo Upload Flow

```mermaid
graph TD
    A[Owner Opens Photos] --> B[All Guest Features + Upload]
    B --> C[Click Upload Button]
    C --> D[Open Upload Modal]

    D --> E[Select Category Dropdown]
    E --> F[Choose Category]
    F --> G[Show File Picker]

    G --> H{Upload Method?}
    H -->|Click Browse| I[Open File Dialog]
    H -->|Drag & Drop| J[Drop Files on Area]

    I --> K[User Selects Files]
    J --> K

    K --> L{Valid Files?}
    L -->|Wrong Format| M[Show Error: JPEG/PNG Only]
    L -->|Too Large >10MB| N[Show Error: Max 10MB]
    L -->|Valid| O[Show File Preview List]

    O --> P[For Each File: Add Caption Optional]
    P --> Q[For Each File: Add Description Optional]

    Q --> R[Set Primary Photo Optional]
    R --> S[Click Upload Button]
    S --> T[Start Upload Progress]

    T --> U[Upload Original File]
    U --> V[Server Creates Display Version]
    V --> W[Server Creates Thumbnail]
    W --> X[Store Photo Metadata]

    X --> Y[Update Progress Bar]
    Y --> Z{All Files Uploaded?}
    Z -->|No| U
    Z -->|Yes| AA[Show Success Message]

    AA --> AB[Close Upload Modal]
    AB --> AC[Refresh Photo Gallery]
    AC --> AD[New Photos Appear in Category]
```

### 3. Owner Photo Management Flow

```mermaid
graph TD
    A[Owner Views Photo in Lightbox] --> B[Show Edit/Delete Options]
    B --> C{Owner Action?}

    C -->|Edit| D[Open Edit Modal]
    D --> E[Show Current Caption]
    D --> F[Show Current Description]
    D --> G[Show Current Category]

    E --> H[Edit Caption]
    F --> I[Edit Description]
    G --> J[Change Category Dropdown]

    H --> K[Click Save Changes]
    I --> K
    J --> K

    K --> L[Update Photo Metadata]
    L --> M[Show Success Message]
    M --> N[Close Edit Modal]
    N --> O[Refresh Display]

    C -->|Delete| P[Show Delete Confirmation]
    P --> Q["Warning: Cannot Undo"]
    Q --> R{Confirm Delete?}

    R -->|No| S[Close Dialog]
    R -->|Yes| T[Delete Original File]
    T --> U[Delete Display Version]
    U --> V[Delete Thumbnail]
    V --> W[Delete Metadata Record]
    W --> X[Log Deletion Action]
    X --> Y[Show Success Message]
    Y --> Z[Close Lightbox]
    Z --> AA[Refresh Gallery]
    AA --> AB[Photo No Longer Appears]

    C -->|Set Primary| AC[Mark as Primary for Category]
    AC --> AD[Unmark Previous Primary]
    AD --> AE[Update Display Order]
    AE --> AF[Show Success Message]
    AF --> O

    C -->|Reorder| AG[Drag to New Position Desktop]
    AG --> AH[Update Display Order]
    AH --> O
```

---

---

## Components

_Component specifications for photo gallery will be added here based on component library extraction._

---

## Mobile Responsive Patterns

_Mobile-specific patterns for photo gallery features will be documented here._

---

## Accessibility Requirements

_Accessibility specifications for photo gallery features will be documented here._

---

## Cross-References

- All photo gallery related flows and components are contained in this file
- For shared UI primitives, see [10_CORE_COMPONENTS.md](./10_CORE_COMPONENTS.md)
- For layout patterns, see [11_LAYOUT_COMPONENTS.md](./11_LAYOUT_COMPONENTS.md)

---

## Revision History

- **v1.0** (2025-10-21): Modularized from monolithic UX files
  - Extracted gallery flows from 01_USER_FLOWS.md
  - Created feature-aligned structure matching requirements docs
