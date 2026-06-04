"""Narrow plan validation tests ported from dgov/tests/test_plan.py."""

from __future__ import annotations

from typing import Any, cast

import pytest

from distributary.plan import (
    PlanSpec,
    PlanUnit,
    PlanUnitFiles,
    _all_touches,
    _are_independent,
    _normalize_path,
    _paths_overlap,
    validate_plan,
)


class TestNormalizePath:
    def test_strips_leading_dot_slash(self):
        assert _normalize_path("./file.txt") == "file.txt"
        assert _normalize_path("./src/main.py") == "src/main.py"

    def test_strips_trailing_slash(self):
        assert _normalize_path("src/") == "src"
        assert _normalize_path("some/path/") == "some/path"

    def test_strips_whitespace(self):
        assert _normalize_path("  file.txt  ") == "file.txt"

    def test_handles_multiple_prefixes_and_suffixes(self):
        assert _normalize_path("./src/") == "src"
        assert _normalize_path("././nested/path///") == "nested/path"

    def test_handles_empty_string(self):
        assert _normalize_path("") == ""

    def test_handles_plain_paths(self):
        assert _normalize_path("file.txt") == "file.txt"
        assert _normalize_path("src/main.py") == "src/main.py"
        assert _normalize_path("/tmp/file.txt") == "/tmp/file.txt"

    def test_preserves_dot_hidden(self):
        assert _normalize_path(".hidden/file.txt") == ".hidden/file.txt"

    def test_preserves_parent_dir(self):
        assert _normalize_path("../file.txt") == "../file.txt"


class TestPathsOverlap:
    def test_identical_paths_overlap(self):
        assert _paths_overlap("src/main.py", "src/main.py") is True
        assert _paths_overlap("./src/main.py", "src/main.py") is True

    def test_parent_child_overlap(self):
        assert _paths_overlap("src/main.py", "src") is True
        assert _paths_overlap("src", "src/main.py") is True

    def test_nested_directory_overlap(self):
        assert _paths_overlap("src/utils/helper.py", "src") is True

    def test_sibling_paths_no_overlap(self):
        assert _paths_overlap("src/main.py", "src/utils.py") is False

    def test_unrelated_paths_no_overlap(self):
        assert _paths_overlap("src/main.py", "tests/test_main.py") is False

    def test_similar_prefix_no_overlap(self):
        assert _paths_overlap("src_main.py", "src/main.py") is False

    def test_empty_path_no_overlap(self):
        assert _paths_overlap("", "src/main.py") is False
        assert _paths_overlap("src/main.py", "") is False

    def test_normalizes_before_comparison(self):
        assert _paths_overlap("./src/main.py", "src/") is True


class TestSlugValidation:
    def test_valid_slug_passes(self):
        plan = PlanSpec(
            name="valid",
            goal="Goal",
            units={
                "task-a": PlanUnit(
                    slug="task-a",
                    summary="Task",
                    prompt="Do it",
                    commit_message="Done",
                    files=PlanUnitFiles(),
                )
            },
        )
        assert validate_plan(plan) == []

    def test_invalid_slug_fails(self):
        plan = PlanSpec(
            name="invalid",
            goal="Goal",
            units={
                "Task_A": PlanUnit(
                    slug="Task_A",
                    summary="Task",
                    prompt="Do it",
                    commit_message="Done",
                    files=PlanUnitFiles(),
                )
            },
        )
        issues = validate_plan(plan)
        assert len(issues) == 1
        assert issues[0].severity == "error"
        assert "Task_A" in issues[0].message

    def test_empty_slug_fails(self):
        plan = PlanSpec(
            name="empty",
            goal="Goal",
            units={
                "": PlanUnit(
                    slug="",
                    summary="Task",
                    prompt="Do it",
                    commit_message="Done",
                    files=PlanUnitFiles(),
                )
            },
        )
        issues = validate_plan(plan)
        assert len(issues) == 1
        assert "Invalid slug" in issues[0].message

    def test_unit_key_must_match_unit_slug(self):
        plan = PlanSpec(
            name="mismatch",
            goal="Goal",
            units={
                "task-a": PlanUnit(
                    slug="task-b",
                    summary="Task",
                    prompt="Do it",
                    commit_message="Done",
                    files=PlanUnitFiles(),
                )
            },
        )

        issues = validate_plan(plan)

        assert len(issues) == 1
        assert "does not match" in issues[0].message


