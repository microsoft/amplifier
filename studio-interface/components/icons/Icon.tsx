/**
 * Studio Icon System
 * German car facility aesthetic: geometric, precise, 24px grid
 */

import React from 'react'

export interface IconProps {
  size?: number | string
  color?: string
  strokeWidth?: number
  className?: string
}

/**
 * Base Icon wrapper
 * All icons built on 24x24 grid with 2px default stroke
 */
export const Icon: React.FC<IconProps & { children: React.ReactNode }> = ({
  size = 24,
  color = 'currentColor',
  strokeWidth = 2,
  className = '',
  children,
}) => {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke={color}
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      xmlns="http://www.w3.org/2000/svg"
    >
      {children}
    </svg>
  )
}

// Device Icons - Outline style
export const DesktopIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <rect x="2" y="3" width="20" height="14" rx="2" />
    <line x1="8" y1="21" x2="16" y2="21" />
    <line x1="12" y1="17" x2="12" y2="21" />
  </Icon>
)

export const TabletIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <rect x="5" y="2" width="14" height="20" rx="2" />
    <line x1="12" y1="18" x2="12.01" y2="18" />
  </Icon>
)

export const MobileIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <rect x="7" y="2" width="10" height="20" rx="2" />
    <line x1="12" y1="18" x2="12.01" y2="18" />
  </Icon>
)

export const WatchIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <rect x="7" y="7" width="10" height="10" rx="2" />
    <path d="M9 3h6" />
    <path d="M9 21h6" />
  </Icon>
)

// Panel Icons - Filled style
export const ConversationIcon: React.FC<IconProps> = (props) => (
  <Icon {...props} strokeWidth={0}>
    <path
      d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h4l4 4 4-4h4c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2z"
      fill="currentColor"
    />
  </Icon>
)

export const HistoryIcon: React.FC<IconProps> = (props) => (
  <Icon {...props} strokeWidth={0}>
    <circle cx="12" cy="12" r="10" fill="currentColor" />
    <path d="M12 6v6l4 2" stroke="white" strokeWidth={2} strokeLinecap="round" />
  </Icon>
)

export const PropertiesIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <circle cx="12" cy="12" r="3" />
    <path d="M12 1v6m0 6v6M5.64 5.64l4.24 4.24m6.36 6.36l4.24 4.24M1 12h6m6 0h6M5.64 18.36l4.24-4.24m6.36-6.36l4.24-4.24" />
  </Icon>
)

export const InspirationIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <rect x="3" y="3" width="18" height="18" rx="2" />
    <circle cx="8.5" cy="8.5" r="1.5" />
    <path d="M21 15l-5-5L5 21" />
  </Icon>
)

// Action Icons
export const PlusIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <line x1="12" y1="5" x2="12" y2="19" />
    <line x1="5" y1="12" x2="19" y2="12" />
  </Icon>
)

export const CloseIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <line x1="18" y1="6" x2="6" y2="18" />
    <line x1="6" y1="6" x2="18" y2="18" />
  </Icon>
)

export const ChevronDownIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <polyline points="6 9 12 15 18 9" />
  </Icon>
)

export const ChevronUpIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <polyline points="18 15 12 9 6 15" />
  </Icon>
)

export const ChevronLeftIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <polyline points="15 18 9 12 15 6" />
  </Icon>
)

export const ChevronRightIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <polyline points="9 18 15 12 9 6" />
  </Icon>
)

export const SendIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <line x1="22" y1="2" x2="11" y2="13" />
    <polygon points="22 2 15 22 11 13 2 9 22 2" />
  </Icon>
)

// State Icons
export const SparkleIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <path d="M12 3v3m0 12v3M3 12h3m12 0h3M6.34 6.34l2.12 2.12m7.08 7.08l2.12 2.12M6.34 17.66l2.12-2.12m7.08-7.08l2.12-2.12" />
    <circle cx="12" cy="12" r="2" fill="currentColor" />
  </Icon>
)

export const LoadingIcon: React.FC<IconProps> = (props) => (
  <Icon {...props} className={`${props.className} animate-spin`}>
    <path d="M21 12a9 9 0 1 1-6.219-8.56" />
  </Icon>
)

export const CheckIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <polyline points="20 6 9 17 4 12" />
  </Icon>
)

export const CopyIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <rect x="9" y="9" width="13" height="13" rx="2" />
    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
  </Icon>
)

export const AlertIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <circle cx="12" cy="12" r="10" />
    <line x1="12" y1="8" x2="12" y2="12" />
    <line x1="12" y1="16" x2="12.01" y2="16" />
  </Icon>
)

// File/Content Icons
export const FileIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
  </Icon>
)

export const ImageIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <rect x="3" y="3" width="18" height="18" rx="2" />
    <circle cx="8.5" cy="8.5" r="1.5" />
    <polyline points="21 15 16 10 5 21" />
  </Icon>
)

export const UploadIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
    <polyline points="17 8 12 3 7 8" />
    <line x1="12" y1="3" x2="12" y2="15" />
  </Icon>
)

