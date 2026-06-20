"""Basic splay tests — no API calls, uses a mock provider."""

from splay.src.angles import CANONICAL_ANGLES
from splay.src.models import Certainty, ConflictType, SplayJob, SplayJobState
from splay.src.orchestrator import SplayOrchestrator
from splay.src.providers import Provider


class MockProvider(Provider):
    """A provider that returns canned responses for testing."""

    def __init__(self, responses: dict[str, str]):
        self.responses = responses

    def infer(self, system_prompt: str, user_prompt: str) -> str:
        # Coherence step has a long system prompt; match on that first
        if "synthesis engine" in system_prompt:
            return self.responses.get("coherence", "Default coherence")
        # Angles now use their own prompt as system_prompt
        for key, value in self.responses.items():
            if key in system_prompt:
                return value
        return "Default response"


def test_splay_basic():
    provider = MockProvider(
        {
            "security": "SECURITY: The code lacks input validation on line 42.",
            "performance": "PERFORMANCE: The loop on line 55 is O(n^2).",
            "coherence": (
                "SYNTHESIS:\n"
                "The code has security and performance issues.\n\n"
                "CONFLICTS:\n"
                "- [TENSION] security vs performance: "
                "Adding validation may slow the loop.\n\n"
                "CERTAINTY: MEDIUM\n\n"
                "NEXT: brief\n"
            ),
        }
    )

    orchestrator = SplayOrchestrator(provider)
    job = SplayJob(
        id="test-1",
        context_refs=["splay/tests/test_splay.py"],
        angles=[
            CANONICAL_ANGLES["security"],
            CANONICAL_ANGLES["performance"],
        ],
    )

    result = orchestrator.submit(job)

    assert job.state == SplayJobState.COMPLETED
    assert "security" in result.raw_summaries
    assert "performance" in result.raw_summaries
    assert result.certainty == Certainty.MEDIUM
    assert result.recommended_next_surface == "brief"
    assert len(result.conflicts) == 1
    assert result.conflicts[0].conflict_type == ConflictType.TENSION

    print("PASS: test_splay_basic")


def test_canonical_angles():
    """Verify all canonical angles are defined and loadable."""
    from splay.src.angles import get_angle, list_angles

    names = list_angles()
    assert "review" in names
    assert "security" in names
    assert "performance" in names
    assert "completeness" in names
    assert "clarity" in names
    assert "authority" in names

    angle = get_angle("review")
    assert angle.name == "review"
    assert "VERDICT:" in angle.prompt
    assert "Blocking" in angle.prompt

    print("PASS: test_canonical_angles")


def test_unstructured_coherence_falls_back_to_raw_synthesis():
    provider = MockProvider(
        {
            "clarity": "The implementation is understandable.",
            "coherence": "The implementation is clear enough to proceed.",
        }
    )
    orchestrator = SplayOrchestrator(provider)
    job = SplayJob(
        id="test-unstructured",
        context_refs=["splay/tests/test_splay.py"],
        angles=[CANONICAL_ANGLES["clarity"]],
    )

    result = orchestrator.submit(job)

    assert result.synthesis == "The implementation is clear enough to proceed."
    assert result.recommended_next_surface == "none"


if __name__ == "__main__":
    test_splay_basic()
    test_canonical_angles()
    test_unstructured_coherence_falls_back_to_raw_synthesis()
