/**
 * Animated Sun Icon - Rotate + scale for theme toggle
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

export const AnimatedSunIcon: React.FC<AnimatedIconProps> = ({
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
        rotate: [0, 180],
        scale: [1, 1.2, 1],
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
      controls.set({ rotate: 0, scale: 1 })
    }
  }, [isActive, shouldReduceMotion, animationSpeed, controls, onAnimationComplete])

  return (
    <motion.div animate={controls} style={{ display: 'inline-flex' }}>
      <Icon {...iconProps}>
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
    </motion.div>
  )
}