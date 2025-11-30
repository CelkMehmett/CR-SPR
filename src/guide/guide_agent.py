"""
🧭 Attention Guide — Guide-RNA Targeting System

Advanced parameter targeting system inspired by CRISPR guide-RNA mechanisms.
Uses attention mechanisms and importance scoring to identify precise model
parameters that require editing for optimal performance.

Think like biology. Code like AI.
"""

import numpy as np
import torch
import torch.nn as nn
from typing import Dict, List, Any
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass

from ..core.base_layers import BaseGuide, TargetSite, DetectionResult
from ..core.genome import FinancialGenome, ParameterGene

logger = logging.getLogger(__name__)


@dataclass
class TargetingContext:
    """
    🎯 PAM Sequence Context
    
    Contextual information for parameter targeting, like the PAM sequence
    that guide-RNA uses to recognize correct binding sites.
    """
    parameter_path: str
    local_neighborhood: Dict[str, Any]
    dependency_graph: Dict[str, List[str]]
    performance_impact: float
    stability_risk: float
    edit_history: List[Dict[str, Any]]


class AttentionTargeting(nn.Module):
    """
    🧠 Neural Attention Mechanism for Parameter Targeting
    
    Deep learning model that learns to identify which parameters
    need editing based on detection results and model state.
    """

    def __init__(self,
                 input_dim: int,
                 hidden_dim: int = 128,
                 num_heads: int = 8,
                 num_layers: int = 3):
        """
        Initialize the attention-based targeting system.
        
        Args:
            input_dim: Dimension of input features
            hidden_dim: Hidden layer dimension
            num_heads: Number of attention heads
            num_layers: Number of transformer layers
        """
        super().__init__()

        self.input_dim = input_dim
        self.hidden_dim = hidden_dim

        # Input projection
        self.input_projection = nn.Linear(input_dim, hidden_dim)

        # Multi-head attention layers
        self.attention_layers = nn.ModuleList([
            nn.MultiheadAttention(hidden_dim, num_heads, batch_first=True)
            for _ in range(num_layers)
        ])

        # Layer normalization
        self.layer_norms = nn.ModuleList([
            nn.LayerNorm(hidden_dim) for _ in range(num_layers)
        ])

        # Output layers for targeting decisions
        self.target_scorer = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid()
        )

        # Priority classifier
        self.priority_classifier = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 5),  # 5 priority levels
            nn.Softmax(dim=-1)
        )

        # Edit type classifier
        self.edit_type_classifier = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 3),  # replace, adjust, remove
            nn.Softmax(dim=-1)
        )

    def forward(self,
                parameter_features: torch.Tensor,
                detection_context: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Forward pass through the attention targeting network.
        
        Args:
            parameter_features: Features for each parameter [batch, params, features]
            detection_context: Detection context vector [batch, context_dim]
            
        Returns:
            Dictionary with targeting predictions
        """
        batch_size, num_params, _ = parameter_features.shape

        # Project inputs to hidden dimension
        x = self.input_projection(parameter_features)

        # Add detection context to each parameter
        context_expanded = detection_context.unsqueeze(1).expand(-1, num_params, -1)
        if context_expanded.shape[-1] == x.shape[-1]:
            x = x + context_expanded

        # Apply attention layers
        for attention, norm in zip(self.attention_layers, self.layer_norms):
            attended, _ = attention(x, x, x)
            x = norm(x + attended)

        # Generate predictions
        target_scores = self.target_scorer(x).squeeze(-1)  # [batch, params]
        priorities = self.priority_classifier(x)           # [batch, params, 5]
        edit_types = self.edit_type_classifier(x)          # [batch, params, 3]

        return {
            'target_scores': target_scores,
            'priorities': priorities,
            'edit_types': edit_types,
            'attention_weights': x  # Return attention representations
        }


class AttentionGuide(BaseGuide):
    """
    🧭 Attention-Based Guide-RNA System
    
    Advanced targeting system that uses neural attention mechanisms
    to identify precise parameters requiring edits. Like guide-RNA
    binding to specific DNA sequences, this system targets model
    parameters with high precision and confidence.
    
    Biological Analogy:
    - Guide-RNA → Attention Mechanism
    - PAM Sequence → Parameter Context
    - Binding Specificity → Targeting Confidence
    - Off-target Effects → Unintended Parameter Changes
    """

    def __init__(self,
                 name: str = "AttentionGuide",
                 max_targets: int = 5,
                 min_confidence: float = 0.7,
                 attention_dim: int = 128,
                 learning_rate: float = 0.001):
        """
        Initialize the attention-based guide system.
        
        Args:
            name: Guide identifier
            max_targets: Maximum simultaneous targets
            min_confidence: Minimum confidence for target selection
            attention_dim: Attention mechanism dimension
            learning_rate: Learning rate for neural components
        """
        super().__init__(name, max_targets)

        self.min_confidence = min_confidence
        self.attention_dim = attention_dim
        self.learning_rate = learning_rate

        # Neural targeting system
        self.attention_model = None
        self.optimizer = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        # Parameter analysis components
        self._parameter_cache = {}
        self._importance_scores = {}
        self._dependency_graph = {}
        self._targeting_history = []

        # Targeting strategies
        self.targeting_strategies = {
            'performance_driven': self._performance_driven_targeting,
            'stability_focused': self._stability_focused_targeting,
            'adaptive_hybrid': self._adaptive_hybrid_targeting
        }

        self.current_strategy = 'adaptive_hybrid'

        logger.info(f"Initialized {self.name} with max_targets={max_targets}")

    def initialize_attention_model(self, input_dim: int) -> None:
        """
        🧠 Initialize the neural attention targeting system.
        
        Args:
            input_dim: Dimension of parameter feature vectors
        """
        self.attention_model = AttentionTargeting(
            input_dim=input_dim,
            hidden_dim=self.attention_dim
        ).to(self.device)

        self.optimizer = torch.optim.Adam(
            self.attention_model.parameters(),
            lr=self.learning_rate
        )

        logger.info(f"Initialized attention model with input_dim={input_dim}")

    def identify_targets(self,
                        detection_result: DetectionResult,
                        model_genome: FinancialGenome) -> List[TargetSite]:
        """
        🎯 Bind to target parameter sequences
        
        Analyze detection results and model state to identify specific
        parameters that should be modified. Like guide-RNA binding to
        complementary DNA sequences with high specificity.
        
        Args:
            detection_result: Anomaly detection results
            model_genome: Current model parameter state
            
        Returns:
            List of validated target sites ranked by priority
        """
        logger.info(f"Identifying targets for anomaly score {detection_result.anomaly_score:.3f}")

        # Extract parameter features from genome
        parameter_features = self._extract_parameter_features(model_genome)

        # Create detection context vector
        detection_context = self._create_detection_context(detection_result)

        # Initialize attention model if needed
        if self.attention_model is None and len(parameter_features) > 0:
            feature_dim = len(list(parameter_features.values())[0])
            self.initialize_attention_model(feature_dim + len(detection_context))

        # Generate candidate targets using multiple strategies
        candidate_targets = []

        # Strategy 1: Attention-based targeting (if model is available)
        if self.attention_model is not None:
            attention_targets = self._attention_based_targeting(
                parameter_features, detection_context, model_genome
            )
            candidate_targets.extend(attention_targets)

        # Strategy 2: Rule-based targeting (always available)
        rule_targets = self._rule_based_targeting(detection_result, model_genome)
        candidate_targets.extend(rule_targets)

        # Strategy 3: Importance-based targeting
        importance_targets = self._importance_based_targeting(detection_result, model_genome)
        candidate_targets.extend(importance_targets)

        # Remove duplicates and rank by confidence
        unique_targets = self._deduplicate_targets(candidate_targets)

        # Validate targets for safety
        validated_targets = self.validate_targets(unique_targets)

        # Select top targets up to max_targets
        final_targets = validated_targets[:self.max_targets]

        # Update targeting history
        self._update_targeting_history(detection_result, final_targets)

        logger.info(f"Selected {len(final_targets)} targets from {len(candidate_targets)} candidates")

        return final_targets

    def validate_targets(self, targets: List[TargetSite]) -> List[TargetSite]:
        """
        ✅ Validate target binding specificity
        
        Check target sites for safety, avoiding off-target effects
        and ensuring edit feasibility. Like validating guide-RNA
        specificity to prevent unintended cuts.
        
        Args:
            targets: Proposed target sites
            
        Returns:
            Filtered and validated target sites
        """
        validated_targets = []

        for target in targets:
            # Check confidence threshold
            if target.confidence < self.min_confidence:
                logger.debug(f"Rejecting target {target.parameter_path}: low confidence {target.confidence:.3f}")
                continue

            # Check for frozen parameters
            try:
                # This would need to be implemented to check if parameter is frozen
                # For now, assume all parameters are editable
                pass
            except Exception as e:
                logger.warning(f"Could not check parameter freeze status for {target.parameter_path}: {str(e)}")

            # Check for recent edits (avoid over-editing)
            if self._was_recently_edited(target.parameter_path):
                logger.debug(f"Rejecting target {target.parameter_path}: recently edited")
                continue

            # Check for parameter dependencies
            if self._has_critical_dependencies(target.parameter_path):
                # Reduce priority for parameters with many dependencies
                target.priority = max(1, target.priority - 1)
                target.rationale += " [has dependencies]"

            # Validate edit type feasibility
            if not self._is_edit_type_feasible(target):
                logger.debug(f"Rejecting target {target.parameter_path}: infeasible edit type {target.edit_type}")
                continue

            validated_targets.append(target)

        # Sort by priority and confidence
        validated_targets.sort(key=lambda t: (t.priority, t.confidence), reverse=True)

        logger.info(f"Validated {len(validated_targets)} targets from {len(targets)} proposals")

        return validated_targets

    def _extract_parameter_features(self, model_genome: FinancialGenome) -> Dict[str, List[float]]:
        """Extract numerical features from model parameters."""
        parameter_features = {}

        for chromosome in model_genome.list_chromosomes():
            for gene in model_genome.list_genes(chromosome):
                param_path = f"{chromosome}.{gene}"

                try:
                    gene_obj = model_genome.get_gene(param_path)
                    features = self._compute_parameter_features(gene_obj)
                    parameter_features[param_path] = features
                except Exception as e:
                    logger.warning(f"Failed to extract features for {param_path}: {str(e)}")

        return parameter_features

    def _compute_parameter_features(self, gene: ParameterGene) -> List[float]:
        """Compute feature vector for a single parameter."""
        features = []

        # Basic parameter properties
        features.append(float(gene.importance_score))
        features.append(float(gene.edit_count))
        features.append(1.0 if gene.frozen else 0.0)

        # Value-based features
        value = gene.value
        if isinstance(value, (int, float)):
            features.extend([
                float(value),
                float(abs(value)),
                float(np.log(abs(value) + 1e-8)),
                float(np.sign(value))
            ])
        elif isinstance(value, np.ndarray):
            features.extend([
                float(np.mean(value)),
                float(np.std(value)),
                float(np.min(value)),
                float(np.max(value)),
                float(np.median(value)),
                float(value.size)
            ])
        else:
            # Default features for unknown types
            features.extend([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

        # Constraint-based features
        if gene.constraints:
            features.append(1.0)  # Has constraints
            if 'min' in gene.constraints:
                features.append(float(gene.constraints['min']))
            else:
                features.append(0.0)
            if 'max' in gene.constraints:
                features.append(float(gene.constraints['max']))
            else:
                features.append(0.0)
        else:
            features.extend([0.0, 0.0, 0.0])  # No constraints

        # Temporal features
        time_since_edit = (datetime.now() - gene.last_modified).total_seconds() / 3600  # Hours
        features.append(float(time_since_edit))

        return features

    def _create_detection_context(self, detection_result: DetectionResult) -> List[float]:
        """Create context vector from detection results."""
        context = [
            float(detection_result.anomaly_score),
            1.0 if detection_result.is_anomalous else 0.0,
            float(detection_result.confidence)
        ]

        # Add metadata features if available
        if 'drift_analysis' in detection_result.metadata:
            drift = detection_result.metadata['drift_analysis']
            context.extend([
                1.0 if drift.get('has_drift', False) else 0.0,
                float(drift.get('drift_scores', {}).get('average', 0.0))
            ])
        else:
            context.extend([0.0, 0.0])

        # Add signature features if available
        if 'signature' in detection_result.metadata:
            signature = detection_result.metadata['signature']
            # Map severity to numeric
            severity_map = {'low': 0.25, 'medium': 0.5, 'high': 0.75, 'critical': 1.0}
            context.append(severity_map.get(signature.severity_level, 0.0))
        else:
            context.append(0.0)

        return context

    def _attention_based_targeting(self,
                                  parameter_features: Dict[str, List[float]],
                                  detection_context: List[float],
                                  model_genome: FinancialGenome) -> List[TargetSite]:
        """Use neural attention to identify target parameters."""
        if not parameter_features or self.attention_model is None:
            return []

        targets = []

        try:
            # Prepare features for neural network
            param_paths = list(parameter_features.keys())
            feature_matrix = np.array([parameter_features[path] for path in param_paths])

            # Combine parameter features with detection context
            context_array = np.array(detection_context)
            context_expanded = np.tile(context_array, (len(param_paths), 1))
            combined_features = np.concatenate([feature_matrix, context_expanded], axis=1)

            # Convert to tensors
            features_tensor = torch.FloatTensor(combined_features).unsqueeze(0).to(self.device)
            context_tensor = torch.FloatTensor(detection_context).unsqueeze(0).to(self.device)

            # Forward pass
            self.attention_model.eval()
            with torch.no_grad():
                predictions = self.attention_model(features_tensor, context_tensor)

            # Extract predictions
            target_scores = predictions['target_scores'].squeeze().cpu().numpy()
            priorities = predictions['priorities'].squeeze().cpu().numpy()
            edit_types = predictions['edit_types'].squeeze().cpu().numpy()

            # Create target sites from predictions
            edit_type_names = ['replace', 'adjust', 'remove']

            for i, param_path in enumerate(param_paths):
                score = float(target_scores[i])

                if score > 0.5:  # Threshold for targeting
                    priority_level = int(np.argmax(priorities[i]) + 1)
                    edit_type = edit_type_names[np.argmax(edit_types[i])]

                    # Get current and suggested target values
                    current_value = model_genome.get_parameter(param_path)
                    target_value = self._suggest_target_value(current_value, edit_type)

                    target = TargetSite(
                        parameter_path=param_path,
                        current_value=current_value,
                        target_value=target_value,
                        confidence=score,
                        priority=priority_level,
                        edit_type=edit_type,
                        rationale=f"Attention model prediction (score={score:.3f})"
                    )

                    targets.append(target)

        except Exception as e:
            logger.error(f"Attention-based targeting failed: {str(e)}")

        return targets

    def _rule_based_targeting(self,
                             detection_result: DetectionResult,
                             model_genome: FinancialGenome) -> List[TargetSite]:
        """Use heuristic rules to identify target parameters."""
        targets = []

        # Target parameters mentioned in affected features
        affected_features = detection_result.affected_features

        for feature in affected_features:
            # Try to map feature names to parameter paths
            possible_paths = self._map_feature_to_parameters(feature, model_genome)

            for param_path in possible_paths:
                try:
                    current_value = model_genome.get_parameter(param_path)
                    gene = model_genome.get_gene(param_path)

                    # Determine edit strategy based on parameter type
                    if gene.param_type == 'hyperparameter':
                        edit_type = 'adjust'
                        confidence = 0.8
                        priority = 3
                    elif gene.param_type == 'weight':
                        edit_type = 'adjust'
                        confidence = 0.7
                        priority = 2
                    else:
                        edit_type = 'replace'
                        confidence = 0.6
                        priority = 1

                    target_value = self._suggest_target_value(current_value, edit_type)

                    target = TargetSite(
                        parameter_path=param_path,
                        current_value=current_value,
                        target_value=target_value,
                        confidence=confidence,
                        priority=priority,
                        edit_type=edit_type,
                        rationale=f"Rule-based targeting: affected feature {feature}"
                    )

                    targets.append(target)

                except Exception as e:
                    logger.warning(f"Failed to create rule-based target for {param_path}: {str(e)}")

        return targets

    def _importance_based_targeting(self,
                                   detection_result: DetectionResult,
                                   model_genome: FinancialGenome) -> List[TargetSite]:
        """Target parameters based on importance scores."""
        targets = []

        # Get high-importance parameters
        critical_params = model_genome.get_critical_parameters(threshold=0.7)

        for param_path, gene in critical_params.items():
            # Higher chance of targeting if anomaly score is high
            targeting_probability = detection_result.anomaly_score * gene.importance_score

            if targeting_probability > 0.5:
                current_value = gene.value

                # Suggest conservative adjustments for important parameters
                edit_type = 'adjust'
                target_value = self._suggest_target_value(current_value, edit_type, conservative=True)

                target = TargetSite(
                    parameter_path=param_path,
                    current_value=current_value,
                    target_value=target_value,
                    confidence=float(targeting_probability),
                    priority=int(gene.importance_score * 5),  # Scale to 1-5
                    edit_type=edit_type,
                    rationale=f"High importance parameter (score={gene.importance_score:.3f})"
                )

                targets.append(target)

        return targets

    def _suggest_target_value(self,
                             current_value: Any,
                             edit_type: str,
                             conservative: bool = False) -> Any:
        """Suggest target value based on current value and edit type."""
        if edit_type == 'remove':
            return None

        if edit_type == 'replace':
            # For replace, suggest a reasonable alternative
            if isinstance(current_value, (int, float)):
                if current_value > 0:
                    return current_value * 0.8  # Reduce by 20%
                return current_value * 1.2  # Increase magnitude by 20%
            if isinstance(current_value, np.ndarray):
                return current_value * 0.9  # Conservative 10% reduction
            return current_value  # Can't suggest replacement for unknown types

        if edit_type == 'adjust':
            # For adjust, suggest small modifications
            if isinstance(current_value, (int, float)):
                adjustment_factor = 0.95 if conservative else 0.9
                if current_value > 0:
                    return current_value * adjustment_factor
                return current_value * (2 - adjustment_factor)
            if isinstance(current_value, np.ndarray):
                adjustment_factor = 0.98 if conservative else 0.95
                return current_value * adjustment_factor
            return current_value

        return current_value

    def _map_feature_to_parameters(self,
                                  feature_name: str,
                                  model_genome: FinancialGenome) -> List[str]:
        """Map detected feature names to parameter paths."""
        parameter_paths = []

        # Simple heuristic mapping - can be made more sophisticated
        for chromosome in model_genome.list_chromosomes():
            for gene in model_genome.list_genes(chromosome):
                param_path = f"{chromosome}.{gene}"

                # Check if feature name relates to parameter path
                if any(keyword in feature_name.lower() for keyword in gene.lower().split('_')):
                    parameter_paths.append(param_path)
                elif any(keyword in feature_name.lower() for keyword in chromosome.lower().split('_')):
                    parameter_paths.append(param_path)

        return parameter_paths

    def _deduplicate_targets(self, targets: List[TargetSite]) -> List[TargetSite]:
        """Remove duplicate targets, keeping the highest confidence ones."""
        unique_targets = {}

        for target in targets:
            path = target.parameter_path

            if path not in unique_targets:
                unique_targets[path] = target
            else:
                # Keep target with higher confidence
                if target.confidence > unique_targets[path].confidence:
                    unique_targets[path] = target

        return list(unique_targets.values())

    def _was_recently_edited(self, parameter_path: str) -> bool:
        """Check if parameter was edited recently."""
        recent_threshold = timedelta(hours=1)  # Don't re-edit within 1 hour

        for history_entry in self._target_history:
            if 'targets' in history_entry:
                for target in history_entry['targets']:
                    if (target.parameter_path == parameter_path and
                        datetime.now() - history_entry['timestamp'] < recent_threshold):
                        return True

        return False

    def _has_critical_dependencies(self, parameter_path: str) -> bool:
        """Check if parameter has critical dependencies."""
        # This would need to be implemented based on model architecture
        # For now, return False (no critical dependencies)
        return False

    def _is_edit_type_feasible(self, target: TargetSite) -> bool:
        """Check if the proposed edit type is feasible for this parameter."""
        # Basic feasibility checks
        if target.edit_type == 'remove' and target.current_value is None:
            return False

        if target.edit_type in ['replace', 'adjust'] and target.target_value is None:
            return False

        return True

    def _update_targeting_history(self,
                                 detection_result: DetectionResult,
                                 targets: List[TargetSite]) -> None:
        """Update targeting history for learning and analysis."""
        history_entry = {
            'timestamp': datetime.now(),
            'detection_result': detection_result,
            'targets': targets,
            'strategy_used': self.current_strategy
        }

        self._targeting_history.append(history_entry)

        # Keep only recent history
        if len(self._targeting_history) > 1000:
            self._targeting_history = self._targeting_history[-1000:]

    def get_targeting_statistics(self) -> Dict[str, Any]:
        """
        📊 Generate targeting performance statistics
        
        Returns:
            Dictionary with targeting performance metrics
        """
        if not self._targeting_history:
            return {'status': 'No targeting history available'}

        total_sessions = len(self._targeting_history)
        total_targets = sum(len(session['targets']) for session in self._targeting_history)

        # Calculate average targets per session
        avg_targets = total_targets / total_sessions if total_sessions > 0 else 0

        # Analyze target distribution by edit type
        edit_type_counts = {'replace': 0, 'adjust': 0, 'remove': 0}
        confidence_scores = []

        for session in self._targeting_history:
            for target in session['targets']:
                edit_type_counts[target.edit_type] = edit_type_counts.get(target.edit_type, 0) + 1
                confidence_scores.append(target.confidence)

        return {
            'total_sessions': total_sessions,
            'total_targets': total_targets,
            'average_targets_per_session': avg_targets,
            'edit_type_distribution': edit_type_counts,
            'average_confidence': np.mean(confidence_scores) if confidence_scores else 0.0,
            'confidence_std': np.std(confidence_scores) if confidence_scores else 0.0,
            'current_strategy': self.current_strategy
        }
