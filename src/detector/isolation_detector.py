"""
🔬 Isolation Detector — Genome Sequencing for Anomalies

Advanced anomaly detection system inspired by genome sequencing techniques.
Uses Isolation Forest and statistical methods to detect model drift, parameter
degradation, and performance anomalies in financial AI systems.

Think like biology. Code like AI.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from typing import Dict, List, Tuple, Any
from datetime import datetime
import logging
from dataclasses import dataclass

from ..core.base_layers import BaseDetector, DetectionResult

logger = logging.getLogger(__name__)


@dataclass
class AnomalySignature:
    """
    🧬 Genetic Anomaly Signature
    
    Detailed fingerprint of an anomaly, like identifying specific
    mutations in a genetic sequence.
    """
    feature_deviations: Dict[str, float]
    anomaly_vector: np.ndarray
    severity_level: str  # 'low', 'medium', 'high', 'critical'
    pattern_type: str    # 'drift', 'spike', 'regime_change', 'degradation'
    affected_regions: List[str]
    confidence_intervals: Dict[str, Tuple[float, float]]


class IsolationDetector(BaseDetector):
    """
    🔬 Isolation Forest Genetic Sequencer
    
    Primary anomaly detection system using isolation forest algorithm
    combined with statistical drift detection. Like a sophisticated
    DNA sequencer that can identify mutations and genetic variations.
    
    Biological Analogy:
    - Isolation Forest → Genetic Screening
    - Feature Space → Genome Landscape  
    - Anomaly Scores → Mutation Severity
    - Contamination → Population Mutation Rate
    """

    def __init__(self,
                 name: str = "IsolationDetector",
                 sensitivity: float = 0.95,
                 contamination: float = 0.1,
                 n_estimators: int = 100,
                 max_samples: str = "auto",
                 drift_window: int = 50):
        """
        Initialize the isolation-based genetic sequencer.
        
        Args:
            name: Detector identifier
            sensitivity: Detection sensitivity (0.0-1.0)
            contamination: Expected fraction of anomalies
            n_estimators: Number of isolation trees
            max_samples: Samples per tree
            drift_window: Window size for drift detection
        """
        super().__init__(name, sensitivity)

        # Isolation Forest parameters
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.max_samples = max_samples
        self.drift_window = drift_window

        # Models and preprocessing
        self.isolation_forest = None
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=0.95)  # Keep 95% of variance

        # Baseline and monitoring
        self._baseline_stats = {}
        self._drift_detector = {}
        self._feature_importance = {}
        self._anomaly_history = []

        # Adaptive thresholds
        self._adaptive_threshold = -0.5  # Anomaly score threshold
        self._threshold_history = []

        logger.info(f"Initialized {self.name} with contamination={contamination}")

    def fit(self, healthy_data: pd.DataFrame) -> None:
        """
        🧬 Sequence healthy genome baseline
        
        Establish the reference genome by training on known-healthy data.
        Like sequencing a reference genome for future comparisons.
        
        Args:
            healthy_data: Clean training data representing normal behavior
        """
        logger.info(f"Training {self.name} on {len(healthy_data)} healthy samples")

        # Store original data for validation
        self._healthy_baseline = healthy_data.copy()

        # Prepare features for isolation forest
        features = self._prepare_features(healthy_data)

        if len(features) == 0:
            raise ValueError("No valid features found in training data")

        # Normalize features
        features_scaled = self.scaler.fit_transform(features)

        # Apply PCA for dimensionality reduction if needed
        if features_scaled.shape[1] > 20:
            features_final = self.pca.fit_transform(features_scaled)
            logger.info(f"Reduced features from {features_scaled.shape[1]} to {features_final.shape[1]} via PCA")
        else:
            features_final = features_scaled
            self.pca = None

        # Train isolation forest
        self.isolation_forest = IsolationForest(
            contamination=self.contamination,
            n_estimators=self.n_estimators,
            max_samples=self.max_samples,
            random_state=42,
            n_jobs=-1
        )

        self.isolation_forest.fit(features_final)

        # Establish baseline statistics for drift detection
        self._compute_baseline_stats(healthy_data)

        # Set initial adaptive threshold based on training scores
        training_scores = self.isolation_forest.decision_function(features_final)
        self._adaptive_threshold = np.percentile(training_scores, 100 * self.contamination)

        logger.info(f"Training complete. Baseline threshold: {self._adaptive_threshold:.3f}")

    def detect(self, data: pd.DataFrame) -> DetectionResult:
        """
        🔍 Analyze genetic sample for mutations
        
        Scan new data for anomalies compared to the healthy baseline.
        Like sequencing a new sample and comparing to reference genome.
        
        Args:
            data: Current data to analyze for anomalies
            
        Returns:
            DetectionResult with comprehensive anomaly information
        """
        if self.isolation_forest is None:
            raise ValueError("Detector not trained. Call fit() first.")

        logger.debug(f"Analyzing {len(data)} samples for anomalies")

        # Prepare features
        features = self._prepare_features(data)

        if len(features) == 0:
            return DetectionResult(
                anomaly_score=0.0,
                is_anomalous=False,
                affected_features=[],
                confidence=0.0,
                timestamp=datetime.now(),
                metadata={'error': 'No valid features found'}
            )

        # Transform features using fitted preprocessors
        try:
            features_scaled = self.scaler.transform(features)

            if self.pca is not None:
                features_final = self.pca.transform(features_scaled)
            else:
                features_final = features_scaled
        except Exception as e:
            logger.error(f"Feature transformation failed: {str(e)}")
            return DetectionResult(
                anomaly_score=0.0,
                is_anomalous=False,
                affected_features=[],
                confidence=0.0,
                timestamp=datetime.now(),
                metadata={'error': f'Transformation failed: {str(e)}'}
            )

        # Get anomaly scores from isolation forest
        anomaly_scores = self.isolation_forest.decision_function(features_final)
        anomaly_predictions = self.isolation_forest.predict(features_final)

        # Calculate overall anomaly score (average of sample scores)
        overall_score = np.mean(anomaly_scores)

        # Determine if anomalous based on adaptive threshold
        is_anomalous = overall_score < self._adaptive_threshold

        # Identify affected features through feature importance analysis
        affected_features = self._identify_affected_features(data, features_final, anomaly_scores)

        # Calculate confidence based on score consistency and magnitude
        confidence = self._calculate_confidence(anomaly_scores, features_final)

        # Perform drift detection
        drift_analysis = self._detect_drift(data)

        # Update adaptive threshold
        self._update_adaptive_threshold(anomaly_scores)

        # Create anomaly signature for detailed analysis
        signature = self._create_anomaly_signature(data, features_final, anomaly_scores)

        # Compile metadata
        metadata = {
            'individual_scores': anomaly_scores.tolist(),
            'predictions': anomaly_predictions.tolist(),
            'drift_analysis': drift_analysis,
            'signature': signature,
            'threshold_used': self._adaptive_threshold,
            'feature_count': len(features[0]) if len(features) > 0 else 0,
            'sample_count': len(data)
        }

        result = DetectionResult(
            anomaly_score=abs(overall_score),  # Use absolute value for interpretability
            is_anomalous=is_anomalous,
            affected_features=affected_features,
            confidence=confidence,
            timestamp=datetime.now(),
            metadata=metadata
        )

        # Store in history for learning
        self._anomaly_history.append(result)

        logger.debug(f"Detection complete: anomaly_score={result.anomaly_score:.3f}, "
                    f"is_anomalous={result.is_anomalous}, confidence={result.confidence:.3f}")

        return result

    def _prepare_features(self, data: pd.DataFrame) -> np.ndarray:
        """
        🧬 Extract genetic features for analysis
        
        Convert raw financial data into features suitable for anomaly detection.
        """
        features = []

        # Handle MultiIndex columns (symbol-based data)
        if isinstance(data.columns, pd.MultiIndex):
            # Group by symbol and extract features
            for symbol in data.columns.levels[0]:
                symbol_data = data.xs(symbol, level=0, axis=1)
                symbol_features = self._extract_symbol_features(symbol_data)
                features.extend(symbol_features)
        else:
            # Regular DataFrame
            features = self._extract_symbol_features(data)

        return np.array(features) if features else np.array([])

    def _extract_symbol_features(self, data: pd.DataFrame) -> List[List[float]]:
        """Extract numerical features from symbol data."""
        features = []

        # Get numeric columns only
        numeric_data = data.select_dtypes(include=[np.number])

        if len(numeric_data.columns) == 0:
            return []

        # Remove NaN values and infinite values
        clean_data = numeric_data.fillna(method='ffill').fillna(0)
        clean_data = clean_data.replace([np.inf, -np.inf], 0)

        # Convert to list of feature vectors (each row is a sample)
        for idx, row in clean_data.iterrows():
            feature_vector = row.values.tolist()

            # Add statistical features
            if len(feature_vector) > 1:
                feature_vector.extend([
                    np.mean(feature_vector),
                    np.std(feature_vector),
                    np.median(feature_vector),
                    np.percentile(feature_vector, 25),
                    np.percentile(feature_vector, 75)
                ])

            features.append(feature_vector)

        return features

    def _compute_baseline_stats(self, data: pd.DataFrame) -> None:
        """Compute baseline statistics for drift detection."""
        self._baseline_stats = {}

        if isinstance(data.columns, pd.MultiIndex):
            for symbol in data.columns.levels[0]:
                symbol_data = data.xs(symbol, level=0, axis=1)
                self._baseline_stats[symbol] = self._compute_symbol_stats(symbol_data)
        else:
            self._baseline_stats['default'] = self._compute_symbol_stats(data)

    def _compute_symbol_stats(self, data: pd.DataFrame) -> Dict[str, float]:
        """Compute statistics for a single symbol's data."""
        numeric_data = data.select_dtypes(include=[np.number])

        stats = {}
        for col in numeric_data.columns:
            series = numeric_data[col].dropna()
            if len(series) > 0:
                stats[col] = {
                    'mean': float(series.mean()),
                    'std': float(series.std()),
                    'median': float(series.median()),
                    'q25': float(series.quantile(0.25)),
                    'q75': float(series.quantile(0.75)),
                    'skew': float(series.skew()),
                    'kurtosis': float(series.kurtosis())
                }

        return stats

    def _detect_drift(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Detect statistical drift compared to baseline."""
        drift_analysis = {
            'has_drift': False,
            'drift_features': [],
            'drift_scores': {},
            'drift_severity': 'none'
        }

        if not self._baseline_stats:
            return drift_analysis

        current_stats = {}
        if isinstance(data.columns, pd.MultiIndex):
            for symbol in data.columns.levels[0]:
                if symbol in self._baseline_stats:
                    symbol_data = data.xs(symbol, level=0, axis=1)
                    current_stats[symbol] = self._compute_symbol_stats(symbol_data)
        else:
            current_stats['default'] = self._compute_symbol_stats(data)

        # Compare current stats to baseline
        drift_scores = []
        drift_features = []

        for symbol_key in current_stats:
            if symbol_key in self._baseline_stats:
                baseline = self._baseline_stats[symbol_key]
                current = current_stats[symbol_key]

                for feature in baseline:
                    if feature in current:
                        # Calculate drift using normalized difference
                        for stat_type in ['mean', 'std']:
                            if stat_type in baseline[feature] and stat_type in current[feature]:
                                baseline_val = baseline[feature][stat_type]
                                current_val = current[feature][stat_type]

                                if baseline_val != 0:
                                    drift_score = abs((current_val - baseline_val) / baseline_val)
                                    drift_scores.append(drift_score)

                                    if drift_score > 0.2:  # 20% change threshold
                                        drift_features.append(f"{symbol_key}.{feature}.{stat_type}")

        if drift_scores:
            avg_drift_score = np.mean(drift_scores)
            max_drift_score = np.max(drift_scores)

            drift_analysis['drift_scores'] = {
                'average': float(avg_drift_score),
                'maximum': float(max_drift_score),
                'individual': drift_scores
            }

            # Determine drift severity
            if max_drift_score > 0.5:
                drift_analysis['drift_severity'] = 'high'
                drift_analysis['has_drift'] = True
            elif max_drift_score > 0.3:
                drift_analysis['drift_severity'] = 'medium'
                drift_analysis['has_drift'] = True
            elif max_drift_score > 0.2:
                drift_analysis['drift_severity'] = 'low'
                drift_analysis['has_drift'] = True

            drift_analysis['drift_features'] = drift_features

        return drift_analysis

    def _identify_affected_features(self,
                                   data: pd.DataFrame,
                                   features: np.ndarray,
                                   anomaly_scores: np.ndarray) -> List[str]:
        """Identify which features contribute most to anomalies."""
        affected_features = []

        if len(anomaly_scores) == 0 or len(features) == 0:
            return affected_features

        # Find samples with highest anomaly scores
        anomaly_threshold = np.percentile(anomaly_scores, 10)  # Bottom 10% of scores
        anomalous_indices = np.where(anomaly_scores <= anomaly_threshold)[0]

        if len(anomalous_indices) == 0:
            return affected_features

        # Analyze feature deviations for anomalous samples
        if hasattr(self, '_feature_names'):
            feature_names = self._feature_names
        else:
            # Generate generic feature names
            feature_names = [f"feature_{i}" for i in range(features.shape[1])]

        # Calculate feature deviations from training mean
        if hasattr(self.scaler, 'mean_'):
            baseline_mean = self.scaler.mean_
            anomalous_features = features[anomalous_indices]

            # Calculate average deviation for each feature
            deviations = np.abs(np.mean(anomalous_features, axis=0) - baseline_mean)

            # Find features with highest deviations
            deviation_threshold = np.percentile(deviations, 75)  # Top 25% of deviations
            significant_features = np.where(deviations >= deviation_threshold)[0]

            affected_features = [feature_names[i] for i in significant_features if i < len(feature_names)]

        return affected_features

    def _calculate_confidence(self,
                             anomaly_scores: np.ndarray,
                             features: np.ndarray) -> float:
        """Calculate confidence in the anomaly detection result."""
        if len(anomaly_scores) == 0:
            return 0.0

        # Factors affecting confidence:
        # 1. Consistency of anomaly scores
        score_std = np.std(anomaly_scores)
        consistency_factor = 1.0 / (1.0 + score_std)

        # 2. Distance from threshold
        avg_score = np.mean(anomaly_scores)
        distance_factor = min(1.0, abs(avg_score - self._adaptive_threshold) / 0.5)

        # 3. Sample size factor
        sample_size_factor = min(1.0, len(anomaly_scores) / 50.0)

        # Combine factors
        confidence = np.mean([consistency_factor, distance_factor, sample_size_factor])

        return float(np.clip(confidence, 0.0, 1.0))

    def _update_adaptive_threshold(self, anomaly_scores: np.ndarray) -> None:
        """Update adaptive threshold based on recent scores."""
        if len(anomaly_scores) == 0:
            return

        # Add current scores to history
        self._threshold_history.extend(anomaly_scores.tolist())

        # Keep only recent history
        if len(self._threshold_history) > 1000:
            self._threshold_history = self._threshold_history[-1000:]

        # Update threshold using exponential moving average
        alpha = 0.1  # Learning rate
        current_percentile = np.percentile(anomaly_scores, 100 * self.contamination)
        self._adaptive_threshold = (1 - alpha) * self._adaptive_threshold + alpha * current_percentile

    def _create_anomaly_signature(self,
                                 data: pd.DataFrame,
                                 features: np.ndarray,
                                 anomaly_scores: np.ndarray) -> AnomalySignature:
        """Create detailed anomaly signature for analysis."""
        # Default signature for invalid inputs
        if len(anomaly_scores) == 0 or len(features) == 0:
            return AnomalySignature(
                feature_deviations={},
                anomaly_vector=np.array([]),
                severity_level='low',
                pattern_type='unknown',
                affected_regions=[],
                confidence_intervals={}
            )

        # Determine severity level
        avg_score = np.mean(anomaly_scores)
        if avg_score < -1.0:
            severity_level = 'critical'
        elif avg_score < -0.7:
            severity_level = 'high'
        elif avg_score < -0.4:
            severity_level = 'medium'
        else:
            severity_level = 'low'

        # Analyze pattern type
        score_trend = np.diff(anomaly_scores) if len(anomaly_scores) > 1 else np.array([0])

        if np.std(anomaly_scores) > 0.3:
            pattern_type = 'spike'
        elif np.mean(score_trend) < -0.1:
            pattern_type = 'degradation'
        elif abs(np.mean(score_trend)) < 0.05:
            pattern_type = 'drift'
        else:
            pattern_type = 'regime_change'

        # Calculate feature deviations
        feature_deviations = {}
        if hasattr(self.scaler, 'mean_') and len(features) > 0:
            baseline_mean = self.scaler.mean_
            current_mean = np.mean(features, axis=0)

            for i, (baseline, current) in enumerate(zip(baseline_mean, current_mean)):
                if baseline != 0:
                    deviation = abs((current - baseline) / baseline)
                    feature_deviations[f'feature_{i}'] = float(deviation)

        return AnomalySignature(
            feature_deviations=feature_deviations,
            anomaly_vector=anomaly_scores,
            severity_level=severity_level,
            pattern_type=pattern_type,
            affected_regions=['financial_data'],  # Could be more specific
            confidence_intervals={'anomaly_score': (float(np.min(anomaly_scores)), float(np.max(anomaly_scores)))}
        )

    def get_detection_summary(self, num_recent: int = 10) -> Dict[str, Any]:
        """
        📊 Generate detection summary report
        
        Compile recent detection history and performance statistics.
        
        Args:
            num_recent: Number of recent detections to include
            
        Returns:
            Summary of detection performance and trends
        """
        if not self._anomaly_history:
            return {'status': 'No detection history available'}

        recent_detections = self._anomaly_history[-num_recent:]

        summary = {
            'total_detections': len(self._anomaly_history),
            'recent_detections': len(recent_detections),
            'anomaly_rate': sum(1 for d in recent_detections if d.is_anomalous) / len(recent_detections),
            'average_confidence': np.mean([d.confidence for d in recent_detections]),
            'average_anomaly_score': np.mean([d.anomaly_score for d in recent_detections]),
            'most_affected_features': self._get_most_affected_features(recent_detections),
            'detection_trends': self._analyze_detection_trends(recent_detections),
            'current_threshold': self._adaptive_threshold
        }

        return summary

    def _get_most_affected_features(self, detections: List[DetectionResult]) -> List[str]:
        """Identify features that appear most frequently in anomalies."""
        feature_counts = {}

        for detection in detections:
            for feature in detection.affected_features:
                feature_counts[feature] = feature_counts.get(feature, 0) + 1

        # Sort by frequency
        sorted_features = sorted(feature_counts.items(), key=lambda x: x[1], reverse=True)

        return [feature for feature, count in sorted_features[:5]]

    def _analyze_detection_trends(self, detections: List[DetectionResult]) -> Dict[str, Any]:
        """Analyze trends in recent detections."""
        if len(detections) < 2:
            return {'trend': 'insufficient_data'}

        scores = [d.anomaly_score for d in detections]
        confidences = [d.confidence for d in detections]

        # Calculate trends
        score_trend = np.polyfit(range(len(scores)), scores, 1)[0]
        confidence_trend = np.polyfit(range(len(confidences)), confidences, 1)[0]

        return {
            'anomaly_score_trend': float(score_trend),
            'confidence_trend': float(confidence_trend),
            'trend_direction': 'increasing' if score_trend > 0 else 'decreasing',
            'stability': 'stable' if abs(score_trend) < 0.01 else 'changing'
        }
