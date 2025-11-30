"""
🧬 CRISPR-FinAI — Bio-Inspired Adaptive Financial Intelligence

A modular framework inspired by CRISPR gene-editing principles for financial modeling
and self-repairing algorithms. Think like biology. Code like AI.

Author: CRISPR-FinAI Project
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "CRISPR-FinAI Project"

# Import core modules
from .core.base_layers import *
from .core.genome import *

__all__ = [
    "BaseDetector",
    "BaseGuide",
    "BaseEditor",
    "BaseRepair",
    "BaseAudit",
    "FinancialGenome",
    "EditResult"
]
