# Reusable Code Patterns

## Overview

Concrete implementation patterns for parallel processing, multi-perspective storage, and emergence detection.

## 1. Parallel Processing

```python
async def run_parallel_agents(agents, data):
    """Run multiple processors in parallel on the same data."""
    tasks = []
    for processor in processors:
        tasks.append(processor.process(data))
    
    # Gather all results, including exceptions
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results and exceptions
    valid_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"Processor {i} failed: {result}")
        else:
            valid_results.append(result)
    
    return valid_results
```

**Use**: Multiple analytical approaches on same data.

## 2. Multi-Perspective Node

```python
class MultiPerspectiveNode:
    """A node with multiple interpretations."""
    
    def __init__(self, node_id):
        self.id = node_id
        self.perspectives = {}  # view_id -> data
        self.timestamps = {}  # view_id -> timestamp
        
    def add_perspective(self, view_id, data, timestamp=None):
        """Add a perspective on this node."""
        self.perspectives[view_id] = data
        self.timestamps[view_id] = timestamp or time.time()
        
    def get_all(self):
        """Get all perspectives."""
        return self.perspectives.copy()
        
    def get_latest(self):
        """Get most recent perspective."""
        if not self.perspectives:
            return None
        latest = max(self.timestamps.items(), key=lambda x: x[1])
        return self.perspectives[latest[0]]
```

**Use**: Store multiple valid interpretations.

## 3. Emergence Detection

```python
def detect_emergence(source_outputs):
    """Find patterns not explicit in any single source."""
    
    # Build frequency map across all outputs
    all_concepts = {}
    agent_concepts = {}
    
    for source_id, output in source_outputs.items():
        source_concepts[source_id] = set(output.get('concepts', []))
        for concept in source_concepts[source_id]:
            all_concepts[concept] = all_concepts.get(concept, 0) + 1
    
    # Find concepts that appear in multiple agents but weren't 
    # explicitly marked as important by any single agent
    emergent = []
    for concept, count in all_concepts.items():
        if count > len(source_outputs) / 2:  # Appears in majority
            # Check if any source marked it as primary
            is_primary = False
            for source_id, output in source_outputs.items():
                if concept in output.get('primary_concepts', []):
                    is_primary = True
                    break
            
            if not is_primary:
                emergent.append({
                    'concept': concept,
                    'frequency': count,
                    'type': 'implicit_consensus'
                })
    
    return emergent
```

**Use**: Cross-source pattern discovery.

## 4. Contradiction Tracking

```python
class ContradictionTracker:
    """Track unresolved contradictions."""
    
    def __init__(self):
        self.contradictions = {}
        self.permanent = [
            ('explicit', 'implicit'),
            ('local', 'global')
        ]
    
    def add(self, topic, view_a, view_b):
        """Store contradiction."""
        if topic not in self.contradictions:
            self.contradictions[topic] = []
        
        self.contradictions[topic].append({
            'a': view_a,
            'b': view_b,
            'timestamp': time.time()
        })
    
    def get_active(self):
        """Get unresolved contradictions."""
        return self.contradictions.copy()
```

**Use**: Track competing viewpoints.

## 5. Alternative Interpretation

```python
def generate_alternatives(text):
    """Generate alternative interpretations."""
    alternatives = {
        'increase': 'decrease',
        'simple': 'complex',
        'fast': 'thorough'
    }
    
    for original, alternative in alternatives.items():
        if original in text:
            yield text.replace(original, alternative)
```

**Use**: Explore different viewpoints.

## 6. Concept Intersection

```python
def find_intersection(concept_a, concept_b):
    """Find productive intersection between concepts."""
    
    if is_opposite(concept_a, concept_b):
        return 'contradiction'
    elif different_domain(concept_a, concept_b):
        return 'cross_domain'
    elif different_scale(concept_a, concept_b):
        return 'scale_difference'
    
    return None
```

**Use**: Find connections between unrelated ideas.

## 7. Layered Memory

```python
class LayeredMemory:
    """Memory with retention levels."""
    
    def __init__(self):
        self.working = []
        self.short_term = {}
        self.long_term = {}
        
    def add(self, item):
        """Add and promote through levels."""
        self.working.append(item)
        
        pattern = self.extract_pattern(item)
        if pattern in [self.extract_pattern(e) for e in self.working[-10:]]:
            self.short_term[pattern] = self.short_term.get(pattern, 0) + 1
            
            if self.short_term[pattern] > 5:
                self.long_term[pattern] = {
                    'count': self.short_term[pattern],
                    'first_seen': time.time()
                }
```

**Use**: Pattern retention and promotion.

## 8. Parallel Insight Generation

```python
async def parallel_insights(data, generators):
    """Generate insights in parallel."""
    
    tasks = [asyncio.create_task(g.generate(data)) for g in generators]
    all_insights = await asyncio.gather(*tasks)
    
    # Deduplicate
    seen = set()
    unique = []
    for insights in all_insights:
        for insight in insights:
            key = str(insight)
            if key not in seen:
                seen.add(key)
                unique.append(insight)
    
    return unique
```

**Use**: Multiple analysis approaches simultaneously.

## 9. Evolution Tracking

```python
class EvolutionTracker:
    """Track how interpretations change over time."""
    
    def __init__(self):
        self.current = {}
        self.history = {}
        
    def update(self, key, value):
        """Update and track history."""
        old = self.current.get(key)
        self.current[key] = value
        
        if key not in self.history:
            self.history[key] = []
        self.history[key].append({
            'value': value,
            'previous': old,
            'timestamp': time.time()
        })
```

**Use**: Track concept evolution.

## 10. Diversity Measurement

```python
class DiversityMetrics:
    """Measure output diversity."""
    
    def measure(self, outputs):
        """Calculate diversity score."""
        unique = len(set(str(o) for o in outputs))
        total = len(outputs)
        return unique / total if total > 0 else 0
```

**Use**: Measure innovation potential.

## Key Patterns

### Parallel Processing
```python
# Run processors in parallel
results = await asyncio.gather(*[p.process(data) for p in processors])
```

### Multi-Perspective Storage
```python
# Store multiple views
for view_id, processor in processors.items():
    node.perspectives[view_id] = processor.process(data)
```

## Summary

Reusable patterns for:
1. Parallel processing
2. Multi-perspective storage
3. Emergence detection
4. Contradiction tracking
5. Diversity measurement