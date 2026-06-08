"""Splay record types — rim-native, not kernel artifacts."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal


class SplayJobState(Enum):
    QUEUED = "queued"
    SPLATTING = "splatting"
    COHERING = "cohering"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Certainty(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ConflictType(Enum):
    CONTRADICTION = "contradiction"
    TENSION = "tension"
    OMISSION = "omission"
    PRIORITY = "priority"


@dataclass
class Angle:
    name: str
    prompt: str
    model_hint: str | None = None
    context_overrides: list[str] | None = None


@dataclass
class AngleSummary:
    angle_name: str
    key_findings: list[str] = field(default_factory=list)
    certainty: Certainty = Certainty.MEDIUM
    recommendation: str | None = None
    raw_job_id: str | None = None


@dataclass
class CrossAngleConflict:
    angles: list[str]
    conflict_type: ConflictType
    description: str
    suggested_resolution: str | None = None


@dataclass
class SplayJob:
    id: str
    context_refs: list[str]
    angles: list[Angle]
    coherence_prompt: str | None = None
    coherence_model: str | None = None
    state: SplayJobState = SplayJobState.QUEUED
    created_by: str | None = None
    created_at: str | None = None
    splatted_at: str | None = None
    cohered_at: str | None = None


@dataclass
class SplayReturn:
    job_id: str
    synthesis: str
    conflicts: list[CrossAngleConflict] = field(default_factory=list)
    certainty: Certainty = Certainty.MEDIUM
    recommended_next_surface: Literal["intent", "brief", "plan", "none"] = "none"
    raw_summaries: dict[str, AngleSummary] = field(default_factory=dict)
