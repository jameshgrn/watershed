"""Splay orchestrator — parallel dispatch with coherence.

Fans out N angle jobs in parallel, then runs a single coherence job.
All jobs are read-only; no writes to the filesystem.
"""

import asyncio
from typing import Literal

from splay.src.models import (
    Angle,
    AngleSummary,
    Certainty,
    CrossAngleConflict,
    ConflictType,
    SplayJob,
    SplayJobState,
    SplayReturn,
)
from splay.src.providers import Provider


DEFAULT_COHERENCE_PROMPT = """\
You are a synthesis engine. You receive N angle summaries from a parallel review
of a single problem. Your job is to produce a coherent synthesis that a human
mediator can act on.

Produce:
1. A concise synthesis (2-4 paragraphs) of the key findings across all angles.
2. A list of conflicts between angles (contradictions, tensions, omissions, priorities).
3. A certainty assessment: HIGH if all angles agree, MEDIUM if there are tensions,
   LOW if there are contradictions.
4. A recommended next action: intent (compile a watershed intent), brief (open an
   Engineer Brief), plan (draft a watershed plan), or none (no action needed).

Format your response as:

SYNTHESIS:
<text>

CONFLICTS:
- [type] angle1 vs angle2: <description> [resolution: <suggestion>]

CERTAINTY: HIGH|MEDIUM|LOW

NEXT: intent|brief|plan|none
"""


class SplayOrchestrator:
    """Run a splay job: parallel angles, then coherence."""

    def __init__(self, provider: Provider):
        self.provider = provider

    def submit(self, job: SplayJob) -> SplayReturn:
        """Run the full splay lifecycle synchronously."""
        job.state = SplayJobState.SPLATTING
        summaries = self._run_angles(job)
        job.splatted_at = "now"

        job.state = SplayJobState.COHERING
        raw = self._run_coherence(job, summaries)
        job.cohered_at = "now"
        job.state = SplayJobState.COMPLETED

        return self._parse_coherence(raw, job.id, summaries)

    def _run_angles(self, job: SplayJob) -> dict[str, AngleSummary]:
        """Dispatch all angles in parallel via asyncio."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(
                asyncio.gather(*[self._run_angle(job, a) for a in job.angles])
            )
        finally:
            loop.close()
        return {s.angle_name: s for s in results}

    async def _run_angle(self, job: SplayJob, angle: Angle) -> AngleSummary:
        """Run a single angle as a read-only inference call."""
        context = self._load_context(job, angle)
        system = (
            f"You are a specialized reviewer. Your angle is: {angle.name}.\n"
            "You are read-only. You may not suggest file edits or code changes. "
            "You report findings only."
        )
        user = f"Context:\n{context}\n\nTask:\n{angle.prompt}"
        raw = self.provider.infer(system, user)
        return self._parse_angle(raw, angle.name)

    def _load_context(self, job: SplayJob, angle: Angle) -> str:
        """Load context files. Concatenate with headers."""
        refs = angle.context_overrides or job.context_refs
        parts = []
        for ref in refs:
            try:
                with open(ref, "r", encoding="utf-8") as f:
                    parts.append(f"--- {ref} ---\n{f.read()}")
            except FileNotFoundError:
                parts.append(f"--- {ref} ---\n[file not found]")
        return "\n\n".join(parts)

    def _parse_angle(self, raw: str, name: str) -> AngleSummary:
        """Parse a raw angle response into a structured summary.

        This is a lightweight parser. For now, we treat the whole response as
        a single key finding. Later we can improve extraction.
        """
        return AngleSummary(
            angle_name=name,
            key_findings=[raw.strip()],
            certainty=Certainty.MEDIUM,
        )

    def _run_coherence(self, job: SplayJob, summaries: dict[str, AngleSummary]) -> str:
        """Run the coherence step as a single inference call."""
        system = job.coherence_prompt or DEFAULT_COHERENCE_PROMPT
        user = self._format_summaries(summaries)
        return self.provider.infer(system, user)

    def _format_summaries(self, summaries: dict[str, AngleSummary]) -> str:
        """Format angle summaries for the coherence prompt."""
        parts = []
        for name, summary in summaries.items():
            parts.append(f"--- {name} ---\n{chr(10).join(summary.key_findings)}")
        return "\n\n".join(parts)

    def _parse_coherence(
        self, raw: str, job_id: str, summaries: dict[str, AngleSummary]
    ) -> SplayReturn:
        """Parse the coherence response into a SplayReturn.

        Uses a simple line-based parser. Tolerates malformed output.
        """
        synthesis = ""
        conflicts: list[CrossAngleConflict] = []
        certainty = Certainty.MEDIUM
        next_surface: Literal["intent", "brief", "plan", "none"] = "none"

        lines = raw.strip().splitlines()
        section = None
        buffer: list[str] = []

        for line in lines:
            if line.startswith("SYNTHESIS:"):
                section = "synthesis"
                continue
            if line.startswith("CONFLICTS:"):
                if section == "synthesis":
                    synthesis = "\n".join(buffer).strip()
                section = "conflicts"
                buffer = []
                continue
            if line.startswith("CERTAINTY:"):
                if section == "conflicts":
                    self._parse_conflicts(buffer, conflicts)
                section = "certainty"
                buffer = []
                val = line.split(":", 1)[-1].strip().upper()
                certainty = self._parse_certainty(val)
                continue
            if line.startswith("NEXT:"):
                section = "next"
                val = line.split(":", 1)[-1].strip().lower()
                if val in {"intent", "brief", "plan", "none"}:
                    next_surface = val
                continue
            buffer.append(line)

        if section == "synthesis" and not synthesis:
            synthesis = "\n".join(buffer).strip()

        return SplayReturn(
            job_id=job_id,
            synthesis=synthesis,
            conflicts=conflicts,
            certainty=certainty,
            recommended_next_surface=next_surface,
            raw_summaries=summaries,
        )

    def _parse_conflicts(self, lines: list[str], out: list[CrossAngleConflict]) -> None:
        """Parse conflict lines from the coherence output."""
        for line in lines:
            line = line.strip()
            if not line.startswith("-"):
                continue
            body = line.lstrip("-").strip()
            # Expected: [type] angle1 vs angle2: description [resolution: suggestion]
            # Lightweight parsing
            match = __import__("re").match(
                r"\[(\w+)\]\s+(.+?)\s+vs\s+(.+?):\s+(.+?)(?:\s+\[resolution:\s+(.+?)\])?$",
                body,
            )
            if not match:
                continue
            ctype = self._parse_conflict_type(match.group(1))
            out.append(
                CrossAngleConflict(
                    angles=[match.group(2).strip(), match.group(3).strip()],
                    conflict_type=ctype,
                    description=match.group(4).strip(),
                    suggested_resolution=match.group(5),
                )
            )

    def _parse_certainty(self, val: str) -> Certainty:
        mapping = {
            "HIGH": Certainty.HIGH,
            "MEDIUM": Certainty.MEDIUM,
            "LOW": Certainty.LOW,
        }
        return mapping.get(val, Certainty.MEDIUM)

    def _parse_conflict_type(self, val: str) -> ConflictType:
        mapping = {
            "CONTRADICTION": ConflictType.CONTRADICTION,
            "TENSION": ConflictType.TENSION,
            "OMISSION": ConflictType.OMISSION,
            "PRIORITY": ConflictType.PRIORITY,
        }
        return mapping.get(val.upper(), ConflictType.TENSION)
