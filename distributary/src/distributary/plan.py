"""Plan schema and validator for distributary.

Ported from dgov plan.py — narrow subset for v0 outbound records.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal

from distributary._compat import _normalize_path, _paths_overlap

_SLUG_RE = re.compile(r"^[a-z0-9-]+$")


@dataclass(frozen=True, slots=True)
class PlanUnitFiles:
    """Exact file scope for a plan unit."""

    create: tuple[str, ...] = ()
    edit: tuple[str, ...] = ()
    delete: tuple[str, ...] = ()
    read: tuple[str, ...] = ()
    touch: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "create", tuple(self.create))
        object.__setattr__(self, "edit", tuple(self.edit))
        object.__setattr__(self, "delete", tuple(self.delete))
        object.__setattr__(self, "read", tuple(self.read))
        object.__setattr__(self, "touch", tuple(self.touch))


@dataclass(frozen=True, slots=True)
class PlanUnit:
    """A single unit of work in a plan."""

    slug: str
    summary: str
    prompt: str
    commit_message: str
    files: PlanUnitFiles
    depends_on: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "depends_on", tuple(self.depends_on))


@dataclass(frozen=True, slots=True)
class PlanSpec:
    """A governor's execution plan."""

    name: str
    goal: str
    units: Mapping[str, PlanUnit]

    def __post_init__(self) -> None:
        object.__setattr__(self, "units", MappingProxyType(dict(self.units)))


@dataclass(frozen=True, slots=True)
class PlanIssue:
    """A validation issue found in a plan."""

    severity: Literal["error", "warning"]
    message: str
    unit: str | None = None


class PlanValidationError(ValueError):
    """Raised when a plan has structural errors that prevent execution."""

    def __init__(self, issues: list[PlanIssue]) -> None:
        self.issues = issues
        msgs = [f"[{i.severity}] {i.message}" for i in issues]
        super().__init__("Plan validation failed:\n" + "\n".join(msgs))


def _all_touches(unit: PlanUnit) -> set[str]:
    """All file paths a unit claims to write (create + edit + delete + touch)."""
    return {
        _normalize_path(p)
        for p in (*unit.files.create, *unit.files.edit, *unit.files.delete, *unit.files.touch)
        if p.strip()
    }


def _are_independent(a: str, b: str, units: Mapping[str, PlanUnit]) -> bool:
    """True if neither unit depends (directly or transitively) on the other."""

    def _reachable(start: str) -> set[str]:
        visited: set[str] = set()
        stack = list(units[start].depends_on) if start in units else []
        while stack:
            node = stack.pop()
            if node in visited:
                continue
            visited.add(node)
            if node in units:
                stack.extend(units[node].depends_on)
        return visited

    return b not in _reachable(a) and a not in _reachable(b)


def _check_file_claim_conflicts(plan: PlanSpec) -> list[PlanIssue]:
    issues: list[PlanIssue] = []
    slugs = list(plan.units.keys())
    for i, slug_a in enumerate(slugs):
        touches_a = _all_touches(plan.units[slug_a])
        if not touches_a:
            continue
        for slug_b in slugs[i + 1 :]:
            issues.extend(_file_conflict_issues(slug_a, touches_a, slug_b, plan.units))
    return issues


def _file_conflict_issues(
    slug_a: str,
    touches_a: set[str],
    slug_b: str,
    units: Mapping[str, PlanUnit],
) -> list[PlanIssue]:
    touches_b = _all_touches(units[slug_b])
    if not touches_b or not _are_independent(slug_a, slug_b, units):
        return []
    return [
        PlanIssue(
            severity="error",
            message=(
                f"File conflict: '{slug_a}' and '{slug_b}' "
                f"both touch '{path_a}' but have no dependency edge"
            ),
        )
        for path_a in touches_a
        for path_b in touches_b
        if _paths_overlap(path_a, path_b)
    ]


def _check_slugs(plan: PlanSpec) -> list[PlanIssue]:
    issues: list[PlanIssue] = []
    for slug, unit in plan.units.items():
        if not _SLUG_RE.match(slug):
            issues.append(
                PlanIssue(
                    severity="error",
                    message=f"Invalid slug '{slug}': must match ^[a-z0-9-]+$",
                    unit=slug,
                )
            )
        if slug != unit.slug:
            issues.append(
                PlanIssue(
                    severity="error",
                    message=f"Plan unit key '{slug}' does not match unit slug '{unit.slug}'",
                    unit=slug,
                )
            )
    return issues


def _check_dependencies(plan: PlanSpec) -> list[PlanIssue]:
    issues: list[PlanIssue] = []
    for slug, unit in plan.units.items():
        for dependency in unit.depends_on:
            if dependency not in plan.units:
                issues.append(
                    PlanIssue(
                        severity="error",
                        message=f"Plan unit '{slug}' depends on unknown unit '{dependency}'",
                        unit=slug,
                    )
                )
    return issues


def _check_cycles(plan: PlanSpec) -> list[PlanIssue]:
    visiting: set[str] = set()
    visited: set[str] = set()

    def _visit(slug: str, path: tuple[str, ...]) -> PlanIssue | None:
        if slug in visiting:
            cycle_start = path.index(slug) if slug in path else 0
            cycle = (*path[cycle_start:], slug)
            return PlanIssue(
                severity="error",
                message=f"Plan dependency cycle: {' -> '.join(cycle)}",
                unit=slug,
            )
        if slug in visited or slug not in plan.units:
            return None
        visiting.add(slug)
        for dependency in plan.units[slug].depends_on:
            issue = _visit(dependency, (*path, slug))
            if issue is not None:
                return issue
        visiting.remove(slug)
        visited.add(slug)
        return None

    issues: list[PlanIssue] = []
    for slug in plan.units:
        issue = _visit(slug, ())
        if issue is not None:
            issues.append(issue)
            break
    return issues


def validate_plan(plan: PlanSpec) -> list[PlanIssue]:
    """Structural validation of a plan.

    Checks:
    1. Slug format
    2. Unit key/slug alignment
    3. Dependency existence and acyclicity
    4. File-claim conflicts between independent tasks
    """
    issues: list[PlanIssue] = []
    issues.extend(_check_slugs(plan))
    issues.extend(_check_dependencies(plan))
    issues.extend(_check_cycles(plan))
    issues.extend(_check_file_claim_conflicts(plan))
    return issues
