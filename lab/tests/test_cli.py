"""CLI tests without model calls."""

import json
import sys
from collections.abc import Sequence
from io import StringIO
from pathlib import Path

from lab.cli import _CommandResult, main
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


def test_state_of_reports_git_lineage_threads_and_prs(tmp_path: Path, monkeypatch):
    _write_state_fixture(tmp_path)

    def fake_run_command(command: Sequence[str], cwd: Path) -> _CommandResult:
        assert cwd == tmp_path
        outputs = {
            ("git", "rev-parse", "--show-toplevel"): str(tmp_path),
            ("git", "branch", "--show-current"): "main",
            ("git", "rev-parse", "--short", "HEAD"): "abc1234",
            ("git", "status", "--porcelain"): "",
            (
                "git",
                "rev-parse",
                "--abbrev-ref",
                "--symbolic-full-name",
                "@{upstream}",
            ): "origin/main",
            ("git", "rev-list", "--left-right", "--count", "HEAD...@{upstream}"): (
                "0\t0"
            ),
            (
                "gh",
                "pr",
                "list",
                "--state",
                "open",
                "--json",
                "number,title,headRefName,isDraft,url",
            ): (
                '[{"number":12,"title":"Do the thing",'
                '"headRefName":"codex/do-thing","isDraft":false,'
                '"url":"https://example.test/pr/12"}]'
            ),
        }
        return _CommandResult(0, outputs[tuple(command)], "")

    monkeypatch.setattr("lab.cli._run_command", fake_run_command)
    stdout = StringIO()
    stderr = StringIO()

    code = main(["state-of", "--root", str(tmp_path)], stdout=stdout, stderr=stderr)

    assert code == 0
    assert stderr.getvalue() == ""
    output = stdout.getvalue()
    assert "Branch: main" in output
    assert "Head: abc1234" in output
    assert "Sync: ahead 0, behind 0" in output
    assert "Working tree: clean" in output
    assert "Seat: 29-rill.md" in output
    assert "Exited: open" in output
    assert "- Outcrop's compilation structure" in output
    assert "#12 Do the thing (codex/do-thing)" in output


def test_state_of_reports_github_unavailable(tmp_path: Path, monkeypatch):
    _write_state_fixture(tmp_path)

    def fake_run_command(command: Sequence[str], cwd: Path) -> _CommandResult:
        assert cwd == tmp_path
        if command[0] == "gh":
            return _CommandResult(1, "", "not authenticated")
        outputs = {
            ("git", "rev-parse", "--show-toplevel"): str(tmp_path),
            ("git", "branch", "--show-current"): "codex/work",
            ("git", "rev-parse", "--short", "HEAD"): "def5678",
            ("git", "status", "--porcelain"): " M file.py",
            (
                "git",
                "rev-parse",
                "--abbrev-ref",
                "--symbolic-full-name",
                "@{upstream}",
            ): "origin/codex/work",
            ("git", "rev-list", "--left-right", "--count", "HEAD...@{upstream}"): (
                "1\t2"
            ),
        }
        return _CommandResult(0, outputs[tuple(command)], "")

    monkeypatch.setattr("lab.cli._run_command", fake_run_command)
    stdout = StringIO()
    stderr = StringIO()

    code = main(["state-of", "--root", str(tmp_path)], stdout=stdout, stderr=stderr)

    assert code == 0
    output = stdout.getvalue()
    assert "Branch: codex/work" in output
    assert "Sync: ahead 1, behind 2" in output
    assert "Working tree: dirty" in output
    assert "- unavailable: not authenticated" in output


