"""End-to-end: intent → PlanSpec → PlanUnit → FileClaim → pending → active."""

from __future__ import annotations

from datetime import UTC, datetime

from distributary import (
    ClaimKind,
    DispatchRun,
    FileClaim,
    PlanSpec,
    PlanUnit,
    PlanUnitFiles,
    adapt_plan_unit_files_to_claims,
    validate_plan,
)


def test_hello_ceremony() -> None:
    # 1. Intent-shaped input (typed dict, not TOML)
    intent = {
        "goal": "Add a greeting module",
        "scope": ["src/greeting.py", "tests/test_greeting.py"],
    }

    # 2. PlanSpec with one PlanUnit
    unit = PlanUnit(
        slug="add-greeting",
        summary="Add greeting module",
        prompt="Create src/greeting.py with a hello function and tests/test_greeting.py.",
        commit_message="feat: add greeting module",
        files=PlanUnitFiles(
            create=("src/greeting.py", "tests/test_greeting.py"),
            read=("README.md",),
        ),
    )
    plan = PlanSpec(
        name="hello-ceremony",
        goal=intent["goal"],
        units={"add-greeting": unit},
    )

    # 3. Validation passes
    issues = validate_plan(plan)
    assert issues == [], f"Unexpected issues: {issues}"

    # 4. FileClaim mirrors
    claims = adapt_plan_unit_files_to_claims(unit.files)
    assert len(claims) == 3
    assert claims[0] == FileClaim(path="src/greeting.py", kind=ClaimKind.Exclusive)
    assert claims[1] == FileClaim(path="tests/test_greeting.py", kind=ClaimKind.Exclusive)
    assert claims[2] == FileClaim(path="README.md", kind=ClaimKind.ReadOnly)

    # 5. DispatchRun: pending
    dispatched_at = datetime(2026, 5, 14, 12, 0, 0, tzinfo=UTC)
    run = DispatchRun(
        from_plan_id="plan:hello-ceremony",
        unit_slug="add-greeting",
        worktree_id="/tmp/wt-hello",
        branch="distributary/hello-ceremony",
        base_commit="abc123",
        agent_model="codex",
        effective_sop_set_hash="sop-hash-1",
        drift_against_plan=False,
        dispatched_by="watermaster:test",
        dispatched_at=dispatched_at,
    )
    assert run.state == "pending"
    assert run.id.startswith("disprun:")

    # 6. DispatchRun: active (preserves id). The v0 ceremony stops at the
    # dispatch boundary; terminal worker results belong to the next slice.
    active = run.start_active()
    assert active.state == "active"
    assert active.id == run.id
