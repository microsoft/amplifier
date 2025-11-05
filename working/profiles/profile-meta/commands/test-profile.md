# Test Profile Command

Validate profile structure, completeness, and usability.

## Usage

```
/test-profile {profile-name}
```

## Validation Checks

### 1. Structure Validation

Check required files and directories exist:

```
profiles/{profile-name}/
├── profile.md          ✓ Required
├── philosophy/         ✓ Required (at least one .md file)
├── commands/          ~ Optional but recommended
└── agents/            ~ Optional
```

### 2. Profile.md Completeness

Verify profile.md contains:
- **The Pitch**: Clear 1-3 paragraph overview
- **Core Philosophy**: Explicit principles and beliefs
- **Process Overview**: Workflow steps or phases
- **When to Use**: Context where profile excels
- **When NOT to Use**: Boundaries and limitations
- **Success Metrics**: How to measure effectiveness
- **Composition**: What resources are imported

### 3. Philosophy Depth

Check philosophy documents:
- At least one philosophy document exists
- Principles are specific and actionable
- Trade-offs are explicit
- Decision-making frameworks are provided

### 4. Process Clarity

Evaluate process definition:
- Workflow steps are clearly defined
- Inputs/outputs for each step are specified
- Approval gates and decision points are marked
- Developer knows what to do next

### 5. Tool Functionality

Test commands and agents:
- Commands execute without errors
- Command descriptions are clear
- Agents load successfully
- Tools align with profile philosophy

### 6. Composition Validation

Check resource references:
- `@shared/*` references are valid
- Cross-profile references exist and are correct
- No broken links or missing resources

### 7. Documentation Quality

Assess overall documentation:
- Clear and concise writing
- Good examples provided
- No jargon without explanation
- Accessible to target audience

## Output Format

```
Profile Test Results: {profile-name}
=====================================

✓ Structure: PASS
✓ Profile.md: PASS
✓ Philosophy: PASS
⚠ Process: PASS (with warnings)
  - Warning: Step 3 inputs not clearly specified
✗ Tools: FAIL
  - Error: Command 'analyze.md' not found
✓ Composition: PASS
✓ Documentation: PASS

Overall: PASS (1 warning, 1 error)

Recommendations:
1. Fix broken command reference in workflow
2. Clarify inputs for process step 3
3. Consider adding example workflows
```

## Success Criteria

- All required files exist
- Profile.md is complete and clear
- Philosophy is well-articulated
- Process is actionable
- Tools work correctly
- Composition is valid
- Documentation is high quality

## When to Run

- After creating a new profile
- Before sharing a profile with others
- When profile feels "off" or unclear
- As part of profile refinement
- Before switching to use a profile for real work