// Floating Panel Icons - Geometric, precise, 24x24 grid
export const MinimizeIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <line x1="5" y1="12" x2="19" y2="12" />
  </Icon>
)

export const MaximizeIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <rect x="5" y="5" width="14" height="14" rx="1" />
  </Icon>
)

export const DockTopLeftIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <path d="M5 5h7v7H5z" />
    <path d="M5 5L19 19" strokeDasharray="2 2" opacity="0.3" />
  </Icon>
)

export const DockTopRightIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <path d="M12 5h7v7h-7z" />
    <path d="M19 5L5 19" strokeDasharray="2 2" opacity="0.3" />
  </Icon>
)

export const DockBottomLeftIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <path d="M5 12h7v7H5z" />
    <path d="M5 19L19 5" strokeDasharray="2 2" opacity="0.3" />
  </Icon>
)

export const DockBottomRightIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <path d="M12 12h7v7h-7z" />
    <path d="M19 19L5 5" strokeDasharray="2 2" opacity="0.3" />
  </Icon>
)

export const ArrowRightIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <line x1="5" y1="12" x2="19" y2="12" />
    <polyline points="12 5 19 12 12 19" />
  </Icon>
)

// Settings Icon - Two horizontal sliders (with more spacing)
export const SettingsIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    {/* Top slider - knob on right */}
    <line x1="4" y1="8" x2="20" y2="8" />
    <circle cx="16" cy="8" r="2" fill="currentColor" />

    {/* Bottom slider - knob on left */}
    <line x1="4" y1="16" x2="20" y2="16" />
    <circle cx="8" cy="16" r="2" fill="currentColor" />
  </Icon>
)

// Project Icon - Folder with document
export const ProjectIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <path d="M3 7V19C3 19.5523 3.44772 20 4 20H20C20.5523 20 21 19.5523 21 19V9C21 8.44772 20.5523 8 20 8H11L9 5H4C3.44772 5 3 5.44772 3 6V7Z" />
    <line x1="7" y1="13" x2="17" y2="13" />
    <line x1="7" y1="16" x2="14" y2="16" />
  </Icon>
)

// Pencil Icon - Edit/rename
export const PencilIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <path d="M17 3L21 7L8 20H4V16L17 3Z" />
    <line x1="14" y1="6" x2="18" y2="10" />
  </Icon>
)

// Home Icon - Grid of 4 squares
export const HomeIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <rect x="3" y="3" width="8" height="8" rx="1" />
    <rect x="13" y="3" width="8" height="8" rx="1" />
    <rect x="3" y="13" width="8" height="8" rx="1" />
    <rect x="13" y="13" width="8" height="8" rx="1" />
  </Icon>
)

// Theme Icons - Sun and Moon for light/dark mode
export const SunIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <circle cx="12" cy="12" r="4" />
    <line x1="12" y1="1" x2="12" y2="3" />
    <line x1="12" y1="21" x2="12" y2="23" />
    <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
    <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
    <line x1="1" y1="12" x2="3" y2="12" />
    <line x1="21" y1="12" x2="23" y2="12" />
    <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
    <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
  </Icon>
)

export const MoonIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
  </Icon>
)

// Phase Icons - Geometric, precise, 24x24 grid
// Discovery: Search and explore (magnifying glass)
export const SearchIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <circle cx="11" cy="11" r="8" />
    <line x1="21" y1="21" x2="16.65" y2="16.65" />
  </Icon>
)

// Exploration: Multiple perspectives (grid of 4 squares)
export const GridIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <rect x="3" y="3" width="7" height="7" rx="1" />
    <rect x="14" y="3" width="7" height="7" rx="1" />
    <rect x="3" y="14" width="7" height="7" rx="1" />
    <rect x="14" y="14" width="7" height="7" rx="1" />
  </Icon>
)

// Expression: Design and creation (layered squares)
export const LayersIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <polygon points="12 2 2 7 12 12 22 7 12 2" />
    <polyline points="2 17 12 22 22 17" />
    <polyline points="2 12 12 17 22 12" />
  </Icon>
)

// Delivery: Package and ship (box)
export const BoxIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
    <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
    <line x1="12" y1="22.08" x2="12" y2="12" />
  </Icon>
)

// Chat toggle icon (message bubble)
export const MessageCircleIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
  </Icon>
)

// Trash/Delete icon
export const TrashIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <polyline points="3 6 5 6 21 6" />
    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
    <line x1="10" y1="11" x2="10" y2="17" />
    <line x1="14" y1="11" x2="14" y2="17" />
  </Icon>
)

// Microphone icon
export const MicIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
    <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
    <line x1="12" y1="19" x2="12" y2="23" />
    <line x1="8" y1="23" x2="16" y2="23" />
  </Icon>
)

// More icons can be added following this pattern

/**
 * Animated icon variants available in ./animated/
 *
 * For icons that communicate state changes or provide feedback,
 * import from './animated/' instead:
 *
 * import { AnimatedCheckIcon } from '@/components/icons/animated'
 *
 * See .design/ICON-ANIMATION-GUIDELINES.md for usage patterns.
 */
