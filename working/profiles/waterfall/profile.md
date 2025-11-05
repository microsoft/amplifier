# Waterfall Profile: Phased Sequential Development

## The Pitch

**When requirements are clear and change is expensive, execute with precision.**

This profile adapts the traditional waterfall methodology for AI-assisted development. Perfect for projects where requirements are well-understood upfront, change is costly (embedded systems, regulated industries, hardware integration), and thorough documentation is mandatory.

Unlike traditional waterfall's rigidity, this AI-assisted version maintains phase discipline while enabling rapid execution within each phase.

## Core Philosophy

**Measure twice, cut once.**

In contexts where mistakes are expensive—whether due to hardware dependencies, regulatory compliance, or deployment costs—it's cheaper to invest heavily in upfront analysis and design than to iterate through implementation.

**Phases are sacred, but execution is fast.**

We maintain strict phase gates (no coding before design approval), but AI accelerates work within each phase. What traditionally took months can take days.

**Documentation is the deliverable.**

Each phase produces comprehensive documentation that serves as both specification and audit trail. Code implements what design documents specify.

## Process Overview

### The Six Phases

#### 1. Requirements Gathering (`/waterfall:requirements`)

**Goal**: Capture complete, unambiguous requirements

**Activities**:
- Stakeholder interviews and analysis
- Use case documentation
- Functional and non-functional requirements
- Acceptance criteria definition
- Risk assessment

**Deliverables**:
- Requirements specification document
- Use case diagrams
- Acceptance test criteria

**Gate**: Requirements review and sign-off

#### 2. System Design (`/waterfall:design`)

**Goal**: Create comprehensive system architecture

**Activities**:
- High-level architecture design
- Component specifications
- Interface definitions
- Database schema design
- Security architecture
- Performance requirements

**Deliverables**:
- System architecture document
- Component specifications
- Interface contracts
- Database design
- Sequence diagrams

**Gate**: Design review and approval

#### 3. Detailed Design (`/waterfall:detailed-design`)

**Goal**: Specify implementation details

**Activities**:
- Module-level design
- Algorithm specifications
- Data structure definitions
- Error handling strategies
- Detailed interface specs

**Deliverables**:
- Detailed design documents per module
- API specifications
- Algorithm descriptions
- State diagrams

**Gate**: Detailed design approval

#### 4. Implementation (`/waterfall:implement`)

**Goal**: Build system according to specifications

**Activities**:
- Code generation from specs
- Unit test implementation
- Code review and inspection
- Continuous integration

**Deliverables**:
- Complete source code
- Unit tests
- Build scripts
- Code documentation

**Gate**: Code review and unit test pass

#### 5. Integration & Testing (`/waterfall:test`)

**Goal**: Verify system meets requirements

**Activities**:
- Integration testing
- System testing
- Performance testing
- Security testing
- User acceptance testing

**Deliverables**:
- Test reports
- Defect logs
- Performance metrics
- UAT sign-off

**Gate**: All tests pass, UAT approved

#### 6. Deployment & Maintenance (`/waterfall:deploy`)

**Goal**: Release to production

**Activities**:
- Deployment planning
- Production deployment
- User training
- Documentation handoff
- Maintenance planning

**Deliverables**:
- Deployment guide
- User manuals
- Operations runbooks
- Maintenance plan

**Gate**: Successful production deployment

## When to Use This Profile

**Perfect for:**
- Embedded systems and hardware integration
- Regulated industries (medical, financial, aerospace)
- Fixed-price contracts with clear scope
- Distributed teams needing clear handoffs
- Projects where change is very expensive
- External integrations with long lead times
- When comprehensive documentation is mandatory

**Not ideal for:**
- Exploratory or research projects
- Rapidly changing requirements
- Startups finding product-market fit
- Web/mobile apps needing frequent iteration
- When speed to market is critical
- Prototypes and proof-of-concepts

## Key Principles

### Phase Discipline

**No phase skipping**: Each phase must complete before the next begins
**No backwards iteration**: Changes require formal change control process
**Documentation gates**: Phase deliverables must be approved
**Audit trail**: Every decision documented with rationale

### Comprehensive Planning

**Requirements are complete**: Capture all requirements upfront
**Design before code**: No implementation until design approved
**Test planning early**: Test cases defined during design
**Risk mitigation**: Identify and plan for risks early

### Formal Change Control

**Change requests**: Formal process for requirement changes
**Impact analysis**: Assess cost/schedule impact of changes
**Approval required**: Changes must be approved by stakeholders
**Documentation updates**: Change history maintained

## Success Metrics

**Good waterfall execution:**
- Requirements completeness > 95% at phase 1 completion
- Design changes during implementation < 5%
- Test pass rate on first integration > 85%
- Deployment defects < 1 per 1000 LOC
- Schedule variance < 15%
- Budget variance < 10%

**Warning signs:**
- Frequent requirements changes
- Design rework during implementation
- High defect rates in testing
- Delayed phase transitions
- Stakeholder dissatisfaction

## Philosophy Foundation

Key document: `@philosophy/phased-development.md`

## Available Commands

- `/waterfall:requirements` - Gather and document requirements
- `/waterfall:design` - Create system architecture
- `/waterfall:detailed-design` - Specify implementation details
- `/waterfall:implement` - Build according to specs
- `/waterfall:test` - Integration and system testing
- `/waterfall:deploy` - Production deployment

## Composition

This profile imports from:
- `@shared/commands/commit.md` - Version control
- `@shared/commands/review-changes.md` - Code review
- `@shared/agents/security-guardian.md` - Security review
- `@shared/agents/database-architect.md` - Database design

## Comparison to Default Profile

| Aspect | Waterfall | Default (DDD) |
|--------|-----------|---------------|
| **Change tolerance** | Low - expensive | High - expected |
| **Planning depth** | Comprehensive upfront | Just-in-time |
| **Phase rigidity** | Strict gates | Flexible iteration |
| **Documentation** | Exhaustive | Sufficient |
| **Approval process** | Formal sign-offs | Lightweight review |
| **Best for** | Clear, stable requirements | Evolving requirements |

---

_"In waterfall, the river flows in one direction—but with AI assistance, it flows fast."_
