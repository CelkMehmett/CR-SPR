"""
Repair/Stabilizer utilities for CRISPR-FinAI

Provides simple, framework-agnostic stabilization routines for a
`FinancialGenome`-like object: backup/rollback, L2-style shrinkage,
clipping, and a stabilization decision helper that can rollback on
severe performance degradation.

This is intentionally minimal and defensive: it works with common
genome APIs (`to_dict`, `from_dict`, `iter_genes`, `set_gene_value`).
"""

from __future__ import annotations
import json
import os
import time
from typing import Any, Dict, Optional, Tuple, List

AUDIT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'logs'))
os.makedirs(AUDIT_DIR, exist_ok=True)


class Stabilizer:
    """Stabilizer: lightweight repair utilities for genome-like objects.

    Contract:
    - backup_state(genome) -> str (path)
    - rollback_from_backup(path, genome) -> bool
    - apply_simple_regularization(genome) -> dict
    - stabilize_after_edit(genome, before_metrics, after_metrics, rollback_threshold) -> dict
    """

    def __init__(self, l2_penalty: float = 1e-4, clip_min: float = -1.0, clip_max: float = 1.0):
        self.l2_penalty = float(l2_penalty)
        self.clip_min = float(clip_min)
        self.clip_max = float(clip_max)

    def backup_state(self, genome: Any) -> str:
        """Serialize genome state to JSON and return the path."""
        try:
            if hasattr(genome, 'to_dict'):
                state = genome.to_dict()
            elif hasattr(genome, '__dict__'):
                state = getattr(genome, '__dict__')
            else:
                raise TypeError('Genome object has no serializable state method')

            ts = int(time.time())
            path = os.path.join(AUDIT_DIR, f'genome_backup_{ts}.json')
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(state, f, default=str, indent=2)
            return path
        except Exception as e:
            raise RuntimeError(f'Failed to backup genome: {e}') from e

    def rollback_from_backup(self, path: str, genome: Any) -> bool:
        """Restore genome state from a backup file.

        Attempts `from_dict` first, then falls back to per-gene setters, then __dict__ update.
        """
        try:
            with open(path, encoding='utf-8') as f:
                state = json.load(f)

            if hasattr(genome, 'from_dict'):
                genome.from_dict(state)
                return True

            # common genome dict layout: {'chromosomes': {chrom: {gene: value}}}
            if hasattr(genome, 'set_gene_value') and isinstance(state, dict):
                chroms = state.get('chromosomes', state)
                if isinstance(chroms, dict):
                    for chrom, genes in chroms.items():
                        if isinstance(genes, dict):
                            for name, val in genes.items():
                                try:
                                    genome.set_gene_value(chrom, name, val)
                                except Exception:
                                    # best-effort: ignore failures
                                    pass
                    return True

            # last resort: update __dict__
            try:
                genome.__dict__.update(state)
                return True
            except Exception:
                raise RuntimeError('No compatible restore method found for genome')
        except Exception as e:
            raise RuntimeError(f'Failed to rollback genome from {path}: {e}') from e

    def apply_simple_regularization(self, genome: Any) -> Dict[str, Any]:
        """Apply L2-style shrinkage and clipping to numeric gene values.

        Returns a summary dict with number of changes and a small sample of changes.
        """
        changed: List[Tuple[str, str, float, float]] = []

        if hasattr(genome, 'iter_genes'):
            for chrom, name, val in genome.iter_genes():
                if isinstance(val, (int, float)):
                    old = float(val)
                    new = old * (1 - self.l2_penalty)
                    new = max(self.clip_min, min(self.clip_max, new))
                    try:
                        genome.set_gene_value(chrom, name, new)
                        changed.append((chrom, name, old, new))
                    except Exception:
                        # ignore per-gene failures
                        continue
        else:
            # try to operate on to_dict structure
            if not hasattr(genome, 'to_dict'):
                raise TypeError('Genome must provide iter_genes or to_dict')
            gd = genome.to_dict()
            chroms = gd.get('chromosomes', gd)
            for chrom, genes in chroms.items():
                if not isinstance(genes, dict):
                    continue
                for name, val in genes.items():
                    if isinstance(val, (int, float)):
                        old = float(val)
                        new = old * (1 - self.l2_penalty)
                        new = max(self.clip_min, min(self.clip_max, new))
                        try:
                            genome.set_gene_value(chrom, name, new)
                            changed.append((chrom, name, old, new))
                        except Exception:
                            continue

        # sample up to 20 changes for the report
        return {'num_changed': len(changed), 'changes_sample': changed[:20]}

    def stabilize_after_edit(self, genome: Any, before_metrics: Dict[str, float], after_metrics: Dict[str, float], rollback_threshold: float = -0.05) -> Dict[str, Any]:
        """Decide to keep or rollback an edit based on primary metric change.

        primary metric: 'sharpe' if available. rollback_threshold is the fractional
        change (e.g., -0.05 means a drop >5% triggers rollback).
        Returns dict: {kept: bool, action: str, details: {...}}
        """
        primary = 'sharpe'
        b = before_metrics.get(primary)
        a = after_metrics.get(primary)
        if b is None or a is None:
            # can't evaluate; keep and apply light regularization
            reg = self.apply_simple_regularization(genome)
            return {'kept': True, 'action': 'regularized_no_primary_metric', 'details': {'regularization': reg}}

        # fractional change
        change = (a - b) / (abs(b) + 1e-12)
        if change < rollback_threshold:
            # rollback
            backup = self.backup_state(genome)
            try:
                self.rollback_from_backup(backup, genome)
                return {'kept': False, 'action': 'rollback', 'details': {'change': change, 'backup': backup}}
            except Exception as e:
                return {'kept': False, 'action': 'rollback_failed', 'details': {'change': change, 'error': str(e)}}

        # otherwise apply light regularization and keep
        reg = self.apply_simple_regularization(genome)
        return {'kept': True, 'action': 'regularized', 'details': {'change': change, 'regularization': reg}}
