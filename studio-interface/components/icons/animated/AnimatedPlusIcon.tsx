/**
 * Animated Plus Icon - Rotate 90° on hover
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

export const AnimatedPlusIcon: React.FC<AnimatedIconProps> = ({
  isActive = false,
  animationSpeed = 1,
  onAnimationComplete,
  ...iconProps
}) => {
  const shouldReduceMotion = useReducedMotion()

  const duration = shouldReduceMotion ? 0 : (100 / animationSpeed) / 1000

  return (
    <motion.div
      style={{ display: 'inline-flex' }}
      whileHover={shouldReduceMotion ? {} : { rotate: 90 }}
      transition={{
        duration,
        ease: 'easeOut',
      }}
      onAnimationComplete={onAnimationComplete}
    >
      <Icon {...iconProps}>
        <line x1="12" y1="5" x2="12" y2="19" />
        <line x1="5" y1="12" x2="19" y2="12" />
      </Icon>
    </motion.div>
  )
}