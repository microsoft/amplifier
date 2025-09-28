#!/usr/bin/env python3
"""Core implementation of the Parallel Evolution Experiments framework."""

import asyncio
import hashlib
import json
import random
import time
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import networkx as nx


class ParadigmType(Enum):
    """Programming paradigms for code generation."""

    FUNCTIONAL = "functional"
    ASYNC = "async"
    OOP = "object_oriented"
    REACTIVE = "reactive"
    DATAFLOW = "dataflow"
    PROCEDURAL = "procedural"
    DECLARATIVE = "declarative"


@dataclass
class CodeGenome:
    """Abstract genetic representation of code functionality."""

    name: str
    function_signature: str
    behavioral_constraints: list[str]
    performance_targets: dict[str, float]
    allowed_paradigms: list[ParadigmType]
    mutation_rate: float = 0.2
    crossover_points: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def genome_id(self) -> str:
        """Generate unique ID for this genome."""
        content = f"{self.name}:{self.function_signature}"
        return hashlib.md5(content.encode()).hexdigest()[:8]


@dataclass
class Phenotype:
    """A specific implementation of a genome."""

    genome: CodeGenome
    paradigm: ParadigmType
    implementation: str
    generation: int
    parents: list[str] = field(default_factory=list)
    mutations_applied: list[str] = field(default_factory=list)
    birth_time: datetime = field(default_factory=datetime.now)
    fitness_scores: dict[str, float] = field(default_factory=dict)

    @property
    def phenotype_id(self) -> str:
        """Generate unique ID for this phenotype."""
        content = f"{self.genome.genome_id}:{self.paradigm.value}:{self.generation}:{time.time()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    @property
    def overall_fitness(self) -> float:
        """Calculate overall fitness score."""
        if not self.fitness_scores:
            return 0.0
        return sum(self.fitness_scores.values()) / len(self.fitness_scores)


@dataclass
class BenchmarkResult:
    """Results from benchmarking a phenotype."""

    phenotype_id: str
    execution_time: float
    memory_usage: float
    cpu_cycles: int
    test_pass_rate: float
    error_count: int
    complexity_score: float
    custom_metrics: dict[str, float] = field(default_factory=dict)


class MutationOperator:
    """Base class for code mutations."""

    def __init__(self, name: str, mutation_strength: float = 0.5):
        self.name = name
        self.mutation_strength = mutation_strength

    async def mutate(self, phenotype: Phenotype) -> Phenotype:
        """Apply mutation to create new variant."""
        raise NotImplementedError


class ParadigmShiftMutation(MutationOperator):
    """Change implementation paradigm."""

    def __init__(self):
        super().__init__("paradigm_shift", mutation_strength=0.8)

    async def mutate(self, phenotype: Phenotype) -> Phenotype:
        """Shift to a different paradigm."""
        available = [p for p in phenotype.genome.allowed_paradigms if p != phenotype.paradigm]

        if not available:
            return phenotype

        new_paradigm = random.choice(available)

        # Create new implementation (in real system, would use LLM)
        new_implementation = f"""
# {new_paradigm.value} implementation of {phenotype.genome.name}
# Generated from {phenotype.paradigm.value} parent
{phenotype.implementation}
# [Paradigm shift applied: {phenotype.paradigm.value} -> {new_paradigm.value}]
"""

        return Phenotype(
            genome=phenotype.genome,
            paradigm=new_paradigm,
            implementation=new_implementation,
            generation=phenotype.generation + 1,
            parents=[phenotype.phenotype_id],
            mutations_applied=phenotype.mutations_applied + [self.name],
        )


class OptimizationMutation(MutationOperator):
    """Apply performance optimizations."""

    optimizations = [
        "add_memoization",
        "vectorize_loops",
        "parallelize_operations",
        "add_early_exits",
        "optimize_data_structures",
        "reduce_allocations",
        "cache_computations",
    ]

    def __init__(self):
        super().__init__("optimization", mutation_strength=0.3)

    async def mutate(self, phenotype: Phenotype) -> Phenotype:
        """Apply random optimization."""
        optimization = random.choice(self.optimizations)

        # Apply optimization (in real system, would modify code)
        new_implementation = f"{phenotype.implementation}\n# Optimization applied: {optimization}"

        return Phenotype(
            genome=phenotype.genome,
            paradigm=phenotype.paradigm,
            implementation=new_implementation,
            generation=phenotype.generation + 1,
            parents=[phenotype.phenotype_id],
            mutations_applied=phenotype.mutations_applied + [f"{self.name}:{optimization}"],
        )


