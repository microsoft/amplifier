/**
 * Animated Upload Icon - Arrow bounces up on upload
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

export const AnimatedUploadIcon: React.FC<AnimatedIconProps> = ({
  isActive = false,
  animationSpeed = 1,
  onAnimationComplete,
  ...iconProps
}) => {
  const shouldReduceMotion = useReducedMotion()
  const arrowControls = useAnimation()

  useEffect(() => {
    if (isActive && !shouldReduceMotion) {
      arrowControls.start({
        y: [0, -4, 0],
        transition: {
          duration: (300 / animationSpeed) / 1000,
          ease: [0.34, 1.56, 0.64, 1], // spring easing
        },
      }).then(() => {
        if (onAnimationComplete) {
          onAnimationComplete()
        }
      })
    } else {
      arrowControls.set({ y: 0 })
    }
  }, [isActive, shouldReduceMotion, animationSpeed, arrowControls, onAnimationComplete])

  return (
    <Icon {...iconProps}>
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <motion.g animate={arrowControls}>
        <polyline points="17 8 12 3 7 8" />
        <line x1="12" y1="3" x2="12" y2="15" />
      </motion.g>
    </Icon>
  )
}