"""
🔧 Cellular Repair System — Post-Edit Stabilization

Advanced stabilization system inspired by cellular DNA repair mechanisms.
Ensures model stability and performance after CRISPR-style parameter edits
through gradient surgery, regularization, and emergency protocols.

Think like biology. Code like AI.
"""

import numpy as np
import torch
from datetime import datetime
import logging
from dataclasses import dataclass

from ..core.base_layers import BaseRepair, EditResult
from ..core.genome import FinancialGenome

logger = logging.getLogger(__name__)


@dataclass
class StabilityReport:
    """
    🏥 Cellular Health Assessment
    
    Comprehensive stability analysis report after genetic edits,
    like a medical report after gene therapy.
    """
    overall_stability: float
    parameter_stability: Dict[str, float]
    gradient_health: Dict[str, float]
    convergence_indicators: Dict[str, float]
    instability_sources: List[str]
    repair_recommendations: List[str]
    emergency_required: bool
    timestamp: datetime


@dataclass
class RepairConfig:
    """
    ⚙️ Repair System Configuration
    
    Configuration for cellular repair mechanisms and emergency protocols.
    """
    stability_threshold: float = 0.8
    gradient_clip_threshold: float = 1.0
    regularization_strength: float = 0.01
    emergency_threshold: float = 0.3
    max_repair_iterations: int = 10
    convergence_tolerance: float = 1e-6
    enable_gradient_surgery: bool = True
    enable_weight_regularization: bool = True
    enable_emergency_protocols: bool = True