class TestPlanSpecImmutability:
    def test_units_mapping_is_immutable(self):
        plan = PlanSpec(
            name="immutable",
            goal="Goal",
            units={
                "task-a": PlanUnit(
                    slug="task-a",
                    summary="Task",
                    prompt="Do it",
                    commit_message="Done",
                    files=PlanUnitFiles(),
                )
            },
        )

        units = cast(Any, plan.units)
        with pytest.raises(TypeError):
            units["task-b"] = PlanUnit(
                slug="task-b",
                summary="Task B",
                prompt="Do B",
                commit_message="B",
                files=PlanUnitFiles(),
            )


class TestDependencyValidation:
    def test_missing_dependency_fails(self):
        plan = PlanSpec(
            name="missing-dep",
            goal="Goal",
            units={
                "task-a": PlanUnit(
                    slug="task-a",
                    summary="Task",
                    prompt="Do it",
                    commit_message="Done",
                    files=PlanUnitFiles(),
                    depends_on=("task-missing",),
                )
            },
        )

        issues = validate_plan(plan)

        assert len(issues) == 1
        assert "unknown unit" in issues[0].message

    def test_dependency_cycle_fails(self):
        plan = PlanSpec(
            name="cycle",
            goal="Goal",
            units={
                "task-a": PlanUnit(
                    slug="task-a",
                    summary="Task A",
                    prompt="Do A",
                    commit_message="A",
                    files=PlanUnitFiles(),
                    depends_on=("task-b",),
                ),
                "task-b": PlanUnit(
                    slug="task-b",
                    summary="Task B",
                    prompt="Do B",
                    commit_message="B",
                    files=PlanUnitFiles(),
                    depends_on=("task-a",),
                ),
            },
        )

        issues = validate_plan(plan)

        assert len(issues) == 1
        assert "cycle" in issues[0].message


class TestFileClaimConflicts:
    def test_detects_conflict_between_independent_tasks(self):
        plan = PlanSpec(
            name="conflict",
            goal="Goal",
            units={
                "a": PlanUnit(
                    slug="a",
                    summary="A",
                    prompt="Do A",
                    commit_message="A",
                    files=PlanUnitFiles(edit=("src/main.py",)),
                ),
                "b": PlanUnit(
                    slug="b",
                    summary="B",
                    prompt="Do B",
                    commit_message="B",
                    files=PlanUnitFiles(edit=("src/main.py",)),
                ),
            },
        )
        issues = validate_plan(plan)
        assert len(issues) == 1
        assert issues[0].severity == "error"
        assert "src/main.py" in issues[0].message

    def test_no_conflict_when_dependent(self):
        plan = PlanSpec(
            name="dep",
            goal="Goal",
            units={
                "a": PlanUnit(
                    slug="a",
                    summary="A",
                    prompt="Do A",
                    commit_message="A",
                    files=PlanUnitFiles(edit=("src/main.py",)),
                ),
                "b": PlanUnit(
                    slug="b",
                    summary="B",
                    prompt="Do B",
                    commit_message="B",
                    files=PlanUnitFiles(edit=("src/main.py",)),
                    depends_on=("a",),
                ),
            },
        )
        assert validate_plan(plan) == []

    def test_no_conflict_different_files(self):
        plan = PlanSpec(
            name="no-conflict",
            goal="Goal",
            units={
                "a": PlanUnit(
                    slug="a",
                    summary="A",
                    prompt="Do A",
                    commit_message="A",
                    files=PlanUnitFiles(edit=("src/foo.py",)),
                ),
                "b": PlanUnit(
                    slug="b",
                    summary="B",
                    prompt="Do B",
                    commit_message="B",
                    files=PlanUnitFiles(edit=("src/bar.py",)),
                ),
            },
        )
        assert validate_plan(plan) == []

    def test_detects_directory_overlap(self):
        plan = PlanSpec(
            name="dir-overlap",
            goal="Goal",
            units={
                "a": PlanUnit(
                    slug="a",
                    summary="A",
                    prompt="Do A",
                    commit_message="A",
                    files=PlanUnitFiles(edit=("src/utils/helper.py",)),
                ),
                "b": PlanUnit(
                    slug="b",
                    summary="B",
                    prompt="Do B",
                    commit_message="B",
                    files=PlanUnitFiles(delete=("src/utils",)),
                ),
            },
        )
        issues = validate_plan(plan)
        assert len(issues) >= 1
        assert issues[0].severity == "error"

    def test_transitive_dependency_not_conflict(self):
        plan = PlanSpec(
            name="transitive",
            goal="Goal",
            units={
                "a": PlanUnit(
                    slug="a",
                    summary="A",
                    prompt="Do A",
                    commit_message="A",
                    files=PlanUnitFiles(edit=("src/main.py",)),
                ),
                "b": PlanUnit(
                    slug="b",
                    summary="B",
                    prompt="Do B",
                    commit_message="B",
                    files=PlanUnitFiles(edit=("src/other.py",)),
                    depends_on=("a",),
                ),
                "c": PlanUnit(
                    slug="c",
                    summary="C",
                    prompt="Do C",
                    commit_message="C",
                    files=PlanUnitFiles(edit=("src/main.py",)),
                    depends_on=("b",),
                ),
            },
        )
        assert validate_plan(plan) == []

    def test_detects_touch_conflict_between_independent_tasks(self):
        plan = PlanSpec(
            name="touch-conflict",
            goal="Goal",
            units={
                "a": PlanUnit(
                    slug="a",
                    summary="A",
                    prompt="Do A",
                    commit_message="A",
                    files=PlanUnitFiles(touch=("src/main.py",)),
                ),
                "b": PlanUnit(
                    slug="b",
                    summary="B",
                    prompt="Do B",
                    commit_message="B",
                    files=PlanUnitFiles(touch=("src/main.py",)),
                ),
            },
        )
        issues = validate_plan(plan)
        assert len(issues) == 1
        assert "src/main.py" in issues[0].message

    def test_detects_touch_vs_edit_conflict(self):
        plan = PlanSpec(
            name="mixed-conflict",
            goal="Goal",
            units={
                "a": PlanUnit(
                    slug="a",
                    summary="A",
                    prompt="Do A",
                    commit_message="A",
                    files=PlanUnitFiles(touch=("src/main.py",)),
                ),
                "b": PlanUnit(
                    slug="b",
                    summary="B",
                    prompt="Do B",
                    commit_message="B",
                    files=PlanUnitFiles(edit=("src/main.py",)),
                ),
            },
        )
        issues = validate_plan(plan)
        assert len(issues) == 1

    def test_read_only_non_conflict(self):
        plan = PlanSpec(
            name="read-only",
            goal="Goal",
            units={
                "a": PlanUnit(
                    slug="a",
                    summary="A",
                    prompt="Do A",
                    commit_message="A",
                    files=PlanUnitFiles(read=("src/main.py",)),
                ),
                "b": PlanUnit(
                    slug="b",
                    summary="B",
                    prompt="Do B",
                    commit_message="B",
                    files=PlanUnitFiles(read=("src/main.py",)),
                ),
            },
        )
        assert validate_plan(plan) == []


