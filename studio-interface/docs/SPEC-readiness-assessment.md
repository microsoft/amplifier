# Readiness Assessment System Specification

## Overview

Replace arbitrary message-count metrics with a multi-dimensional, evidence-based assessment that determines when a project is ready to progress from Discovery to the next phase.

## Core Principles (Amplified System Thinking)

1. **Multi-dimensional assessment** - Multiple signals, not a single metric
2. **Observable evidence** - Based on canvas artifacts and conversation depth, not time
3. **User agency** - System suggests readiness, user decides when to progress
4. **Context-aware** - Different projects need different depth
5. **Transparent progress** - User can see what's covered and what's missing

---

## Data Model

### Context Completeness Dimensions

Five key dimensions that must be understood before progressing:

| Dimension | What it measures | Examples |
|-----------|------------------|----------|
| **Purpose** | Project goals, what it needs to accomplish | "Build a landing page to convert visitors", "Redesign to feel more premium" |
| **Audience** | Target users, their needs, behaviors | "Tech-savvy millennials", "B2B decision makers", "Mobile-first users" |
| **Content** | What needs to be communicated | "Product features, pricing, testimonials", "Portfolio work, contact info" |
| **Constraints** | Budget, timeline, technical limits | "Launch in 2 weeks", "$5k budget", "Must work on IE11" |
| **Feeling** | Desired emotional response, brand personality | "Playful and energetic", "Trustworthy and professional", "Minimal and zen" |

### Context Dimension Schema

```typescript
interface ContextDimension {
  covered: boolean        // Has this been discussed?
  confidence: number      // 0-100: How well do we understand it?
  lastUpdated: number     // Timestamp of last update
  evidence: string[]      // Message IDs or artifact IDs that contributed
}
```

### Readiness Assessment Schema

```typescript
interface ReadinessAssessment {
  // Canvas density (physical evidence of work)
  canvasArtifactCount: number

  // Context completeness (conversation depth)
  contextCompleteness: {
    purpose: ContextDimension
    audience: ContextDimension
    content: ContextDimension
    constraints: ContextDimension
    feeling: ContextDimension
  }

  // Calculated metrics
  overallScore: number        // 0-100, weighted calculation
  readyToProgress: boolean    // True if score >= threshold
  missingDimensions: string[] // What still needs attention

  // Metadata
  lastAssessed: number        // Timestamp of last calculation
  assessmentCount: number     // How many times assessed (for tracking)
}
```

---

## Database Design Options

### Option 1: JSONB in `projects.context` (Start Here)

**Schema:**
```sql
-- No migration needed, use existing column
-- projects.context JSONB already exists

-- Example JSONB structure:
{
  "purpose": "...",
  "audience": "...",
  "industry": "...",
  "constraints": [...],
  "canvasArtifacts": [...],
  "readinessAssessment": {
    "canvasArtifactCount": 7,
    "contextCompleteness": {
      "purpose": { "covered": true, "confidence": 85, "lastUpdated": 1234567890, "evidence": ["msg-1", "msg-3"] },
      "audience": { "covered": true, "confidence": 90, "lastUpdated": 1234567890, "evidence": ["msg-2"] },
      "content": { "covered": false, "confidence": 40, "lastUpdated": 1234567890, "evidence": [] },
      "constraints": { "covered": true, "confidence": 75, "lastUpdated": 1234567890, "evidence": ["msg-4"] },
      "feeling": { "covered": false, "confidence": 30, "lastUpdated": 1234567890, "evidence": [] }
    },
    "overallScore": 64,
    "readyToProgress": false,
    "missingDimensions": ["content", "feeling"],
    "lastAssessed": 1234567890,
    "assessmentCount": 12
  }
}
```

**Pros:**
- No migration needed
- Flexible for iteration
- All project data in one place
- Atomic updates

**Cons:**
- Harder to query/aggregate across projects
- No schema enforcement
- JSONB can get large

