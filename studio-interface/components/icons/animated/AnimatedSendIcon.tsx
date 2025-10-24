/**
 * Animated Send Icon - Scale + translate on click
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

export const AnimatedSendIcon: React.FC<AnimatedIconProps> = ({
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
        x: [0, 2, 0],
        y: [0, -2, 0],
        transition: {
          duration: (200 / animationSpeed) / 1000,
          ease: 'easeOut',
        },
      }).then(() => {
        if (onAnimationComplete) {
          onAnimationComplete()
        }
      })
    } else {
      controls.set({ scale: 1, x: 0, y: 0 })
    }
  }, [isActive, shouldReduceMotion, animationSpeed, controls, onAnimationComplete])

  return (
    <motion.div animate={controls} style={{ display: 'inline-flex' }}>
      <Icon {...iconProps}>
        <line x1="22" y1="2" x2="11" y2="13" />
        <polygon points="22 2 15 22 11 13 2 9 22 2" />
      </Icon>
    </motion.div>
  )
}