def test_verify_run_emits_passing_evidence(tmp_path: Path):
    spec = tmp_path / "verification.json"
    manifest = tmp_path / "manifest.json"
    spec.write_text(json.dumps({"checks": ["smoke"]}), encoding="utf-8")
    manifest.write_text(
        json.dumps(
            {
                "checks": {
                    "smoke": {
                        "command": [
                            sys.executable,
                            "-c",
                            "print('smoke passed')",
                        ],
                        "cwd": ".",
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    stdout = StringIO()
    stderr = StringIO()

    code = main(
        [
            "verify",
            "run",
            "--root",
            str(tmp_path),
            "--spec",
            str(spec),
            "--manifest",
            str(manifest),
        ],
        stdout=stdout,
        stderr=stderr,
    )

    assert code == 0
    assert stderr.getvalue() == ""
    evidence = json.loads(stdout.getvalue())
    assert evidence["runner"] == "lab.verification"
    assert evidence["verification_spec"] == {"checks": ["smoke"]}
    assert evidence["verdict"] == "pass"
    assert evidence["checks"][0]["status"] == "pass"
    assert evidence["checks"][0]["stdout"] == "smoke passed\n"


def test_verify_run_fails_missing_manifest_entry(tmp_path: Path):
    spec = tmp_path / "verification.json"
    manifest = tmp_path / "manifest.json"
    spec.write_text(json.dumps({"checks": ["missing"]}), encoding="utf-8")
    manifest.write_text(json.dumps({"checks": {}}), encoding="utf-8")
    stdout = StringIO()
    stderr = StringIO()

    code = main(
        [
            "verify",
            "run",
            "--root",
            str(tmp_path),
            "--spec",
            str(spec),
            "--manifest",
            str(manifest),
        ],
        stdout=stdout,
        stderr=stderr,
    )

    assert code == 1
    assert stderr.getvalue() == ""
    evidence = json.loads(stdout.getvalue())
    assert evidence["verdict"] == "fail"
    assert evidence["checks"][0]["status"] == "fail"
    assert "no command manifest entry" in evidence["checks"][0]["stderr"]


def test_verify_run_writes_failing_evidence_file(tmp_path: Path):
    spec = tmp_path / "verification.json"
    manifest = tmp_path / "manifest.json"
    output = tmp_path / "evidence" / "verification-evidence.json"
    spec.write_text(json.dumps({"checks": ["fails"]}), encoding="utf-8")
    manifest.write_text(
        json.dumps(
            {
                "checks": {
                    "fails": {
                        "command": [
                            sys.executable,
                            "-c",
                            "import sys; print('bad', file=sys.stderr); sys.exit(7)",
                        ],
                        "cwd": ".",
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    stdout = StringIO()
    stderr = StringIO()

    code = main(
        [
            "verify",
            "run",
            "--root",
            str(tmp_path),
            "--spec",
            str(spec),
            "--manifest",
            str(manifest),
            "--evidence",
            str(output),
            "--pretty",
        ],
        stdout=stdout,
        stderr=stderr,
    )

    assert code == 1
    assert stderr.getvalue() == ""
    assert f"Evidence: {output}" in stdout.getvalue()
    assert "Verdict: fail" in stdout.getvalue()
    evidence = json.loads(output.read_text(encoding="utf-8"))
    assert evidence["verdict"] == "fail"
    assert evidence["checks"][0]["exit_code"] == 7
    assert evidence["checks"][0]["stderr"] == "bad\n"


def _write_state_fixture(root: Path) -> None:
    lineage = root / "sketches" / "lineage"
    lineage.mkdir(parents=True)
    (lineage / "28-cutbank.md").write_text(
        "# 28 - Cutbank\n\nEntered: 2026-06-20 18:28 EDT\nExited: 2026-06-20\n",
        encoding="utf-8",
    )
    (lineage / "29-rill.md").write_text(
        "# 29 - Rill\n\nEntered: 2026-06-20 19:43 EDT\n",
        encoding="utf-8",
    )
    (root / "sketches" / "THINKING.md").write_text(
        "## Open brainstorms (next up)\n\n"
        "1. **Outcrop's compilation structure.** Paper drop -> typed Reference.\n"
        "2. **Event subscription model.** Deferred.\n",
        encoding="utf-8",
    )
