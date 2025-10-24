import React from 'react';
import { HeroButton } from '../components/hero-button-refined/HeroButton';
import { ArrowRight, Play } from 'lucide-react';

/**
 * Example: Hero Section with Multiple Button Variants
 *
 * This example demonstrates:
 * 1. Visual hierarchy using different variants
 * 2. Size differentiation for importance
 * 3. Icon usage for affordance
 * 4. Responsive full-width buttons on mobile
 */

const HeroSectionExample: React.FC = () => {
  return (
    <section className="hero-section">
      <div className="hero-content">
        <h1 className="hero-title">
          Transform Your Workflow with AI-Powered Productivity
        </h1>

        <p className="hero-description">
          Join 50,000+ teams using our platform to streamline operations,
          boost collaboration, and achieve more in less time.
        </p>

        {/* Primary CTA - Magnetic variant for premium feel */}
        <div className="hero-actions">
          <HeroButton
            variant="magnetic"
            size="lg"
            icon={<ArrowRight size={24} />}
            iconPosition="right"
            onClick={() => {
              console.log('Primary CTA clicked');
              // Navigate to signup
            }}
          >
            Start Free Trial
          </HeroButton>

          {/* Secondary CTA - Ghost Slide for subtlety */}
          <HeroButton
            variant="ghost-slide"
            size="lg"
            icon={<Play size={24} />}
            iconPosition="left"
            onClick={() => {
              console.log('Watch demo clicked');
              // Open video modal
            }}
          >
            Watch Demo
          </HeroButton>
        </div>

        {/* Social proof */}
        <div className="hero-social-proof">
          <p className="social-proof-text">
            Trusted by industry leaders
          </p>
          {/* Company logos would go here */}
        </div>
      </div>
    </section>
  );
};

/**
 * Example: E-commerce Product Page
 *
 * Demonstrates:
 * 1. Ripple variant for tactile checkout feedback
 * 2. Custom brand color matching
 * 3. Full-width mobile-friendly buttons
 */

const ProductPageExample: React.FC = () => {
  return (
    <section className="product-page">
      <div className="product-details">
        <h2>Premium Wireless Headphones</h2>
        <p className="price">$299.99</p>

        {/* Add to Cart - Ripple for confirmation feel */}
        <HeroButton
          variant="ripple"
          size="lg"
          customColor="linear-gradient(135deg, #F97316 0%, #EA580C 100%)"
          fullWidth
          onClick={() => {
            console.log('Add to cart clicked');
            // Add to cart logic
          }}
        >
          Add to Cart
        </HeroButton>

        {/* Wishlist - Ghost Slide for secondary action */}
        <HeroButton
          variant="ghost-slide"
          size="md"
          fullWidth
          onClick={() => {
            console.log('Add to wishlist clicked');
            // Wishlist logic
          }}
        >
          Add to Wishlist
        </HeroButton>
      </div>
    </section>
  );
};

/**
 * Example: Gaming Interface
 *
 * Demonstrates:
 * 1. Neon Pulse for energetic gaming aesthetic
 * 2. Particle Burst for celebratory moments
 * 3. Custom vibrant colors
 */

const GamingInterfaceExample: React.FC = () => {
  const [score, setScore] = React.useState(0);

  return (
    <section className="gaming-interface">
      <div className="game-ui">
        <h2 className="score">Score: {score}</h2>

        {/* Play Button - Neon Pulse for energy */}
        <HeroButton
          variant="neon-pulse"
          size="xl"
          customColor="linear-gradient(135deg, #00f5a0 0%, #00d9f5 100%)"
          onClick={() => {
            console.log('Play clicked');
            // Start game
          }}
        >
          Play Now
        </HeroButton>

        {/* Claim Reward - Particle Burst for celebration */}
        <HeroButton
          variant="particle-burst"
          size="lg"
          onClick={() => {
            console.log('Reward claimed');
            setScore(score + 100);
            // Claim reward logic
          }}
        >
          Claim Daily Reward
        </HeroButton>
      </div>
    </section>
  );
};

/**
 * Example: Creative Portfolio
 *
 * Demonstrates:
 * 1. Liquid Morph for artistic, organic feel
 * 2. Custom gradient matching brand
 * 3. Different sizes for visual rhythm
 */

