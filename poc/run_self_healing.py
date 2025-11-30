"""Compatibility wrapper to expose `run` from the POC runner.

This ensures imports using lowercase `poc` work regardless of filesystem casing.
"""
from __future__ import annotations
import importlib

try:
    mod = importlib.import_module('poC.run_self_healing')
except Exception:
    # fallback to local implementation if present
    mod = importlib.import_module('poC.run_self_healing')

run = getattr(mod, 'run')