**Queries:**
```sql
-- Find projects ready to progress
SELECT id, name
FROM projects
WHERE context->'readinessAssessment'->>'readyToProgress' = 'true';

-- Find projects with low audience confidence
SELECT id, name, context->'readinessAssessment'->'contextCompleteness'->'audience'->>'confidence' as audience_confidence
FROM projects
WHERE (context->'readinessAssessment'->'contextCompleteness'->'audience'->>'confidence')::int < 50;
```

---

### Option 2: Separate `readiness_assessments` Table (RECOMMENDED - Hybrid Approach)

**Schema:** (Follows amplified-spaces pattern of structured + JSONB)
```sql
CREATE TABLE readiness_assessments (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

  -- Canvas metrics (structured for querying)
  canvas_artifact_count INTEGER NOT NULL DEFAULT 0,

  -- Calculated metrics (structured for querying)
  overall_score INTEGER CHECK (overall_score BETWEEN 0 AND 100),
  ready_to_progress BOOLEAN DEFAULT FALSE,
  missing_dimensions TEXT[], -- Array for queryable lists

  -- Context completeness (JSONB for flexibility)
  context_completeness JSONB NOT NULL DEFAULT '{
    "purpose": {"covered": false, "confidence": 0, "lastUpdated": null, "evidence": []},
    "audience": {"covered": false, "confidence": 0, "lastUpdated": null, "evidence": []},
    "content": {"covered": false, "confidence": 0, "lastUpdated": null, "evidence": []},
    "constraints": {"covered": false, "confidence": 0, "lastUpdated": null, "evidence": []},
    "feeling": {"covered": false, "confidence": 0, "lastUpdated": null, "evidence": []}
  }'::jsonb,

  -- Metadata
  assessed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  assessment_count INTEGER DEFAULT 1,

  -- Indexes
  UNIQUE(project_id) -- One assessment per project (UPSERT pattern)
);

-- Indexes for performance
CREATE INDEX idx_readiness_assessments_project_id ON readiness_assessments(project_id);
CREATE INDEX idx_readiness_assessments_ready_to_progress ON readiness_assessments(ready_to_progress);
CREATE INDEX idx_readiness_assessments_overall_score ON readiness_assessments(overall_score DESC);

-- GIN index for JSONB queries (if needed later)
CREATE INDEX idx_readiness_assessments_context ON readiness_assessments USING GIN(context_completeness);

-- RLS Policies
ALTER TABLE readiness_assessments ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view readiness for their projects"
  ON readiness_assessments FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM projects
      WHERE projects.id = readiness_assessments.project_id
      AND projects.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update readiness for their projects"
  ON readiness_assessments FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM projects
      WHERE projects.id = readiness_assessments.project_id
      AND projects.user_id = auth.uid()
    )
  );
```

**Pros:**
- ✅ Follows amplified-spaces pattern (structured + JSONB)
- ✅ Fast queries on structured columns (`ready_to_progress`, `overall_score`)
- ✅ Flexible dimension tracking in JSONB (easy to add new dimensions)
- ✅ Better for analytics ("How many projects are ready?")
- ✅ Clean separation of concerns (projects vs readiness)
- ✅ Can add indexes for performance

**Cons:**
- Requires migration (but only once)
- One more table to sync
- JSONB queries need `->` syntax

**Queries:**
```sql
-- Find projects ready to progress (simple query on structured column)
SELECT p.id, p.name, ra.overall_score
FROM projects p
JOIN readiness_assessments ra ON ra.project_id = p.id
WHERE ra.ready_to_progress = TRUE;

-- Get audience confidence for a project (JSONB query)
SELECT
  p.name,
  ra.context_completeness->'audience'->>'confidence' as audience_confidence
FROM projects p
JOIN readiness_assessments ra ON ra.project_id = p.id
WHERE p.id = 'some-uuid';

-- Projects stuck on specific dimensions (array query)
SELECT p.name, ra.missing_dimensions
FROM projects p
JOIN readiness_assessments ra ON ra.project_id = p.id
WHERE 'audience' = ANY(ra.missing_dimensions);

-- Average overall score across all projects (structured column)
SELECT AVG(overall_score) as avg_score
FROM readiness_assessments;
```