const PortfolioExample: React.FC = () => {
  return (
    <section className="portfolio">
      <div className="portfolio-hero">
        <h1>Creative Director & Designer</h1>
        <p>Crafting digital experiences that inspire</p>

        {/* View Work - Liquid Morph for artistic vibe */}
        <HeroButton
          variant="liquid-morph"
          size="lg"
          customColor="linear-gradient(135deg, #fa709a 0%, #fee140 100%)"
          onClick={() => {
            console.log('View work clicked');
            // Scroll to portfolio section
          }}
        >
          View My Work
        </HeroButton>

        {/* Contact - Ghost Slide for subtlety */}
        <HeroButton
          variant="ghost-slide"
          size="md"
          onClick={() => {
            console.log('Contact clicked');
            // Navigate to contact form
          }}
        >
          Get In Touch
        </HeroButton>
      </div>
    </section>
  );
};

/**
 * Example: Form with Validation
 *
 * Demonstrates:
 * 1. Disabled state
 * 2. Size progression (submit is larger)
 * 3. Full-width mobile-friendly layout
 */

const FormExample: React.FC = () => {
  const [formValid, setFormValid] = React.useState(false);

  return (
    <section className="form-section">
      <form className="signup-form">
        <h2>Create Your Account</h2>

        {/* Form fields would go here */}
        <input
          type="email"
          placeholder="Email"
          onChange={(e) => {
            // Validation logic
            setFormValid(e.target.value.includes('@'));
          }}
        />

        {/* Submit - Disabled until form is valid */}
        <HeroButton
          variant="magnetic"
          size="lg"
          fullWidth
          disabled={!formValid}
          onClick={(e) => {
            e.preventDefault();
            console.log('Form submitted');
            // Submit logic
          }}
        >
          Create Account
        </HeroButton>

        {/* Cancel - Smaller, subtle */}
        <HeroButton
          variant="ghost-slide"
          size="sm"
          fullWidth
          onClick={() => {
            console.log('Form cancelled');
            // Cancel logic
          }}
        >
          Cancel
        </HeroButton>
      </form>
    </section>
  );
};

/**
 * Example: Button Showcase (All Variants)
 *
 * Useful for:
 * 1. Visual comparison
 * 2. Testing interactions
 * 3. Demonstrating to stakeholders
 */

const ShowcaseExample: React.FC = () => {
  const variants = [
    'magnetic',
    'ripple',
    'ghost-slide',
    'neon-pulse',
    'liquid-morph',
    'particle-burst',
  ] as const;

  const sizes = ['sm', 'md', 'lg', 'xl'] as const;

  return (
    <section className="showcase">
      <h1>Hero Button - All Variants</h1>

      {/* Variants Showcase */}
      <div className="variants-grid">
        {variants.map((variant) => (
          <div key={variant} className="variant-demo">
            <h3>{variant}</h3>
            <HeroButton
              variant={variant}
              size="lg"
              onClick={() => console.log(`${variant} clicked`)}
            >
              {variant.split('-').map((word) =>
                word.charAt(0).toUpperCase() + word.slice(1)
              ).join(' ')}
            </HeroButton>
          </div>
        ))}
      </div>

      {/* Sizes Showcase */}
      <div className="sizes-grid">
        <h2>Sizes</h2>
        {sizes.map((size) => (
          <HeroButton
            key={size}
            variant="magnetic"
            size={size}
            onClick={() => console.log(`${size} clicked`)}
          >
            Size: {size.toUpperCase()}
          </HeroButton>
        ))}
      </div>

      {/* States Showcase */}
      <div className="states-grid">
        <h2>States</h2>

        <div>
          <h3>Default</h3>
          <HeroButton variant="magnetic" size="md">
            Default
          </HeroButton>
        </div>

        <div>
          <h3>Disabled</h3>
          <HeroButton variant="magnetic" size="md" disabled>
            Disabled
          </HeroButton>
        </div>

        <div>
          <h3>With Left Icon</h3>
          <HeroButton
            variant="magnetic"
            size="md"
            icon={<ArrowRight size={20} />}
            iconPosition="left"
          >
            Left Icon
          </HeroButton>
        </div>

        <div>
          <h3>With Right Icon</h3>
          <HeroButton
            variant="magnetic"
            size="md"
            icon={<ArrowRight size={20} />}
            iconPosition="right"
          >
            Right Icon
          </HeroButton>
        </div>

        <div>
          <h3>Full Width</h3>
          <HeroButton variant="magnetic" size="md" fullWidth>
            Full Width
          </HeroButton>
        </div>
      </div>
    </section>
  );
};

// Export all examples
export {
  HeroSectionExample,
  ProductPageExample,
  GamingInterfaceExample,
  PortfolioExample,
  FormExample,
  ShowcaseExample,
};

// Default export for convenience
export default ShowcaseExample;
