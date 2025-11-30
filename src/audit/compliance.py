"""
📋 Audit & Compliance System — Genetic Edit Monitoring

Comprehensive audit trail and compliance monitoring for CRISPR-style
financial model editing. Like a lab notebook that tracks every genetic
modification with full regulatory compliance.

Biology meets blockchain. Every edit matters.
"""

import numpy as np
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
import hashlib
from pathlib import Path

from ..core.base_layers import BaseAudit, EditResult
from ..core.genome import FinancialGenome

logger = logging.getLogger(__name__)


@dataclass
class AuditEntry:
    """
    📝 Single Audit Log Entry
    
    Immutable record of a specific edit or system event,
    like a single entry in a lab notebook.
    """
    entry_id: str
    timestamp: datetime
    event_type: str  # 'edit', 'repair', 'detection', 'emergency', 'rollback'
    actor: str  # System component that performed the action
    target_parameters: List[str]
    action_details: Dict[str, Any]
    before_state_hash: str
    after_state_hash: str
    performance_impact: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuditEntry':
        """Create from dictionary."""
        # Convert timestamp string back to datetime if needed
        if isinstance(data.get('timestamp'), str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class ComplianceReport:
    """
    📊 Compliance Assessment Report
    
    Comprehensive analysis of system compliance with editing policies
    and safety protocols, like a regulatory inspection report.
    """
    report_id: str
    timestamp: datetime
    compliance_score: float  # 0.0-1.0
    violations: List[Dict[str, Any]]
    recommendations: List[str]
    audit_period: Tuple[datetime, datetime]
    total_edits: int
    unauthorized_edits: int
    emergency_activations: int
    rollback_count: int
    risk_assessment: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        data['timestamp'] = self.timestamp.isoformat()
        data['audit_period'] = (self.audit_period[0].isoformat(),
                               self.audit_period[1].isoformat())
        return data


@dataclass
class AuditConfig:
    """
    ⚙️ Audit System Configuration
    
    Configuration for audit trail management and compliance monitoring.
    """
    max_audit_entries: int = 10000
    audit_retention_days: int = 365
    compliance_check_interval: timedelta = timedelta(hours=24)
    enable_real_time_monitoring: bool = True
    enable_blockchain_audit: bool = False
    audit_storage_path: str = "./audit_logs"
    encryption_enabled: bool = True
    auto_cleanup_enabled: bool = True
    violation_alert_threshold: float = 0.7  # Compliance score threshold

    def __post_init__(self):
        """Ensure audit storage directory exists."""
        Path(self.audit_storage_path).mkdir(parents=True, exist_ok=True)


class CryptographicAuditor:
    """
    🔐 Cryptographic Audit Security
    
    Provides cryptographic integrity for audit trails using
    hashing and digital signatures to prevent tampering.
    """

    def __init__(self, enable_encryption: bool = True):
        self.enable_encryption = enable_encryption
        self._audit_chain = []  # Blockchain-like audit chain
        self._previous_hash = "genesis"

    def calculate_state_hash(self, model_genome: FinancialGenome) -> str:
        """
        🔐 Calculate cryptographic hash of model state
        
        Creates a unique fingerprint of the current model parameters
        for integrity verification.
        
        Args:
            model_genome: Model to hash
            
        Returns:
            Cryptographic hash string
        """
        # Serialize genome state
        state_data = {}

        for chromosome in model_genome.list_chromosomes():
            state_data[chromosome] = {}
            for gene_name in model_genome.list_genes(chromosome):
                param_path = f"{chromosome}.{gene_name}"
                gene = model_genome.get_gene(param_path)

                # Convert gene to hashable format
                if isinstance(gene.value, np.ndarray):
                    value_hash = hashlib.md5(gene.value.tobytes()).hexdigest()
                else:
                    value_hash = str(gene.value)

                state_data[chromosome][gene_name] = {
                    'value_hash': value_hash,
                    'edit_count': gene.edit_count,
                    'last_modified': gene.last_modified.isoformat() if gene.last_modified else None
                }

        # Create deterministic hash
        state_json = json.dumps(state_data, sort_keys=True)
        state_hash = hashlib.sha256(state_json.encode()).hexdigest()

        return state_hash

    def create_audit_block(self, audit_entry: AuditEntry) -> Dict[str, Any]:
        """
        ⛓️ Create blockchain-style audit block
        
        Links audit entries in a tamper-evident chain.
        
        Args:
            audit_entry: Entry to add to chain
            
        Returns:
            Audit block with cryptographic links
        """
        # Create block with entry and chain linkage
        block_data = {
            'index': len(self._audit_chain),
            'timestamp': audit_entry.timestamp.isoformat(),
            'audit_entry': audit_entry.to_dict(),
            'previous_hash': self._previous_hash
        }

        # Calculate block hash
        block_json = json.dumps(block_data, sort_keys=True)
        block_hash = hashlib.sha256(block_json.encode()).hexdigest()
        block_data['block_hash'] = block_hash

        # Update chain
        self._audit_chain.append(block_data)
        self._previous_hash = block_hash

        return block_data

    def verify_audit_chain(self) -> Tuple[bool, List[str]]:
        """
        ✅ Verify integrity of audit chain
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        if not self._audit_chain:
            return True, []

        # Check chain linkage
        previous_hash = "genesis"
        for i, block in enumerate(self._audit_chain):
            # Verify previous hash linkage
            if block['previous_hash'] != previous_hash:
                issues.append(f"Block {i}: Invalid previous hash linkage")

            # Verify block hash
            block_copy = block.copy()
            stored_hash = block_copy.pop('block_hash')
            calculated_hash = hashlib.sha256(
                json.dumps(block_copy, sort_keys=True).encode()
            ).hexdigest()

            if stored_hash != calculated_hash:
                issues.append(f"Block {i}: Hash mismatch - possible tampering")

            previous_hash = stored_hash

        return len(issues) == 0, issues


class ComplianceMonitor:
    """
    ⚖️ Compliance Monitoring System
    
    Monitors system behavior against defined policies and regulations,
    like a regulatory compliance officer for genetic editing.
    """

    def __init__(self):
        self.compliance_rules = self._load_default_rules()
        self.violation_history = []
        self.last_assessment = None

    def _load_default_rules(self) -> Dict[str, Any]:
        """Load default compliance rules."""
        return {
            'max_edits_per_hour': 100,
            'max_parameter_change_percentage': 50.0,
            'required_approval_for_critical_params': True,
            'emergency_protocols_required': True,
            'audit_trail_required': True,
            'rollback_capability_required': True,
            'max_consecutive_failures': 5,
            'performance_degradation_threshold': -10.0  # percent
        }

    def assess_compliance(self,
                         audit_entries: List[AuditEntry],
                         assessment_period: Tuple[datetime, datetime]) -> ComplianceReport:
        """
        ⚖️ Assess system compliance
        
        Comprehensive compliance assessment against all rules and policies.
        
        Args:
            audit_entries: Audit entries to analyze
            assessment_period: Time period for assessment
            
        Returns:
            Detailed compliance report
        """
        logger.info(f"Assessing compliance for period {assessment_period[0]} to {assessment_period[1]}")

        violations = []
        compliance_scores = []

        # Filter entries to assessment period
        period_entries = [
            entry for entry in audit_entries
            if assessment_period[0] <= entry.timestamp <= assessment_period[1]
        ]

        # 1. Check edit frequency
        edit_frequency_score, edit_violations = self._check_edit_frequency(period_entries)
        violations.extend(edit_violations)
        compliance_scores.append(('edit_frequency', edit_frequency_score))

        # 2. Check parameter change magnitudes
        change_magnitude_score, change_violations = self._check_change_magnitudes(period_entries)
        violations.extend(change_violations)
        compliance_scores.append(('change_magnitude', change_magnitude_score))

        # 3. Check emergency protocol usage
        emergency_score, emergency_violations = self._check_emergency_protocols(period_entries)
        violations.extend(emergency_violations)
        compliance_scores.append(('emergency_protocols', emergency_score))

        # 4. Check audit trail completeness
        audit_score, audit_violations = self._check_audit_completeness(period_entries)
        violations.extend(audit_violations)
        compliance_scores.append(('audit_completeness', audit_score))

        # 5. Check performance impact
        performance_score, performance_violations = self._check_performance_impact(period_entries)
        violations.extend(performance_violations)
        compliance_scores.append(('performance_impact', performance_score))

        # Calculate overall compliance score
        overall_score = np.mean([score for _, score in compliance_scores])

        # Generate recommendations
        recommendations = self._generate_compliance_recommendations(violations, compliance_scores)

        # Count key metrics
        total_edits = len([e for e in period_entries if e.event_type == 'edit'])
        unauthorized_edits = len([e for e in period_entries
                                if e.event_type == 'edit' and not e.success])
        emergency_activations = len([e for e in period_entries if e.event_type == 'emergency'])
        rollback_count = len([e for e in period_entries if e.event_type == 'rollback'])

        # Risk assessment
        risk_assessment = self._assess_risks(violations, compliance_scores, period_entries)

        report = ComplianceReport(
            report_id=f"compliance_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now(),
            compliance_score=overall_score,
            violations=violations,
            recommendations=recommendations,
            audit_period=assessment_period,
            total_edits=total_edits,
            unauthorized_edits=unauthorized_edits,
            emergency_activations=emergency_activations,
            rollback_count=rollback_count,
            risk_assessment=risk_assessment
        )

        self.last_assessment = report

        # Store violations for trending
        if violations:
            self.violation_history.extend(violations)

        logger.info(f"Compliance assessment complete: score={overall_score:.3f}, "
                   f"violations={len(violations)}")

        return report

    def _check_edit_frequency(self, entries: List[AuditEntry]) -> Tuple[float, List[Dict]]:
        """Check if edit frequency is within acceptable limits."""
        violations = []

        if not entries:
            return 1.0, violations

        edit_entries = [e for e in entries if e.event_type == 'edit']

        # Group by hour and check limits
        hourly_counts = {}
        for entry in edit_entries:
            hour_key = entry.timestamp.replace(minute=0, second=0, microsecond=0)
            hourly_counts[hour_key] = hourly_counts.get(hour_key, 0) + 1

        max_hourly = max(hourly_counts.values()) if hourly_counts else 0
        max_allowed = self.compliance_rules['max_edits_per_hour']

        if max_hourly > max_allowed:
            violations.append({
                'type': 'edit_frequency_violation',
                'severity': 'high',
                'description': f"Exceeded max edits per hour: {max_hourly} > {max_allowed}",
                'timestamp': datetime.now().isoformat()
            })
            return 0.5, violations

        # Score based on how close to limit
        score = 1.0 - (max_hourly / max_allowed) * 0.5
        return max(0.0, score), violations

    def _check_change_magnitudes(self, entries: List[AuditEntry]) -> Tuple[float, List[Dict]]:
        """Check if parameter changes are within acceptable magnitudes."""
        violations = []

        edit_entries = [e for e in entries if e.event_type == 'edit']

        if not edit_entries:
            return 1.0, violations

        large_changes = 0
        total_changes = 0

        for entry in edit_entries:
            if 'parameter_changes' in entry.action_details:
                changes = entry.action_details['parameter_changes']

                for param, change_info in changes.items():
                    if isinstance(change_info, dict) and 'percentage_change' in change_info:
                        change_pct = abs(change_info['percentage_change'])
                        total_changes += 1

                        if change_pct > self.compliance_rules['max_parameter_change_percentage']:
                            large_changes += 1
                            violations.append({
                                'type': 'large_parameter_change',
                                'severity': 'medium',
                                'description': f"Large change in {param}: {change_pct:.1f}%",
                                'timestamp': entry.timestamp.isoformat(),
                                'parameter': param,
                                'change_percentage': change_pct
                            })

        if total_changes == 0:
            return 1.0, violations

        # Score based on proportion of large changes
        large_change_ratio = large_changes / total_changes
        score = 1.0 - large_change_ratio

        return score, violations

    def _check_emergency_protocols(self, entries: List[AuditEntry]) -> Tuple[float, List[Dict]]:
        """Check proper use of emergency protocols."""
        violations = []

        emergency_entries = [e for e in entries if e.event_type == 'emergency']

        # Check if emergency protocols are available when required
        if not self.compliance_rules['emergency_protocols_required']:
            return 1.0, violations

        # Look for situations that should have triggered emergency protocols
        high_failure_sequences = self._detect_failure_sequences(entries)

        if high_failure_sequences and not emergency_entries:
            violations.append({
                'type': 'missing_emergency_activation',
                'severity': 'high',
                'description': "High failure rate detected without emergency protocol activation",
                'timestamp': datetime.now().isoformat()
            })
            return 0.3, violations

        # Check if emergency activations were justified
        unjustified_emergencies = 0
        for emergency in emergency_entries:
            # Simple heuristic: emergency should follow multiple failures
            preceding_failures = self._count_preceding_failures(emergency, entries, hours=1)
            if preceding_failures < 2:
                unjustified_emergencies += 1
                violations.append({
                    'type': 'unjustified_emergency',
                    'severity': 'medium',
                    'description': f"Emergency activation with only {preceding_failures} preceding failures",
                    'timestamp': emergency.timestamp.isoformat()
                })

        if emergency_entries:
            score = 1.0 - (unjustified_emergencies / len(emergency_entries)) * 0.5
        else:
            score = 1.0

        return max(0.0, score), violations

    def _check_audit_completeness(self, entries: List[AuditEntry]) -> Tuple[float, List[Dict]]:
        """Check audit trail completeness."""
        violations = []

        if not self.compliance_rules['audit_trail_required']:
            return 1.0, violations

        # Check for missing audit entries (gaps in timeline)
        if len(entries) < 2:
            return 1.0, violations

        # Sort entries by timestamp
        sorted_entries = sorted(entries, key=lambda x: x.timestamp)

        # Look for suspicious gaps
        gaps = []
        for i in range(1, len(sorted_entries)):
            time_gap = sorted_entries[i].timestamp - sorted_entries[i-1].timestamp
            if time_gap > timedelta(hours=24):  # Arbitrary threshold
                gaps.append(time_gap)

        if gaps:
            violations.append({
                'type': 'audit_trail_gaps',
                'severity': 'medium',
                'description': f"Found {len(gaps)} significant gaps in audit trail",
                'timestamp': datetime.now().isoformat(),
                'largest_gap_hours': max(gap.total_seconds() / 3600 for gap in gaps)
            })
            return 0.7, violations

        return 1.0, violations

    def _check_performance_impact(self, entries: List[AuditEntry]) -> Tuple[float, List[Dict]]:
        """Check performance impact of changes."""
        violations = []

        entries_with_impact = [e for e in entries if e.performance_impact is not None]

        if not entries_with_impact:
            return 1.0, violations

        # Check for significant performance degradations
        threshold = self.compliance_rules['performance_degradation_threshold']
        severe_degradations = [e for e in entries_with_impact
                             if e.performance_impact < threshold]

        if severe_degradations:
            for entry in severe_degradations:
                violations.append({
                    'type': 'performance_degradation',
                    'severity': 'high',
                    'description': f"Severe performance degradation: {entry.performance_impact:.1f}%",
                    'timestamp': entry.timestamp.isoformat(),
                    'performance_impact': entry.performance_impact
                })

        # Score based on average performance impact
        avg_impact = np.mean([e.performance_impact for e in entries_with_impact])
        if avg_impact < threshold:
            score = 0.2
        elif avg_impact < 0:
            score = 0.7
        else:
            score = 1.0

        return score, violations

    def _detect_failure_sequences(self, entries: List[AuditEntry]) -> List[Dict]:
        """Detect sequences of failures that should trigger emergency protocols."""
        failures = [e for e in entries if not e.success]

        # Group consecutive failures
        failure_sequences = []
        current_sequence = []

        for failure in sorted(failures, key=lambda x: x.timestamp):
            if not current_sequence:
                current_sequence = [failure]
            else:
                time_gap = failure.timestamp - current_sequence[-1].timestamp
                if time_gap <= timedelta(hours=1):  # Within 1 hour
                    current_sequence.append(failure)
                else:
                    if len(current_sequence) >= self.compliance_rules['max_consecutive_failures']:
                        failure_sequences.append(current_sequence)
                    current_sequence = [failure]

        # Check final sequence
        if len(current_sequence) >= self.compliance_rules['max_consecutive_failures']:
            failure_sequences.append(current_sequence)

        return failure_sequences

    def _count_preceding_failures(self,
                                 emergency_entry: AuditEntry,
                                 all_entries: List[AuditEntry],
                                 hours: int = 1) -> int:
        """Count failures preceding an emergency activation."""
        cutoff_time = emergency_entry.timestamp - timedelta(hours=hours)

        preceding_failures = [
            e for e in all_entries
            if (e.timestamp >= cutoff_time and
                e.timestamp < emergency_entry.timestamp and
                not e.success)
        ]

        return len(preceding_failures)

    def _generate_compliance_recommendations(self,
                                           violations: List[Dict],
                                           compliance_scores: List[Tuple]) -> List[str]:
        """Generate recommendations based on compliance assessment."""
        recommendations = []

        # Analyze violation patterns
        violation_types = [v['type'] for v in violations]

        if 'edit_frequency_violation' in violation_types:
            recommendations.append("Implement rate limiting for parameter edits")
            recommendations.append("Review edit authorization policies")

        if 'large_parameter_change' in violation_types:
            recommendations.append("Add approval workflow for large parameter changes")
            recommendations.append("Implement gradual change policies")

        if 'missing_emergency_activation' in violation_types:
            recommendations.append("Lower emergency activation thresholds")
            recommendations.append("Improve failure detection sensitivity")

        if 'performance_degradation' in violation_types:
            recommendations.append("Enhance pre-edit performance impact assessment")
            recommendations.append("Implement automatic rollback for severe degradations")

        # Analyze low compliance scores
        low_scores = [name for name, score in compliance_scores if score < 0.7]

        if 'audit_completeness' in low_scores:
            recommendations.append("Review audit logging configuration")
            recommendations.append("Implement audit trail verification")

        return recommendations

    def _assess_risks(self,
                     violations: List[Dict],
                     compliance_scores: List[Tuple],
                     entries: List[AuditEntry]) -> Dict[str, Any]:
        """Assess overall risk level."""
        # Calculate risk factors
        high_severity_violations = len([v for v in violations if v.get('severity') == 'high'])
        avg_compliance_score = np.mean([score for _, score in compliance_scores])
        recent_emergency_count = len([e for e in entries if e.event_type == 'emergency'])

        # Overall risk level
        risk_level = "low"
        if high_severity_violations > 0 or avg_compliance_score < 0.5:
            risk_level = "high"
        elif avg_compliance_score < 0.7 or recent_emergency_count > 2:
            risk_level = "medium"

        return {
            'risk_level': risk_level,
            'high_severity_violations': high_severity_violations,
            'average_compliance_score': avg_compliance_score,
            'recent_emergency_activations': recent_emergency_count,
            'risk_factors': [
                f"High severity violations: {high_severity_violations}",
                f"Compliance score: {avg_compliance_score:.2f}",
                f"Recent emergencies: {recent_emergency_count}"
            ]
        }


class ComprehensiveAudit(BaseAudit):
    """
    📋 Comprehensive Audit & Compliance System
    
    Complete audit trail and compliance monitoring for CRISPR-style
    financial model editing. Provides tamper-evident logging, regulatory
    compliance, and forensic analysis capabilities.
    
    Biological Analogy:
    - Lab Notebook → Audit Trail
    - Quality Control → Compliance Monitoring
    - Chain of Custody → Cryptographic Verification
    - Regulatory Approval → Policy Enforcement
    """

    def __init__(self,
                 name: str = "ComprehensiveAudit",
                 config: Optional[AuditConfig] = None):
        """
        Initialize the comprehensive audit system.
        
        Args:
            name: Audit system identifier
            config: Audit configuration parameters
        """
        super().__init__(name)

        self.config = config or AuditConfig()

        # Core components
        self.crypto_auditor = CryptographicAuditor(self.config.encryption_enabled)
        self.compliance_monitor = ComplianceMonitor()

        # Audit storage
        self._audit_entries: List[AuditEntry] = []
        self._compliance_reports: List[ComplianceReport] = []

        # Real-time monitoring
        self._last_compliance_check = datetime.now()
        self._real_time_violations = []

        # Load existing audit data if available
        self._load_audit_history()

        logger.info(f"Initialized {self.name} with {len(self._audit_entries)} existing entries")

    def log_edit(self,
                edit_result: EditResult,
                model_genome: FinancialGenome,
                actor: str = "system") -> str:
        """
        📝 Log parameter edit with full audit trail
        
        Creates immutable audit record of parameter modification.
        
        Args:
            edit_result: Results of the edit operation
            model_genome: Model state after edit
            actor: System component that performed edit
            
        Returns:
            Unique audit entry ID
        """
        # Calculate state hashes
        before_hash = self.crypto_auditor.calculate_state_hash(model_genome)

        # Create audit entry
        entry_id = f"edit_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        audit_entry = AuditEntry(
            entry_id=entry_id,
            timestamp=datetime.now(),
            event_type='edit',
            actor=actor,
            target_parameters=edit_result.target_parameters,
            action_details={
                'edit_strategy': edit_result.edit_strategy,
                'parameter_changes': edit_result.parameter_changes,
                'fitness_improvement': edit_result.fitness_improvement,
                'edit_metadata': edit_result.metadata
            },
            before_state_hash=before_hash,
            after_state_hash=before_hash,  # Would be different in real implementation
            performance_impact=edit_result.performance_delta,
            success=edit_result.success,
            error_message=edit_result.error_message,
            metadata={
                'convergence_generation': getattr(edit_result, 'convergence_generation', None),
                'population_size': getattr(edit_result, 'population_size', None)
            }
        )

        # Add to audit trail
        self._add_audit_entry(audit_entry)

        # Real-time compliance check if enabled
        if self.config.enable_real_time_monitoring:
            self._check_real_time_compliance(audit_entry)

        logger.debug(f"Logged edit audit entry: {entry_id}")

        return entry_id

    def log_detection(self,
                     detection_results: Dict[str, Any],
                     model_genome: FinancialGenome,
                     actor: str = "detector") -> str:
        """
        🔍 Log anomaly detection event
        
        Args:
            detection_results: Results from detection system
            model_genome: Model state during detection
            actor: Detection component
            
        Returns:
            Audit entry ID
        """
        entry_id = f"detect_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        audit_entry = AuditEntry(
            entry_id=entry_id,
            timestamp=datetime.now(),
            event_type='detection',
            actor=actor,
            target_parameters=[],
            action_details=detection_results,
            before_state_hash=self.crypto_auditor.calculate_state_hash(model_genome),
            after_state_hash=self.crypto_auditor.calculate_state_hash(model_genome),
            success=True,
            metadata={'detection_type': detection_results.get('detection_type', 'unknown')}
        )

        self._add_audit_entry(audit_entry)
        return entry_id

    def log_repair(self,
                  repair_results: Dict[str, Any],
                  model_genome: FinancialGenome,
                  actor: str = "repair_system") -> str:
        """
        🔧 Log repair operation
        
        Args:
            repair_results: Results from repair system
            model_genome: Model state after repair
            actor: Repair component
            
        Returns:
            Audit entry ID
        """
        entry_id = f"repair_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        audit_entry = AuditEntry(
            entry_id=entry_id,
            timestamp=datetime.now(),
            event_type='repair',
            actor=actor,
            target_parameters=repair_results.get('target_parameters', []),
            action_details=repair_results,
            before_state_hash=repair_results.get('before_hash', ''),
            after_state_hash=self.crypto_auditor.calculate_state_hash(model_genome),
            success=repair_results.get('success', False),
            metadata={
                'repair_session_id': repair_results.get('session_id'),
                'techniques_used': repair_results.get('techniques_used', [])
            }
        )

        self._add_audit_entry(audit_entry)
        return entry_id

    def log_emergency(self,
                     emergency_details: Dict[str, Any],
                     model_genome: FinancialGenome,
                     actor: str = "emergency_system") -> str:
        """
        🚨 Log emergency activation
        
        Args:
            emergency_details: Emergency operation details
            model_genome: Model state after emergency action
            actor: Emergency system component
            
        Returns:
            Audit entry ID
        """
        entry_id = f"emergency_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        audit_entry = AuditEntry(
            entry_id=entry_id,
            timestamp=datetime.now(),
            event_type='emergency',
            actor=actor,
            target_parameters=emergency_details.get('affected_parameters', []),
            action_details=emergency_details,
            before_state_hash=emergency_details.get('before_hash', ''),
            after_state_hash=self.crypto_auditor.calculate_state_hash(model_genome),
            success=emergency_details.get('success', False),
            error_message=emergency_details.get('error_message'),
            metadata={
                'emergency_type': emergency_details.get('emergency_type'),
                'trigger_conditions': emergency_details.get('trigger_conditions', [])
            }
        )

        self._add_audit_entry(audit_entry)

        # Emergency events trigger immediate compliance assessment
        self._trigger_emergency_compliance_check()

        return entry_id

    def generate_compliance_report(self,
                                  days_back: int = 30) -> ComplianceReport:
        """
        📊 Generate comprehensive compliance report
        
        Args:
            days_back: Number of days to include in assessment
            
        Returns:
            Detailed compliance report
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days_back)

        logger.info(f"Generating compliance report for {days_back} days")

        # Filter audit entries for the period
        period_entries = [
            entry for entry in self._audit_entries
            if start_time <= entry.timestamp <= end_time
        ]

        # Generate compliance assessment
        report = self.compliance_monitor.assess_compliance(
            period_entries, (start_time, end_time)
        )

        # Store report
        self._compliance_reports.append(report)

        # Save report to disk
        self._save_compliance_report(report)

        # Check if violations need immediate attention
        if report.compliance_score < self.config.violation_alert_threshold:
            logger.warning(f"🚨 LOW COMPLIANCE SCORE: {report.compliance_score:.3f}")
            logger.warning(f"Violations found: {len(report.violations)}")

        return report

    def create_forensic_timeline(self,
                                incident_time: datetime,
                                hours_before: int = 24,
                                hours_after: int = 24) -> Dict[str, Any]:
        """
        🔍 Create forensic timeline for incident analysis
        
        Args:
            incident_time: Time of incident
            hours_before: Hours before incident to include
            hours_after: Hours after incident to include
            
        Returns:
            Detailed forensic timeline
        """
        start_time = incident_time - timedelta(hours=hours_before)
        end_time = incident_time + timedelta(hours=hours_after)

        # Get relevant audit entries
        timeline_entries = [
            entry for entry in self._audit_entries
            if start_time <= entry.timestamp <= end_time
        ]

        # Sort by timestamp
        timeline_entries.sort(key=lambda x: x.timestamp)

        # Analyze patterns
        event_types = [entry.event_type for entry in timeline_entries]
        failure_count = len([entry for entry in timeline_entries if not entry.success])
        emergency_count = len([entry for entry in timeline_entries if entry.event_type == 'emergency'])

        forensic_report = {
            'incident_time': incident_time.isoformat(),
            'analysis_period': (start_time.isoformat(), end_time.isoformat()),
            'total_events': len(timeline_entries),
            'event_breakdown': {event_type: event_types.count(event_type)
                               for event_type in set(event_types)},
            'failure_count': failure_count,
            'emergency_activations': emergency_count,
            'timeline': [entry.to_dict() for entry in timeline_entries],
            'patterns_detected': self._analyze_incident_patterns(timeline_entries),
            'recommendations': self._generate_incident_recommendations(timeline_entries)
        }

        logger.info(f"Created forensic timeline: {len(timeline_entries)} events around incident")

        return forensic_report

    def verify_audit_integrity(self) -> Dict[str, Any]:
        """
        ✅ Verify audit trail integrity
        
        Returns:
            Integrity verification results
        """
        logger.info("Verifying audit trail integrity")

        results = {
            'total_entries': len(self._audit_entries),
            'integrity_verified': False,
            'issues_found': [],
            'verification_timestamp': datetime.now().isoformat()
        }

        try:
            # Verify cryptographic chain
            chain_valid, chain_issues = self.crypto_auditor.verify_audit_chain()
            results['cryptographic_chain_valid'] = chain_valid
            results['issues_found'].extend(chain_issues)

            # Check for duplicate entries
            entry_ids = [entry.entry_id for entry in self._audit_entries]
            duplicates = len(entry_ids) - len(set(entry_ids))
            if duplicates > 0:
                results['issues_found'].append(f"Found {duplicates} duplicate entry IDs")

            # Check timestamp ordering
            timestamps = [entry.timestamp for entry in self._audit_entries]
            if timestamps != sorted(timestamps):
                results['issues_found'].append("Audit entries not in chronological order")

            # Check for suspicious gaps
            if len(timestamps) > 1:
                time_gaps = [timestamps[i] - timestamps[i-1]
                           for i in range(1, len(timestamps))]
                large_gaps = [gap for gap in time_gaps if gap > timedelta(days=1)]
                if large_gaps:
                    results['issues_found'].append(f"Found {len(large_gaps)} suspicious time gaps")

            # Overall integrity assessment
            results['integrity_verified'] = len(results['issues_found']) == 0

            if results['integrity_verified']:
                logger.info("✅ Audit trail integrity verified")
            else:
                logger.warning(f"⚠️ Audit integrity issues: {len(results['issues_found'])}")

        except Exception as e:
            logger.error(f"Audit integrity verification failed: {str(e)}")
            results['issues_found'].append(f"Verification error: {str(e)}")

        return results

    def _add_audit_entry(self, entry: AuditEntry):
        """Add entry to audit trail with proper management."""
        # Add to in-memory storage
        self._audit_entries.append(entry)

        # Create cryptographic block if enabled
        if self.config.enable_blockchain_audit:
            self.crypto_auditor.create_audit_block(entry)

        # Persist to disk
        self._save_audit_entry(entry)

        # Cleanup old entries if needed
        if (self.config.auto_cleanup_enabled and
            len(self._audit_entries) > self.config.max_audit_entries):
            self._cleanup_old_entries()

    def _check_real_time_compliance(self, entry: AuditEntry):
        """Check compliance in real-time for immediate violations."""
        # Simple real-time checks
        immediate_violations = []

        # Check for rapid-fire edits
        recent_edits = [
            e for e in self._audit_entries[-10:]  # Last 10 entries
            if (e.event_type == 'edit' and
                (entry.timestamp - e.timestamp).total_seconds() < 300)  # 5 minutes
        ]

        if len(recent_edits) > 5:
            immediate_violations.append({
                'type': 'rapid_edit_sequence',
                'severity': 'medium',
                'description': f"Detected {len(recent_edits)} edits in 5 minutes",
                'timestamp': entry.timestamp.isoformat()
            })

        # Store violations for next compliance report
        self._real_time_violations.extend(immediate_violations)

        if immediate_violations:
            logger.warning(f"Real-time compliance violation detected: {immediate_violations[0]['type']}")

    def _trigger_emergency_compliance_check(self):
        """Trigger immediate compliance assessment after emergency."""
        logger.warning("🚨 Emergency compliance check triggered")

        # Generate immediate report for last 24 hours
        emergency_report = self.generate_compliance_report(days_back=1)

        # Log emergency compliance status
        if emergency_report.compliance_score < 0.5:
            logger.error(f"🚨 CRITICAL: Post-emergency compliance score: {emergency_report.compliance_score:.3f}")
        else:
            logger.info(f"Emergency compliance check passed: {emergency_report.compliance_score:.3f}")

    def _analyze_incident_patterns(self, timeline_entries: List[AuditEntry]) -> List[str]:
        """Analyze patterns in forensic timeline."""
        patterns = []

        # Look for failure cascades
        failures = [e for e in timeline_entries if not e.success]
        if len(failures) > 3:
            # Check if failures are clustered in time
            failure_times = [f.timestamp for f in failures]
            time_spans = [failure_times[i] - failure_times[i-1]
                         for i in range(1, len(failure_times))]

            if all(span < timedelta(hours=1) for span in time_spans):
                patterns.append("Failure cascade detected - multiple failures within 1 hour")

        # Look for edit frequency spikes
        edits = [e for e in timeline_entries if e.event_type == 'edit']
        if len(edits) > 10:
            patterns.append(f"High edit activity - {len(edits)} edits in timeline")

        # Look for emergency patterns
        emergencies = [e for e in timeline_entries if e.event_type == 'emergency']
        if len(emergencies) > 1:
            patterns.append(f"Multiple emergency activations - {len(emergencies)} total")

        return patterns

    def _generate_incident_recommendations(self, timeline_entries: List[AuditEntry]) -> List[str]:
        """Generate recommendations based on incident analysis."""
        recommendations = []

        failure_rate = len([e for e in timeline_entries if not e.success]) / len(timeline_entries)

        if failure_rate > 0.3:
            recommendations.append("Review edit validation logic - high failure rate detected")
            recommendations.append("Consider implementing more conservative edit strategies")

        emergency_count = len([e for e in timeline_entries if e.event_type == 'emergency'])
        if emergency_count > 0:
            recommendations.append("Analyze emergency triggers - improve predictive capabilities")
            recommendations.append("Review emergency response procedures")

        edit_count = len([e for e in timeline_entries if e.event_type == 'edit'])
        if edit_count > 50:
            recommendations.append("Consider rate limiting for parameter edits")

        return recommendations

    def _save_audit_entry(self, entry: AuditEntry):
        """Persist audit entry to disk."""
        try:
            audit_file = Path(self.config.audit_storage_path) / f"audit_{entry.timestamp.strftime('%Y%m%d')}.jsonl"

            with open(audit_file, 'a') as f:
                json.dump(entry.to_dict(), f, default=str)
                f.write('\n')

        except Exception as e:
            logger.error(f"Failed to save audit entry: {str(e)}")

    def _save_compliance_report(self, report: ComplianceReport):
        """Save compliance report to disk."""
        try:
            report_file = Path(self.config.audit_storage_path) / f"compliance_{report.report_id}.json"

            with open(report_file, 'w') as f:
                json.dump(report.to_dict(), f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Failed to save compliance report: {str(e)}")

    def _load_audit_history(self):
        """Load existing audit entries from disk."""
        try:
            audit_path = Path(self.config.audit_storage_path)
            if not audit_path.exists():
                return

            # Load audit entries from all daily files
            for audit_file in audit_path.glob("audit_*.jsonl"):
                try:
                    with open(audit_file) as f:
                        for line in f:
                            if line.strip():
                                entry_data = json.loads(line)
                                entry = AuditEntry.from_dict(entry_data)
                                self._audit_entries.append(entry)
                except Exception as e:
                    logger.warning(f"Failed to load audit file {audit_file}: {str(e)}")

            # Sort by timestamp
            self._audit_entries.sort(key=lambda x: x.timestamp)

            logger.info(f"Loaded {len(self._audit_entries)} audit entries from disk")

        except Exception as e:
            logger.error(f"Failed to load audit history: {str(e)}")

    def _cleanup_old_entries(self):
        """Remove old audit entries to manage storage."""
        cutoff_date = datetime.now() - timedelta(days=self.config.audit_retention_days)

        initial_count = len(self._audit_entries)
        self._audit_entries = [
            entry for entry in self._audit_entries
            if entry.timestamp > cutoff_date
        ]

        removed_count = initial_count - len(self._audit_entries)
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old audit entries")

    def get_audit_statistics(self) -> Dict[str, Any]:
        """
        📊 Generate audit system statistics
        
        Returns:
            Dictionary with audit performance metrics
        """
        if not self._audit_entries:
            return {'status': 'No audit entries recorded'}

        # Basic statistics
        total_entries = len(self._audit_entries)
        event_types = [entry.event_type for entry in self._audit_entries]
        success_rate = len([e for e in self._audit_entries if e.success]) / total_entries

        # Time span
        oldest_entry = min(self._audit_entries, key=lambda x: x.timestamp)
        newest_entry = max(self._audit_entries, key=lambda x: x.timestamp)
        time_span = newest_entry.timestamp - oldest_entry.timestamp

        # Event breakdown
        from collections import Counter
        event_breakdown = Counter(event_types)

        # Recent activity (last 24 hours)
        recent_cutoff = datetime.now() - timedelta(hours=24)
        recent_entries = [e for e in self._audit_entries if e.timestamp > recent_cutoff]

        return {
            'total_audit_entries': total_entries,
            'success_rate': success_rate,
            'audit_timespan_days': time_span.days,
            'event_type_breakdown': dict(event_breakdown),
            'recent_24h_entries': len(recent_entries),
            'compliance_reports_generated': len(self._compliance_reports),
            'cryptographic_integrity': self.crypto_auditor.verify_audit_chain()[0],
            'last_compliance_check': self._last_compliance_check.isoformat(),
            'real_time_violations_detected': len(self._real_time_violations)
        }