class CrossoverOperator:
    """Combine genetic material from successful variants."""

    async def crossover(self, parent1: Phenotype, parent2: Phenotype) -> Phenotype:
        """Create offspring by combining parent traits."""
        # Select dominant paradigm based on fitness
        if parent1.overall_fitness > parent2.overall_fitness:
            paradigm = parent1.paradigm
            base_implementation = parent1.implementation
        else:
            paradigm = parent2.paradigm
            base_implementation = parent2.implementation

        # Combine implementations (simplified for demo)
        combined = f"""
# Crossover offspring from:
# Parent 1: {parent1.phenotype_id} (fitness: {parent1.overall_fitness:.2f})
# Parent 2: {parent2.phenotype_id} (fitness: {parent2.overall_fitness:.2f})
{base_implementation}
# Inherited optimizations from both parents
"""

        return Phenotype(
            genome=parent1.genome,  # Assume same genome
            paradigm=paradigm,
            implementation=combined,
            generation=max(parent1.generation, parent2.generation) + 1,
            parents=[parent1.phenotype_id, parent2.phenotype_id],
            mutations_applied=[],  # Fresh start for mutations
        )


class FitnessEvaluator:
    """Comprehensive fitness evaluation across multiple dimensions."""

    def __init__(self):
        self.dimensions = {
            "performance": {"weight": 0.3, "metrics": ["execution_time", "memory_usage", "cpu_cycles"]},
            "correctness": {"weight": 0.4, "metrics": ["test_pass_rate", "edge_case_handling", "error_recovery"]},
            "maintainability": {"weight": 0.2, "metrics": ["complexity", "modularity", "readability"]},
            "adaptability": {"weight": 0.1, "metrics": ["extensibility", "configuration_flexibility"]},
        }

    async def evaluate(self, phenotype: Phenotype, test_data: Any = None) -> dict[str, float]:
        """Run comprehensive fitness evaluation."""
        # Simulate benchmark execution
        await asyncio.sleep(0.1)  # Simulate execution time

        # Generate mock fitness scores (in real system, would run actual tests)
        fitness = {
            "execution_time": random.uniform(0.1, 2.0),
            "memory_usage": random.uniform(10, 100),
            "test_pass_rate": random.uniform(0.7, 1.0),
            "complexity": random.uniform(1, 10),
            "overall": 0,
        }

        # Calculate weighted overall fitness
        overall = 0
        for _dimension, config in self.dimensions.items():
            dim_score = random.uniform(0.5, 1.0)  # Simplified
            overall += dim_score * config["weight"]

        fitness["overall"] = overall
        return fitness


class ParallelBenchmarkRunner:
    """Run benchmarks for multiple variants simultaneously."""

    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.evaluator = FitnessEvaluator()

    async def benchmark_population(
        self, population: list[Phenotype], test_data: Any = None
    ) -> dict[str, BenchmarkResult]:
        """Run benchmarks in parallel isolated environments."""
        semaphore = asyncio.Semaphore(self.max_workers)

        async def benchmark_with_limit(phenotype: Phenotype) -> tuple[str, BenchmarkResult]:
            async with semaphore:
                result = await self._run_isolated_benchmark(phenotype, test_data)
                return phenotype.phenotype_id, result

        # Run benchmarks in parallel
        tasks = [benchmark_with_limit(p) for p in population]
        results = await asyncio.gather(*tasks)

        return dict(results)

    async def _run_isolated_benchmark(self, phenotype: Phenotype, test_data: Any) -> BenchmarkResult:
        """Run benchmark in isolated environment."""
        # Simulate isolated execution
        start_time = time.time()

        # Evaluate fitness
        fitness = await self.evaluator.evaluate(phenotype, test_data)

        # Create benchmark result
        return BenchmarkResult(
            phenotype_id=phenotype.phenotype_id,
            execution_time=time.time() - start_time,
            memory_usage=random.uniform(50, 200),
            cpu_cycles=random.randint(1000000, 10000000),
            test_pass_rate=fitness.get("test_pass_rate", 0.9),
            error_count=random.randint(0, 5),
            complexity_score=fitness.get("complexity", 5),
            custom_metrics=fitness,
        )


