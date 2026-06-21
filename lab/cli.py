"""Lab-wide command-line entrypoint."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

from splay import Angle, GemmaProvider, SplayJob, SplayOrchestrator, resolve_angles
from splay.src.providers import FireworksProvider, Provider, ProviderError


class CliError(Exception):
    """Raised for user-correctable CLI errors."""


@dataclass(frozen=True)
class _CommandResult:
    returncode: int
    stdout: str
    stderr: str


def main(
    argv: Sequence[str] | None = None,
    provider: Provider | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    out = stdout or sys.stdout
    err = stderr or sys.stderr
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "state-of":
            return _run_state_of(args, out)
        if args.command == "splay" and args.splay_command == "review":
            return _run_splay_review(args, provider, out)
    except (CliError, ProviderError) as exc:
        print(f"error: {exc}", file=err)
        return 1

    parser.print_help(file=err)
    return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lab")
    subcommands = parser.add_subparsers(dest="command")

    state_of = subcommands.add_parser("state-of")
    state_of.add_argument(
        "--root",
        default=".",
        help="Repository root or path inside the watershed checkout.",
    )
    state_of.add_argument(
        "--no-github",
        action="store_true",
        help="Skip GitHub PR lookup.",
    )

    splay = subcommands.add_parser("splay")
    splay_subcommands = splay.add_subparsers(dest="splay_command")

    review = splay_subcommands.add_parser("review")
    review.add_argument(
        "--file",
        dest="files",
        action="append",
        required=True,
        help="File to include as splay context; repeat for multiple files.",
    )
    review.add_argument(
        "--angles",
        default="review",
        help="Comma-separated canonical splay angles.",
    )
    review.add_argument(
        "--provider",
        choices=("gemma", "fireworks"),
        default="gemma",
        help="Inference provider.",
    )
    review.add_argument("--base-url", help="OpenAI-compatible base URL for Gemma.")
    review.add_argument("--model", help="Model override.")
    review.add_argument("--api-key", help="Provider API key override.")
    review.add_argument("--timeout", type=float, default=120.0, help="Request timeout.")
    review.add_argument("--job-id", help="Splay job id.")
    review.add_argument(
        "--show-raw",
        action="store_true",
        help="Print raw angle summaries after the synthesis.",
    )
    return parser


def _run_state_of(args: argparse.Namespace, out: TextIO) -> int:
    root = _repo_root(Path(args.root))
    branch = _require_command(["git", "branch", "--show-current"], root).stdout
    head = _require_command(["git", "rev-parse", "--short", "HEAD"], root).stdout
    status = _require_command(["git", "status", "--porcelain"], root).stdout
    upstream = _upstream(root)
    latest_lineage = _latest_lineage(root)
    open_threads = _open_thread_titles(root)
    prs, pr_error = _open_pull_requests(root, skip=args.no_github)

    print("Watershed State", file=out)
    print(f"Root: {root}", file=out)
    print(f"Branch: {branch or '[detached]'}", file=out)
    print(f"Head: {head}", file=out)
    if upstream:
        ahead, behind = _ahead_behind(root)
        print(f"Upstream: {upstream}", file=out)
        print(f"Sync: ahead {ahead}, behind {behind}", file=out)
    else:
        print("Upstream: none", file=out)
        print("Sync: untracked branch", file=out)
    print(f"Working tree: {'clean' if not status else 'dirty'}", file=out)

    print("", file=out)
    print("Latest Lineage", file=out)
    if latest_lineage:
        print(f"Seat: {latest_lineage['seat']}", file=out)
        print(f"Entered: {latest_lineage['entered']}", file=out)
        print(f"Exited: {latest_lineage['exited']}", file=out)
    else:
        print("No lineage entries found", file=out)

    print("", file=out)
    print("Open Threads", file=out)
    if open_threads:
        for title in open_threads:
            print(f"- {title}", file=out)
    else:
        print("- none found", file=out)

    print("", file=out)
    print("Open PRs", file=out)
    if pr_error:
        print(f"- unavailable: {pr_error}", file=out)
    elif prs:
        for pr in prs:
            draft = " draft" if pr.get("isDraft") else ""
            print(
                f"- #{pr['number']}{draft} {pr['title']} "
                f"({pr['headRefName']}) {pr['url']}",
                file=out,
            )
    else:
        print("- none", file=out)
    return 0


def _run_splay_review(
    args: argparse.Namespace,
    injected_provider: Provider | None,
    out: TextIO,
) -> int:
    context_refs = _validate_context_refs(args.files)
    angles = _parse_angles(args.angles)
    provider = injected_provider or _build_provider(args)
    job = SplayJob(
        id=args.job_id or f"splay:{uuid.uuid4().hex}",
        context_refs=context_refs,
        angles=angles,
    )
    result = SplayOrchestrator(provider).submit(job)

    print(f"Job: {result.job_id}", file=out)
    print(f"State: {job.state.value}", file=out)
    print(f"Certainty: {result.certainty.value}", file=out)
    print(f"Next: {result.recommended_next_surface}", file=out)
    print("", file=out)
    print("Synthesis:", file=out)
    print(result.synthesis or "[empty synthesis]", file=out)

    if result.conflicts:
        print("", file=out)
        print("Conflicts:", file=out)
        for conflict in result.conflicts:
            angles_text = " vs ".join(conflict.angles)
            print(
                f"- [{conflict.conflict_type.value}] {angles_text}: "
                f"{conflict.description}",
                file=out,
            )
            if conflict.suggested_resolution:
                print(f"  Resolution: {conflict.suggested_resolution}", file=out)

    if args.show_raw:
        print("", file=out)
        print("Raw Angle Summaries:", file=out)
        for name, summary in result.raw_summaries.items():
            print("", file=out)
            print(f"--- {name} ---", file=out)
            print("\n".join(summary.key_findings), file=out)

    return 0


def _validate_context_refs(files: Sequence[str]) -> list[str]:
    refs: list[str] = []
    for value in files:
        path = Path(value)
        if not path.is_file():
            raise CliError(f"context file does not exist: {path}")
        refs.append(str(path))
    return refs


def _parse_angles(raw: str) -> list[Angle]:
    names = [name.strip() for name in raw.split(",") if name.strip()]
    if not names:
        raise CliError("--angles must name at least one angle")
    try:
        return resolve_angles(names)
    except KeyError as exc:
        raise CliError(f"unknown splay angle: {exc.args[0]}") from exc


def _build_provider(args: argparse.Namespace) -> Provider:
    if args.provider == "gemma":
        return GemmaProvider(
            base_url=args.base_url,
            model=args.model,
            api_key=args.api_key,
            timeout=args.timeout,
        )
    if args.base_url:
        raise CliError("--base-url is only valid with --provider gemma")
    return FireworksProvider(
        api_key=args.api_key,
        model=args.model,
        timeout=args.timeout,
    )


def _repo_root(path: Path) -> Path:
    result = _require_command(["git", "rev-parse", "--show-toplevel"], path)
    return Path(result.stdout)


def _upstream(root: Path) -> str | None:
    result = _run_command(
        ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"],
        root,
    )
    if result.returncode != 0:
        return None
    return result.stdout


def _ahead_behind(root: Path) -> tuple[int, int]:
    result = _require_command(
        ["git", "rev-list", "--left-right", "--count", "HEAD...@{upstream}"],
        root,
    )
    left, right = result.stdout.split()
    return int(left), int(right)


def _latest_lineage(root: Path) -> dict[str, str] | None:
    entries = sorted(
        (root / "sketches" / "lineage").glob("[0-9][0-9]-*.md"),
        key=lambda path: int(path.name.split("-", 1)[0]),
    )
    if not entries:
        return None
    latest = entries[-1]
    text = latest.read_text(encoding="utf-8")
    return {
        "seat": latest.name,
        "entered": _field_value(text, "Entered") or "unknown",
        "exited": _field_value(text, "Exited") or "open",
    }


def _field_value(text: str, field: str) -> str | None:
    prefix = f"{field}:"
    for line in text.splitlines():
        if line.startswith(prefix):
            value = line[len(prefix) :].strip()
            return value or None
    return None


def _open_thread_titles(root: Path) -> list[str]:
    thinking = root / "sketches" / "THINKING.md"
    if not thinking.is_file():
        return []
    titles: list[str] = []
    in_open_threads = False
    for line in thinking.read_text(encoding="utf-8").splitlines():
        if line.startswith("## Open brainstorms"):
            in_open_threads = True
            continue
        if not in_open_threads:
            continue
        match = re.match(r"\d+\.\s+\*\*(.+?)\*\*", line)
        if match:
            titles.append(match.group(1))
    return titles


def _open_pull_requests(
    root: Path,
    *,
    skip: bool,
) -> tuple[list[dict[str, object]], str | None]:
    if skip:
        return [], None
    result = _run_command(
        [
            "gh",
            "pr",
            "list",
            "--state",
            "open",
            "--json",
            "number,title,headRefName,isDraft,url",
        ],
        root,
    )
    if result.returncode != 0:
        return [], result.stderr or result.stdout or "gh pr list failed"
    try:
        data = json.loads(result.stdout or "[]")
    except json.JSONDecodeError as exc:
        return [], f"could not parse gh output: {exc}"
    if not isinstance(data, list):
        return [], "gh output was not a list"
    return [item for item in data if isinstance(item, dict)], None


def _require_command(command: Sequence[str], cwd: Path) -> _CommandResult:
    result = _run_command(command, cwd)
    if result.returncode == 0:
        return result
    detail = result.stderr or result.stdout or "no output"
    raise CliError(f"command failed in {cwd}: {' '.join(command)}: {detail}")


def _run_command(command: Sequence[str], cwd: Path) -> _CommandResult:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            check=False,
            text=True,
        )
    except OSError as exc:
        raise CliError(f"could not run {' '.join(command)} in {cwd}: {exc}") from exc
    return _CommandResult(
        returncode=completed.returncode,
        stdout=completed.stdout.strip(),
        stderr=completed.stderr.strip(),
    )


if __name__ == "__main__":
    raise SystemExit(main())