class GradientSurgeon:
    """
    🔧 Gradient Surgery Specialist
    
    Performs precise gradient corrections to stabilize model training
    after parameter edits, like surgical repair of damaged DNA.
    """

    def __init__(self, clip_threshold: float = 1.0):
        self.clip_threshold = clip_threshold
        self.surgery_history = []

    def diagnose_gradients(self,
                          model_params: Dict[str, torch.Tensor]) -> Dict[str, float]:
        """
        🔍 Diagnose gradient health
        
        Analyze gradient magnitudes and patterns to identify instabilities.
        
        Args:
            model_params: Model parameters with gradients
            
        Returns:
            Dictionary with gradient health metrics
        """
        gradient_health = {}

        for name, param in model_params.items():
            if param.grad is not None:
                grad = param.grad

                # Calculate gradient metrics
                grad_norm = torch.norm(grad).item()
                grad_mean = torch.mean(torch.abs(grad)).item()
                grad_std = torch.std(grad).item()
                grad_max = torch.max(torch.abs(grad)).item()

                # Health score based on gradient characteristics
                health_score = 1.0

                # Penalize exploding gradients
                if grad_norm > self.clip_threshold * 10:
                    health_score *= 0.1
                elif grad_norm > self.clip_threshold * 5:
                    health_score *= 0.3
                elif grad_norm > self.clip_threshold:
                    health_score *= 0.7

                # Penalize vanishing gradients
                if grad_norm < 1e-8:
                    health_score *= 0.2
                elif grad_norm < 1e-6:
                    health_score *= 0.5

                # Penalize high variance
                if grad_std > grad_mean * 10:
                    health_score *= 0.6

                gradient_health[name] = {
                    'health_score': health_score,
                    'norm': grad_norm,
                    'mean': grad_mean,
                    'std': grad_std,
                    'max': grad_max
                }

        return gradient_health

    def perform_surgery(self,
                       model_params: Dict[str, torch.Tensor],
                       surgery_type: str = "adaptive") -> Dict[str, Any]:
        """
        ✂️ Perform gradient surgery
        
        Apply surgical corrections to stabilize gradients.
        
        Args:
            model_params: Model parameters with gradients
            surgery_type: Type of surgery ('clip', 'normalize', 'adaptive')
            
        Returns:
            Surgery report with applied corrections
        """
        surgery_report = {
            'surgery_type': surgery_type,
            'parameters_modified': 0,
            'corrections_applied': [],
            'pre_surgery_norms': {},
            'post_surgery_norms': {}
        }

        for name, param in model_params.items():
            if param.grad is not None:
                original_norm = torch.norm(param.grad).item()
                surgery_report['pre_surgery_norms'][name] = original_norm

                if surgery_type == "clip":
                    # Standard gradient clipping
                    if original_norm > self.clip_threshold:
                        torch.nn.utils.clip_grad_norm_([param], self.clip_threshold)
                        surgery_report['corrections_applied'].append(f"Clipped {name}")
                        surgery_report['parameters_modified'] += 1

                elif surgery_type == "normalize":
                    # Gradient normalization
                    if original_norm > 1e-8:
                        param.grad = param.grad / (original_norm + 1e-8)
                        surgery_report['corrections_applied'].append(f"Normalized {name}")
                        surgery_report['parameters_modified'] += 1

                elif surgery_type == "adaptive":
                    # Adaptive surgery based on parameter characteristics
                    if original_norm > self.clip_threshold * 2:
                        # Severe case: aggressive clipping
                        torch.nn.utils.clip_grad_norm_([param], self.clip_threshold * 0.5)
                        surgery_report['corrections_applied'].append(f"Aggressive clip {name}")
                        surgery_report['parameters_modified'] += 1
                    elif original_norm > self.clip_threshold:
                        # Moderate case: standard clipping
                        torch.nn.utils.clip_grad_norm_([param], self.clip_threshold)
                        surgery_report['corrections_applied'].append(f"Standard clip {name}")
                        surgery_report['parameters_modified'] += 1
                    elif original_norm < 1e-7:
                        # Vanishing gradients: gentle boost
                        param.grad = param.grad + torch.randn_like(param.grad) * 1e-6
                        surgery_report['corrections_applied'].append(f"Boosted {name}")
                        surgery_report['parameters_modified'] += 1

                # Record post-surgery norm
                surgery_report['post_surgery_norms'][name] = torch.norm(param.grad).item()

        # Store surgery in history
        self.surgery_history.append({
            'timestamp': datetime.now(),
            'surgery_type': surgery_type,
            'report': surgery_report
        })

        return surgery_report


