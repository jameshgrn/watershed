"""Live splay test — uses the Fireworks API.

Usage:
    FIREWORKS_API_KEY=... PYTHONPATH=/Users/jakegearon/projects/watershed python splay/tests/test_splay_live.py

Expects a valid Fireworks API key.
This is a real test with real tokens. It targets a small file to minimize cost.
"""

import os
import sys

from splay.src.models import Angle, SplayJob
from splay.src.orchestrator import SplayOrchestrator
from splay.src.providers import FireworksProvider


def main():
    if "FIREWORKS_API_KEY" not in os.environ:
        print("FIREWORKS_API_KEY not set. Exiting.")
        sys.exit(1)

    provider = FireworksProvider()
    orchestrator = SplayOrchestrator(provider)

    job = SplayJob(
        id="live-test-1",
        context_refs=["splay/DESIGN.md"],
        angles=[
            Angle(
                name="completeness",
                prompt="Does this design document cover all the necessary surfaces, boundaries, and edge cases? What is missing?",
            ),
            Angle(
                name="clarity",
                prompt="Is this design clear enough for a Watermaster to implement? Which parts are ambiguous or need more detail?",
            ),
            Angle(
                name="authority",
                prompt="Does this design respect the watershed boundary between rim and kernel? Does it assign authority correctly?",
            ),
        ],
    )

    print("Submitting splay job...")
    result = orchestrator.submit(job)
    print(f"\nJob state: {job.state.value}")
    print(f"Certainty: {result.certainty.value}")
    print(f"Recommended next: {result.recommended_next_surface}")

    print("\n=== RAW SUMMARIES ===")
    for name, summary in result.raw_summaries.items():
        print(f"\n--- {name} ---")
        for finding in summary.key_findings:
            print(finding[:500])

    print("\n=== CONFLICTS ===")
    for c in result.conflicts:
        print(
            f"[{c.conflict_type.value}] {c.angles[0]} vs {c.angles[1]}: {c.description}"
        )
        if c.suggested_resolution:
            print(f"  Resolution: {c.suggested_resolution}")

    print("\n=== SYNTHESIS ===")
    print(result.synthesis)


if __name__ == "__main__":
    main()
