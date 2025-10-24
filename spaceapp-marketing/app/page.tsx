'use client'

import { useState, useEffect } from 'react'
import styles from './page.module.css'

// Space Logo Components
// Using actual brand assets from designer
const SpaceLogoWithText = ({ height = 40 }: { height?: number }) => {
  return (
    <img
      src="/Space-w-text.png"
      alt="Space - Proactive AI for teams"
      height={height}
      style={{ display: 'block', height: `${height}px`, width: 'auto' }}
    />
  )
}

const SpaceLogoIcon = ({ size = 50 }: { size?: number }) => {
  return (
    <img
      src="/spaceid.png"
      alt="Space Logo"
      width={size}
      height={size}
      style={{ display: 'block' }}
    />
  )
}

export default function Home() {
  const [activeScenario, setActiveScenario] = useState(0)
  const [activeTab, setActiveTab] = useState('marketing')
  const [isAutoPlaying, setIsAutoPlaying] = useState(true)

  const scenarios = [
    {
      label: 'Marketing Team',
      subtitle: 'Your team is launching a campaign. Space doesn\'t wait—it proactively surfaces: "Social spend up 200% but only 10% convert—should we reallocate to email?"',
      examples: [
        { badge: 'Asks', text: '"CFO concern unaddressed for 2 weeks—schedule executive alignment?"' },
        { badge: 'Surfaces', text: '"7 of 10 interviews cite price barrier—explore sub-$100 option?"' },
        { badge: 'Suggests', text: '"Legal review takes 3 weeks—start now to meet Q4 deadline"' }
      ]
    },
    {
      label: 'Sales Team',
      subtitle: 'You\'re closing enterprise deals. Space proactively flags: "Champion moved to competitor—3 stalled deals at risk. Reconnect with economic buyer?"',
      examples: [
        { badge: 'Asks', text: '"Security questionnaire pending—escalate to fast-track Q4 close?"' },
        { badge: 'Surfaces', text: '"5 prospects asked about SOC2—compliance page could unlock $800K"' },
        { badge: 'Suggests', text: '"CFO prefers annual contracts—update proposal to increase deal value 3x"' }
      ]
    },
    {
      label: 'Product Team',
      subtitle: 'You\'re shipping a new feature. Space notices: "12 beta users hit same error—onboarding flow broken. Address before launch?"',
      examples: [
        { badge: 'Asks', text: '"API latency up 40% since deploy—rollback or investigate root cause?"' },
        { badge: 'Surfaces', text: '"8 support tickets request mobile app—strategic priority to evaluate?"' },
        { badge: 'Suggests', text: '"Feature flag shows 80% drop-off—A/B test simpler flow?"' }
      ]
    },
    {
      label: 'Leadership Team',
      subtitle: 'You\'re planning Q4 strategy. Space surfaces: "Customer churn doubled in enterprise tier—pricing misalignment or product gap?"',
      examples: [
        { badge: 'Asks', text: '"3 departments building AI features—consolidate roadmap to avoid duplication?"' },
        { badge: 'Surfaces', text: '"Competitor launched at half our price—reassess go-to-market positioning?"' },
        { badge: 'Suggests', text: '"Hiring velocity down 30%—review compensation or expand talent sources?"' }
      ]
    },
    {
      label: 'Operations Team',
      subtitle: 'You\'re optimizing workflows. Space alerts: "Invoice processing takes 8 days—automation could save 120 hours monthly"',
      examples: [
        { badge: 'Asks', text: '"Vendor contract expires in 30 days—renew or renegotiate terms?"' },
        { badge: 'Surfaces', text: '"Support tickets spike Mondays—staffing issue or system downtime pattern?"' },
        { badge: 'Suggests', text: '"3 tools overlap for project tracking—consolidate to reduce overhead?"' }
      ]
    },
    {
      label: 'Customer Success',
      subtitle: 'You\'re managing accounts. Space detects: "Top customer usage down 60% for 3 weeks—proactive check-in to prevent churn?"',
      examples: [
        { badge: 'Asks', text: '"5 accounts inactive since onboarding—time for proactive outreach?"' },
        { badge: 'Surfaces', text: '"4 customers requested same feature—prioritize for retention impact?"' },
        { badge: 'Suggests', text: '"Renewal in 45 days but no exec engagement—schedule QBR now?"' }
      ]
    }
  ]

  // Auto-advance carousel
  useEffect(() => {
    if (!isAutoPlaying) return

    const timer = setInterval(() => {
      setActiveScenario((prev) => (prev + 1) % scenarios.length)
    }, 6000)

    return () => clearInterval(timer)
  }, [isAutoPlaying, scenarios.length])

  const scenarioTabs = [
    {
      id: 'marketing',
      emoji: '🎯',
      title: 'Launch campaign that exceeds revenue targets',
      outcome: 'Generate $2M pipeline from Q4 launch',
      steps: [
        {
          title: 'Space builds campaign canvas',
          description: 'Pipeline Tracker, Channel Performance, Creative Assets. Pulls historical insight: "Email drove 70% of pipeline in similar launches."'
        },
        {
          title: 'Team collaborates with shared context',
          description: 'Designer uploads concepts—Space notes successful patterns. Writer explores objections—Space surfaces insights from sales calls. Everyone sees real-time progress.'
        },
        {
          title: 'Space proactively asks and suggests',
          description: '"Social spend up 200% but only 10% convert—reallocate to email?" · "Webinar series converting 3x—shift $50K from social?"'
        }
      ],
      result: 'Team hits $2.1M because Space kept everyone focused on revenue, not just activities.'
    },
    {
      id: 'sales',
      emoji: '💼',
      title: 'Close enterprise deals with perfect coordination',
      outcome: 'Close $500K Fortune 500 deal by Q4',
      steps: [
        {
          title: 'Space creates deal room',
          description: 'Stakeholder Map, Decision Criteria, Competition Tracker. Links similar won deals automatically to surface what worked before.'
        },
        {
          title: 'Team stays synchronized',
          description: 'AE logs discovery—Space extracts requirements. SE documents tech review—Space tracks concerns. Success Manager adds context. All see unified status.'
        },
        {
          title: 'Space flags risks and suggests actions',
          description: '"CFO concern unaddressed 2 weeks—schedule executive alignment?" · "Legal review takes 3 weeks—start now to meet Q4 close?"'
        }
      ],
      result: 'Deal closes on time—entire team coordinated, nothing fell through cracks.'
    },
    {
      id: 'product',
      emoji: '👩‍💻',
      title: 'Make confident decisions backed by complete research',
      outcome: 'Decide by Q1 whether to enter SMB market',
      steps: [
        {
          title: 'Space builds validation framework',
          description: 'Interview Tracker, Competitive Analysis, Market Sizing, Technical Feasibility. Suggests questions from similar market entries.'
        },
        {
          title: 'Team insights automatically connect',
          description: 'PM logs interviews—Space finds patterns across 15 conversations. Designer tests UX—Space tracks valued features. Engineer estimates—Space compares to past efforts.'
        },
        {
          title: 'Space synthesizes for clarity',
          description: '"7 of 10 cite price barrier—recommend sub-$100 option" · "Simplified onboarding tested well—full implementation not essential"'
        }
      ],
      result: 'Clear decision backed by complete synthesis—six months later, everyone remembers why you decided.'
    },
    {
      id: 'cross-functional',
      emoji: '🚀',
      title: 'Execute complex launches with perfect sync',
      outcome: 'Launch in Europe with 100 customers by Q2',
      steps: [
        {
          title: 'Space orchestrates across functions',
          description: 'Cross-functional canvas: Compliance Tracker, Localization Status, Sales Readiness, Product Adaptation. Maps dependencies between teams.'
        },
        {
          title: 'Work flows seamlessly',
          description: 'Legal documents GDPR—auto-informs all teams. Marketing adapts messaging—Space ensures compliance. Sales defines pricing—Space validates against research.'
        },
        {
          title: 'Space highlights coordination needs',
          description: '"Marketing materials ready for legal review" · "Sales training complete—enable pilot meetings" · "Product localization ready for Germany"'
        }
      ],
      result: 'Launch succeeds with 127 customers—all teams synchronized, every dependency managed.'
    }
  ]

  return (
    <main className={styles.main}>
      {/* Navigation */}
      <nav className={styles.nav}>
        <div className="container">
          <div className={styles.navContent}>
            <a href="/" className={styles.logoLink}>
              <SpaceLogoWithText height={36} />
            </a>
            <div className={styles.navLinks}>
              <a href="#how-it-works">How it works</a>
              <a href="#scenarios">Examples</a>
              <a href="#difference">Why proactive</a>
              <a href="#cta" className={styles.btnPrimary}>Start free</a>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className={styles.hero}>
        <div className="container">
          <div className={styles.heroContent}>
            <div className={styles.heroKicker}>The shift from reactive to proactive intelligence</div>
            <h1 className={styles.heroTitle}>AI that asks before you do</h1>
            <p className={styles.heroTagline}>
              ChatGPT waits for your questions. Space notices patterns, surfaces insights,
              and asks the questions your team needs to answer—before critical moments pass.
            </p>

            {/* Hero Carousel */}
            <div className={styles.heroCarousel}>
              {scenarios.map((scenario, index) => (
                <div
                  key={index}
                  className={`${styles.heroScenario} ${activeScenario === index ? styles.active : ''}`}
                >
                  <span className={styles.heroLabel}>{scenario.label}</span>
                  <p className={styles.heroSubtitle}>{scenario.subtitle}</p>
                  <div className={styles.heroExamples}>
                    {scenario.examples.map((example, i) => (
                      <div key={i} className={styles.heroCard}>
                        <span className={styles.heroBadge}>{example.badge}</span>
                        <p>{example.text}</p>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {/* Carousel Controls */}
            <div className={styles.carouselControls}>
              <button
                className={styles.carouselArrow}
                onClick={() => {
                  setIsAutoPlaying(false)
                  setActiveScenario((prev) => (prev - 1 + scenarios.length) % scenarios.length)
                }}
                aria-label="Previous scenario"
              >
                ‹
              </button>
              <div className={styles.carouselDots}>
                {scenarios.map((_, index) => (
                  <button
                    key={index}
                    className={`${styles.carouselDot} ${activeScenario === index ? styles.active : ''}`}
                    onClick={() => {
                      setIsAutoPlaying(false)
                      setActiveScenario(index)
                    }}
                    aria-label={`Go to scenario ${index + 1}`}
                  />
                ))}
              </div>
              <button
                className={styles.carouselArrow}
                onClick={() => {
                  setIsAutoPlaying(false)
                  setActiveScenario((prev) => (prev + 1) % scenarios.length)
                }}
                aria-label="Next scenario"
              >
                ›
              </button>
            </div>

            <div className={styles.heroCta}>
              <a href="#cta" className={`${styles.btnPrimary} ${styles.btnLarge}`}>
                Start free with your team
              </a>
              <a href="#how-it-works" className={`${styles.btnSecondary} ${styles.btnLarge}`}>
                See how it works
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* The Problem You Feel */}
      <section className={`${styles.section} ${styles.problemSection}`}>
        <div className="container">
          <div className={styles.problemContent}>
            <h2 className={styles.problemTitle}>You're managing tools. Your team needs intelligence.</h2>
            <div className={styles.problemGrid}>
              <div className={styles.problemCard}>
                <div className={styles.problemIcon}>⚠️</div>
                <h3>Critical insights hide in scattered conversations</h3>
                <p>
                  CFO raises pricing concerns in Slack. Product logs competitive pressure. Sales reports objections.
                  By the time you connect the dots, the quarter is lost.
                </p>
              </div>
              <div className={styles.problemCard}>
                <div className={styles.problemIcon}>⏱️</div>
                <h3>Opportunities pass while you ask questions</h3>
                <p>
                  You need to know legal review takes 3 weeks. You find out with 2 weeks to launch.
                  Reactive AI waits for you to ask. Proactive AI tells you before it matters.
                </p>
              </div>
              <div className={styles.problemCard}>
                <div className={styles.problemIcon}>🔄</div>
                <h3>Your team fragments across disconnected tools</h3>
                <p>
                  Slack for chat. Notion for docs. Jira for tasks. Figma for design. Linear for eng.
                  Information scatters. Context disappears. Coordination becomes the bottleneck.
                </p>
              </div>
            </div>
            <div className={styles.problemTransition}>
              <p>What if your team had intelligence that <strong>acts before issues become crises?</strong></p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className={`${styles.section} ${styles.howItWorks}`}>
        <div className="container">
          <h2 className={styles.sectionTitle}>How it works</h2>

          <div className={styles.valueFlow}>
            <div className={styles.flowStep}>
              <div className={styles.flowIcon}>1</div>
              <h3>Define outcome</h3>
              <p>"Generate $2M pipeline"</p>
            </div>
            <div className={styles.flowArrow}>→</div>
            <div className={styles.flowStep}>
              <div className={styles.flowIcon}>2</div>
              <h3>Space builds canvas</h3>
              <p>Custom workspace with modules for your goal</p>
            </div>
            <div className={styles.flowArrow}>→</div>
            <div className={styles.flowStep}>
              <div className={styles.flowIcon}>3</div>
              <h3>Team collaborates</h3>
              <p>Everyone works in shared context</p>
            </div>
            <div className={styles.flowArrow}>→</div>
            <div className={`${styles.flowStep} ${styles.highlight}`}>
              <div className={styles.flowIcon}>4</div>
              <h3>Space drives progress</h3>
              <p>Proactively asks, surfaces, suggests</p>
            </div>
          </div>

          <div className={styles.pillars}>
            <div className={styles.pillar}>
              <span className={styles.pillarIcon}>🎨</span>
              <h3>Custom workspaces</h3>
              <p>Not templates. Generated for your specific goal.</p>
            </div>
            <div className={styles.pillar}>
              <span className={styles.pillarIcon}>⚡</span>
              <h3>Proactive intelligence</h3>
              <p>Asks questions. Surfaces insights. Suggests actions.</p>
            </div>
            <div className={styles.pillar}>
              <span className={styles.pillarIcon}>🤝</span>
              <h3>Team intelligence</h3>
              <p>Shared context. Compounding knowledge.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Reactive vs Proactive - The Living Comparison */}
      <section id="difference" className={`${styles.section} ${styles.comparison}`}>
        <div className="container">
          <h2 className={styles.sectionTitle}>See the difference in real-time</h2>
          <p className={styles.sectionSubtitle}>
            Reactive AI waits for you. Proactive AI works with you. Watch the same scenario play out both ways.
          </p>

          <div className={styles.comparisonGrid}>
            {/* Reactive AI Side */}
            <div className={styles.compareColumn}>
              <div className={styles.compareHeader}>
                <h3>Reactive AI</h3>
                <span className={styles.compareTag}>ChatGPT, Claude, etc.</span>
              </div>

              <div className={styles.scenarioContext}>
                <strong>Scenario:</strong> Marketing team launching campaign
              </div>

              <div className={styles.compareFlow}>
                <div className={styles.compareStep}>
                  <div className={styles.stepTime}>0:00</div>
                  <div className={styles.stepContent}>
                    <div className={styles.stepLabel}>You ask</div>
                    <p>"How's our campaign performing?"</p>
                  </div>
                </div>
                <div className={styles.compareStep}>
                  <div className={styles.stepTime}>0:45</div>
                  <div className={styles.stepContent}>
                    <div className={styles.stepLabel}>AI responds</div>
                    <p>"Social spend is up 200%, generating leads"</p>
                  </div>
                </div>
                <div className={styles.compareStep}>
                  <div className={styles.stepTime}>1:30</div>
                  <div className={styles.stepContent}>
                    <div className={styles.stepLabel}>You ask</div>
                    <p>"What's the conversion rate?"</p>
                  </div>
                </div>
                <div className={styles.compareStep}>
                  <div className={styles.stepTime}>2:15</div>
                  <div className={styles.stepContent}>
                    <div className={styles.stepLabel}>AI responds</div>
                    <p>"Conversion rate is 10%"</p>
                  </div>
                </div>
                <div className={styles.compareStep}>
                  <div className={styles.stepTime}>3:00</div>
                  <div className={styles.stepContent}>
                    <div className={styles.stepLabel}>You realize</div>
                    <p>"We're burning budget on low-converting traffic"</p>
                  </div>
                </div>
              </div>

              <div className={styles.compareResult}>
                <div className={styles.resultTime}>⏱️ 8 minutes</div>
                <div className={styles.resultLabel}>You had to ask the right questions</div>
              </div>
            </div>

            {/* Proactive AI Side */}
            <div className={`${styles.compareColumn} ${styles.highlight}`}>
              <div className={styles.compareHeader}>
                <h3>Proactive AI</h3>
                <span className={`${styles.compareTag} ${styles.spaceTag}`}>Space</span>
              </div>

              <div className={styles.scenarioContext}>
                <strong>Same scenario:</strong> Marketing team launching campaign
              </div>

              <div className={styles.compareFlow}>
                <div className={`${styles.compareStep} ${styles.proactive}`}>
                  <div className={styles.stepTime}>0:00</div>
                  <div className={styles.stepContent}>
                    <div className={styles.stepLabel}>Space notices</div>
                    <p>Pattern detected: Social spend up 200%</p>
                  </div>
                </div>
                <div className={`${styles.compareStep} ${styles.proactive}`}>
                  <div className={styles.stepTime}>0:05</div>
                  <div className={styles.stepContent}>
                    <div className={styles.stepLabel}>Space analyzes</div>
                    <p>Cross-references with conversion data: Only 10% converting</p>
                  </div>
                </div>
                <div className={`${styles.compareStep} ${styles.proactive}`}>
                  <div className={styles.stepTime}>0:10</div>
                  <div className={styles.stepContent}>
                    <div className={styles.stepLabel}>Space asks</div>
                    <p><strong>"Social spend up 200% but only 10% convert—reallocate to email?"</strong></p>
                  </div>
                </div>
                <div className={`${styles.compareStep} ${styles.proactive}`}>
                  <div className={styles.stepTime}>0:30</div>
                  <div className={styles.stepContent}>
                    <div className={styles.stepLabel}>You decide</div>
                    <p>"Yes, shift $50K to email campaign"</p>
                  </div>
                </div>
              </div>

              <div className={`${styles.compareResult} ${styles.proactiveResult}`}>
                <div className={styles.resultTime}>⚡ 30 seconds</div>
                <div className={styles.resultLabel}>Space asked the question you needed</div>
              </div>
            </div>
          </div>

          <div className={styles.comparisonInsight}>
            <p>
              <strong>The difference?</strong> Reactive AI waits for perfect questions.
              Proactive AI identifies patterns, connects information, and surfaces insights
              <strong> before critical moments pass.</strong>
            </p>
          </div>

          <div className={styles.proactiveExamples}>
            <h3>What proactive looks like</h3>
            <div className={styles.examplesGrid}>
              <div className={styles.exampleCard}>
                <span className={styles.exampleType}>Asks</span>
                <p>"Social spend up 200%—reallocate?"</p>
              </div>
              <div className={styles.exampleCard}>
                <span className={styles.exampleType}>Surfaces</span>
                <p>"CFO concern unaddressed for 2 weeks"</p>
              </div>
              <div className={styles.exampleCard}>
                <span className={styles.exampleType}>Suggests</span>
                <p>"Start legal review now to hit deadline"</p>
              </div>
              <div className={styles.exampleCard}>
                <span className={styles.exampleType}>Highlights</span>
                <p>"7 of 10 cite price—explore $100 option"</p>
              </div>
              <div className={styles.exampleCard}>
                <span className={styles.exampleType}>Prepares</span>
                <p>"Trajectory at $1.2M—need 40% more"</p>
              </div>
              <div className={styles.exampleCard}>
                <span className={styles.exampleType}>Connects</span>
                <p>"Email drove 70% in similar launches"</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Scenarios */}
      <section id="scenarios" className={`${styles.section} ${styles.scenarios}`}>
        <div className="container">
          <h2 className={styles.sectionTitle}>See teams achieving outcomes</h2>
          <p className={styles.sectionSubtitle}>Choose your team type</p>

          <div className={styles.scenarioTabs}>
            {scenarioTabs.map((tab) => (
              <button
                key={tab.id}
                className={`${styles.tabBtn} ${activeTab === tab.id ? styles.active : ''}`}
                onClick={() => setActiveTab(tab.id)}
              >
                {tab.emoji} {tab.id.charAt(0).toUpperCase() + tab.id.slice(1).replace('-', ' ')}
              </button>
            ))}
          </div>

          {scenarioTabs.map((tab) => (
            <div
              key={tab.id}
              className={`${styles.scenarioPanel} ${activeTab === tab.id ? styles.active : ''}`}
            >
              <div className={styles.scenarioHeader}>
                <span className={styles.scenarioEmoji}>{tab.emoji}</span>
                <h3>{tab.title}</h3>
              </div>
              <div className={styles.outcomeBanner}>
                <strong>Your outcome:</strong> {tab.outcome}
              </div>
              <div className={styles.scenarioSteps}>
                {tab.steps.map((step, index) => (
                  <div key={index} className={styles.scenarioStep}>
                    <h4>{step.title}</h4>
                    <p>{step.description}</p>
                  </div>
                ))}
              </div>
              <div className={styles.scenarioResult}>
                <strong>Result:</strong> {tab.result}
              </div>
            </div>
          ))}

          {/* Quick Scenarios */}
          <div className={styles.quickScenarios}>
            <h3>More ways teams win</h3>
            <div className={styles.quickGrid}>
              <div className={styles.quickCard}>
                <span className={styles.quickEmoji}>🏢</span>
                <h4>Operations</h4>
                <p><strong>Hire 20 engineers in Q1</strong></p>
                <p>Space identifies top conversion channels, ensures perfect coordination—you hit 22 hires.</p>
              </div>
              <div className={styles.quickCard}>
                <span className={styles.quickEmoji}>🎓</span>
                <h4>Customer success</h4>
                <p><strong>Reduce churn by 30%</strong></p>
                <p>Space surfaces risk patterns across touchpoints—churn drops to 9%, exceeding goal.</p>
              </div>
              <div className={styles.quickCard}>
                <span className={styles.quickEmoji}>📊</span>
                <h4>Finance</h4>
                <p><strong>Complete annual budget</strong></p>
                <p>Historical context persists year-over-year—Space keeps assumptions aligned across departments.</p>
              </div>
              <div className={styles.quickCard}>
                <span className={styles.quickEmoji}>⚖️</span>
                <h4>Legal</h4>
                <p><strong>Achieve SOC 2 compliance</strong></p>
                <p>Space maps activities to requirements, auto-organizes evidence—certification on first audit.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section id="cta" className={`${styles.section} ${styles.cta}`}>
        <div className="container">
          <div className={styles.ctaContent}>
            <h2>Start achieving breakthrough outcomes with your team</h2>
            <p className={styles.ctaSubtitle}>
              Free to start. No credit card required. Invite up to 10 team members.
            </p>
            <div className={styles.ctaButtons}>
              <a href="#" className={`${styles.btnPrimary} ${styles.btnLarge}`}>
                Start free
              </a>
              <a href="#" className={`${styles.btnSecondary} ${styles.btnLarge}`}>
                See demo
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className={styles.footer}>
        <div className="container">
          <div className={styles.footerGrid}>
            <div className={styles.footerCol}>
              <div className={styles.footerLogo}>
                <SpaceLogoIcon size={40} />
              </div>
              <p>Proactive intelligence that removes friction between teams and their mission.</p>
            </div>
            <div className={styles.footerCol}>
              <h4>Product</h4>
              <ul>
                <li><a href="#">Features</a></li>
                <li><a href="#">Pricing</a></li>
                <li><a href="#">Security</a></li>
                <li><a href="#">Changelog</a></li>
              </ul>
            </div>
            <div className={styles.footerCol}>
              <h4>Company</h4>
              <ul>
                <li><a href="#">About</a></li>
                <li><a href="#">Blog</a></li>
                <li><a href="#">Careers</a></li>
                <li><a href="#">Contact</a></li>
              </ul>
            </div>
            <div className={styles.footerCol}>
              <h4>Resources</h4>
              <ul>
                <li><a href="#">Documentation</a></li>
                <li><a href="#">Help Center</a></li>
                <li><a href="#">Community</a></li>
                <li><a href="#">API</a></li>
              </ul>
            </div>
          </div>
          <div className={styles.footerBottom}>
            <p>&copy; 2024 Space. Built to remove the mediation between teams and their mission.</p>
          </div>
        </div>
      </footer>
    </main>
  )
}
