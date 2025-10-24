/**
 * Studio Design Tokens
 * Centralized design system tokens
 */

export { colors, type Colors } from './colors'
export { typography, type Typography } from './typography'
export { behaviors, type Behaviors } from './behaviors'
export { spacing, type Spacing } from './spacing'
export { effects, type Effects } from './effects'

// Combined export for convenience
import { colors } from './colors'
import { typography } from './typography'
import { behaviors } from './behaviors'
import { spacing } from './spacing'
import { effects } from './effects'

export const tokens = {
  colors,
  typography,
  behaviors,
  spacing,
  effects,
} as const
