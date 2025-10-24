/**
 * Animated Close Icon - Rotate 45° on hover
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

export const AnimatedCloseIcon: React.FC<AnimatedIconProps> = ({
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
      whileHover={shouldReduceMotion ? {} : { rotate: 45 }}
      transition={{
        duration,
        ease: 'easeOut',
      }}
      onAnimationComplete={onAnimationComplete}
    >
      <Icon {...iconProps}>
        <line x1="18" y1="6" x2="6" y2="18" />
        <line x1="6" y1="6" x2="18" y2="18" />
      </Icon>
    </motion.div>
  )
}