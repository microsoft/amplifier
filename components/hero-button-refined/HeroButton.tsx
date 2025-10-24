import React from 'react';
import './HeroButton.css';

export interface HeroButtonProps {
  /**
   * Button variant - each with distinct personality
   */
  variant?: 'magnetic' | 'ripple' | 'ghost-slide' | 'neon-pulse' | 'liquid-morph' | 'particle-burst';

  /**
   * Button size
   */
  size?: 'sm' | 'md' | 'lg' | 'xl';

  /**
   * Button content
   */
  children: React.ReactNode;

  /**
   * Click handler
   */
  onClick?: () => void;

  /**
   * Disabled state
   */
  disabled?: boolean;

  /**
   * Full width
   */
  fullWidth?: boolean;

  /**
   * Icon (optional)
   */
  icon?: React.ReactNode;

  /**
   * Icon position
   */
  iconPosition?: 'left' | 'right';

  /**
   * Custom color (within guardrails)
   */
  customColor?: string;
}

export const HeroButton: React.FC<HeroButtonProps> = ({
  variant = 'magnetic',
  size = 'md',
  children,
  onClick,
  disabled = false,
  fullWidth = false,
  icon,
  iconPosition = 'left',
  customColor,
}) => {
  const buttonRef = React.useRef<HTMLButtonElement>(null);
  const [mousePosition, setMousePosition] = React.useState({ x: 0, y: 0 });
  const [isHovered, setIsHovered] = React.useState(false);

  // Magnetic effect (only for magnetic variant)
  const handleMouseMove = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (variant !== 'magnetic' || disabled) return;

    const button = buttonRef.current;
    if (!button) return;

    const rect = button.getBoundingClientRect();
    const x = e.clientX - rect.left - rect.width / 2;
    const y = e.clientY - rect.top - rect.height / 2;

    // Limit magnetic pull to 8px
    const distance = Math.sqrt(x * x + y * y);
    const maxDistance = 40;
    const strength = Math.min(distance / maxDistance, 1);

    setMousePosition({
      x: (x / rect.width) * 8 * strength,
      y: (y / rect.height) * 8 * strength,
    });
  };

  const handleMouseLeave = () => {
    setMousePosition({ x: 0, y: 0 });
    setIsHovered(false);
  };

  const handleMouseEnter = () => {
    setIsHovered(true);
  };

  // Ripple effect (only for ripple variant)
  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (disabled) return;

    if (variant === 'ripple') {
      const button = buttonRef.current;
      if (!button) return;

      const ripple = document.createElement('span');
      const rect = button.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height);
      const x = e.clientX - rect.left - size / 2;
      const y = e.clientY - rect.top - size / 2;

      ripple.style.width = ripple.style.height = `${size}px`;
      ripple.style.left = `${x}px`;
      ripple.style.top = `${y}px`;
      ripple.classList.add('ripple-effect');

      button.appendChild(ripple);

      setTimeout(() => {
        ripple.remove();
      }, 600);
    }

    onClick?.();
  };

  const classNames = [
    'hero-button',
    `hero-button--${variant}`,
    `hero-button--${size}`,
    fullWidth ? 'hero-button--full-width' : '',
    disabled ? 'hero-button--disabled' : '',
    isHovered ? 'hero-button--hovered' : '',
  ]
    .filter(Boolean)
    .join(' ');

  const style: React.CSSProperties = {
    transform:
      variant === 'magnetic'
        ? `translate(${mousePosition.x}px, ${mousePosition.y}px)`
        : undefined,
    ...(customColor ? { '--custom-color': customColor } as React.CSSProperties : {}),
  };

  return (
    <button
      ref={buttonRef}
      className={classNames}
      onClick={handleClick}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      onMouseEnter={handleMouseEnter}
      disabled={disabled}
      style={style}
      type="button"
    >
      <span className="hero-button__content">
        {icon && iconPosition === 'left' && (
          <span className="hero-button__icon hero-button__icon--left">{icon}</span>
        )}
        <span className="hero-button__text">{children}</span>
        {icon && iconPosition === 'right' && (
          <span className="hero-button__icon hero-button__icon--right">{icon}</span>
        )}
      </span>

      {/* Variant-specific decorative elements */}
      {variant === 'ghost-slide' && <span className="hero-button__ghost" />}
      {variant === 'neon-pulse' && <span className="hero-button__glow" />}
      {variant === 'liquid-morph' && <span className="hero-button__liquid" />}
      {variant === 'particle-burst' && (
        <span className="hero-button__particles">
          {[...Array(12)].map((_, i) => (
            <span key={i} className="hero-button__particle" />
          ))}
        </span>
      )}
    </button>
  );
};

export default HeroButton;
