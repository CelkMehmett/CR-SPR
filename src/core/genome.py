"""
🧬 Financial Genome — Model Parameter Structure

Represents the complete parameter "genome" of a financial model,
enabling CRISPR-like precision editing and state management.

Think like biology. Code like AI.
"""

from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
import json
import hashlib
from pathlib import Path


@dataclass
class ParameterGene:
    """
    🧬 Individual Parameter Gene
    
    Represents a single parameter in the model genome, containing
    its value, metadata, and edit history like a gene sequence.
    """
    name: str
    value: Any
    param_type: str  # 'weight', 'bias', 'hyperparameter', 'strategy'
    shape: Optional[Tuple] = None
    constraints: Optional[Dict[str, Any]] = None
    last_modified: datetime = field(default_factory=datetime.now)
    edit_count: int = 0
    frozen: bool = False  # Prevent editing if True
    importance_score: float = 0.5  # 0.0-1.0, higher = more critical

    def __post_init__(self):
        """Post-initialization validation and setup."""
        if isinstance(self.value, np.ndarray):
            self.shape = self.value.shape
        elif hasattr(self.value, 'shape'):
            self.shape = tuple(self.value.shape)

    def get_hash(self) -> str:
        """Generate hash of current parameter value for change detection."""
        if isinstance(self.value, np.ndarray):
            return hashlib.md5(self.value.tobytes()).hexdigest()
        return hashlib.md5(str(self.value).encode()).hexdigest()

    def update_value(self, new_value: Any, edit_reason: str = "manual"):
        """
        Update parameter value with change tracking.
        
        Args:
            new_value: New parameter value
            edit_reason: Reason for the edit (for audit trail)
        """
        if self.frozen:
            raise ValueError(f"Parameter {self.name} is frozen and cannot be edited")

        self.value = new_value
        self.last_modified = datetime.now()
        self.edit_count += 1

        # Update shape if needed
        if isinstance(new_value, np.ndarray):
            self.shape = new_value.shape
        elif hasattr(new_value, 'shape'):
            self.shape = tuple(new_value.shape)


