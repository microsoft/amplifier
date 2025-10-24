/**
 * Animated Check Icon - Success confirmation with draw-in animation
 * German car facility aesthetic: precise, purposeful motion
 *
 * Animation: Draws checkmark naturally from left to right
 * 1. Short stroke (left side, downward)
 * 2. Long stroke (right side, upward)
 */

import React from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import { Icon, IconProps } from '../Icon'

export interface AnimatedIconProps extends IconProps {
  isActive?: boolean
  animationSpeed?: number
  onAnimationComplete?: () => void
}

export const AnimatedCheckIcon: React.FC<AnimatedIconProps> = ({
  isActive = false,
  animationSpeed = 1,
  onAnimationComplete,
  ...iconProps
}) => {
  const shouldReduceMotion = useReducedMotion()

  // Timing for natural drawing motion
  const shortStrokeDuration = shouldReduceMotion ? 0 : (150 / animationSpeed) / 1000
  const longStrokeDuration = shouldReduceMotion ? 0 : (200 / animationSpeed) / 1000
  const strokeDelay = shouldReduceMotion ? 0 : (100 / animationSpeed) / 1000

  return (
    <Icon {...iconProps}>
      {/* Short stroke - left side, downward (draws first) */}
      <motion.line
        x1="4"
        y1="12"
        x2="9"
        y2="17"
        initial={{ pathLength: 1, opacity: 1 }}
        animate={isActive ? { pathLength: [0, 1], opacity: [0, 1] } : { pathLength: 1, opacity: 1 }}
        transition={{
          duration: shortStrokeDuration,
          ease: [0.4, 0, 0.2, 1], // cubic-bezier for smooth drawing
        }}
        style={{
          pathLength: shouldReduceMotion ? 1 : undefined,
          opacity: shouldReduceMotion ? 1 : undefined,
        }}
      />

      {/* Long stroke - right side, upward (draws second) */}
      <motion.line
        x1="9"
        y1="17"
        x2="20"
        y2="6"
        initial={{ pathLength: 1, opacity: 1 }}
        animate={isActive ? { pathLength: [0, 1], opacity: [0, 1] } : { pathLength: 1, opacity: 1 }}
        transition={{
          duration: longStrokeDuration,
          delay: strokeDelay,
          ease: [0.4, 0, 0.2, 1],
        }}
        onAnimationComplete={onAnimationComplete}
        style={{
          pathLength: shouldReduceMotion ? 1 : undefined,
          opacity: shouldReduceMotion ? 1 : undefined,
        }}
      />
    </Icon>
  )
}