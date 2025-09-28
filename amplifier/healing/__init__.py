"""
Amplifier Self-Healing System.

A modular system for automated code health improvement through AI-powered refactoring.
"""

from amplifier.healing.core.auto_healer import AutoHealer
from amplifier.healing.core.health_monitor import HealthMonitor
from amplifier.healing.core.health_monitor import ModuleHealth
from amplifier.healing.experiments.evolution import EvolutionExperiments

__all__ = [
    "HealthMonitor",
    "ModuleHealth",
    "AutoHealer",
    "EvolutionExperiments",
]

__version__ = "1.0.0"
