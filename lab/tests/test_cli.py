"""CLI tests without model calls."""

from io import StringIO
from pathlib import Path

from lab.cli import main
from splay.src.providers import Provider


class FakeProvider(Provider):
    def __init__(self):
        self.calls: list[tuple[str, str]] = []

    def infer(self, system_prompt: str, user_prompt: str) -> str:
        self.calls.append((system_prompt, user_prompt))
        if "synthesis engine" in system_prompt:
            return (
                "SYNTHESIS:\n"
                "The reviewed file is ready.\n\n"
                "CONFLICTS:\n\n"
                "CERTAINTY: HIGH\n\n"
                "NEXT: none\n"
            )
        return "angle finding"


def test_splay_review_cli_runs_with_injected_provider(tmp_path: Path):
    target = tmp_path / "target.py"
    target.write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    provider = FakeProvider()
    stdout = StringIO()
    stderr = StringIO()

    code = main(
        [
            "splay",
            "review",
            "--file",
            str(target),
            "--angles",
            "clarity,correctness",
            "--job-id",
            "test-job",
        ],
        provider=provider,
        stdout=stdout,
        stderr=stderr,
    )

    assert code == 0
    assert stderr.getvalue() == ""
    output = stdout.getvalue()
    assert "Job: test-job" in output
    assert "State: completed" in output
    assert "Certainty: high" in output
    assert "The reviewed file is ready." in output
    assert len(provider.calls) == 3


def test_splay_review_cli_rejects_missing_file():
    stdout = StringIO()
    stderr = StringIO()

    code = main(
        ["splay", "review", "--file", "does-not-exist.py"],
        provider=FakeProvider(),
        stdout=stdout,
        stderr=stderr,
    )

    assert code == 1
    assert "context file does not exist" in stderr.getvalue()


def test_splay_review_cli_rejects_unknown_angle(tmp_path: Path):
    target = tmp_path / "target.py"
    target.write_text("x = 1\n", encoding="utf-8")
    stdout = StringIO()
    stderr = StringIO()

    code = main(
        ["splay", "review", "--file", str(target), "--angles", "bogus"],
        provider=FakeProvider(),
        stdout=stdout,
        stderr=stderr,
    )

    assert code == 1
    assert "unknown splay angle: bogus" in stderr.getvalue()
