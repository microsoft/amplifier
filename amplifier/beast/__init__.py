"""
BEAST: Behavioral Execution And State Tracking
An AI-resistant evaluation framework that verifies actual behavior, not claimed behavior.
"""

from .contracts import BehavioralContract
from .contracts import ContractVerifier
from .failures import FailureDatabase
from .failures import FailurePattern
from .tracer import ExecutionTrace
from .tracer import ExecutionTracer
from .validator import RealWorldValidator

__version__ = "0.1.0"

__all__ = [
    "ExecutionTracer",
    "ExecutionTrace",
    "BehavioralContract",
    "ContractVerifier",
    "RealWorldValidator",
    "FailureDatabase",
    "FailurePattern",
]
