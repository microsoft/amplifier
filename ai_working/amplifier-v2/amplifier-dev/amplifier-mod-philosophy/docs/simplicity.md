# Principle of Simplicity

## Core Philosophy

Embrace radical simplicity in all design and implementation decisions. Complex systems emerge from simple, well-understood components working together, not from complex components.

## Guidelines

### Start Simple, Stay Simple

- Begin with the minimal viable implementation
- Add complexity only when proven necessary
- Regularly question and remove unnecessary complexity
- Prefer explicit over implicit behavior

### Clear Over Clever

- Write code that is immediately understandable
- Avoid clever tricks that sacrifice readability
- Choose boring, proven solutions over novel ones
- Document the "why" when simplicity isn't obvious

### YAGNI (You Aren't Gonna Need It)

- Don't build for hypothetical future requirements
- Solve today's problems with today's code
- It's easier to add features than remove them
- Trust that future needs will be clearer when they arrive

### Composition Over Complexity

- Build complex behavior from simple, composable pieces
- Each component should do one thing well
- Prefer many simple functions over few complex ones
- Design interfaces that are hard to misuse

## Examples

### Good: Simple and Direct

```python
def calculate_total(items):
    """Calculate the total price of items."""
    return sum(item.price for item in items)
```

### Avoid: Over-engineered

```python
class TotalCalculator:
    def __init__(self, strategy_factory):
        self.strategy = strategy_factory.create_strategy()

    def calculate(self, items):
        return self.strategy.execute(items)
```

## Remember

- The best code is often the code you don't write
- Simplicity is the ultimate sophistication
- If you can't explain it simply, you don't understand it well enough
- Every line of code is a liability; make each one count