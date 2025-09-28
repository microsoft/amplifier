"""Parallel Evolution Experiments framework for Amplifier.

This module implements evolutionary computation for code optimization,
where multiple variants compete and evolve in parallel to find optimal
implementations.
"""

from .core import CodeGenome
from .core import CrossoverOperator
from .core import EvolutionController
from .core import FitnessEvaluator
from .core import GeneticMemoryBank
from .core import MutationOperator
from .core import OptimizationMutation
from .core import ParadigmShiftMutation
from .core import ParadigmType
from .core import ParallelBenchmarkRunner
from .core import Phenotype
from .core import TournamentSelection

__all__ = [
    "CodeGenome",
    "Phenotype",
    "ParadigmType",
    "MutationOperator",
    "ParadigmShiftMutation",
    "OptimizationMutation",
    "CrossoverOperator",
    "FitnessEvaluator",
    "ParallelBenchmarkRunner",
    "TournamentSelection",
    "GeneticMemoryBank",
    "EvolutionController",
]
