# Module: Claim Validation

## Purpose
Validate claims against stored memories to detect contradictions

## Inputs
- **validate_text**: text (str), memories (list[StoredMemory])
- **validate_claim**: claim (str), memories (list[StoredMemory])

## Outputs
- **validate_text**: ValidationResult with claims and conflicts
- **validate_claim**: ClaimValidation with support/contradiction

## Side Effects
- None - pure validation logic

## Dependencies
- memory.models: StoredMemory model
- search: MemorySearcher for finding relevant memories

## Public Interface
```python
from validation import ClaimValidator, ValidationResult
from memory import MemoryStore

# Initialize
store = MemoryStore()
validator = ClaimValidator()

# Validate text containing claims
text = "I always use dark mode and prefer email notifications"
memories = store.get_all()
result = validator.validate_text(text, memories)

# Check for contradictions
for claim in result.claims:
    if claim.contradicts:
        print(f"Contradiction found: {claim.claim}")
        print(f"Conflicts with: {claim.conflicting_memory.content}")
```