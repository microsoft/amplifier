/**
 * Animated Copy Icon - Quick scale bounce on action
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

export const AnimatedCopyIcon: React.FC<AnimatedIconProps> = ({
  isActive = false,
  animationSpeed = 1,
  onAnimationComplete,
  ...iconProps
}) => {
  const shouldReduceMotion = useReducedMotion()
  const controls = useAnimation()

  useEffect(() => {
    if (isActive && !shouldReduceMotion) {
      controls.start({
        scale: [1, 1.1, 1],
        transition: {
          duration: (100 / animationSpeed) / 1000,
          ease: [0.34, 1.56, 0.64, 1], // spring easing
        },
      }).then(() => {
        if (onAnimationComplete) {
          onAnimationComplete()
        }
      })
    } else {
      controls.set({ scale: 1 })
    }
  }, [isActive, shouldReduceMotion, animationSpeed, controls, onAnimationComplete])

  return (
    <motion.div animate={controls} style={{ display: 'inline-flex' }}>
      <Icon {...iconProps}>
        <rect x="9" y="9" width="13" height="13" rx="2" />
        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
      </Icon>
    </motion.div>
  )
}