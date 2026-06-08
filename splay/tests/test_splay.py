"""Basic splay tests — no API calls, uses a mock provider."""

from splay.src.models import Angle, SplayJob, SplayJobState, Certainty, ConflictType
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
        for key, value in self.responses.items():
            if key in user_prompt:
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
            Angle(name="security", prompt="Review security"),
            Angle(name="performance", prompt="Review performance"),
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


if __name__ == "__main__":
    test_splay_basic()