class FinancialGenome:
    """
    🧬 Financial Model Genome
    
    Complete parameter structure of a financial model, organized like
    a biological genome with chromosomes (modules), genes (parameters),
    and regulatory regions (constraints and metadata).
    
    Biological Analogy:
    - Genome → Complete Model
    - Chromosome → Model Module/Layer
    - Gene → Individual Parameter
    - Alleles → Parameter Variants
    - Mutations → Parameter Changes
    """

    def __init__(self, name: str, model_type: str = "financial_ml"):
        """
        Initialize a new financial genome.
        
        Args:
            name: Identifier for this model genome
            model_type: Type of model (e.g., 'trading_strategy', 'risk_model')
        """
        self.name = name
        self.model_type = model_type
        self.creation_time = datetime.now()
        self.last_edit_time = datetime.now()

        # Genome structure - organized by chromosomes (modules)
        self._chromosomes: Dict[str, Dict[str, ParameterGene]] = {}

        # Genome metadata
        self._metadata = {
            'version': '1.0',
            'generation': 1,
            'parent_genomes': [],
            'performance_metrics': {},
            'edit_history': []
        }

        # Health and integrity tracking
        self._health_score = 1.0
        self._integrity_hash = ""
        self._backup_snapshots = []

    def add_chromosome(self, chromosome_name: str) -> None:
        """
        🧬 Add a new chromosome (module) to the genome.
        
        Args:
            chromosome_name: Name of the new chromosome/module
        """
        if chromosome_name not in self._chromosomes:
            self._chromosomes[chromosome_name] = {}

    def add_gene(self,
                 chromosome: str,
                 gene_name: str,
                 value: Any,
                 param_type: str = "parameter",
                 constraints: Optional[Dict[str, Any]] = None,
                 importance: float = 0.5) -> None:
        """
        🧬 Add a new gene (parameter) to a chromosome.
        
        Args:
            chromosome: Chromosome name to add gene to
            gene_name: Name of the parameter
            value: Initial parameter value
            param_type: Type of parameter
            constraints: Value constraints and bounds
            importance: Importance score (0.0-1.0)
        """
        if chromosome not in self._chromosomes:
            self.add_chromosome(chromosome)

        gene = ParameterGene(
            name=gene_name,
            value=value,
            param_type=param_type,
            constraints=constraints,
            importance_score=importance
        )

        self._chromosomes[chromosome][gene_name] = gene
        self._update_integrity_hash()

    def get_parameter(self, path: str) -> Any:
        """
        🔍 Get parameter value by path (chromosome.gene).
        
        Args:
            path: Parameter path in format "chromosome.gene"
            
        Returns:
            Parameter value
        """
        parts = path.split('.')
        if len(parts) != 2:
            raise ValueError(f"Invalid parameter path: {path}. Use format 'chromosome.gene'")

        chromosome, gene = parts
        if chromosome not in self._chromosomes:
            raise KeyError(f"Chromosome '{chromosome}' not found")

        if gene not in self._chromosomes[chromosome]:
            raise KeyError(f"Gene '{gene}' not found in chromosome '{chromosome}'")

        return self._chromosomes[chromosome][gene].value

    def set_parameter(self, path: str, value: Any, edit_reason: str = "manual") -> None:
        """
        ✂️ Set parameter value by path (used by editors).
        
        Args:
            path: Parameter path in format "chromosome.gene"
            value: New parameter value
            edit_reason: Reason for the edit
        """
        parts = path.split('.')
        if len(parts) != 2:
            raise ValueError(f"Invalid parameter path: {path}")

        chromosome, gene = parts
        if chromosome not in self._chromosomes:
            raise KeyError(f"Chromosome '{chromosome}' not found")

        if gene not in self._chromosomes[chromosome]:
            raise KeyError(f"Gene '{gene}' not found")

        old_value = self._chromosomes[chromosome][gene].value
        self._chromosomes[chromosome][gene].update_value(value, edit_reason)

        # Update genome metadata
        self.last_edit_time = datetime.now()
        self._metadata['edit_history'].append({
            'path': path,
            'old_value': str(old_value),
            'new_value': str(value),
            'timestamp': self.last_edit_time,
            'reason': edit_reason
        })

        self._update_integrity_hash()

    def get_gene(self, path: str) -> ParameterGene:
        """
        🧬 Get complete gene object by path.
        
        Args:
            path: Parameter path in format "chromosome.gene"
            
        Returns:
            Complete ParameterGene object
        """
        parts = path.split('.')
        if len(parts) != 2:
            raise ValueError(f"Invalid parameter path: {path}")

        chromosome, gene = parts
        return self._chromosomes[chromosome][gene]

    def list_chromosomes(self) -> List[str]:
        """📋 List all chromosome names."""
        return list(self._chromosomes.keys())

    def list_genes(self, chromosome: str) -> List[str]:
        """📋 List all gene names in a chromosome."""
        if chromosome not in self._chromosomes:
            raise KeyError(f"Chromosome '{chromosome}' not found")
        return list(self._chromosomes[chromosome].keys())

    def get_all_parameters(self) -> Dict[str, Any]:
        """
        📊 Get all parameters as a flat dictionary.
        
        Returns:
            Dictionary with full paths as keys and values
        """
        params = {}
        for chromosome_name, chromosome in self._chromosomes.items():
            for gene_name, gene in chromosome.items():
                path = f"{chromosome_name}.{gene_name}"
                params[path] = gene.value
        return params

    def get_critical_parameters(self, threshold: float = 0.7) -> Dict[str, ParameterGene]:
        """
        🎯 Get parameters with high importance scores.
        
        Args:
            threshold: Minimum importance score to include
            
        Returns:
            Dictionary of critical parameters
        """
        critical = {}
        for chromosome_name, chromosome in self._chromosomes.items():
            for gene_name, gene in chromosome.items():
                if gene.importance_score >= threshold:
                    path = f"{chromosome_name}.{gene_name}"
                    critical[path] = gene
        return critical

    def freeze_parameter(self, path: str) -> None:
        """🔒 Freeze a parameter to prevent editing."""
        gene = self.get_gene(path)
        gene.frozen = True

    def unfreeze_parameter(self, path: str) -> None:
        """🔓 Unfreeze a parameter to allow editing."""
        gene = self.get_gene(path)
        gene.frozen = False

    def create_snapshot(self) -> Dict[str, Any]:
        """
        📸 Create a complete genome snapshot for backup/rollback.
        
        Returns:
            Complete genome state as a serializable dictionary
        """
        snapshot = {
            'name': self.name,
            'model_type': self.model_type,
            'creation_time': self.creation_time.isoformat(),
            'snapshot_time': datetime.now().isoformat(),
            'metadata': self._metadata.copy(),
            'chromosomes': {}
        }

        for chrom_name, chromosome in self._chromosomes.items():
            snapshot['chromosomes'][chrom_name] = {}
            for gene_name, gene in chromosome.items():
                snapshot['chromosomes'][chrom_name][gene_name] = {
                    'name': gene.name,
                    'value': gene.value.tolist() if isinstance(gene.value, np.ndarray) else gene.value,
                    'param_type': gene.param_type,
                    'shape': gene.shape,
                    'constraints': gene.constraints,
                    'last_modified': gene.last_modified.isoformat(),
                    'edit_count': gene.edit_count,
                    'frozen': gene.frozen,
                    'importance_score': gene.importance_score
                }

        return snapshot

    def restore_from_snapshot(self, snapshot: Dict[str, Any]) -> None:
        """
        📡 Restore genome state from a snapshot.
        
        Args:
            snapshot: Previously created genome snapshot
        """
        self.name = snapshot['name']
        self.model_type = snapshot['model_type']
        self.creation_time = datetime.fromisoformat(snapshot['creation_time'])
        self._metadata = snapshot['metadata'].copy()

        # Clear current state
        self._chromosomes.clear()

        # Restore chromosomes and genes
        for chrom_name, chromosome_data in snapshot['chromosomes'].items():
            self.add_chromosome(chrom_name)

            for gene_name, gene_data in chromosome_data.items():
                # Convert list back to numpy array if needed
                value = gene_data['value']
                if gene_data['shape'] and isinstance(value, list):
                    value = np.array(value).reshape(gene_data['shape'])

                gene = ParameterGene(
                    name=gene_data['name'],
                    value=value,
                    param_type=gene_data['param_type'],
                    shape=gene_data['shape'],
                    constraints=gene_data['constraints'],
                    last_modified=datetime.fromisoformat(gene_data['last_modified']),
                    edit_count=gene_data['edit_count'],
                    frozen=gene_data['frozen'],
                    importance_score=gene_data['importance_score']
                )

                self._chromosomes[chrom_name][gene_name] = gene

        self._update_integrity_hash()

    def save_to_file(self, filepath: Union[str, Path]) -> None:
        """
        💾 Save genome to file.
        
        Args:
            filepath: Path to save the genome
        """
        snapshot = self.create_snapshot()

        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w') as f:
            json.dump(snapshot, f, indent=2, default=str)

    def load_from_file(self, filepath: Union[str, Path]) -> None:
        """
        📂 Load genome from file.
        
        Args:
            filepath: Path to load the genome from
        """
        with open(filepath) as f:
            snapshot = json.load(f)

        self.restore_from_snapshot(snapshot)

    def calculate_health_score(self) -> float:
        """
        🏥 Calculate overall genome health score.
        
        Considers parameter consistency, constraint violations,
        and overall stability indicators.
        
        Returns:
            Health score (0.0-1.0), higher = healthier
        """
        total_params = 0
        healthy_params = 0

        for chromosome in self._chromosomes.values():
            for gene in chromosome.values():
                total_params += 1

                # Check constraints
                if gene.constraints:
                    if self._check_constraints(gene):
                        healthy_params += 1
                else:
                    healthy_params += 1

        if total_params == 0:
            return 1.0

        self._health_score = healthy_params / total_params
        return self._health_score

    def _check_constraints(self, gene: ParameterGene) -> bool:
        """Check if a gene's value satisfies its constraints."""
        if not gene.constraints:
            return True

        value = gene.value
        constraints = gene.constraints

        # Check bounds
        if 'min' in constraints and np.any(value < constraints['min']):
            return False
        if 'max' in constraints and np.any(value > constraints['max']):
            return False

        # Check type constraints
        if 'dtype' in constraints:
            expected_type = constraints['dtype']
            if not isinstance(value, expected_type):
                return False

        return True

    def _update_integrity_hash(self) -> None:
        """Update the genome integrity hash for change detection."""
        # Create a hash based on all parameter values
        hash_input = ""
        for chromosome_name in sorted(self._chromosomes.keys()):
            for gene_name in sorted(self._chromosomes[chromosome_name].keys()):
                gene = self._chromosomes[chromosome_name][gene_name]
                hash_input += f"{chromosome_name}.{gene_name}:{gene.get_hash()}"

        self._integrity_hash = hashlib.sha256(hash_input.encode()).hexdigest()

    def get_integrity_hash(self) -> str:
        """Get current genome integrity hash."""
        return self._integrity_hash

    def __str__(self) -> str:
        """String representation of the genome."""
        total_params = sum(len(chrom) for chrom in self._chromosomes.values())
        health = self.calculate_health_score()

        return (f"FinancialGenome(name='{self.name}', "
                f"chromosomes={len(self._chromosomes)}, "
                f"parameters={total_params}, "
                f"health={health:.3f})")

    def __repr__(self) -> str:
        """Detailed representation of the genome."""
        return self.__str__()