---

## Calculation Logic

### Overall Score Formula

Weighted average of:
- **Canvas density**: 30% weight (5+ artifacts = 100%, 0 artifacts = 0%)
- **Context completeness**: 70% weight (average of 5 dimension confidences)

```typescript
function calculateOverallScore(assessment: ReadinessAssessment): number {
  // Canvas density score (0-100)
  const canvasDensityScore = Math.min(100, (assessment.canvasArtifactCount / 5) * 100)

  // Context completeness score (average of 5 dimensions)
  const dimensions = assessment.contextCompleteness
  const contextScore = (
    dimensions.purpose.confidence +
    dimensions.audience.confidence +
    dimensions.content.confidence +
    dimensions.constraints.confidence +
    dimensions.feeling.confidence
  ) / 5

  // Weighted average
  const overallScore = (canvasDensityScore * 0.3) + (contextScore * 0.7)

  return Math.round(overallScore)
}
```

### Ready to Progress Threshold

```typescript
function isReadyToProgress(assessment: ReadinessAssessment): boolean {
  // Must have overall score >= 70
  if (assessment.overallScore < 70) return false

  // Must have at least 5 canvas artifacts
  if (assessment.canvasArtifactCount < 5) return false

  // At least 3 of 5 dimensions must be covered
  const dimensions = Object.values(assessment.contextCompleteness)
  const coveredCount = dimensions.filter(d => d.covered).length
  if (coveredCount < 3) return false

  return true
}
```

---

## How Claude Updates Assessment

After each AI message, Claude analyzes the conversation and returns structured data:

**Request to Claude:**
```json
{
  "messages": [...],
  "canvasArtifacts": [...],
  "currentAssessment": { /* existing assessment */ }
}
```

**Response from Claude:**
```json
{
  "message": "I see you're targeting tech-savvy millennials...",
  "assessmentUpdate": {
    "audience": {
      "covered": true,
      "confidence": 85,
      "evidence": ["msg-abc-123"]
    },
    "feeling": {
      "covered": false,
      "confidence": 40,
      "evidence": []
    }
  }
}
```

Frontend merges this with existing assessment and saves to database.

---

## UI Display

### Compact Indicator (Always Visible)

In toolbar or sidebar:
```
Discovery Progress: 64% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Expanded View (Modal or Panel)

```
Discovery Progress
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 64%

Context Understanding:
✅ Project Goals      85% confident
✅ Target Audience    90% confident
⚠️  Content Scope     40% needs clarity
✅ Constraints        75% confident
○  Visual Direction   30% not started

Canvas: 7 artifacts added

Ready to progress to Exploration? Not yet.
Still need: Content scope, Visual direction
```

---

## Recommendation: Hybrid Approach (Following amplified-spaces Patterns)

**Based on analysis of [amplified-spaces database patterns](/Users/alexlopez/Sites/OCTO/amplified-spaces/supabase/migrations):**

### Pattern Analysis

amplified-spaces uses:
1. **Separate tables for state tracking** - `knowledge_items.status`, `artifacts.processing_status`, `processing_jobs.status`
2. **JSONB for flexible metadata** - `metadata JSONB` columns within structured tables
3. **Status enums with CHECK constraints** - `CHECK (status IN ('pending', 'processing', 'completed'))`
4. **Separate tracking tables** - `processing_jobs` separate from `artifacts` for queue management

**Examples from their codebase:**

```sql
-- knowledge_items: Separate table with status + JSONB metadata
CREATE TABLE knowledge_items (
  id UUID PRIMARY KEY,
  status TEXT NOT NULL DEFAULT 'processing'
    CHECK (status IN ('processing', 'ready', 'error')),
  metadata JSONB DEFAULT '{}',  -- Flexible data
  tags TEXT[] DEFAULT '{}',     -- Array for queryable lists
  ...
);

