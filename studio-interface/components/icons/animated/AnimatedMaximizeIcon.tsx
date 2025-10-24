/**
 * Animated Maximize Icon - Scale from center
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

export const AnimatedMaximizeIcon: React.FC<AnimatedIconProps> = ({
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
        scale: [1, 1.15, 1],
        transition: {
          duration: (200 / animationSpeed) / 1000,
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
    <motion.div
      animate={controls}
      style={{ display: 'inline-flex', transformOrigin: 'center' }}
    >
      <Icon {...iconProps}>
        <rect x="5" y="5" width="14" height="14" rx="1" />
      </Icon>
    </motion.div>
  )
}