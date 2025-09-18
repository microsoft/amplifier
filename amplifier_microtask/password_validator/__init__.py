"""Password Validator Module

A comprehensive password validation and strength assessment library.
"""

from .validator import PasswordValidator
from .models import ValidationResult, ValidationRule, StrengthResult, PasswordAnalysis, StrengthLevel, ValidatorConfig
from .strength import StrengthCalculator
from .rules import (
    create_min_length_rule,
    create_uppercase_rule,
    create_lowercase_rule,
    create_digit_rule,
    create_special_char_rule,
    get_default_rules,
)

__version__ = "1.0.0"

__all__ = [
    # Main classes
    "PasswordValidator",
    "StrengthCalculator",
    # Models
    "ValidationResult",
    "ValidationRule",
    "StrengthResult",
    "PasswordAnalysis",
    "StrengthLevel",
    "ValidatorConfig",
    # Rule factories
    "create_min_length_rule",
    "create_uppercase_rule",
    "create_lowercase_rule",
    "create_digit_rule",
    "create_special_char_rule",
    "get_default_rules",
]
