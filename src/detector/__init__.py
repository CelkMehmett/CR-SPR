"""
🔬 Detector Module — Genome Sequencing Laboratory

Exports anomaly detection components for the CRISPR-FinAI system.
"""

from .isolation_detector import *

__all__ = [
    "IsolationDetector",
    "AnomalySignature"
]