class TestAllTouches:
    def test_collects_all_write_paths(self):
        unit = PlanUnit(
            slug="u",
            summary="U",
            prompt="Do U",
            commit_message="U",
            files=PlanUnitFiles(
                create=("a.py",),
                edit=("b.py",),
                delete=("c.py",),
                touch=("d.py",),
                read=("e.py",),
            ),
        )
        assert _all_touches(unit) == {"a.py", "b.py", "c.py", "d.py"}

    def test_ignores_empty_and_whitespace(self):
        unit = PlanUnit(
            slug="u",
            summary="U",
            prompt="Do U",
            commit_message="U",
            files=PlanUnitFiles(
                create=("", "  ", "a.py"),
            ),
        )
        assert _all_touches(unit) == {"a.py"}


class TestAreIndependent:
    def test_independent_when_no_deps(self):
        units = {
            "a": PlanUnit(
                slug="a", summary="A", prompt="A", commit_message="A", files=PlanUnitFiles()
            ),
            "b": PlanUnit(
                slug="b", summary="B", prompt="B", commit_message="B", files=PlanUnitFiles()
            ),
        }
        assert _are_independent("a", "b", units) is True

    def test_not_independent_when_direct_dep(self):
        units = {
            "a": PlanUnit(
                slug="a", summary="A", prompt="A", commit_message="A", files=PlanUnitFiles()
            ),
            "b": PlanUnit(
                slug="b",
                summary="B",
                prompt="B",
                commit_message="B",
                files=PlanUnitFiles(),
                depends_on=("a",),
            ),
        }
        assert _are_independent("a", "b", units) is False

    def test_not_independent_when_transitive_dep(self):
        units = {
            "a": PlanUnit(
                slug="a", summary="A", prompt="A", commit_message="A", files=PlanUnitFiles()
            ),
            "b": PlanUnit(
                slug="b",
                summary="B",
                prompt="B",
                commit_message="B",
                files=PlanUnitFiles(),
                depends_on=("a",),
            ),
            "c": PlanUnit(
                slug="c",
                summary="C",
                prompt="C",
                commit_message="C",
                files=PlanUnitFiles(),
                depends_on=("b",),
            ),
        }
        assert _are_independent("a", "c", units) is False
