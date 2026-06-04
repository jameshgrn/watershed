"""FileClaim adapter tests — kernel contract shape verification."""

from __future__ import annotations

from distributary.claims import ClaimKind, FileClaim, adapt_plan_unit_files_to_claims
from distributary.plan import PlanUnitFiles


class TestClaimKind:
    def test_members(self):
        assert ClaimKind.ReadOnly == "ReadOnly"
        assert ClaimKind.Exclusive == "Exclusive"
        assert ClaimKind.Shared == "Shared"


class TestFileClaim:
    def test_normalized_path(self):
        claim = FileClaim(path="./src/", kind=ClaimKind.Exclusive)
        assert claim.normalized_path() == "src"

    def test_covers_exact_path(self):
        claim = FileClaim(path="src", kind=ClaimKind.Exclusive)
        assert claim.covers_path("src") is True

    def test_covers_descendant(self):
        claim = FileClaim(path="src", kind=ClaimKind.Exclusive)
        assert claim.covers_path("src/lib.rs") is True

    def test_does_not_cover_sibling_prefix(self):
        claim = FileClaim(path="src", kind=ClaimKind.Exclusive)
        assert claim.covers_path("srcibling/lib.rs") is False
        assert claim.covers_path("src2/lib.rs") is False

    def test_grants_write_excludes_read_only(self):
        read_only = FileClaim(path="src", kind=ClaimKind.ReadOnly)
        exclusive = FileClaim(path="src", kind=ClaimKind.Exclusive)
        assert read_only.grants_write_to("src/lib.rs") is False
        assert exclusive.grants_write_to("src/lib.rs") is True

    def test_conflicts_exclusive_vs_exclusive(self):
        dir_claim = FileClaim(path="src", kind=ClaimKind.Exclusive)
        file_claim = FileClaim(path="src/lib.rs", kind=ClaimKind.Exclusive)
        assert dir_claim.conflicts_with(file_claim) is True

    def test_no_conflict_with_read_only(self):
        dir_claim = FileClaim(path="src", kind=ClaimKind.Exclusive)
        read_only = FileClaim(path="src/lib.rs", kind=ClaimKind.ReadOnly)
        assert dir_claim.conflicts_with(read_only) is False

    def test_no_conflict_shared_vs_shared(self):
        a = FileClaim(path="src/lib.rs", kind=ClaimKind.Shared)
        b = FileClaim(path="./src/lib.rs", kind=ClaimKind.Shared)
        assert a.conflicts_with(b) is False

    def test_conflict_shared_vs_exclusive(self):
        shared = FileClaim(path="src/lib.rs", kind=ClaimKind.Shared)
        exclusive = FileClaim(path="src/lib.rs", kind=ClaimKind.Exclusive)
        assert shared.conflicts_with(exclusive) is True


class TestAdaptPlanUnitFilesToClaims:
    def test_read_maps_to_read_only(self):
        files = PlanUnitFiles(read=("src/core.py",))
        claims = adapt_plan_unit_files_to_claims(files)
        assert len(claims) == 1
        assert claims[0].kind is ClaimKind.ReadOnly
        assert claims[0].path == "src/core.py"

    def test_edit_maps_to_exclusive(self):
        files = PlanUnitFiles(edit=("src/core.py",))
        claims = adapt_plan_unit_files_to_claims(files)
        assert len(claims) == 1
        assert claims[0].kind is ClaimKind.Exclusive

    def test_create_maps_to_exclusive(self):
        files = PlanUnitFiles(create=("src/new.py",))
        claims = adapt_plan_unit_files_to_claims(files)
        assert claims[0].kind is ClaimKind.Exclusive

    def test_delete_maps_to_exclusive(self):
        files = PlanUnitFiles(delete=("src/old.py",))
        claims = adapt_plan_unit_files_to_claims(files)
        assert claims[0].kind is ClaimKind.Exclusive

    def test_touch_maps_to_exclusive(self):
        files = PlanUnitFiles(touch=("src/foo.py",))
        claims = adapt_plan_unit_files_to_claims(files)
        assert claims[0].kind is ClaimKind.Exclusive

    def test_write_wins_dedup(self):
        files = PlanUnitFiles(
            read=("src/core.py",),
            edit=("src/core.py",),
        )
        claims = adapt_plan_unit_files_to_claims(files)
        assert len(claims) == 1
        assert claims[0].kind is ClaimKind.Exclusive

    def test_stable_order(self):
        files = PlanUnitFiles(
            create=("a.py",),
            edit=("b.py",),
            read=("c.py",),
        )
        claims = adapt_plan_unit_files_to_claims(files)
        paths = [c.path for c in claims]
        assert paths == ["a.py", "b.py", "c.py"]

    def test_no_shared_emitted(self):
        files = PlanUnitFiles(
            create=("a.py",),
            read=("b.py",),
        )
        claims = adapt_plan_unit_files_to_claims(files)
        assert all(c.kind is not ClaimKind.Shared for c in claims)

    def test_empty_returns_empty(self):
        files = PlanUnitFiles()
        claims = adapt_plan_unit_files_to_claims(files)
        assert claims == ()

    def test_normalizes_paths(self):
        files = PlanUnitFiles(create=("./src/",))
        claims = adapt_plan_unit_files_to_claims(files)
        assert claims[0].path == "src"
