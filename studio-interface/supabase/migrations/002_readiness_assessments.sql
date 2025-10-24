-- Readiness Assessment System Migration
-- Date: 2025-10-15
-- Description: Implements multi-dimensional readiness assessment for project progression
--              Following amplified-spaces pattern: structured columns + JSONB metadata
--              Replaces arbitrary message counts with observable evidence-based metrics

-- ============================================================================
-- READINESS ASSESSMENTS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS readiness_assessments (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

  -- Canvas metrics (structured for querying)
  canvas_artifact_count INTEGER NOT NULL DEFAULT 0,

  -- Calculated metrics (structured for querying)
  overall_score INTEGER CHECK (overall_score BETWEEN 0 AND 100),
  ready_to_progress BOOLEAN DEFAULT FALSE,
  missing_dimensions TEXT[] DEFAULT ARRAY[]::TEXT[], -- Array for queryable lists

  -- Context completeness (JSONB for flexibility)
  -- 5 dimensions: purpose, audience, content, constraints, feeling
  -- Each tracked with: covered (bool), confidence (0-100), lastUpdated (timestamp), evidence (message IDs)
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

  -- Constraints
  UNIQUE(project_id) -- One assessment per project (UPSERT pattern)
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Primary lookups
CREATE INDEX IF NOT EXISTS idx_readiness_assessments_project_id
  ON readiness_assessments(project_id);

-- Analytics queries
CREATE INDEX IF NOT EXISTS idx_readiness_assessments_ready_to_progress
  ON readiness_assessments(ready_to_progress);

CREATE INDEX IF NOT EXISTS idx_readiness_assessments_overall_score
  ON readiness_assessments(overall_score DESC);

-- JSONB queries (optional, add when needed)
CREATE INDEX IF NOT EXISTS idx_readiness_assessments_context
  ON readiness_assessments USING GIN(context_completeness);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

ALTER TABLE readiness_assessments ENABLE ROW LEVEL SECURITY;

-- Users can view readiness assessments for their own projects
CREATE POLICY "Users can view readiness for their projects"
  ON readiness_assessments FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM projects
      WHERE projects.id = readiness_assessments.project_id
      AND projects.user_id = auth.uid()
    )
  );

-- Users can create readiness assessments for their own projects
CREATE POLICY "Users can create readiness for their projects"
  ON readiness_assessments FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM projects
      WHERE projects.id = readiness_assessments.project_id
      AND projects.user_id = auth.uid()
    )
  );

-- Users can update readiness assessments for their own projects
CREATE POLICY "Users can update readiness for their projects"
  ON readiness_assessments FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM projects
      WHERE projects.id = readiness_assessments.project_id
      AND projects.user_id = auth.uid()
    )
  );

-- Users can delete readiness assessments for their own projects
CREATE POLICY "Users can delete readiness for their projects"
  ON readiness_assessments FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM projects
      WHERE projects.id = readiness_assessments.project_id
      AND projects.user_id = auth.uid()
    )
  );

-- ============================================================================
-- UTILITY FUNCTIONS
-- ============================================================================

-- Function to upsert readiness assessment (create or update)
CREATE OR REPLACE FUNCTION upsert_readiness_assessment(
  p_project_id UUID,
  p_canvas_artifact_count INTEGER,
  p_context_completeness JSONB,
  p_overall_score INTEGER,
  p_ready_to_progress BOOLEAN,
  p_missing_dimensions TEXT[]
)
RETURNS UUID
LANGUAGE SQL
SECURITY DEFINER
AS $$
  INSERT INTO readiness_assessments (
    project_id,
    canvas_artifact_count,
    context_completeness,
    overall_score,
    ready_to_progress,
    missing_dimensions,
    assessed_at,
    assessment_count
  )
  VALUES (
    p_project_id,
    p_canvas_artifact_count,
    p_context_completeness,
    p_overall_score,
    p_ready_to_progress,
    p_missing_dimensions,
    NOW(),
    1
  )
  ON CONFLICT (project_id) DO UPDATE SET
    canvas_artifact_count = EXCLUDED.canvas_artifact_count,
    context_completeness = EXCLUDED.context_completeness,
    overall_score = EXCLUDED.overall_score,
    ready_to_progress = EXCLUDED.ready_to_progress,
    missing_dimensions = EXCLUDED.missing_dimensions,
    assessed_at = NOW(),
    assessment_count = readiness_assessments.assessment_count + 1
  RETURNING id;
$$;

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE readiness_assessments IS 'Multi-dimensional assessment tracking project readiness for phase progression. Uses Canvas Density (30%) + Context Completeness (70%) to determine when sufficient understanding exists to move forward.';

COMMENT ON COLUMN readiness_assessments.canvas_artifact_count IS 'Number of artifacts on canvas (links, notes, images, etc). Threshold: 5+ for readiness.';

COMMENT ON COLUMN readiness_assessments.overall_score IS 'Calculated score (0-100) from weighted formula: (canvas_density * 0.3) + (context_completeness * 0.7). Threshold: 70+ for readiness.';

COMMENT ON COLUMN readiness_assessments.ready_to_progress IS 'Boolean flag indicating project has sufficient context to progress. Requires: score >= 70, artifacts >= 5, and 3/5 dimensions covered.';

COMMENT ON COLUMN readiness_assessments.context_completeness IS 'JSONB tracking 5 dimensions: purpose, audience, content, constraints, feeling. Each has covered (bool), confidence (0-100), lastUpdated (timestamp), evidence (message IDs).';

COMMENT ON COLUMN readiness_assessments.missing_dimensions IS 'Array of dimension names that still need attention. Used for UI guidance.';

COMMENT ON FUNCTION upsert_readiness_assessment IS 'Creates or updates readiness assessment for a project. Increments assessment_count on updates.';
