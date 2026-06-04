"""Deposit v0 tests."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass
from datetime import UTC, datetime, timedelta, timezone
from typing import Any, cast

import pytest

from tributary import (
    CreatedFileChange,
    DeletedFileChange,
    Deposit,
    DepositState,
    FileChangeSet,
    ModifiedFileChange,
    derive_deposit_id,
    submit_deposit_from_dispatch_run,
)

HASH_A = "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
HASH_B = "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
HASH_C = "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"


@dataclass(frozen=True, slots=True)
class DispatchRunStub:
    id: str
    state: str
    worktree_id: str


def _dt(offset: int = 0) -> datetime:
    return datetime(2026, 5, 16, 12, 0, offset, tzinfo=UTC)


def _done_run() -> DispatchRunStub:
    return DispatchRunStub(
        id="disprun:abc123",
        state="done",
        worktree_id="/tmp/wt-a",
    )


def _changes() -> FileChangeSet:
    return FileChangeSet(
        (
            ModifiedFileChange(
                path="./src/changed.py",
                before_content_hash=HASH_A,
                after_content_hash=HASH_B,
                mode="100644",
            ),
            CreatedFileChange(
                path="tests/test_changed.py",
                after_content_hash=HASH_C,
            ),
        )
    )


def test_submit_deposit_from_done_dispatch_run() -> None:
    deposit = submit_deposit_from_dispatch_run(
        _done_run(),
        commit_ref="abc123",
        claims=("claim:tests", "claim:code"),
        file_changes=_changes(),
        submitted_at=_dt(),
    )

    assert deposit.id.startswith("deposit:")
    assert deposit.from_dispatch_run_id == "disprun:abc123"
    assert deposit.worktree_id == "/tmp/wt-a"
    assert deposit.state == "submitted"
    assert deposit.claims == ("claim:code", "claim:tests")
    assert deposit.file_changes.changes[0].path == "src/changed.py"


def test_submit_deposit_rejects_non_done_dispatch_run() -> None:
    run = DispatchRunStub(id="disprun:abc123", state="active", worktree_id="/tmp/wt-a")

    with pytest.raises(ValueError, match="state 'done'"):
        submit_deposit_from_dispatch_run(
            run,
            commit_ref=None,
            claims=("claim:code",),
            file_changes=_changes(),
            submitted_at=_dt(),
        )


def test_submit_deposit_rejects_non_dispatch_id() -> None:
    run = DispatchRunStub(id="task:abc123", state="done", worktree_id="/tmp/wt-a")

    with pytest.raises(ValueError, match="disprun"):
        submit_deposit_from_dispatch_run(
            run,
            commit_ref=None,
            claims=("claim:code",),
            file_changes=_changes(),
            submitted_at=_dt(),
        )


def test_deposit_id_is_stable_and_excludes_submission_timestamp() -> None:
    first = submit_deposit_from_dispatch_run(
        _done_run(),
        commit_ref=None,
        claims=("claim:code",),
        file_changes=_changes(),
        submitted_at=_dt(),
    )
    second = submit_deposit_from_dispatch_run(
        _done_run(),
        commit_ref=None,
        claims=("claim:code",),
        file_changes=_changes(),
        submitted_at=_dt(1),
    )

    assert first.id == second.id


def test_deposit_id_changes_with_file_content() -> None:
    first = derive_deposit_id(
        from_dispatch_run_id="disprun:abc123",
        claims=("claim:code",),
        file_changes=FileChangeSet((CreatedFileChange("a.py", HASH_A),)),
        commit_ref=None,
    )
    second = derive_deposit_id(
        from_dispatch_run_id="disprun:abc123",
        claims=("claim:code",),
        file_changes=FileChangeSet((CreatedFileChange("a.py", HASH_B),)),
        commit_ref=None,
    )

    assert first != second


def test_file_change_set_canonicalizes_order_for_identity() -> None:
    left = FileChangeSet(
        (
            CreatedFileChange("b.py", HASH_B),
            CreatedFileChange("a.py", HASH_A),
        )
    )
    right = FileChangeSet(
        (
            CreatedFileChange("a.py", HASH_A),
            CreatedFileChange("b.py", HASH_B),
        )
    )

    assert left.changes == right.changes
    assert left.identity() == right.identity()


def test_file_change_set_rejects_duplicate_paths() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        FileChangeSet(
            (
                CreatedFileChange("a.py", HASH_A),
                ModifiedFileChange("a.py", HASH_A, HASH_B),
            )
        )


def test_file_change_kinds_carry_only_relevant_hashes_in_identity() -> None:
    changes = FileChangeSet(
        (
            CreatedFileChange("a.py", HASH_A),
            ModifiedFileChange("b.py", HASH_A, HASH_B),
            DeletedFileChange("c.py", HASH_C),
        )
    )

    assert changes.identity() == (
        {
            "kind": "create",
            "path": "a.py",
            "before_content_hash": None,
            "after_content_hash": HASH_A,
            "mode": None,
        },
        {
            "kind": "modify",
            "path": "b.py",
            "before_content_hash": HASH_A,
            "after_content_hash": HASH_B,
            "mode": None,
        },
        {
            "kind": "delete",
            "path": "c.py",
            "before_content_hash": HASH_C,
            "after_content_hash": None,
            "mode": None,
        },
    )


@pytest.mark.parametrize(
    "change",
    [
        lambda: CreatedFileChange("/abs.py", HASH_A),
        lambda: CreatedFileChange("../escape.py", HASH_A),
        lambda: CreatedFileChange("src//bad.py", HASH_A),
        lambda: CreatedFileChange("src/bad.py", ""),
        lambda: CreatedFileChange("src/bad.py", " hash "),
        lambda: CreatedFileChange("src/bad.py", HASH_A, mode=""),
    ],
)
def test_file_change_rejects_invalid_path_hash_or_mode(change) -> None:
    with pytest.raises(ValueError):
        change()


def test_deposit_rejects_empty_claims() -> None:
    with pytest.raises(ValueError, match="claims"):
        submit_deposit_from_dispatch_run(
            _done_run(),
            commit_ref=None,
            claims=(),
            file_changes=_changes(),
            submitted_at=_dt(),
        )


@pytest.mark.parametrize("claim", ["Claim:Code", "claim code", " claim:code", ""])
def test_deposit_rejects_invalid_claims(claim: str) -> None:
    with pytest.raises(ValueError, match="claims"):
        submit_deposit_from_dispatch_run(
            _done_run(),
            commit_ref=None,
            claims=(claim,),
            file_changes=_changes(),
            submitted_at=_dt(),
        )


def test_deposit_rejects_duplicate_claims() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        submit_deposit_from_dispatch_run(
            _done_run(),
            commit_ref=None,
            claims=("claim:code", "claim:code"),
            file_changes=_changes(),
            submitted_at=_dt(),
        )


def test_deposit_rejects_naive_submitted_at() -> None:
    with pytest.raises(ValueError, match="submitted_at"):
        submit_deposit_from_dispatch_run(
            _done_run(),
            commit_ref=None,
            claims=("claim:code",),
            file_changes=_changes(),
            submitted_at=datetime(2026, 5, 16, 12, 0, 0),
        )


def test_deposit_rejects_non_utc_submitted_at() -> None:
    with pytest.raises(ValueError, match="UTC"):
        submit_deposit_from_dispatch_run(
            _done_run(),
            commit_ref=None,
            claims=("claim:code",),
            file_changes=_changes(),
            submitted_at=datetime(2026, 5, 16, 12, 0, 0, tzinfo=timezone(timedelta(hours=1))),
        )


def test_deposit_rejects_invalid_state() -> None:
    with pytest.raises(ValueError, match="Invalid Deposit state"):
        Deposit(
            from_dispatch_run_id="disprun:abc123",
            worktree_id="/tmp/wt-a",
            commit_ref=None,
            claims=("claim:code",),
            file_changes=_changes(),
            submitted_at=_dt(),
            state=cast(DepositState, "needs_human"),
        )


def test_deposit_rejects_invalid_supersedes_id() -> None:
    with pytest.raises(ValueError, match="supersedes"):
        Deposit(
            from_dispatch_run_id="disprun:abc123",
            worktree_id="/tmp/wt-a",
            commit_ref=None,
            claims=("claim:code",),
            file_changes=_changes(),
            submitted_at=_dt(),
            supersedes="disprun:abc123",
        )


def test_deposit_allows_empty_file_change_set_for_no_op_claim() -> None:
    deposit = submit_deposit_from_dispatch_run(
        _done_run(),
        commit_ref=None,
        claims=("no-op",),
        file_changes=FileChangeSet(),
        submitted_at=_dt(),
    )

    assert deposit.file_changes.changes == ()
    assert deposit.id.startswith("deposit:")


def test_deposit_is_frozen() -> None:
    deposit = submit_deposit_from_dispatch_run(
        _done_run(),
        commit_ref=None,
        claims=("claim:code",),
        file_changes=_changes(),
        submitted_at=_dt(),
    )

    with pytest.raises(FrozenInstanceError):
        _assign_state(deposit)


def _assign_state(deposit: Any) -> None:
    deposit.state = "validated"