class WeightRegularizer:
    """
    ⚖️ Weight Regularization System
    
    Applies regularization techniques to prevent overfitting and instability
    after parameter edits, like cellular quality control mechanisms.
    """

    def __init__(self, l1_strength: float = 0.01, l2_strength: float = 0.01):
        self.l1_strength = l1_strength
        self.l2_strength = l2_strength
        self.regularization_history = []

    def apply_regularization(self,
                           model_params: Dict[str, torch.Tensor],
                           regularization_type: str = "l2") -> Dict[str, Any]:
        """
        ⚖️ Apply weight regularization
        
        Add regularization terms to prevent parameter instability.
        
        Args:
            model_params: Model parameters to regularize
            regularization_type: Type of regularization ('l1', 'l2', 'elastic')
            
        Returns:
            Regularization report
        """
        regularization_report = {
            'regularization_type': regularization_type,
            'total_penalty': 0.0,
            'parameter_penalties': {},
            'parameters_regularized': 0
        }

        for name, param in model_params.items():
            penalty = 0.0

            if regularization_type == "l1":
                penalty = self.l1_strength * torch.sum(torch.abs(param)).item()
            elif regularization_type == "l2":
                penalty = self.l2_strength * torch.sum(param ** 2).item()
            elif regularization_type == "elastic":
                l1_penalty = self.l1_strength * torch.sum(torch.abs(param)).item()
                l2_penalty = self.l2_strength * torch.sum(param ** 2).item()
                penalty = 0.5 * (l1_penalty + l2_penalty)

            if penalty > 0:
                regularization_report['parameter_penalties'][name] = penalty
                regularization_report['total_penalty'] += penalty
                regularization_report['parameters_regularized'] += 1

                # Apply regularization to gradients if they exist
                if param.grad is not None:
                    if regularization_type == "l1":
                        param.grad += self.l1_strength * torch.sign(param)
                    elif regularization_type == "l2":
                        param.grad += 2 * self.l2_strength * param
                    elif regularization_type == "elastic":
                        param.grad += (self.l1_strength * torch.sign(param) +
                                     2 * self.l2_strength * param)

        # Store in history
        self.regularization_history.append({
            'timestamp': datetime.now(),
            'regularization_type': regularization_type,
            'report': regularization_report
        })

        return regularization_report