-- artifacts: Separate table tracking processing state
CREATE TABLE artifacts (
  id UUID PRIMARY KEY,
  processing_status TEXT NOT NULL DEFAULT 'pending'
    CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
  processing_error TEXT,        -- Structured column for errors
  chunk_count INTEGER NOT NULL DEFAULT 0,  -- Calculated metric
  ...
);

-- processing_jobs: Queue management in separate table
CREATE TABLE processing_jobs (
  id UUID PRIMARY KEY,
  artifact_id UUID REFERENCES artifacts(id),
  status TEXT NOT NULL DEFAULT 'queued'
    CHECK (status IN ('queued', 'processing', 'completed', 'failed', 'retrying')),
  payload JSONB NOT NULL DEFAULT '{}',  -- Flexible job data
  result JSONB,                         -- Flexible results
  ...
);
```

**Key Pattern:** Structured columns for querying (`status`, `chunk_count`) + JSONB for flexible data (`metadata`, `payload`)

### Recommended Approach: Separate Table with JSONB Metadata

**Schema:**
```sql
CREATE TABLE readiness_assessments (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

  -- Canvas metrics
  canvas_artifact_count INTEGER NOT NULL DEFAULT 0,

  -- Overall calculated metrics
  overall_score INTEGER CHECK (overall_score BETWEEN 0 AND 100),
  ready_to_progress BOOLEAN DEFAULT FALSE,
  missing_dimensions TEXT[], -- Array of dimension names

  -- Context completeness stored as JSONB (flexible, following their pattern)
  context_completeness JSONB NOT NULL DEFAULT '{
    "purpose": {"covered": false, "confidence": 0, "lastUpdated": null, "evidence": []},
    "audience": {"covered": false, "confidence": 0, "lastUpdated": null, "evidence": []},
    "content": {"covered": false, "confidence": 0, "lastUpdated": null, "evidence": []},
    "constraints": {"covered": false, "confidence": 0, "lastUpdated": null, "evidence": []},
    "feeling": {"covered": false, "confidence": 0, "lastUpdated": null, "evidence": []}
  }'::jsonb,

  -- Metadata
  assessed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  assessment_count INTEGER DEFAULT 1,

  -- Indexes
  UNIQUE(project_id) -- One assessment per project (UPSERT pattern)
);
```

**Why This Approach:**
- ✅ Follows amplified-spaces pattern of separate state tracking tables
- ✅ Uses JSONB for flexible dimension data (like their `metadata` columns)
- ✅ Structured columns for querying (`overall_score`, `ready_to_progress`)
- ✅ Easy to query "ready projects" without parsing JSONB
- ✅ Can add analytics queries across all projects
- ✅ Clean separation of concerns (projects vs readiness)

### Phase 1: Implement Separate Table (This PR)
- Create `readiness_assessments` table migration
- Implement calculation logic
- Build basic UI indicator
- UPSERT pattern: one assessment per project

### Phase 2: Add Claude Analysis (Next)
- Update chat API to analyze messages
- Return assessment updates in structured format
- Frontend merges and saves to database
- Auto-calculate scores on update

### Phase 3: Analytics & Refinement (Later)
- Add aggregate queries (average scores, stuck dimensions)
- Build admin dashboard showing readiness across projects
- Refine thresholds based on real usage data

---

## Open Questions

1. **How often do we recalculate?** After every message? Every 5 messages? On-demand?
2. **Who calculates confidence scores?** Claude (AI analysis) or rule-based (keyword matching)?
3. **Do we show the indicator to users immediately?** Or wait until score > 20%?
4. **Can users manually mark dimensions as "covered"?** Or is it AI-only?
5. **Should we track assessment history?** Or just current state?

---

## Next Steps

1. Review this spec with team
2. Decide: JSONB or separate table?
3. Check `amplified-spaces` for patterns to follow
4. Implement Phase 1 (store in JSONB, basic calculation)
5. Test with real projects to validate thresholds
