/**
 * Animated Moon Icon - Scale + fade for theme toggle
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

export const AnimatedMoonIcon: React.FC<AnimatedIconProps> = ({
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
        scale: [1, 1.2, 1],
        rotate: [0, 15, 0],
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
      controls.set({ scale: 1, rotate: 0 })
    }
  }, [isActive, shouldReduceMotion, animationSpeed, controls, onAnimationComplete])

  return (
    <motion.div animate={controls} style={{ display: 'inline-flex' }}>
      <Icon {...iconProps}>
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
      </Icon>
    </motion.div>
  )
}