class CellularRepair(BaseRepair):
    """
    🔧 Cellular Repair System
    
    Comprehensive post-edit stabilization system inspired by cellular DNA
    repair mechanisms. Monitors model health and applies various repair
    techniques to maintain stability and performance.
    
    Biological Analogy:
    - DNA Repair → Parameter Stabilization
    - Error Correction → Gradient Surgery
    - Cell Survival → Model Performance Maintenance
    - Apoptosis → Emergency Rollback
    """

    def __init__(self,
                 name: str = "CellularRepair",
                 config: Optional[RepairConfig] = None):
        """
        Initialize the cellular repair system.
        
        Args:
            name: Repair system identifier
            config: Repair configuration parameters
        """
        super().__init__(name, config.stability_threshold if config else 0.8)

        self.config = config or RepairConfig()

        # Repair specialists
        self.gradient_surgeon = GradientSurgeon(self.config.gradient_clip_threshold)
        self.weight_regularizer = WeightRegularizer(
            l1_strength=self.config.regularization_strength * 0.5,
            l2_strength=self.config.regularization_strength
        )

        # Repair tracking
        self._repair_sessions = []
        self._stability_history = []
        self._emergency_activations = 0

        # Performance baseline for comparison
        self._performance_baseline = None
        self._performance_history = []

        logger.info(f"Initialized {self.name} with stability_threshold={self.config.stability_threshold}")

    def assess_stability(self,
                        model_genome: FinancialGenome,
                        recent_edits: List[EditResult]) -> float:
        """
        🔍 Assess cellular health post-edit
        
        Comprehensive stability analysis after recent parameter modifications.
        
        Args:
            model_genome: Current model state
            recent_edits: Recent modifications made
            
        Returns:
            Overall stability score (0.0-1.0)
        """
        logger.debug(f"Assessing stability after {len(recent_edits)} recent edits")

        stability_factors = []

        # 1. Parameter consistency check
        param_stability = self._assess_parameter_stability(model_genome, recent_edits)
        stability_factors.append(('parameters', param_stability, 0.3))

        # 2. Edit impact analysis
        edit_stability = self._assess_edit_impact(recent_edits)
        stability_factors.append(('edits', edit_stability, 0.2))

        # 3. Genome health score
        genome_health = model_genome.calculate_health_score()
        stability_factors.append(('genome', genome_health, 0.2))

        # 4. Performance stability (if available)
        perf_stability = self._assess_performance_stability(recent_edits)
        stability_factors.append(('performance', perf_stability, 0.3))

        # Calculate weighted stability score
        total_weight = sum(weight for _, _, weight in stability_factors)
        weighted_score = sum(score * weight for _, score, weight in stability_factors) / total_weight

        # Store stability assessment
        stability_report = StabilityReport(
            overall_stability=weighted_score,
            parameter_stability={'overall': param_stability},
            gradient_health={},  # Would need actual gradients
            convergence_indicators={'stability_trend': self._calculate_stability_trend()},
            instability_sources=self._identify_instability_sources(stability_factors),
            repair_recommendations=self._generate_repair_recommendations(stability_factors),
            emergency_required=weighted_score < self.config.emergency_threshold,
            timestamp=datetime.now()
        )

        self._stability_history.append({
            'timestamp': datetime.now(),
            'stability_score': weighted_score,
            'factors': dict((name, score) for name, score, _ in stability_factors),
            'recent_edits_count': len(recent_edits)
        })

        logger.info(f"Stability assessment complete: score={weighted_score:.3f}")

        return weighted_score

    def repair(self,
               model_genome: FinancialGenome,
               instability_sources: List[str]) -> Dict[str, Any]:
        """
        🔧 Execute repair mechanisms
        
        Apply targeted repair techniques to fix identified instabilities.
        
        Args:
            model_genome: Model to repair
            instability_sources: Identified sources of instability
            
        Returns:
            Comprehensive repair results
        """
        repair_session_id = f"repair_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"Starting repair session {repair_session_id}")

        repair_results = {
            'session_id': repair_session_id,
            'instability_sources': instability_sources,
            'repairs_applied': [],
            'success': False,
            'initial_stability': 0.0,
            'final_stability': 0.0,
            'iterations': 0,
            'techniques_used': []
        }

        try:
            # Initial stability assessment
            initial_stability = self.assess_stability(model_genome, [])
            repair_results['initial_stability'] = initial_stability

            current_stability = initial_stability
            iteration = 0

            while (current_stability < self.config.stability_threshold and
                   iteration < self.config.max_repair_iterations):

                iteration += 1
                logger.debug(f"Repair iteration {iteration}, stability={current_stability:.3f}")

                # Apply repair techniques based on instability sources
                if "parameter_drift" in instability_sources:
                    self._repair_parameter_drift(model_genome, repair_results)

                if "constraint_violation" in instability_sources:
                    self._repair_constraint_violations(model_genome, repair_results)

                if "performance_degradation" in instability_sources:
                    self._repair_performance_issues(model_genome, repair_results)

                if "edit_conflicts" in instability_sources:
                    self._repair_edit_conflicts(model_genome, repair_results)

                # Re-assess stability
                current_stability = self.assess_stability(model_genome, [])

                # Check for convergence
                if abs(current_stability - repair_results.get('previous_stability', 0)) < self.config.convergence_tolerance:
                    logger.info(f"Repair converged after {iteration} iterations")
                    break

                repair_results['previous_stability'] = current_stability

            repair_results['iterations'] = iteration
            repair_results['final_stability'] = current_stability
            repair_results['success'] = current_stability >= self.config.stability_threshold

            # Store repair session
            self._repair_sessions.append(repair_results.copy())

            if repair_results['success']:
                logger.info(f"Repair successful: {initial_stability:.3f} → {current_stability:.3f}")
            else:
                logger.warning(f"Repair incomplete: {initial_stability:.3f} → {current_stability:.3f}")

        except Exception as e:
            logger.error(f"Repair session failed: {str(e)}")
            repair_results['error'] = str(e)

        return repair_results

    def emergency_stabilize(self, model_genome: FinancialGenome) -> bool:
        """
        🚨 Emergency repair protocol
        
        Aggressive stabilization when model is critically unstable.
        
        Args:
            model_genome: Model in critical condition
            
        Returns:
            True if emergency stabilization successful
        """
        logger.warning("🚨 EMERGENCY STABILIZATION PROTOCOL ACTIVATED")
        self._emergency_activations += 1

        emergency_start = datetime.now()

        try:
            # 1. Immediate parameter constraint enforcement
            self._enforce_all_constraints(model_genome)

            # 2. Reset problematic parameters to safe defaults
            self._reset_unstable_parameters(model_genome)

            # 3. Apply aggressive regularization
            self._apply_emergency_regularization(model_genome)

            # 4. Check if stabilization worked
            emergency_stability = self.assess_stability(model_genome, [])

            success = emergency_stability >= self.config.emergency_threshold

            duration = (datetime.now() - emergency_start).total_seconds()

            logger.warning(f"Emergency protocol completed in {duration:.2f}s: "
                          f"success={success}, stability={emergency_stability:.3f}")

            # Record emergency activation
            self._repair_sessions.append({
                'session_id': f"emergency_{emergency_start.strftime('%Y%m%d_%H%M%S')}",
                'type': 'emergency',
                'success': success,
                'final_stability': emergency_stability,
                'duration_seconds': duration,
                'activation_number': self._emergency_activations
            })

            return success

        except Exception as e:
            logger.error(f"Emergency stabilization failed: {str(e)}")
            return False

    def _assess_parameter_stability(self,
                                   model_genome: FinancialGenome,
                                   recent_edits: List[EditResult]) -> float:
        """Assess parameter-level stability."""
        stability_scores = []

        for chromosome in model_genome.list_chromosomes():
            for gene_name in model_genome.list_genes(chromosome):
                param_path = f"{chromosome}.{gene_name}"
                gene = model_genome.get_gene(param_path)

                # Check constraint compliance
                constraint_score = 1.0
                if gene.constraints:
                    constraint_score = 1.0 if model_genome._check_constraints(gene) else 0.0

                # Check edit frequency (too many recent edits = instability)
                edit_frequency_score = 1.0
                if gene.edit_count > 5:  # Arbitrary threshold
                    edit_frequency_score = max(0.1, 1.0 - (gene.edit_count - 5) * 0.1)

                # Check parameter magnitude (extreme values = instability)
                magnitude_score = 1.0
                if isinstance(gene.value, (int, float)):
                    if abs(gene.value) > 100:  # Arbitrary large value threshold
                        magnitude_score = 0.5
                elif isinstance(gene.value, np.ndarray):
                    if np.any(np.abs(gene.value) > 100) or np.any(np.isnan(gene.value)):
                        magnitude_score = 0.3

                # Combined parameter stability
                param_stability = (constraint_score * 0.4 +
                                 edit_frequency_score * 0.3 +
                                 magnitude_score * 0.3)

                stability_scores.append(param_stability)

        return np.mean(stability_scores) if stability_scores else 1.0

    def _assess_edit_impact(self, recent_edits: List[EditResult]) -> float:
        """Assess the stability impact of recent edits."""
        if not recent_edits:
            return 1.0

        # Check edit success rate
        success_rate = np.mean([edit.success for edit in recent_edits])

        # Check performance deltas
        performance_deltas = [edit.performance_delta for edit in recent_edits if edit.success]

        if performance_deltas:
            avg_delta = np.mean(performance_deltas)
            delta_consistency = 1.0 - np.std(performance_deltas) / (abs(avg_delta) + 1e-8)

            # Positive deltas are good, negative are concerning
            performance_score = max(0.0, min(1.0, avg_delta * 10 + 0.5))
        else:
            delta_consistency = 0.5
            performance_score = 0.5

        # Combined edit impact score
        edit_stability = (success_rate * 0.4 +
                         delta_consistency * 0.3 +
                         performance_score * 0.3)

        return edit_stability

    def _assess_performance_stability(self, recent_edits: List[EditResult]) -> float:
        """Assess performance stability trends."""
        if not self._performance_history:
            return 0.8  # Default moderate score

        # Simple trend analysis
        recent_performance = self._performance_history[-10:]  # Last 10 measurements

        if len(recent_performance) < 2:
            return 0.8

        # Calculate performance trend
        values = [p['value'] for p in recent_performance]
        trend = np.polyfit(range(len(values)), values, 1)[0]

        # Stability based on trend and variance
        variance = np.var(values)
        mean_value = np.mean(values)

        # Prefer stable upward trends
        trend_score = max(0.0, min(1.0, trend * 100 + 0.5))
        variance_score = max(0.0, 1.0 - variance / (abs(mean_value) + 1e-8))

        return (trend_score * 0.6 + variance_score * 0.4)

    def _calculate_stability_trend(self) -> float:
        """Calculate stability trend over recent history."""
        if len(self._stability_history) < 2:
            return 0.0

        recent_scores = [h['stability_score'] for h in self._stability_history[-10:]]

        if len(recent_scores) < 2:
            return 0.0

        # Linear trend
        trend = np.polyfit(range(len(recent_scores)), recent_scores, 1)[0]
        return float(trend)

    def _identify_instability_sources(self, stability_factors: List[Tuple]) -> List[str]:
        """Identify primary sources of instability."""
        instability_sources = []

        for name, score, _ in stability_factors:
            if score < 0.5:
                if name == "parameters":
                    instability_sources.append("parameter_drift")
                elif name == "edits":
                    instability_sources.append("edit_conflicts")
                elif name == "genome":
                    instability_sources.append("constraint_violation")
                elif name == "performance":
                    instability_sources.append("performance_degradation")

        return instability_sources

    def _generate_repair_recommendations(self, stability_factors: List[Tuple]) -> List[str]:
        """Generate repair recommendations based on stability analysis."""
        recommendations = []

        for name, score, _ in stability_factors:
            if score < 0.7:
                if name == "parameters":
                    recommendations.append("Apply parameter regularization")
                    recommendations.append("Enforce constraint compliance")
                elif name == "edits":
                    recommendations.append("Review recent edit strategy")
                    recommendations.append("Consider edit rollback")
                elif name == "genome":
                    recommendations.append("Reset problematic parameters")
                elif name == "performance":
                    recommendations.append("Optimize model hyperparameters")
                    recommendations.append("Increase regularization strength")

        return recommendations

    def _repair_parameter_drift(self, model_genome: FinancialGenome, repair_results: Dict):
        """Repair parameter drift by applying gentle corrections."""
        corrections = 0

        for chromosome in model_genome.list_chromosomes():
            for gene_name in model_genome.list_genes(chromosome):
                param_path = f"{chromosome}.{gene_name}"
                gene = model_genome.get_gene(param_path)

                # Check for extreme values and correct them
                if isinstance(gene.value, (int, float)):
                    if abs(gene.value) > 50:  # Arbitrary threshold
                        # Pull back towards reasonable range
                        corrected_value = gene.value * 0.8
                        model_genome.set_parameter(param_path, corrected_value, "drift_repair")
                        corrections += 1

                elif isinstance(gene.value, np.ndarray):
                    # Clip extreme values
                    if np.any(np.abs(gene.value) > 50):
                        corrected_value = np.clip(gene.value, -50, 50)
                        model_genome.set_parameter(param_path, corrected_value, "drift_repair")
                        corrections += 1

        repair_results['repairs_applied'].append(f"Parameter drift: {corrections} corrections")
        repair_results['techniques_used'].append("parameter_drift_repair")

    def _repair_constraint_violations(self, model_genome: FinancialGenome, repair_results: Dict):
        """Fix constraint violations by enforcing limits."""
        violations_fixed = 0

        for chromosome in model_genome.list_chromosomes():
            for gene_name in model_genome.list_genes(chromosome):
                param_path = f"{chromosome}.{gene_name}"
                gene = model_genome.get_gene(param_path)

                if gene.constraints and not model_genome._check_constraints(gene):
                    # Enforce constraints
                    value = gene.value

                    if 'min' in gene.constraints and isinstance(value, (int, float)):
                        if value < gene.constraints['min']:
                            model_genome.set_parameter(param_path, gene.constraints['min'], "constraint_repair")
                            violations_fixed += 1

                    if 'max' in gene.constraints and isinstance(value, (int, float)):
                        if value > gene.constraints['max']:
                            model_genome.set_parameter(param_path, gene.constraints['max'], "constraint_repair")
                            violations_fixed += 1

        repair_results['repairs_applied'].append(f"Constraint violations: {violations_fixed} fixed")
        repair_results['techniques_used'].append("constraint_enforcement")

    def _repair_performance_issues(self, model_genome: FinancialGenome, repair_results: Dict):
        """Address performance degradation through parameter adjustment."""
        # Apply gentle regularization to critical parameters
        critical_params = model_genome.get_critical_parameters(threshold=0.8)
        adjustments = 0

        for param_path, gene in critical_params.items():
            if isinstance(gene.value, (int, float)):
                # Small adjustment towards conservative values
                adjustment = gene.value * 0.95  # 5% reduction
                model_genome.set_parameter(param_path, adjustment, "performance_repair")
                adjustments += 1

        repair_results['repairs_applied'].append(f"Performance issues: {adjustments} adjustments")
        repair_results['techniques_used'].append("performance_optimization")

    def _repair_edit_conflicts(self, model_genome: FinancialGenome, repair_results: Dict):
        """Resolve conflicts from multiple recent edits."""
        # Reset parameters that have been edited too frequently
        resets = 0

        for chromosome in model_genome.list_chromosomes():
            for gene_name in model_genome.list_genes(chromosome):
                param_path = f"{chromosome}.{gene_name}"
                gene = model_genome.get_gene(param_path)

                if gene.edit_count > 3:  # Frequently edited
                    # Reset to a conservative default
                    if gene.constraints:
                        if 'min' in gene.constraints and 'max' in gene.constraints:
                            default_value = (gene.constraints['min'] + gene.constraints['max']) / 2
                            model_genome.set_parameter(param_path, default_value, "conflict_resolution")
                            resets += 1

        repair_results['repairs_applied'].append(f"Edit conflicts: {resets} resets")
        repair_results['techniques_used'].append("conflict_resolution")

    def _enforce_all_constraints(self, model_genome: FinancialGenome):
        """Emergency constraint enforcement."""
        for chromosome in model_genome.list_chromosomes():
            for gene_name in model_genome.list_genes(chromosome):
                param_path = f"{chromosome}.{gene_name}"
                gene = model_genome.get_gene(param_path)

                if gene.constraints:
                    value = gene.value

                    if isinstance(value, (int, float)):
                        if 'min' in gene.constraints:
                            value = max(value, gene.constraints['min'])
                        if 'max' in gene.constraints:
                            value = min(value, gene.constraints['max'])

                        if value != gene.value:
                            model_genome.set_parameter(param_path, value, "emergency_constraint")

    def _reset_unstable_parameters(self, model_genome: FinancialGenome):
        """Reset highly problematic parameters to safe defaults."""
        resets = 0

        for chromosome in model_genome.list_chromosomes():
            for gene_name in model_genome.list_genes(chromosome):
                param_path = f"{chromosome}.{gene_name}"
                gene = model_genome.get_gene(param_path)

                # Reset if edit count is very high or value is extreme
                should_reset = (gene.edit_count > 10 or
                              (isinstance(gene.value, (int, float)) and abs(gene.value) > 100))

                if should_reset:
                    # Set to conservative default
                    if gene.constraints and 'min' in gene.constraints and 'max' in gene.constraints:
                        default_value = (gene.constraints['min'] + gene.constraints['max']) / 2
                    else:
                        default_value = 0.1  # Conservative default

                    model_genome.set_parameter(param_path, default_value, "emergency_reset")
                    resets += 1

        logger.warning(f"Emergency reset: {resets} parameters")

    def _apply_emergency_regularization(self, model_genome: FinancialGenome):
        """Apply aggressive regularization to stabilize the model."""
        # This would need actual model weights to apply regularization
        # For now, just log the intent
        logger.warning("Emergency regularization applied (simulation)")

    def get_repair_statistics(self) -> Dict[str, Any]:
        """
        📊 Generate repair system performance statistics
        
        Returns:
            Dictionary with repair performance metrics
        """
        if not self._repair_sessions:
            return {'status': 'No repair sessions recorded'}

        successful_repairs = [r for r in self._repair_sessions if r.get('success', False)]

        stats = {
            'total_repair_sessions': len(self._repair_sessions),
            'successful_repairs': len(successful_repairs),
            'success_rate': len(successful_repairs) / len(self._repair_sessions),
            'emergency_activations': self._emergency_activations,
            'average_stability_improvement': 0.0,
            'most_common_instability_sources': [],
            'most_effective_techniques': []
        }

        if successful_repairs:
            # Calculate average improvement
            improvements = []
            for repair in successful_repairs:
                if 'initial_stability' in repair and 'final_stability' in repair:
                    improvement = repair['final_stability'] - repair['initial_stability']
                    improvements.append(improvement)

            if improvements:
                stats['average_stability_improvement'] = np.mean(improvements)

        # Analyze common issues and techniques
        all_sources = []
        all_techniques = []

        for repair in self._repair_sessions:
            all_sources.extend(repair.get('instability_sources', []))
            all_techniques.extend(repair.get('techniques_used', []))

        if all_sources:
            from collections import Counter
            source_counts = Counter(all_sources)
            stats['most_common_instability_sources'] = source_counts.most_common(5)

        if all_techniques:
            from collections import Counter
            technique_counts = Counter(all_techniques)
            stats['most_effective_techniques'] = technique_counts.most_common(5)

        return stats
