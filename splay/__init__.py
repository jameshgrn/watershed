"""Splay - parallel inference with coherence for watershed.

A watershed-native rim surface. Provider backends are swappable; the package
ships Fireworks and local OpenAI-compatible Gemma providers.
"""

from splay.src.angles import CANONICAL_ANGLES, get_angle, list_angles, resolve_angles
from splay.src.models import (
    Angle,
    AngleSummary,
    CrossAngleConflict,
    SplayJob,
    SplayReturn,
)
from splay.src.orchestrator import SplayOrchestrator
from splay.src.providers import (
    FireworksProvider,
    GemmaProvider,
    OpenAICompatibleProvider,
)

__all__ = [
    "Angle",
    "AngleSummary",
    "CANONICAL_ANGLES",
    "CrossAngleConflict",
    "SplayJob",
    "SplayReturn",
    "SplayOrchestrator",
    "FireworksProvider",
    "GemmaProvider",
    "OpenAICompatibleProvider",
    "get_angle",
    "list_angles",
    "resolve_angles",
]
