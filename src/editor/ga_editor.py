"""
✂️ Genetic Algorithm Editor — Cas-AI Cutting System

Advanced parameter editing system inspired by CRISPR Cas proteins.
Uses genetic algorithms and optimization techniques to perform precise
model parameter modifications with surgical precision.

Think like biology. Code like AI.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable
from datetime import datetime
import logging
from dataclasses import dataclass, field
import random
import copy

from ..core.base_layers import BaseEditor, EditResult, TargetSite
from ..core.genome import FinancialGenome
from .evaluators import evaluate_population

logger = logging.getLogger(__name__)


@dataclass
class Individual:
    """
    🧬 Genetic Individual — Parameter Configuration
    
    Represents a single parameter configuration in the genetic algorithm
    population, like an individual organism with specific genetic traits.
    """
    genome: Dict[str, Any]
    fitness: float = 0.0
    age: int = 0
    generation: int = 0
    parent_ids: List[str] = field(default_factory=list)
    mutation_history: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.id = f"ind_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"


@dataclass
class EditingConfig:
    """
    ⚙️ Cas-AI Configuration
    
    Configuration parameters for the genetic algorithm editor,
    controlling editing behavior and optimization strategy.
    """
    population_size: int = 50
    num_generations: int = 100
    mutation_rate: float = 0.1
    crossover_rate: float = 0.8
    selection_pressure: float = 2.0
    elitism_ratio: float = 0.1
    diversity_threshold: float = 0.8
    convergence_threshold: float = 1e-6
    max_stagnant_generations: int = 20
    # Maximum age (in generations) an individual can have before pruning; 0=disabled
    max_individual_age: int = 10
    # Speciation / fitness-sharing runtime knobs (backwards-compatible)
    enable_speciation: bool = False
    speciation_k: Optional[int] = None
    # legacy alias expected by tests
    species_k: Optional[int] = None
    # Fitness sharing
    enable_fitness_sharing: bool = False
    sharing_radius: float = 0.5
    sharing_alpha: float = 1.0
    # Hall-of-fame per-species size
    species_hof_k: int = 5


class FitnessFunction:
    """
    🎯 Fitness Evaluation System
    
    Evaluates the quality of parameter configurations using
    performance metrics and stability measures.
    """

    def __init__(self,
                 objective_function: Optional[Callable] = None,
                 constraints: Optional[List[Callable]] = None,
                 weights: Optional[Dict[str, float]] = None):
        """
        Initialize fitness evaluation system.
        
        Args:
            objective_function: Primary performance evaluation function
            constraints: List of constraint functions
            weights: Weights for multi-objective optimization
        """
        self.objective_function = objective_function or self._default_objective
        self.constraints = constraints or []
        self.weights = weights or {'performance': 0.7, 'stability': 0.2, 'simplicity': 0.1}

        self._evaluation_history = []
        self._best_fitness = -np.inf

    def evaluate(self, individual: Individual, context: Dict[str, Any] = None) -> float:
        """
        🎯 Evaluate individual fitness
        
        Calculate comprehensive fitness score considering performance,
        stability, and other objectives.
        
        Args:
            individual: Individual to evaluate
            context: Additional context for evaluation
            
        Returns:
            Fitness score (higher is better)
        """
        try:
            # If this individual encodes joint edits (batch/co-evolution), apply
            # the edited values to a temporary copy of the model genome and
            # evaluate the objective on the resulting parameter set.
            joint_mode = False
            genome_for_metrics = individual.genome

            if ('edited_values' in individual.genome and context
                    and 'targets' in context and 'model_genome' in context):
                try:
                    # Create a temporary genome from snapshot to avoid mutating real model
                    model_genome: FinancialGenome = context['model_genome']
                    snapshot = model_genome.create_snapshot()
                    temp_genome = FinancialGenome(name=f"tmp_{model_genome.name}")
                    temp_genome.restore_from_snapshot(snapshot)

                    edited_values = individual.genome.get('edited_values', [])
                    targets = context['targets']

                    for idx, tgt in enumerate(targets):
                        if idx < len(edited_values):
                            try:
                                temp_genome.set_parameter(tgt.parameter_path, edited_values[idx])
                            except Exception:
                                # If applying an edit fails for this target, skip it
                                continue

                    # Evaluate objective on the temp genome's flat parameter dict
                    performance_score = self.objective_function(temp_genome.get_all_parameters(), context)
                    # Use the temp genome's flat parameters for subsequent metric evaluations
                    joint_mode = True
                    genome_for_metrics = temp_genome.get_all_parameters()
                except Exception as e:
                    logger.warning(f"Joint genome evaluation failed: {e}")
                    performance_score = -1000.0
            else:
                # Primary objective evaluation for normal individuals
                performance_score = self.objective_function(individual.genome, context)
                genome_for_metrics = individual.genome

            # Stability evaluation - use temp genome flat params for joint individuals
            stability_score = self._evaluate_stability(genome_for_metrics, context)

            # Simplicity evaluation (prefer simpler solutions)
            simplicity_score = self._evaluate_simplicity(genome_for_metrics)

            # Constraint violations
            constraint_penalty = self._evaluate_constraints(individual.genome, context)

            # Weighted combination
            fitness = (
                self.weights['performance'] * performance_score +
                self.weights['stability'] * stability_score +
                self.weights['simplicity'] * simplicity_score -
                constraint_penalty
            )

            # Track best fitness
            if fitness > self._best_fitness:
                self._best_fitness = fitness
                logger.debug(f"New best fitness: {fitness:.6f}")

            # Store evaluation history
            self._evaluation_history.append({
                'individual_id': individual.id,
                'fitness': fitness,
                'performance': performance_score,
                'stability': stability_score,
                'simplicity': simplicity_score,
                'penalty': constraint_penalty,
                'timestamp': datetime.now()
            })

            return fitness

        except Exception as e:
            logger.error(f"Fitness evaluation failed for {individual.id}: {str(e)}")
            return -1000.0  # Heavily penalize evaluation failures

    def _default_objective(self, genome: Dict[str, Any], context: Dict[str, Any] = None) -> float:
        """Default objective function when none provided."""
        # Simple default: minimize sum of squared parameter values
        total_value = 0.0
        for key, value in genome.items():
            if isinstance(value, (int, float)):
                total_value += value ** 2
            elif isinstance(value, np.ndarray):
                total_value += np.sum(value ** 2)

        return -total_value  # Negative because we want to minimize

    def _evaluate_stability(self, genome: Dict[str, Any], context: Dict[str, Any] = None) -> float:
        """Evaluate parameter configuration stability."""
        stability_score = 1.0

        # Check for extreme values
        for key, value in genome.items():
            if isinstance(value, (int, float)):
                if abs(value) > 100:  # Arbitrary large value threshold
                    stability_score *= 0.8
            elif isinstance(value, np.ndarray):
                if np.any(np.abs(value) > 100):
                    stability_score *= 0.8
                if np.any(np.isnan(value)) or np.any(np.isinf(value)):
                    stability_score *= 0.5

        return stability_score

    def _evaluate_simplicity(self, genome: Dict[str, Any]) -> float:
        """Evaluate solution simplicity (Occam's razor)."""
        complexity_penalty = 0.0

        for key, value in genome.items():
            if isinstance(value, np.ndarray):
                # Penalize large arrays
                complexity_penalty += np.log(value.size + 1) * 0.01

        return 1.0 - complexity_penalty

    def _evaluate_constraints(self, genome: Dict[str, Any], context: Dict[str, Any] = None) -> float:
        """Evaluate constraint violations."""
        total_penalty = 0.0

        for constraint_func in self.constraints:
            try:
                violation = constraint_func(genome, context)
                if violation > 0:
                    total_penalty += violation
            except Exception as e:
                logger.warning(f"Constraint evaluation failed: {str(e)}")
                total_penalty += 10.0  # Heavy penalty for constraint evaluation failure

        return total_penalty


class GeneticAlgorithmEditor(BaseEditor):
    """
    ✂️ Genetic Algorithm Cas-AI System
    
    Advanced parameter editing system using genetic algorithms to evolve
    optimal parameter configurations. Like Cas proteins performing precise
    DNA cuts and modifications, this system applies evolutionary pressure
    to find optimal parameter edits.
    
    Biological Analogy:
    - Genetic Algorithm → Directed Evolution
    - Individual → Parameter Configuration
    - Mutation → Parameter Perturbation
    - Crossover → Parameter Recombination
    - Selection → Fitness-based Survival
    """

    def __init__(self,
                 name: str = "GeneticEditor",
                 edit_rate: float = 0.1,
                 config: Optional[EditingConfig] = None,
                 fitness_function: Optional[FitnessFunction] = None,
                 seed: Optional[int] = None):
        """
        Initialize the genetic algorithm editor.
        
        Args:
            name: Editor identifier
            edit_rate: Base mutation rate for parameter changes
            config: Genetic algorithm configuration
            fitness_function: Fitness evaluation system
        """
        super().__init__(name, edit_rate)

        self.config = config or EditingConfig()
        self.fitness_function = fitness_function or FitnessFunction()

        # Evolution tracking
        self._population = []
        self._generation_history = []
        self._best_individual = None
        self._convergence_history = []
        # Hall of fame: store top-K historically best individuals (shallow summaries)
        self.hall_of_fame: List[Dict[str, Any]] = []
        # Per-species hall-of-fame: mapping species_id -> list of summaries
        self.species_hall_of_fame: Dict[int, List[Dict[str, Any]]] = {}
        # Per-generation best per species telemetry (map species_id -> list of bests over time)
        self._species_best_history: Dict[int, List[float]] = {}

        # Mutation strategies
        self.mutation_strategies = {
            'gaussian': self._gaussian_mutation,
            'uniform': self._uniform_mutation,
            'adaptive': self._adaptive_mutation,
            'polynomial': self._polynomial_mutation
        }

        self.current_mutation_strategy = 'adaptive'

        # Crossover strategies
        self.crossover_strategies = {
            'single_point': self._single_point_crossover,
            'uniform': self._uniform_crossover,
            'arithmetic': self._arithmetic_crossover,
            'simulated_binary': self._simulated_binary_crossover
        }

        self.current_crossover_strategy = 'arithmetic'
        # Timestamps for the most recent evolution run (used for telemetry)
        self._evolution_start_time: Optional[datetime] = None
        self._evolution_end_time: Optional[datetime] = None

        # Recorded, deterministic per-generation weight history for telemetry
        # Format: {'timestamps': [iso_ts,...], 'weights': {'SYM': [v1, v2, ...], ...}}
        self._record_weights: bool = True
        self._recorded_weight_history: Dict[str, Any] = {'timestamps': [], 'weights': {}}

        # Keep a baseline mutation rate for adaptive adjustments
        self._base_mutation_rate = float(self.config.mutation_rate)

        logger.info(f"Initialized {self.name} with population_size={self.config.population_size}")

        # Reproducibility
        self._seed = seed
        if seed is not None:
            try:
                np.random.seed(seed)
                random.seed(seed)
            except Exception:
                pass

        # Pluggable operators (default to built-in implementations)
        # selection_operator: callable -> returns an Individual
        # crossover_operator: callable(parent1, parent2) -> (child1, child2)
        # mutation_operator: callable(individual, context) -> mutated_individual
        self.selection_operator = lambda: self._tournament_selection()
        self.crossover_operator = lambda p1, p2: self._crossover(p1, p2)
        self.mutation_operator = lambda ind, ctx: self._mutate(ind, ctx)
        # Operator telemetry
        self._operator_stats = {'selection': 0, 'crossover': 0, 'mutation': 0}
        # Parallel evaluation options
        self.use_parallel_evaluation: bool = False
        self._evaluator_workers: Optional[int] = None
        # Parallel backend choice: 'multiprocessing' or 'ray'
        self._parallel_backend: str = 'multiprocessing'
        # Speciation / niching options
        # Initialize speciation settings from config for backward compatibility
        self.use_speciation: bool = bool(getattr(self.config, 'enable_speciation', False))
        # threshold for grouping (distance) - default kept for compatibility
        self.speciation_threshold: float = float(getattr(self.config, 'sharing_radius', 0.5))
        # per-species hall-of-fame max age (in generations) for runtime pruning (None=disabled)
        self._species_hof_max_age: Optional[int] = None

    def set_parallel_evaluation(self, enabled: bool, workers: Optional[int] = None) -> None:
        """Enable or disable parallel evaluation of populations.

        Args:
            enabled: True to use the evaluator on offspring evaluations
            workers: number of worker processes to use (None = auto)
        """
        self.use_parallel_evaluation = bool(enabled)
        # Allow workers to be an int (multiprocessing) or the string 'ray'
        if isinstance(workers, str) and workers.lower() == 'ray':
            self._parallel_backend = 'ray'
            self._evaluator_workers = None
        else:
            self._parallel_backend = 'multiprocessing'
            self._evaluator_workers = workers

    def edit(self,
             target_site: TargetSite,
             model_genome: FinancialGenome) -> EditResult:
        """
        ✂️ Perform precision evolutionary edit
        
        Execute parameter modification using genetic algorithm optimization
        to find the best edit for the specific target site.
        
        Args:
            target_site: Specific parameter location and edit specification
            model_genome: Model parameters to modify
            
        Returns:
            EditResult documenting the evolutionary edit process
        """
        edit_start_time = datetime.now()
        edit_id = f"edit_{edit_start_time.strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"

        logger.info(f"Starting evolutionary edit {edit_id} for {target_site.parameter_path}")

        try:
            # Store original value for rollback
            original_value = copy.deepcopy(target_site.current_value)

            # Create optimization context
            context = {
                'target_site': target_site,
                'model_genome': model_genome,
                'edit_type': target_site.edit_type,
                'original_value': original_value
            }

            # Initialize population around current parameter value
            self._initialize_population(target_site, context)

            # Evolve population to find optimal edit
            best_individual = self._evolve_population(context)

            # Apply the best found edit
            if best_individual:
                new_value = best_individual.genome.get('edited_value', target_site.target_value)

                # Update the model genome
                model_genome.set_parameter(
                    target_site.parameter_path,
                    new_value,
                    f"GA edit {edit_id}"
                )

                # Calculate performance delta (if possible)
                performance_delta = self._calculate_performance_delta(
                    original_value, new_value, context
                )

                success = True
                after_value = new_value

                logger.info(f"Edit {edit_id} successful: {original_value} -> {new_value}")

            else:
                # Evolution failed - no improvement found
                success = False
                after_value = original_value
                performance_delta = 0.0
                logger.warning(f"Edit {edit_id} failed: no improvement found")

            # Create rollback data
            rollback_data = {
                'original_value': original_value,
                'parameter_path': target_site.parameter_path,
                'edit_timestamp': edit_start_time,
                'evolution_history': self._generation_history[-10:] if self._generation_history else []
            }

            # Compile edit metadata
            metadata = {
                'evolution_generations': len(self._generation_history),
                'population_size': self.config.population_size,
                'mutation_strategy': self.current_mutation_strategy,
                'crossover_strategy': self.current_crossover_strategy,
                'best_fitness': best_individual.fitness if best_individual else 0.0,
                'convergence_achieved': self._check_convergence(),
                'edit_duration_seconds': (datetime.now() - edit_start_time).total_seconds()
            }

            # Create edit result
            edit_result = EditResult(
                edit_id=edit_id,
                target_site=target_site,
                success=success,
                before_value=original_value,
                after_value=after_value,
                performance_delta=performance_delta,
                timestamp=edit_start_time,
                rollback_data=rollback_data,
                metadata=metadata
            )

            # Store in edit history
            self._edit_history.append(edit_result)

            return edit_result

        except Exception as e:
            logger.error(f"Edit {edit_id} failed with exception: {str(e)}")

            # Create failure result
            return EditResult(
                edit_id=edit_id,
                target_site=target_site,
                success=False,
                before_value=target_site.current_value,
                after_value=target_site.current_value,
                performance_delta=0.0,
                timestamp=edit_start_time,
                rollback_data={'error': str(e)},
                metadata={'error': str(e)}
            )

    def batch_edit(self,
                   targets: List[TargetSite],
                   model_genome: FinancialGenome) -> List[EditResult]:
        """
        🔄 Execute coordinated evolutionary edits
        
        Perform multiple related edits simultaneously using co-evolution
        to ensure they work together harmoniously.
        
        Args:
            targets: List of target sites to edit
            model_genome: Model parameters to modify
            
        Returns:
            List of edit results for each target
        """
        logger.info(f"Starting batch evolution for {len(targets)} targets")

        # If multiple targets, run a simple co-evolution routine that evolves
        # a joint population where each individual encodes edits for all targets.
        if len(targets) > 1:
            try:
                return self._batch_coevolution_edit(targets, model_genome)
            except Exception as e:
                logger.warning(f"Co-evolution failed, falling back to sequential edits: {e}")

        # Fallback: sequential processing (preserves previous behavior)
        edit_results = []
        for target in targets:
            result = self.edit(target, model_genome)
            edit_results.append(result)

            # Stop if critical edit fails
            if not result.success and getattr(target, 'priority', 0) >= 4:
                logger.warning("Critical edit failed, stopping batch edit")
                break

        return edit_results

    def _batch_coevolution_edit(self, targets: List[TargetSite], model_genome: FinancialGenome) -> List[EditResult]:
        """Simple co-evolution: each individual contains an 'edited_values' list for all targets.

        This is a conservative implementation that encodes all target edits into a single
        genome dict under 'edited_values' and performs GA over that joint space. The best
        individual's values are applied to the model_genome atomically.
        """
        # Build joint context
        context = {
            'targets': targets,
            'model_genome': model_genome
        }

        # Initialize joint population
        joint_population = self._initialize_population_batch(targets, context)

        # Temporarily replace population and evolve
        old_population = self._population
        self._population = joint_population

        best_joint = self._evolve_population(context)

        # Restore original population placeholder
        self._population = old_population

        edit_results: List[EditResult] = []

        if not best_joint:
            logger.warning("Batch co-evolution returned no best individual")
            # Return failed results for each target
            for t in targets:
                edit_results.append(EditResult(
                    edit_id=f"batch_fail_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    target_site=t,
                    success=False,
                    before_value=t.current_value,
                    after_value=t.current_value,
                    performance_delta=0.0,
                    timestamp=datetime.now(),
                    rollback_data={},
                    metadata={'error': 'no_best_individual'}
                ))
            return edit_results

        # Apply best edits atomically
        edited_values = best_joint.genome.get('edited_values', [])

        for idx, target in enumerate(targets):
            before = copy.deepcopy(target.current_value)
            new_val = edited_values[idx] if idx < len(edited_values) else before

            try:
                model_genome.set_parameter(target.parameter_path, new_val, f"Batch GA edit {datetime.now().strftime('%Y%m%d_%H%M%S')}")
                perf_delta = self._calculate_performance_delta(before, new_val, context)
                success = True
            except Exception as e:
                logger.warning(f"Failed to apply batch edit to {target.parameter_path}: {e}")
                new_val = before
                perf_delta = 0.0
                success = False

            edit_results.append(EditResult(
                edit_id=f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{idx}",
                target_site=target,
                success=success,
                before_value=before,
                after_value=new_val,
                performance_delta=perf_delta,
                timestamp=datetime.now(),
                rollback_data={'original_value': before},
                metadata={'source': 'batch_coevolution', 'best_fitness': best_joint.fitness}
            ))

        # Record to edit history
        self._edit_history.extend(edit_results)

        return edit_results

    def _initialize_population_batch(self, targets: List[TargetSite], context: Dict[str, Any]) -> List[Individual]:
        """Initialize a joint population encoding edits for all targets."""
        population: List[Individual] = []

        for i in range(self.config.population_size):
            edited_values = []
            for t in targets:
                curr = t.current_value
                targ = t.target_value
                # Use same perturbation rules as single-target init
                if t.edit_type == 'replace':
                    if isinstance(targ, (int, float)):
                        perturbation = np.random.normal(0, abs(targ) * 0.1 + 0.01)
                        val = targ + perturbation
                    elif isinstance(targ, np.ndarray):
                        perturbation = np.random.normal(0, np.std(targ) * 0.1, targ.shape)
                        val = targ + perturbation
                    else:
                        val = targ
                elif t.edit_type == 'adjust':
                    if isinstance(curr, (int, float)) and isinstance(targ, (int, float)):
                        alpha = np.random.random()
                        val = alpha * curr + (1 - alpha) * targ
                        val += np.random.normal(0, abs(val) * 0.05 + 0.001)
                    elif isinstance(curr, np.ndarray) and isinstance(targ, np.ndarray):
                        alpha = np.random.random()
                        val = alpha * curr + (1 - alpha) * targ
                        val += np.random.normal(0, np.std(val) * 0.05, val.shape)
                    else:
                        val = targ
                else:
                    # Unknown edit type: fall back to current value and log
                    logger.debug(f"Unknown edit_type '{t.edit_type}' for target {getattr(t, 'parameter_path', '<unknown>')} - falling back to current value")
                    val = curr

                edited_values.append(val)

            individual = Individual(genome={'edited_values': edited_values}, generation=0)
            individual.fitness = self.fitness_function.evaluate(individual, context)
            population.append(individual)

        # Sort and return
        population.sort(key=lambda x: x.fitness, reverse=True)
        return population

    def _initialize_population(self, target_site: TargetSite, context: Dict[str, Any]) -> None:
        """Initialize population around the target parameter value."""
        self._population.clear()

        current_value = target_site.current_value
        target_value = target_site.target_value

        for i in range(self.config.population_size):
            # Create individual with perturbed parameter value
            if target_site.edit_type == 'replace':
                # For replace edits, sample around the target value
                if isinstance(target_value, (int, float)):
                    perturbation = np.random.normal(0, abs(target_value) * 0.1 + 0.01)
                    individual_value = target_value + perturbation
                elif isinstance(target_value, np.ndarray):
                    perturbation = np.random.normal(0, np.std(target_value) * 0.1, target_value.shape)
                    individual_value = target_value + perturbation
                else:
                    individual_value = target_value

            elif target_site.edit_type == 'adjust':
                # For adjust edits, sample between current and target
                if isinstance(current_value, (int, float)) and isinstance(target_value, (int, float)):
                    alpha = np.random.random()
                    individual_value = alpha * current_value + (1 - alpha) * target_value

                    # Add small random perturbation
                    perturbation = np.random.normal(0, abs(individual_value) * 0.05 + 0.001)
                    individual_value += perturbation

                elif isinstance(current_value, np.ndarray) and isinstance(target_value, np.ndarray):
                    alpha = np.random.random()
                    individual_value = alpha * current_value + (1 - alpha) * target_value

                    # Add small random perturbation
                    perturbation = np.random.normal(0, np.std(individual_value) * 0.05, individual_value.shape)
                    individual_value += perturbation
                else:
                    individual_value = target_value

            else:  # remove
                individual_value = None

            # Create individual
            individual = Individual(
                genome={'edited_value': individual_value},
                generation=0
            )

            # Evaluate fitness
            individual.fitness = self.fitness_function.evaluate(individual, context)

            self._population.append(individual)

        # Sort by fitness and initialize best individual defensively
        self._population.sort(key=lambda x: x.fitness, reverse=True)
        if self._population:
            self._best_individual = self._population[0]
            logger.debug(f"Initialized population with best fitness: {self._best_individual.fitness:.6f}")
        else:
            # Ensure best individual is at least a placeholder to avoid None errors
            self._best_individual = Individual(genome={}, fitness=-np.inf)
            logger.debug("Initialized empty population; created placeholder best individual")

    def _evolve_population(self, context: Dict[str, Any]) -> Optional[Individual]:
        """Evolve the population to find optimal parameter edit."""
        # Mark evolution start time for telemetry
        self._generation_history.clear()
        self._evolution_start_time = datetime.now()
        self._evolution_end_time = None
        stagnant_generations = 0
        # Defensive: ensure there is an initial population
        if not self._population:
            logger.warning("Evolve called with empty population; nothing to do")
            return None

        # Ensure _best_individual is initialized
        if self._best_individual is None:
            self._best_individual = max(self._population, key=lambda x: x.fitness)

        for generation in range(self.config.num_generations):
            # Early age-based pruning: remove overly old individuals from the current population
            try:
                max_age_early = int(self.config.max_individual_age)
                if max_age_early > 0 and self._population:
                    # increment ages for current population
                    for ind in self._population:
                        try:
                            ind.age = int(getattr(ind, 'age', 0)) + 1
                        except Exception:
                            ind.age = 1

                    keep_early = [ind for ind in self._population if getattr(ind, 'age', 0) <= max_age_early]
                    pruned_early = [ind for ind in self._population if getattr(ind, 'age', 0) > max_age_early]
                    if pruned_early:
                        logger.debug(f"Early pruning {len(pruned_early)} individuals older than {max_age_early}")
                        for pind in pruned_early:
                            try:
                                if getattr(pind, 'fitness', -float('inf')) > -1e9:
                                    self.add_to_hall_of_fame(pind)
                            except Exception:
                                logger.exception('Failed to add pruned individual to hall_of_fame (early)')

                        # refill to keep population size using the known best individual
                        num_needed_early = self.config.population_size - len(keep_early)
                        new_inds_early = []
                        base_early = self._best_individual or (keep_early[0] if keep_early else None)
                        for _ in range(max(0, num_needed_early)):
                            if base_early is None:
                                break
                            try:
                                child = self._mutate(copy.deepcopy(base_early), context)
                                child.age = 0
                                child.fitness = self.fitness_function.evaluate(child, context)
                                new_inds_early.append(child)
                            except Exception:
                                logger.exception('Failed to create replacement individual during early pruning')

                        self._population = keep_early + new_inds_early
                        if len(self._population) < self.config.population_size:
                            while len(self._population) < self.config.population_size and base_early is not None:
                                c = copy.deepcopy(base_early)
                                c.age = 0
                                c.fitness = self.fitness_function.evaluate(c, context)
                                self._population.append(c)
            except Exception:
                logger.exception('Early age-based pruning failed')

            # Create new generation
            new_population = []

            # Elitism: keep best individuals
            elite_count = int(self.config.population_size * self.config.elitism_ratio)
            new_population.extend(self._population[:elite_count])

            # Generate offspring through selection, crossover, and mutation
            while len(new_population) < self.config.population_size:
                # Selection (pluggable)
                # record operator telemetry
                try:
                    self._operator_stats['selection'] += 1
                except Exception:
                    pass
                parent1 = self.selection_operator()
                try:
                    self._operator_stats['selection'] += 1
                except Exception:
                    pass
                parent2 = self.selection_operator()

                # Crossover
                if np.random.random() < self.config.crossover_rate:
                    try:
                        self._operator_stats['crossover'] += 1
                    except Exception:
                        pass
                    child1, child2 = self.crossover_operator(parent1, parent2)
                else:
                    child1, child2 = copy.deepcopy(parent1), copy.deepcopy(parent2)

                # Mutation
                if np.random.random() < self.config.mutation_rate:
                    try:
                        self._operator_stats['mutation'] += 1
                    except Exception:
                        pass
                    child1 = self.mutation_operator(child1, context)
                if np.random.random() < self.config.mutation_rate:
                    try:
                        self._operator_stats['mutation'] += 1
                    except Exception:
                        pass
                    child2 = self.mutation_operator(child2, context)

                # Add to new population (fitness assigned later, possibly in batch)
                new_population.extend([child1, child2])

            # Trim to population size
            new_population = new_population[:self.config.population_size]

            # Update population; evaluate fitnesses either individually or in batch
            self._population = new_population
            if self.use_parallel_evaluation:
                # Choose backend: Ray preferred if configured
                if self._parallel_backend == 'ray':
                    try:
                        from .evaluators_ray import evaluate_population_ray

                        # batch_size: if _evaluator_workers provided and >0, use it as batch size hint
                        batch_size = max(1, self._evaluator_workers) if (self._evaluator_workers and isinstance(self._evaluator_workers, int)) else 64
                        fitnesses = evaluate_population_ray(self._population,
                                                           lambda ind, ctx: self.fitness_function.evaluate(ind, ctx),
                                                           context,
                                                           ray_address=None,
                                                           batch_size=batch_size,
                                                           reuse_actors=False)
                        for ind, f in zip(self._population, fitnesses):
                            ind.fitness = f
                    except ImportError:
                        logger.warning('Ray is not available; falling back to multiprocessing evaluator')
                        try:
                            fitnesses = evaluate_population(self._population, lambda ind, ctx: self.fitness_function.evaluate(ind, ctx), context, workers=self._evaluator_workers)
                            for ind, f in zip(self._population, fitnesses):
                                ind.fitness = f
                        except Exception:
                            logger.exception('Parallel evaluation failed; falling back to per-individual')
                            for ind in self._population:
                                ind.fitness = self.fitness_function.evaluate(ind, context)
                    except Exception:
                        logger.exception('Ray parallel evaluation failed; falling back to per-individual')
                        for ind in self._population:
                            ind.fitness = self.fitness_function.evaluate(ind, context)
                else:
                    try:
                        fitnesses = evaluate_population(self._population, lambda ind, ctx: self.fitness_function.evaluate(ind, ctx), context, workers=self._evaluator_workers)
                        for ind, f in zip(self._population, fitnesses):
                            ind.fitness = f
                    except Exception:
                        logger.exception('Parallel evaluation failed; falling back to per-individual')
                        for ind in self._population:
                            ind.fitness = self.fitness_function.evaluate(ind, context)
            else:
                for ind in self._population:
                    ind.fitness = self.fitness_function.evaluate(ind, context)

            self._population.sort(key=lambda x: x.fitness, reverse=True)

            # If speciation is enabled, assign species and apply fitness sharing
            species_ids = None
            if self.use_speciation:
                try:
                    species_ids = self._assign_species(None)
                    # compute per-species best and record telemetry
                    species_best = {}
                    for ind, sid in zip(self._population, species_ids):
                        sid_key = sid if sid is not None else -1
                        species_best[sid_key] = max(species_best.get(sid_key, -1e9), getattr(ind, 'fitness', -1e9))
                    # store per-species bests into the dict of histories
                    for sid_k, best_val in species_best.items():
                        self._species_best_history.setdefault(int(sid_k), []).append(float(best_val))
                    self._apply_fitness_sharing(species_ids)
                except Exception:
                    logger.exception('Speciation/fitness-sharing failed')
            else:
                # ensure we append an empty mapping per generation for alignment
                # _species_best_history is a dict mapping species_id -> list of bests
                # When speciation is disabled, align histories by appending a placeholder
                try:
                    if isinstance(self._species_best_history, dict) and self._species_best_history:
                        for sid in list(self._species_best_history.keys()):
                            try:
                                self._species_best_history[sid].append(float('nan'))
                            except Exception:
                                # fallback to None if conversion fails
                                self._species_best_history[sid].append(None)
                    else:
                        # nothing to align yet; keep empty mapping
                        pass
                except Exception:
                    logger.exception('Failed to align species_best_history for generation')

            # Age increment and pruning (post-evaluation) - reuse early pruning semantics
            try:
                max_age = int(self.config.max_individual_age)
                if max_age > 0 and self._population:
                    # increment ages
                    for ind in self._population:
                        try:
                            ind.age = int(getattr(ind, 'age', 0)) + 1
                        except Exception:
                            ind.age = 1

                    # prune individuals older than max_age
                    keep = [ind for ind in self._population if getattr(ind, 'age', 0) <= max_age]
                    pruned = [ind for ind in self._population if getattr(ind, 'age', 0) > max_age]
                    if pruned:
                        logger.debug(f"Pruning {len(pruned)} individuals older than {max_age}")
                        # Add pruned high-fitness individuals to hall_of_fame
                        for pind in pruned:
                            try:
                                # Only add if decent fitness
                                if getattr(pind, 'fitness', -float('inf')) > -1e9:
                                    self.add_to_hall_of_fame(pind)
                            except Exception:
                                logger.exception('Failed to add pruned individual to hall_of_fame')

                        # Refill population by mutating the current best individual
                        num_needed = self.config.population_size - len(keep)
                        new_inds = []
                        base = self._best_individual or (keep[0] if keep else None)
                        for _ in range(max(0, num_needed)):
                            if base is None:
                                break
                            try:
                                child = self._mutate(copy.deepcopy(base), context)
                                child.age = 0
                                child.fitness = self.fitness_function.evaluate(child, context)
                                new_inds.append(child)
                            except Exception:
                                logger.exception('Failed to create replacement individual during pruning')

                        self._population = keep + new_inds
                        # Ensure we have the configured population size
                        if len(self._population) < self.config.population_size:
                            # pad with copies of best individual
                            while len(self._population) < self.config.population_size and base is not None:
                                c = copy.deepcopy(base)
                                c.age = 0
                                c.fitness = self.fitness_function.evaluate(c, context)
                                self._population.append(c)
            except Exception:
                logger.exception('Age-based pruning failed')

            # Update best individual
            current_best = self._population[0]
            # Defensive: compute improvement relative to last known best
            try:
                improvement = current_best.fitness - (self._best_individual.fitness if self._best_individual else -np.inf)
            except Exception:
                improvement = current_best.fitness

            if improvement > self.config.convergence_threshold:
                self._best_individual = current_best
                stagnant_generations = 0
            else:
                stagnant_generations += 1

            # Track generation statistics
            fitnesses = [ind.fitness for ind in self._population]
            # Compute diversity metric for population and include in stats
            try:
                diversity = self._compute_population_diversity(self._population)
            except Exception:
                diversity = 0.0
            generation_stats = {
                'generation': generation,
                'best_fitness': current_best.fitness,
                'avg_fitness': np.mean(fitnesses),
                'fitness_std': np.std(fitnesses),
                'improvement': improvement,
                'diversity': diversity
            }
            # If context contains 'targets' and the best individual encodes joint
            # edited_values (batch/co-evolution), create a lightweight per-symbol
            # weight summary that dashboards can render. This maps a short symbol
            # token (derived from the target.parameter_path) to a normalized
            # magnitude computed from the best individual's edits for that symbol.
            try:
                if context and isinstance(context, dict) and 'targets' in context and hasattr(current_best, 'genome'):
                    ev = current_best.genome.get('edited_values') if isinstance(current_best.genome, dict) else None
                    if isinstance(ev, list) and ev:
                        # Aggregate absolute edit magnitudes per symbol
                        sym_sums = {}
                        targets = context.get('targets') or []
                        for idx, tgt in enumerate(targets):
                            try:
                                path = getattr(tgt, 'parameter_path', '') or str(tgt)
                                # common pattern: '<SYMBOL>_strategy.<param>' -> extract SYMBOL
                                sym = path.split('.')[0].split('_')[0]
                                val = ev[idx] if idx < len(ev) else 0.0
                                amt = float(abs(val)) if isinstance(val, (int, float)) else 0.0
                            except Exception:
                                amt = 0.0
                                sym = f"t{idx}"
                            sym_sums[sym] = sym_sums.get(sym, 0.0) + amt

                        total_amt = float(sum(sym_sums.values())) if sum(sym_sums.values()) else 1.0
                        weights = {s: (sym_sums.get(s, 0.0) / total_amt) for s in sym_sums}
                        generation_stats['weights'] = weights
            except Exception:
                # Don't let telemetry instrumentation break evolution
                logger.exception('Failed to compute per-generation weights for telemetry')

            # Deterministic recording: append a timestamped weight vector per generation
            try:
                if getattr(self, '_record_weights', False):
                    gw = generation_stats.get('weights') or {}
                    ts = datetime.now().isoformat()

                    # Append timestamp
                    self._recorded_weight_history.setdefault('timestamps', []).append(ts)

                    recorded = self._recorded_weight_history.setdefault('weights', {})

                    # Keys that already exist in recorded history
                    existing_keys = set(recorded.keys())
                    new_keys = set(gw.keys())

                    # For keys present previously but missing in this generation, append None
                    for k in existing_keys - new_keys:
                        try:
                            recorded[k].append(None)
                        except Exception:
                            # If recorded list corrupted, reinitialize
                            recorded[k] = [None] * (len(self._recorded_weight_history['timestamps']) - 1) + [None]

                    # For new keys in this generation, create a list padded with None for prior timestamps
                    for k in new_keys - existing_keys:
                        pad_len = len(self._recorded_weight_history['timestamps']) - 1
                        recorded[k] = [None] * pad_len

                    # Now append the current values for all keys in gw
                    for k in new_keys:
                        try:
                            v = gw.get(k)
                            recorded[k].append(float(v) if v is not None else None)
                        except Exception:
                            recorded[k].append(None)

                    # If there were no explicit weights but a single edit target exists, try to infer
                    if not new_keys:
                        inferred_sym = None
                        inferred_val = None
                        # Prefer context.targets -> context.target_site
                        if context and isinstance(context, dict):
                            if 'targets' in context and isinstance(context.get('targets'), list) and context.get('targets'):
                                tgt = context['targets'][0]
                                path = getattr(tgt, 'parameter_path', None)
                                if path:
                                    inferred_sym = path.split('.')[0].split('_')[0]
                            elif 'target_site' in context and context.get('target_site') is not None:
                                tgt = context.get('target_site')
                                path = getattr(tgt, 'parameter_path', None)
                                if path:
                                    inferred_sym = path.split('.')[0].split('_')[0]

                        # Fallback: inspect best individual's genome keys
                        if inferred_sym is None and hasattr(current_best, 'genome') and isinstance(current_best.genome, dict):
                            for key in current_best.genome.keys():
                                try:
                                    if isinstance(key, str) and ('.' in key or '_' in key):
                                        inferred_sym = str(key).split('.')[0].split('_')[0]
                                        break
                                except Exception:
                                    continue

                        # If we can infer a symbol, map its weight to 1.0 (single-target prominence)
                        if inferred_sym:
                            recorded.setdefault(inferred_sym, [None] * (len(self._recorded_weight_history['timestamps']) - 1))
                            recorded[inferred_sym].append(1.0)

            except Exception:
                logger.exception('Failed to append deterministic weight history for generation')
            # Record species count if speciation applied
            try:
                if self.use_speciation and species_ids is not None:
                    generation_stats['species_count'] = len(set(species_ids))
                else:
                    generation_stats['species_count'] = 0
            except Exception:
                generation_stats['species_count'] = 0

            self._generation_history.append(generation_stats)

            logger.debug(f"Generation {generation}: best={current_best.fitness:.6f}, "
                        f"avg={np.mean(fitnesses):.6f}, improvement={improvement:.6f}")

            # Check convergence
            if stagnant_generations >= self.config.max_stagnant_generations:
                logger.info(f"Evolution converged after {generation} generations")
                break

            # Adaptive strategy adjustment
            if generation > 0 and generation % 20 == 0:
                self._adapt_strategies(generation_stats)

        # Mark evolution end time for telemetry
        self._evolution_end_time = datetime.now()
        return self._best_individual

    # -------------------- Checkpointing / Reproducibility --------------------
    def save_checkpoint(self, path: str) -> None:
        """Save exploration state to a checkpoint file (pickle).

        This allows long GA runs to be resumed later. Checkpoints contain
        population, best individual, generation history and RNG state.
        """
        try:
            import pickle
            state = {
                'population': self._population,
                'best_individual': self._best_individual,
                'generation_history': self._generation_history,
                'convergence_history': self._convergence_history,
                'hall_of_fame': self.hall_of_fame,
                'species_hall_of_fame': self.species_hall_of_fame,
                'species_best_history': self._species_best_history,
                'config': self.config,
                'current_mutation_strategy': self.current_mutation_strategy,
                'current_crossover_strategy': self.current_crossover_strategy,
                'edit_rate': self.edit_rate,
                'seed': self._seed,
                'numpy_rng_state': np.random.get_state(),
                'py_random_state': random.getstate()
            }
            with open(path, 'wb') as fh:
                pickle.dump(state, fh)
        except Exception:
            logger.exception('Failed to save checkpoint to %s', path)

    def load_checkpoint(self, path: str) -> None:
        """Load a checkpoint previously saved with save_checkpoint.

        Restores population, best individual, generation history and RNG state.
        """
        try:
            import pickle
            with open(path, 'rb') as fh:
                state = pickle.load(fh)

            self._population = state.get('population', [])
            self._best_individual = state.get('best_individual')
            self._generation_history = state.get('generation_history', [])
            self._convergence_history = state.get('convergence_history', [])
            self.hall_of_fame = state.get('hall_of_fame', [])
            self.species_hall_of_fame = state.get('species_hall_of_fame', {})
            self._species_best_history = state.get('species_best_history', {})
            self.config = state.get('config', self.config)
            self.current_mutation_strategy = state.get('current_mutation_strategy', self.current_mutation_strategy)
            self.current_crossover_strategy = state.get('current_crossover_strategy', self.current_crossover_strategy)
            self.edit_rate = state.get('edit_rate', self.edit_rate)
            self._seed = state.get('seed', self._seed)

            # Restore RNGs
            try:
                np.random.set_state(state.get('numpy_rng_state'))
            except Exception:
                pass
            try:
                random.setstate(state.get('py_random_state'))
            except Exception:
                pass
        except Exception:
            logger.exception('Failed to load checkpoint from %s', path)

    def _tournament_selection(self, tournament_size: int = 3) -> Individual:
        """Tournament selection for parent selection."""
        tournament = random.sample(self._population, min(tournament_size, len(self._population)))
        # If speciation fitness sharing is enabled, prefer shared_fitness when present
        def _score(ind: Individual):
            return getattr(ind, 'shared_fitness', ind.fitness)

        return max(tournament, key=_score)

    def set_speciation(self, enabled: bool, threshold: Optional[float] = None) -> None:
        """Enable or disable speciation / fitness-sharing.

        Args:
            enabled: whether to enable speciation
            threshold: optional distance threshold to pass to _assign_species
        """
        self.use_speciation = bool(enabled)
        if threshold is not None:
            self.speciation_threshold = float(threshold)
        # If enabling, switch the selection operator to speciation-aware
        if self.use_speciation:
            self.selection_operator = lambda: self._speciation_selection()
        else:
            self.selection_operator = lambda: self._tournament_selection()

    def _speciation_selection(self) -> Individual:
        """Select a parent by first choosing a species uniformly, then doing
        a small tournament inside that species using shared_fitness.
        This helps preserve niches during selection.
        """
        # Ensure species ids are available
        species_ids = [getattr(ind, 'species_id', None) for ind in self._population]
        if any(sid is None for sid in species_ids):
            species_ids = self._assign_species(None)

        # Build mapping species -> member indices
        mapping = {}
        for idx, sid in enumerate(species_ids):
            mapping.setdefault(sid, []).append(self._population[idx])

        # Choose species uniformly at random among non-empty
        species_list = [s for s, members in mapping.items() if members]
        if not species_list:
            # fallback
            return self._tournament_selection()

        chosen = random.choice(species_list)
        members = mapping[chosen]
        # Tournament among members (size 2)
        if len(members) == 1:
            return members[0]
        a, b = random.sample(members, min(2, len(members)))
        # use shared_fitness if present
        sa = getattr(a, 'shared_fitness', a.fitness)
        sb = getattr(b, 'shared_fitness', b.fitness)
        return a if sa >= sb else b


    def _crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        """Apply crossover strategy to create offspring."""
        strategy_func = self.crossover_strategies[self.current_crossover_strategy]
        return strategy_func(parent1, parent2)

    def _arithmetic_crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        """Arithmetic crossover for numerical parameters."""
        alpha = np.random.random()

        child1_genome = {}
        child2_genome = {}

        for key in parent1.genome:
            value1 = parent1.genome[key]
            value2 = parent2.genome[key]

            if isinstance(value1, (int, float)) and isinstance(value2, (int, float)):
                child1_genome[key] = alpha * value1 + (1 - alpha) * value2
                child2_genome[key] = (1 - alpha) * value1 + alpha * value2
            elif isinstance(value1, np.ndarray) and isinstance(value2, np.ndarray):
                child1_genome[key] = alpha * value1 + (1 - alpha) * value2
                child2_genome[key] = (1 - alpha) * value1 + alpha * value2
            else:
                # For non-numeric types, randomly choose parent
                if np.random.random() < 0.5:
                    child1_genome[key] = value1
                    child2_genome[key] = value2
                else:
                    child1_genome[key] = value2
                    child2_genome[key] = value1

        child1 = Individual(genome=child1_genome, parent_ids=[parent1.id, parent2.id])
        child2 = Individual(genome=child2_genome, parent_ids=[parent1.id, parent2.id])

        return child1, child2

    def _uniform_crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        """Uniform crossover - randomly choose genes from parents."""
        child1_genome = {}
        child2_genome = {}

        for key in parent1.genome:
            if np.random.random() < 0.5:
                child1_genome[key] = parent1.genome[key]
                child2_genome[key] = parent2.genome[key]
            else:
                child1_genome[key] = parent2.genome[key]
                child2_genome[key] = parent1.genome[key]

        child1 = Individual(genome=child1_genome, parent_ids=[parent1.id, parent2.id])
        child2 = Individual(genome=child2_genome, parent_ids=[parent1.id, parent2.id])

        return child1, child2

    def _single_point_crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        """Single point crossover for array-based parameters."""
        # This is mainly for array parameters
        child1_genome = copy.deepcopy(parent1.genome)
        child2_genome = copy.deepcopy(parent2.genome)

        for key in parent1.genome:
            value1 = parent1.genome[key]
            value2 = parent2.genome[key]

            if isinstance(value1, np.ndarray) and isinstance(value2, np.ndarray) and value1.size > 1:
                crossover_point = np.random.randint(1, value1.size)

                # Flatten, crossover, reshape
                flat1 = value1.flatten()
                flat2 = value2.flatten()

                child1_flat = np.concatenate([flat1[:crossover_point], flat2[crossover_point:]])
                child2_flat = np.concatenate([flat2[:crossover_point], flat1[crossover_point:]])

                child1_genome[key] = child1_flat.reshape(value1.shape)
                child2_genome[key] = child2_flat.reshape(value2.shape)

        child1 = Individual(genome=child1_genome, parent_ids=[parent1.id, parent2.id])
        child2 = Individual(genome=child2_genome, parent_ids=[parent1.id, parent2.id])

        return child1, child2

    def _simulated_binary_crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        """Simulated binary crossover for real-valued parameters."""
        eta = 2.0  # Distribution index

        child1_genome = {}
        child2_genome = {}

        for key in parent1.genome:
            value1 = parent1.genome[key]
            value2 = parent2.genome[key]

            if isinstance(value1, (int, float)) and isinstance(value2, (int, float)):
                if abs(value1 - value2) > 1e-14:
                    if value1 > value2:
                        value1, value2 = value2, value1

                    rand = np.random.random()
                    if rand <= 0.5:
                        beta = (2 * rand) ** (1.0 / (eta + 1))
                    else:
                        beta = (1.0 / (2 * (1 - rand))) ** (1.0 / (eta + 1))

                    child1_genome[key] = 0.5 * ((1 + beta) * value1 + (1 - beta) * value2)
                    child2_genome[key] = 0.5 * ((1 - beta) * value1 + (1 + beta) * value2)
                else:
                    child1_genome[key] = value1
                    child2_genome[key] = value2
            else:
                # Fall back to simple assignment
                child1_genome[key] = value1
                child2_genome[key] = value2

        child1 = Individual(genome=child1_genome, parent_ids=[parent1.id, parent2.id])
        child2 = Individual(genome=child2_genome, parent_ids=[parent1.id, parent2.id])

        return child1, child2

    def _mutate(self, individual: Individual, context: Dict[str, Any]) -> Individual:
        """Apply mutation strategy to individual."""
        strategy_func = self.mutation_strategies[self.current_mutation_strategy]
        return strategy_func(individual, context)

    def _gaussian_mutation(self, individual: Individual, context: Dict[str, Any]) -> Individual:
        """Gaussian mutation for numerical parameters."""
        mutated = copy.deepcopy(individual)

        for key in mutated.genome:
            value = mutated.genome[key]

            if isinstance(value, (int, float)):
                mutation_strength = abs(value) * self.edit_rate + 0.001
                perturbation = np.random.normal(0, mutation_strength)
                mutated.genome[key] = value + perturbation

            elif isinstance(value, np.ndarray):
                mutation_strength = np.std(value) * self.edit_rate + 0.001
                perturbation = np.random.normal(0, mutation_strength, value.shape)
                mutated.genome[key] = value + perturbation

        mutated.mutation_history.append(f"gaussian_{datetime.now().strftime('%H%M%S')}")
        return mutated

    def _uniform_mutation(self, individual: Individual, context: Dict[str, Any]) -> Individual:
        """Uniform mutation within parameter bounds."""
        mutated = copy.deepcopy(individual)

        for key in mutated.genome:
            value = mutated.genome[key]

            if isinstance(value, (int, float)):
                # Mutate within ±20% of current value
                range_val = abs(value) * 0.2 + 0.01
                perturbation = np.random.uniform(-range_val, range_val)
                mutated.genome[key] = value + perturbation

            elif isinstance(value, np.ndarray):
                range_val = np.std(value) * 0.2 + 0.01
                perturbation = np.random.uniform(-range_val, range_val, value.shape)
                mutated.genome[key] = value + perturbation

        mutated.mutation_history.append(f"uniform_{datetime.now().strftime('%H%M%S')}")
        return mutated

    def _adaptive_mutation(self, individual: Individual, context: Dict[str, Any]) -> Individual:
        """Adaptive mutation based on fitness and generation."""
        # Use lower mutation rate for higher fitness individuals
        adaptive_rate = self.edit_rate * (1.0 - individual.fitness / (abs(individual.fitness) + 1.0))
        adaptive_rate = max(0.001, min(0.5, adaptive_rate))  # Clamp to reasonable range

        # Temporarily adjust edit rate
        original_rate = self.edit_rate
        self.edit_rate = adaptive_rate

        # Apply Gaussian mutation with adaptive rate
        mutated = self._gaussian_mutation(individual, context)

        # Restore original rate
        self.edit_rate = original_rate

        mutated.mutation_history.append(f"adaptive_{datetime.now().strftime('%H%M%S')}")
        return mutated

    def _polynomial_mutation(self, individual: Individual, context: Dict[str, Any]) -> Individual:
        """Polynomial mutation for bounded parameters."""
        eta_m = 20.0  # Distribution index
        mutated = copy.deepcopy(individual)

        for key in mutated.genome:
            value = mutated.genome[key]

            if isinstance(value, (int, float)):
                rand = np.random.random()

                if rand < 0.5:
                    delta = (2 * rand) ** (1.0 / (eta_m + 1)) - 1
                else:
                    delta = 1 - (2 * (1 - rand)) ** (1.0 / (eta_m + 1))

                mutation_strength = abs(value) * self.edit_rate + 0.001
                mutated.genome[key] = value + delta * mutation_strength

        mutated.mutation_history.append(f"polynomial_{datetime.now().strftime('%H%M%S')}")
        return mutated

    def _adapt_strategies(self, generation_stats: Dict[str, Any]) -> None:
        """Adapt mutation and crossover strategies based on evolution progress."""
        # Simple adaptive strategy: increase mutation rate if fitness is stagnating
        recent_improvements = [gen['improvement'] for gen in self._generation_history[-5:]]
        avg_improvement = np.mean(recent_improvements) if recent_improvements else 0.0
        # Also adapt based on diversity metric if available
        diversity = generation_stats.get('diversity', None)

        if avg_improvement < self.config.convergence_threshold:
            # Increase exploration by switching strategy
            if self.current_mutation_strategy == 'gaussian':
                self.current_mutation_strategy = 'uniform'
            elif self.current_mutation_strategy == 'uniform':
                self.current_mutation_strategy = 'adaptive'

            logger.debug(f"Adapted mutation strategy to: {self.current_mutation_strategy}")

        # If diversity is low, increase mutation rate temporarily to escape local optima
        try:
            if diversity is not None:
                if diversity < self.config.diversity_threshold:
                    # Increase mutation rate up to a cap
                    new_rate = min(0.5, self.config.mutation_rate * 1.5 + 0.01)
                    logger.debug(f"Low diversity ({diversity:.3f}) -> increasing mutation_rate {self.config.mutation_rate:.3f} -> {new_rate:.3f}")
                    self.config.mutation_rate = new_rate
                else:
                    # Decay mutation rate back towards baseline slowly
                    self.config.mutation_rate = max(self._base_mutation_rate, self.config.mutation_rate * 0.95)
        except Exception:
            logger.exception('Failed to adapt mutation rate based on diversity')

    def _compute_population_diversity(self, population: List[Individual]) -> float:
        """Compute a simple diversity metric for the current population.

        Returns:
            A float in [0, +inf) representing average pairwise normalized distance.
            For genomes without numeric content, returns 0.0.
        """
        # Build numeric vectors for each individual by flattening numeric fields
        vectors = []
        for ind in population:
            vec = []
            for k, v in ind.genome.items():
                if isinstance(v, (int, float)):
                    vec.append(float(v))
                elif isinstance(v, np.ndarray):
                    try:
                        flat = v.flatten().astype(float)
                        vec.extend(flat.tolist())
                    except Exception:
                        continue
                # skip non-numeric types
            if vec:
                vectors.append(np.array(vec, dtype=float))

        if len(vectors) < 2:
            return 0.0

        # Pad vectors to same length
        max_len = max(v.shape[0] for v in vectors)
        mat = np.zeros((len(vectors), max_len), dtype=float)
        for i, v in enumerate(vectors):
            mat[i, :v.shape[0]] = v

        # Compute pairwise Euclidean distances
        dists = []
        for i in range(len(mat)):
            for j in range(i + 1, len(mat)):
                d = np.linalg.norm(mat[i] - mat[j])
                dists.append(d)

        if not dists:
            return 0.0

        # Normalize by sqrt of vector length to make scale less dependent on dimensionality
        norm = np.sqrt(max_len) if max_len > 0 else 1.0
        return float(np.mean(dists) / norm)

    def _genome_to_vector(self, genome: Dict[str, Any]) -> Optional[np.ndarray]:
        """Convert numeric parts of a genome to a flat numpy vector (or None)."""
        vec = []
        for k, v in genome.items():
            if isinstance(v, (int, float)):
                vec.append(float(v))
            elif isinstance(v, np.ndarray):
                try:
                    flat = v.flatten().astype(float)
                    vec.extend(flat.tolist())
                except Exception:
                    continue
        if not vec:
            return None
        return np.array(vec, dtype=float)

    def _assign_species(self, threshold: Optional[float] = None) -> List[int]:
        """Assign species ids to current population using a simple distance threshold.

        Returns a list of species indices aligned with `self._population`.
        """
        if threshold is None:
            threshold = float(self.speciation_threshold)

        vectors = [self._genome_to_vector(ind.genome) for ind in self._population]
        species = [-1] * len(vectors)
        current_species = 0

        for i, vi in enumerate(vectors):
            if species[i] != -1:
                continue
            # If vector is None, assign its own species
            if vi is None:
                species[i] = current_species
                current_species += 1
                continue

            species[i] = current_species
            for j in range(i + 1, len(vectors)):
                if species[j] != -1:
                    continue
                vj = vectors[j]
                if vj is None:
                    continue
                # pad shorter vector
                max_len = max(vi.size, vj.size)
                a = np.zeros(max_len)
                b = np.zeros(max_len)
                a[:vi.size] = vi
                b[:vj.size] = vj
                dist = float(np.linalg.norm(a - b) / np.sqrt(max_len))
                if dist <= threshold:
                    species[j] = current_species

            current_species += 1

        # Attach species id to individuals for convenience
        for ind, sid in zip(self._population, species):
            setattr(ind, 'species_id', sid)
            # also set legacy-friendly attribute `species` used by some tests
            try:
                setattr(ind, 'species', sid)
            except Exception:
                pass

        return species

    def _apply_fitness_sharing(self, species_ids: Optional[List[int]] = None) -> None:
        """Apply fitness sharing by dividing fitness of individuals by species size."""
        explicit_call = species_ids is not None
        if species_ids is None:
            species_ids = self._assign_species(None)

        # Count species sizes
        counts = {}
        for sid in species_ids:
            counts[sid] = counts.get(sid, 0) + 1

        for ind, sid in zip(self._population, species_ids):
            size = counts.get(sid, 1)
            # Compute shared fitness and store it on the individual.
            try:
                shared = ind.fitness / float(size) if size > 0 else ind.fitness
                ind.shared_fitness = shared
                # If fitness sharing is enabled in config and this was not an explicit
                # call with a species list passed in, also modify the individual's
                # reported fitness so downstream selection observes sharing.
                if getattr(self.config, 'enable_fitness_sharing', False) and not explicit_call:
                    ind.fitness = shared
            except Exception:
                ind.shared_fitness = ind.fitness

    def _calculate_performance_delta(self,
                                   original_value: Any,
                                   new_value: Any,
                                   context: Dict[str, Any]) -> float:
        """Calculate the performance improvement from the edit."""
        try:
            # Create individuals for comparison
            original_individual = Individual(genome={'edited_value': original_value})
            new_individual = Individual(genome={'edited_value': new_value})

            # Evaluate both
            original_fitness = self.fitness_function.evaluate(original_individual, context)
            new_fitness = self.fitness_function.evaluate(new_individual, context)

            return new_fitness - original_fitness

        except Exception as e:
            logger.warning(f"Could not calculate performance delta: {str(e)}")
            return 0.0

    def _check_convergence(self) -> bool:
        """Check if evolution has converged."""
        if len(self._generation_history) < 10:
            return False

        recent_improvements = [gen['improvement'] for gen in self._generation_history[-10:]]
        avg_improvement = np.mean(recent_improvements)

        return avg_improvement < self.config.convergence_threshold

    def add_to_hall_of_fame(self, individual: Individual, k: int = 10) -> None:
        """Add an individual to the hall-of-fame (keep top-k by fitness).

        Stores a compact summary (id, fitness, generation, genome summary).
        """
        try:
            summary = {
                'id': getattr(individual, 'id', None),
                'fitness': getattr(individual, 'fitness', None),
                'generation': getattr(individual, 'generation', None),
                'genome': self._summarize_genome(individual.genome)
            }

            # Insert and keep unique IDs
            existing_ids = {h.get('id') for h in self.hall_of_fame}
            if summary['id'] in existing_ids:
                # Update entry
                self.hall_of_fame = [h if h.get('id') != summary['id'] else summary for h in self.hall_of_fame]
            else:
                self.hall_of_fame.append(summary)

            # Sort by fitness desc and trim
            try:
                self.hall_of_fame.sort(key=lambda x: x.get('fitness', -float('inf')), reverse=True)
            except Exception:
                pass

            if len(self.hall_of_fame) > k:
                self.hall_of_fame = self.hall_of_fame[:k]
        except Exception:
            logger.exception('Failed to add individual to hall_of_fame')

    def add_to_species_hall_of_fame(self, species_id: int, individual: Individual) -> None:
        """Add an individual to the per-species hall-of-fame (keep top-k by fitness).

        Each species maintains its own top-K historical summaries. This is useful
        for tracking niche champions.
        """
        try:
            k = int(getattr(self.config, 'species_hof_k', 5) or 5)
            summary = {
                'id': getattr(individual, 'id', None),
                'fitness': getattr(individual, 'fitness', None),
                'generation': getattr(individual, 'generation', None),
                'genome': self._summarize_genome(individual.genome)
            }

            bucket = self.species_hall_of_fame.setdefault(species_id, [])
            existing_ids = {h.get('id') for h in bucket}
            if summary['id'] in existing_ids:
                # update existing
                self.species_hall_of_fame[species_id] = [h if h.get('id') != summary['id'] else summary for h in bucket]
            else:
                bucket.append(summary)

            # sort and trim
            try:
                bucket.sort(key=lambda x: x.get('fitness', -float('inf')), reverse=True)
            except Exception:
                pass
            if len(bucket) > k:
                self.species_hall_of_fame[species_id] = bucket[:k]
        except Exception:
            logger.exception('Failed to add to species_hall_of_fame')

    def prune_species_hof(self, current_generation: Optional[int] = None) -> None:
        """Prune all species hall-of-fame buckets to the current configured `species_hof_k`.

        Args:
            current_generation: optional generation number to use when applying age-based pruning;
                                if None, the method will infer it from evolution history or entries.
        """
        try:
            k = int(getattr(self.config, 'species_hof_k', 5) or 5)
            for sid, bucket in list(self.species_hall_of_fame.items()):
                try:
                    # Optionally remove old entries by generation age first
                    if getattr(self, '_species_hof_max_age', None) is not None:
                        try:
                            max_age = int(self._species_hof_max_age)
                            # Determine a reference generation (use last generation if available)
                            if current_generation is not None:
                                current_gen = int(current_generation)
                            elif self._generation_history:
                                current_gen = int(self._generation_history[-1].get('generation', 0))
                            else:
                                # fallback: compute max generation among entries
                                current_gen = max((e.get('generation', 0) for b in self.species_hall_of_fame.values() for e in b), default=0)

                            new_bucket = [e for e in bucket if (current_gen - int(e.get('generation', 0))) <= max_age]
                        except Exception:
                            new_bucket = bucket
                    else:
                        new_bucket = bucket

                    new_bucket.sort(key=lambda x: x.get('fitness', -float('inf')), reverse=True)
                    self.species_hall_of_fame[sid] = new_bucket[:k]
                except Exception:
                    continue
        except Exception:
            logger.exception('Failed to prune species_hall_of_fame')

    def set_species_hof_config(self, k: Optional[int] = None, max_age: Optional[int] = None) -> None:
        """Runtime update for species hall-of-fame sizing and pruning policy.

        Args:
            k: new per-species hall-of-fame size (if None, leaves current value)
            max_age: maximum age (in generations) to keep entries in species HOF (None = disabled)
        """
        try:
            if k is not None:
                self.config.species_hof_k = int(k)
            if max_age is not None:
                # store runtime max age and prune accordingly
                try:
                    self._species_hof_max_age = int(max_age)
                except Exception:
                    self._species_hof_max_age = None
            # prune to new setting immediately
            self.prune_species_hof()
        except Exception:
            logger.exception('Failed to update species_hof_config')

    def _summarize_genome(self, genome: Dict[str, Any], max_items: int = 10) -> Dict[str, Any]:
        """Create a compact summary of a genome for telemetry and storage.

        This avoids embedding large arrays directly in telemetry by reporting
        shapes and small samples where appropriate.
        """
        summary: Dict[str, Any] = {}
        count = 0
        for k, v in genome.items():
            if count >= max_items:
                break
            if isinstance(v, (int, float, str)):
                summary[k] = v
            elif isinstance(v, np.ndarray):
                summary[k] = {'shape': v.shape, 'dtype': str(v.dtype)}
            elif isinstance(v, list):
                summary[k] = {'type': 'list', 'len': len(v), 'sample': v[:3]}
            elif isinstance(v, dict):
                summary[k] = {'type': 'dict', 'keys': list(v.keys())[:3]}
            else:
                try:
                    summary[k] = str(v)
                except Exception:
                    summary[k] = {'type': type(v).__name__}
            count += 1

        # If genome is empty, provide a placeholder
        if not summary:
            return {'note': 'empty_genome'}

        return summary

    def get_evolution_statistics(self) -> Dict[str, Any]:
        """
        📊 Generate evolution performance statistics
        
        Returns:
            Dictionary with evolution performance metrics
        """
        if not self._generation_history:
            return {'status': 'No evolution history available'}

        fitnesses = [gen['best_fitness'] for gen in self._generation_history]
        improvements = [gen['improvement'] for gen in self._generation_history]

        # Per-generation aggregates
        best_per_gen = fitnesses
        avg_per_gen = [gen.get('avg_fitness', 0.0) for gen in self._generation_history]
        std_per_gen = [gen.get('fitness_std', 0.0) for gen in self._generation_history]
        diversity_per_gen = [gen.get('diversity', 0.0) for gen in self._generation_history]

        # Best individual snapshot (compact)
        best_ind = self._best_individual
        best_summary = None
        if best_ind:
            try:
                genome_summary = self._summarize_genome(best_ind.genome)
            except Exception:
                genome_summary = {'note': 'could_not_summarize'}

            best_summary = {
                'id': getattr(best_ind, 'id', None),
                'fitness': getattr(best_ind, 'fitness', None),
                'generation': getattr(best_ind, 'generation', None),
                'genome_summary': genome_summary
            }

        # Timing telemetry
        start_ts = self._evolution_start_time.isoformat() if self._evolution_start_time else None
        end_ts = self._evolution_end_time.isoformat() if self._evolution_end_time else None
        run_time = None
        if self._evolution_start_time and self._evolution_end_time:
            run_time = (self._evolution_end_time - self._evolution_start_time).total_seconds()

        base_stats = {
            'total_generations': len(self._generation_history),
            'generations_run': len(self._generation_history),
            'final_fitness': fitnesses[-1] if fitnesses else 0.0,
            'best_fitness': max(fitnesses) if fitnesses else 0.0,
            'total_improvement': (fitnesses[-1] - fitnesses[0]) if len(fitnesses) > 1 else 0.0,
            'average_improvement_per_generation': np.mean(improvements) if improvements else 0.0,
            'convergence_achieved': self._check_convergence(),
            'mutation_strategy': self.current_mutation_strategy,
            'crossover_strategy': self.current_crossover_strategy,
            'population_size': self.config.population_size,
            'edit_success_rate': len([e for e in self._edit_history if e.success]) / max(1, len(self._edit_history)),
            'best_individual': best_summary,
            'best_per_generation': best_per_gen,
            'avg_per_generation': avg_per_gen,
            'std_per_generation': std_per_gen,
            'diversity_per_generation': diversity_per_gen,
            'final_diversity': diversity_per_gen[-1] if diversity_per_gen else 0.0,
            'mutation_rate': self.config.mutation_rate,
            'crossover_rate': self.config.crossover_rate,
            'operator_stats': self._operator_stats,
            'species_best_per_generation': self._species_best_history,
            'species_hall_of_fame': self.species_hall_of_fame,
            'num_generations_configured': self.config.num_generations,
            'run_start_time': start_ts,
            'run_end_time': end_ts,
            'run_time_seconds': run_time
        }
        # Prefer the deterministic recorded weight history if present
        try:
            if getattr(self, '_recorded_weight_history', None) and self._recorded_weight_history.get('timestamps'):
                # Sanitize recorded history: ensure per-symbol lists align with timestamps length
                rh = self._recorded_weight_history
                ts_len = len(rh.get('timestamps') or [])
                clean_weights = {}
                for k, lst in (rh.get('weights') or {}).items():
                    try:
                        if not isinstance(lst, list):
                            lst = list(lst)
                        # Trim long lists to the most recent ts_len entries
                        if len(lst) > ts_len:
                            clean = lst[-ts_len:]
                        else:
                            # Pad shorter lists with None at the end
                            clean = list(lst) + [None] * (ts_len - len(lst))
                    except Exception:
                        clean = [None] * ts_len
                    clean_weights[k] = clean

                base_stats['weight_history'] = {'timestamps': list(rh.get('timestamps') or []), 'weights': clean_weights}
                return base_stats

            # Otherwise, fall back to extracting from per-generation stats and hall_of_fame
            weight_history = {'timestamps': [], 'weights': {}}

            # First, check if per-generation stats include a 'weights' entry
            for gen in self._generation_history:
                gw = gen.get('weights') or gen.get('strategy_weights')
                if isinstance(gw, dict) and gw:
                    label = f"gen_{int(gen.get('generation', len(weight_history['timestamps'])))}"
                    weight_history['timestamps'].append(label)
                    for k, v in gw.items():
                        weight_history['weights'].setdefault(k, [])
                        weight_history['weights'][k].append(float(v) if v is not None else None)

            # If nothing found in per-generation stats, try hall_of_fame entries
            if not weight_history['timestamps'] and self.hall_of_fame:
                hof_sorted = sorted([h for h in self.hall_of_fame if isinstance(h, dict)], key=lambda x: int(x.get('generation', 0)))
                for h in hof_sorted:
                    genome = h.get('genome') or {}
                    gw = None
                    if isinstance(genome, dict):
                        gw = genome.get('weights') or genome.get('strategy_weights')
                    if isinstance(gw, dict) and gw:
                        label = f"gen_{int(h.get('generation', 0))}"
                        weight_history['timestamps'].append(label)
                        for k, v in gw.items():
                            weight_history['weights'].setdefault(k, [])
                            weight_history['weights'][k].append(float(v) if v is not None else None)

            if not weight_history['timestamps']:
                weight_history = {'timestamps': [], 'weights': {}}

            base_stats['weight_history'] = weight_history
            return base_stats
        except Exception:
            # If anything fails, return base stats without a weight_history key
            return base_stats

    def log_run_to_mlflow(self, mlflow_client: Optional[Any] = None, experiment_name: Optional[str] = None) -> bool:
        """Log the recent evolution run to MLflow (if available).

        Args:
            mlflow_client: optional imported mlflow module instance; if None, will attempt to import mlflow.
            experiment_name: optional experiment name to create/select.

        Returns:
            True if logging was performed, False if MLflow is not available or logging failed.
        """
        try:
            mlflow = mlflow_client
            if mlflow is None:
                try:
                    import mlflow  # type: ignore
                    mlflow = mlflow
                except Exception:
                    logger.info('MLflow not available; skipping MLflow logging')
                    return False

            # Prepare stats and params
            stats = self.get_evolution_statistics() if self._generation_history else {}
            params = {
                'population_size': int(getattr(self.config, 'population_size', 0)),
                'num_generations': int(getattr(self.config, 'num_generations', 0)),
                'mutation_rate': float(getattr(self.config, 'mutation_rate', 0.0)),
                'crossover_rate': float(getattr(self.config, 'crossover_rate', 0.0))
            }

            if experiment_name:
                try:
                    mlflow.set_experiment(experiment_name)
                except Exception:
                    logger.exception('Failed to set MLflow experiment %s', experiment_name)

            with mlflow.start_run():
                try:
                    mlflow.log_params(params)
                except Exception:
                    logger.exception('Failed to log MLflow params')

                # Log a few scalar metrics if available
                try:
                    if stats:
                        mlflow.log_metric('best_fitness', float(stats.get('best_fitness', 0.0)))
                        mlflow.log_metric('final_fitness', float(stats.get('final_fitness', 0.0)))
                        mlflow.log_metric('total_generations', int(stats.get('total_generations', 0)))
                except Exception:
                    logger.exception('Failed to log MLflow metrics')

                # Persist hall_of_fame as a small JSON artifact
                try:
                    import tempfile
                    import json
                    tmp = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
                    json.dump(self.hall_of_fame or {}, tmp, default=str)
                    tmp.flush()
                    tmp.close()
                    mlflow.log_artifact(tmp.name, artifact_path='hall_of_fame')
                except Exception:
                    logger.exception('Failed to log hall_of_fame artifact to MLflow')

            return True
        except Exception:
            logger.exception('Unexpected error while attempting MLflow logging')
            return False
