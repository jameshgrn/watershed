"""Lab-wide command-line entrypoint."""

from __future__ import annotations

import argparse
import sys
import uuid
from collections.abc import Sequence
from pathlib import Path
from typing import TextIO

from splay import Angle, GemmaProvider, SplayJob, SplayOrchestrator, resolve_angles
from splay.src.providers import FireworksProvider, Provider, ProviderError


class CliError(Exception):
    """Raised for user-correctable CLI errors."""


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


if __name__ == "__main__":
    raise SystemExit(main())