class TournamentSelection:
    """Tournament-based selection of fittest variants."""

    def __init__(self, tournament_size: int = 4, selection_pressure: float = 0.7):
        self.tournament_size = tournament_size
        self.selection_pressure = selection_pressure

    async def select_winners(
        self, population: list[Phenotype], fitness_results: dict[str, BenchmarkResult]
    ) -> list[Phenotype]:
        """Run tournament and select winners."""
        # Sort by fitness
        sorted_pop = sorted(
            population, key=lambda p: fitness_results[p.phenotype_id].custom_metrics.get("overall", 0), reverse=True
        )

        # Select top performers based on selection pressure
        num_winners = max(2, int(len(population) * self.selection_pressure))
        winners = sorted_pop[:num_winners]

        # Add some random selection for diversity
        if len(sorted_pop) > num_winners:
            diversity_picks = random.sample(sorted_pop[num_winners:], min(2, len(sorted_pop) - num_winners))
            winners.extend(diversity_picks)

        return winners


class GeneticMemoryBank:
    """Long-term memory of successful evolutionary patterns."""

    def __init__(self, data_dir: Path = Path(".evolution_memory")):
        self.data_dir = data_dir
        self.data_dir.mkdir(exist_ok=True)
        self.successful_patterns: dict[str, dict] = {}
        self.failed_patterns: dict[str, dict] = {}
        self.lineage_graph = nx.DiGraph()
        self.load_memory()

    def record_success(self, phenotype: Phenotype, fitness: BenchmarkResult):
        """Record successful evolutionary pattern."""
        pattern_id = f"{phenotype.genome.name}:{phenotype.paradigm.value}:{phenotype.generation}"

        self.successful_patterns[pattern_id] = {
            "phenotype_id": phenotype.phenotype_id,
            "genome": phenotype.genome.name,
            "paradigm": phenotype.paradigm.value,
            "fitness": fitness.custom_metrics.get("overall", 0),
            "mutations": phenotype.mutations_applied,
            "generation": phenotype.generation,
            "timestamp": datetime.now().isoformat(),
        }

        # Update lineage graph
        self.lineage_graph.add_node(phenotype.phenotype_id, fitness=fitness.custom_metrics.get("overall", 0))

        for parent_id in phenotype.parents:
            self.lineage_graph.add_edge(parent_id, phenotype.phenotype_id)

        self.save_memory()

    def suggest_mutations(self, phenotype: Phenotype) -> list[MutationOperator]:
        """Suggest mutations based on historical success."""
        # Find similar successful patterns
        similar = [
            p
            for p in self.successful_patterns.values()
            if p["genome"] == phenotype.genome.name and p["paradigm"] == phenotype.paradigm.value
        ]

        if not similar:
            # Default mutations
            return [ParadigmShiftMutation(), OptimizationMutation()]

        # Analyze successful mutations
        successful_mutations = set()
        for pattern in similar:
            successful_mutations.update(pattern["mutations"])

        # Create mutation operators based on history
        mutations = []
        if "paradigm_shift" in str(successful_mutations):
            mutations.append(ParadigmShiftMutation())
        if "optimization" in str(successful_mutations):
            mutations.append(OptimizationMutation())

        return mutations if mutations else [OptimizationMutation()]

    def get_lineage(self, phenotype_id: str) -> list[str]:
        """Get ancestral lineage of a phenotype."""
        if phenotype_id not in self.lineage_graph:
            return []

        ancestors = nx.ancestors(self.lineage_graph, phenotype_id)
        return list(ancestors)

    def save_memory(self):
        """Persist memory to disk."""
        memory_file = self.data_dir / "genetic_memory.json"
        data = {
            "successful_patterns": self.successful_patterns,
            "failed_patterns": self.failed_patterns,
            "lineage_nodes": list(self.lineage_graph.nodes(data=True)),
            "lineage_edges": list(self.lineage_graph.edges()),
        }
        memory_file.write_text(json.dumps(data, indent=2))

    def load_memory(self):
        """Load memory from disk."""
        memory_file = self.data_dir / "genetic_memory.json"
        if memory_file.exists():
            data = json.loads(memory_file.read_text())
            self.successful_patterns = data.get("successful_patterns", {})
            self.failed_patterns = data.get("failed_patterns", {})

            # Reconstruct graph
            self.lineage_graph.clear()
            for node, attrs in data.get("lineage_nodes", []):
                self.lineage_graph.add_node(node, **attrs)
            self.lineage_graph.add_edges_from(data.get("lineage_edges", []))


