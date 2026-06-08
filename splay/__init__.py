"""Splay — Parallel inference with coherence for watershed.

A watershed-native rim surface. Uses the Fireworks backend (same as FirePass)
but owns the orchestration, record types, and coherence step.
"""

from splay.src.models import (
    Angle,
    AngleSummary,
    CrossAngleConflict,
    SplayJob,
    SplayReturn,
)
from splay.src.orchestrator import SplayOrchestrator
from splay.src.providers import FireworksProvider

__all__ = [
    "Angle",
    "AngleSummary",
    "CrossAngleConflict",
    "SplayJob",
    "SplayReturn",
    "SplayOrchestrator",
    "FireworksProvider",
]
