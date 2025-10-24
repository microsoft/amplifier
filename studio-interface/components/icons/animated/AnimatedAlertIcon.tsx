/**
 * Animated Alert Icon - Warning with shake + grow on exclamation point
 * German car facility aesthetic: precise, purposeful motion
 */

import React, { useEffect } from 'react'
import { motion, useReducedMotion, useAnimation } from 'framer-motion'
import { Icon, IconProps } from '../Icon'

export interface AnimatedIconProps extends IconProps {
  isActive?: boolean
  animationSpeed?: number
  onAnimationComplete?: () => void
}

export const AnimatedAlertIcon: React.FC<AnimatedIconProps> = ({
  isActive = false,
  animationSpeed = 1,
  onAnimationComplete,
  ...iconProps
}) => {
  const shouldReduceMotion = useReducedMotion()
  const exclamationControls = useAnimation()

  useEffect(() => {
    if (isActive && !shouldReduceMotion) {
      exclamationControls.start({
        x: [0, -1, 1, -1, 1, 0],
        scale: [1, 1.2, 1],
        transition: {
          duration: (300 / animationSpeed) / 1000,
          ease: 'easeOut',
        },
      }).then(() => {
        if (onAnimationComplete) {
          onAnimationComplete()
        }
      })
    } else {
      exclamationControls.set({ x: 0, scale: 1 })
    }
  }, [isActive, shouldReduceMotion, animationSpeed, exclamationControls, onAnimationComplete])

  return (
    <Icon {...iconProps}>
      <circle cx="12" cy="12" r="10" />
      <motion.g animate={exclamationControls}>
        <line x1="12" y1="8" x2="12" y2="12" />
        <line x1="12" y1="16" x2="12.01" y2="16" />
      </motion.g>
    </Icon>
  )
}