class EvolutionController:
    """Main controller for evolutionary experiments."""

    def __init__(
        self,
        genome: CodeGenome,
        population_size: int = 20,
        generations: int = 100,
        mutation_rate: float = 0.2,
        crossover_rate: float = 0.3,
    ):
        self.genome = genome
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate

        self.benchmark_runner = ParallelBenchmarkRunner()
        self.selector = TournamentSelection()
        self.memory_bank = GeneticMemoryBank()
        self.crossover_op = CrossoverOperator()

    async def initialize_population(self) -> list[Phenotype]:
        """Create initial population with diverse implementations."""
        population = []

        for i, paradigm in enumerate(self.genome.allowed_paradigms[: self.population_size]):
            phenotype = Phenotype(
                genome=self.genome,
                paradigm=paradigm,
                implementation=f"# Initial {paradigm.value} implementation\n# Generation 0, Individual {i}",
                generation=0,
            )
            population.append(phenotype)

        # Fill remaining slots with random paradigms
        while len(population) < self.population_size:
            paradigm = random.choice(self.genome.allowed_paradigms)
            phenotype = Phenotype(
                genome=self.genome,
                paradigm=paradigm,
                implementation=f"# Random {paradigm.value} implementation\n# Generation 0",
                generation=0,
            )
            population.append(phenotype)

        return population

    async def evolve_generation(self, population: list[Phenotype], generation: int) -> list[Phenotype]:
        """Evolve one generation."""
        print(f"\n=== Generation {generation} ===")

        # Parallel fitness evaluation
        print(f"Evaluating {len(population)} phenotypes in parallel...")
        fitness_results = await self.benchmark_runner.benchmark_population(population)

        # Update fitness scores
        for phenotype in population:
            if phenotype.phenotype_id in fitness_results:
                result = fitness_results[phenotype.phenotype_id]
                phenotype.fitness_scores = result.custom_metrics

        # Tournament selection
        winners = await self.selector.select_winners(population, fitness_results)
        print(f"Selected {len(winners)} winners")

        # Record successful patterns
        for winner in winners[:3]:  # Top 3
            self.memory_bank.record_success(winner, fitness_results[winner.phenotype_id])

        # Generate next generation
        next_generation = []

        # Elitism - keep best performers
        elite_count = max(2, int(self.population_size * 0.1))
        next_generation.extend(winners[:elite_count])

        # Generate offspring
        while len(next_generation) < self.population_size:
            if random.random() < self.crossover_rate and len(winners) >= 2:
                # Crossover
                parent1, parent2 = random.sample(winners, 2)
                offspring = await self.crossover_op.crossover(parent1, parent2)
            else:
                # Mutation
                parent = random.choice(winners)
                mutations = self.memory_bank.suggest_mutations(parent)
                if mutations:
                    mutation_op = random.choice(mutations)
                    offspring = await mutation_op.mutate(parent)
                else:
                    offspring = parent  # Clone

            offspring.generation = generation
            next_generation.append(offspring)

        return next_generation[: self.population_size]

    async def run_evolution(self) -> Phenotype:
        """Run full evolution experiment."""
        print(f"Starting evolution for {self.genome.name}")
        print(f"Population size: {self.population_size}, Generations: {self.generations}")

        # Initialize population
        population = await self.initialize_population()

        # Evolution loop
        for generation in range(1, self.generations + 1):
            population = await self.evolve_generation(population, generation)

            # Report progress
            best = max(population, key=lambda p: p.overall_fitness)
            print(f"Best fitness: {best.overall_fitness:.3f} ({best.paradigm.value})")

        # Return champion
        champion = max(population, key=lambda p: p.overall_fitness)
        print(f"\n🏆 Evolution complete! Champion: {champion.phenotype_id}")
        print(f"   Paradigm: {champion.paradigm.value}")
        print(f"   Fitness: {champion.overall_fitness:.3f}")
        print(f"   Mutations: {champion.mutations_applied}")

        return champion


async def example_evolution():
    """Example: Evolve a sorting function."""
    # Define the genome
    sorting_genome = CodeGenome(
        name="optimal_sort",
        function_signature="def sort(items: list[T]) -> list[T]",
        behavioral_constraints=["Must return sorted list", "Must handle empty lists", "Must be stable"],
        performance_targets={"time_complexity": 1.5, "space_complexity": 1.0, "cache_efficiency": 0.8},
        allowed_paradigms=[
            ParadigmType.FUNCTIONAL,
            ParadigmType.PROCEDURAL,
            ParadigmType.OOP,
            ParadigmType.ASYNC,
        ],
    )

    # Create evolution controller
    evolution = EvolutionController(genome=sorting_genome, population_size=10, generations=5)

    # Run evolution
    champion = await evolution.run_evolution()

    # Show lineage
    lineage = evolution.memory_bank.get_lineage(champion.phenotype_id)
    print(f"\nChampion lineage: {len(lineage)} ancestors")

    return champion


if __name__ == "__main__":
    # Run example evolution
    asyncio.run(example_evolution())
