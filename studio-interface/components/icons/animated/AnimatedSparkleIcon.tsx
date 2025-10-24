/**
 * Animated Sparkle Icon - Pulse on activation for AI generation
 * German car facility aesthetic: precise, purposeful motion
 */

import React from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import { Icon, IconProps } from '../Icon'

export interface AnimatedIconProps extends IconProps {
  isActive?: boolean
  animationSpeed?: number
  onAnimationComplete?: () => void
}

export const AnimatedSparkleIcon: React.FC<AnimatedIconProps> = ({
  isActive = false,
  animationSpeed = 1,
  onAnimationComplete,
  ...iconProps
}) => {
  const shouldReduceMotion = useReducedMotion()

  const duration = shouldReduceMotion ? 0 : (500 / animationSpeed) / 1000

  return (
    <motion.div
      style={{ display: 'inline-flex' }}
      animate={isActive && !shouldReduceMotion ? {
        rotate: [0, 360],
      } : {}}
      transition={{
        duration: duration * 2,
        ease: 'linear',
        repeat: isActive ? Infinity : 0,
      }}
      onAnimationComplete={onAnimationComplete}
    >
      <motion.div
        animate={isActive && !shouldReduceMotion ? {
          scale: [1, 1.1, 1],
        } : { scale: 1 }}
        transition={{
          duration,
          ease: 'easeInOut',
          repeat: isActive ? Infinity : 0,
        }}
      >
        <Icon {...iconProps}>
          <path d="M12 3v3m0 12v3M3 12h3m12 0h3M6.34 6.34l2.12 2.12m7.08 7.08l2.12 2.12M6.34 17.66l2.12-2.12m7.08-7.08l2.12-2.12" />
          <circle cx="12" cy="12" r="2" fill="currentColor" />
        </Icon>
      </motion.div>
    </motion.div>
  )
}