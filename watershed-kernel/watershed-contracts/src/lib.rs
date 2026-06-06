use schemars::JsonSchema;
use serde::{Deserialize, Serialize};
use std::path::{Component, Path, PathBuf};
use thiserror::Error;

/// Structured intent recovered before claims or dispatch can exist.
#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
pub struct RecoveredIntent {
    pub goal: String,
    pub scope: Vec<String>,
    pub constraints: Vec<String>,
    pub non_goals: Vec<String>,
}

/// Discrete category for the work a plan represents.
#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
pub enum WorkClass {
    Feature,
    Fix,
    Refactor,
    Investigation,
    Documentation,
    Test,
    Chore,
}

/// A claimed file path and the authority requested over it.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
pub struct FileClaim {
    pub path: PathBuf,
    pub kind: ClaimKind,
}

impl FileClaim {
    /// Returns the canonical authority path form for a claim or touched file path.
    pub fn normalize_path(path: impl AsRef<Path>) -> Result<String, FileClaimPathError> {
        normalize_claim_path(path.as_ref())
    }

    /// Returns the path form used when comparing claim authority.
    pub fn normalized_path(&self) -> Result<String, FileClaimPathError> {
        normalize_claim_path(&self.path)
    }

    /// Returns an error if this claim cannot carry legal path authority.
    pub fn validate_path(&self) -> Result<(), FileClaimPathError> {
        self.normalized_path().map(|_| ())
    }

    /// Returns whether this claim's path authority covers `path`.
    pub fn covers_path(&self, path: impl AsRef<Path>) -> Result<bool, FileClaimPathError> {
        Ok(path_covers(
            &self.normalized_path()?,
            &normalize_claim_path(path.as_ref())?,
        ))
    }

    /// Returns whether this claim grants write authority for `path`.
    pub fn grants_write_to(&self, path: impl AsRef<Path>) -> Result<bool, FileClaimPathError> {
        let claim_path = self.normalized_path()?;
        let target_path = normalize_claim_path(path.as_ref())?;

        if matches!(self.kind, ClaimKind::ReadOnly) {
            return Ok(false);
        }

        Ok(path_covers(&claim_path, &target_path))
    }

    /// Returns whether this claim and `other` cannot legally run independently.
    pub fn conflicts_with(&self, other: &FileClaim) -> Result<bool, FileClaimPathError> {
        let left_path = self.normalized_path()?;
        let right_path = other.normalized_path()?;

        if matches!(self.kind, ClaimKind::ReadOnly)
            || matches!(other.kind, ClaimKind::ReadOnly)
            || matches!(
                (&self.kind, &other.kind),
                (ClaimKind::Shared, ClaimKind::Shared)
            )
        {
            return Ok(false);
        }

        Ok(path_covers(&left_path, &right_path) || path_covers(&right_path, &left_path))
    }
}

/// The kind of access a plan claims for a file.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
pub enum ClaimKind {
    ReadOnly,
    Exclusive,
    Shared,
}

/// In-memory description of how task success is checked.
#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
pub struct VerificationSpec {
    pub checks: Vec<String>,
}

/// In-memory description of how task work is reverted.
#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
pub struct RollbackSpec {
    pub steps: Vec<String>,
}

/// Governance rules applied when a compiled plan is validated.
#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
pub struct Policy {
    pub require_claims: bool,
    pub allow_shared_claims: bool,
    pub max_retries: Option<u32>,
    pub required_pressure_tests: Vec<String>,
}

/// A named invariant and the deterministic test that enforces it.
#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
pub struct PressureTest {
    pub name: String,
    pub claim: String,
    pub enforced_by: String,
}

/// Errors raised while handling shared contract data.
#[derive(Debug, Error)]
pub enum ContractError {
    #[error("invalid contract data: {reason}")]
    InvalidData { reason: String },
}

/// Errors raised when a file claim path cannot carry legal authority.
#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum FileClaimPathError {
    #[error("path is empty or current-directory only")]
    Empty,
    #[error("path must be relative: {path}")]
    Absolute { path: String },
    #[error("path must not contain parent traversal: {path}")]
    ParentTraversal { path: String },
    #[error("path contains a non-Unicode component: {path}")]
    NonUnicode { path: String },
}

fn normalize_claim_path(path: &Path) -> Result<String, FileClaimPathError> {
    let original = path.display().to_string();
    let mut parts = Vec::new();

    for component in path.components() {
        match component {
            Component::Prefix(_) | Component::RootDir => {
                return Err(FileClaimPathError::Absolute { path: original });
            }
            Component::ParentDir => {
                return Err(FileClaimPathError::ParentTraversal { path: original });
            }
            Component::CurDir => {}
            Component::Normal(part) => {
                let Some(part) = part.to_str() else {
                    return Err(FileClaimPathError::NonUnicode { path: original });
                };
                if part.trim().is_empty() {
                    return Err(FileClaimPathError::Empty);
                }
                parts.push(part.to_owned());
            }
        }
    }

    if parts.is_empty() {
        return Err(FileClaimPathError::Empty);
    }

    Ok(parts.join("/"))
}

fn path_covers(claim_path: &str, path: &str) -> bool {
    if claim_path.is_empty() || path.is_empty() {
        return false;
    }

    claim_path == path || path.starts_with(&format!("{claim_path}/"))
}

pub const DISPATCH_UNVALIDATED_PLAN: &str = "dispatch_unvalidated_plan";
pub const DISPATCH_TWICE: &str = "dispatch_twice";
pub const CONSTRUCT_MERGE_FROM_OUTSIDE: &str = "construct_merge_from_distributary";
pub const CONSTRUCT_BASELINE_FROM_OUTSIDE: &str = "construct_baseline_from_distributary";
pub const SKIP_INTENT_RECOVERY: &str = "skip_intent_recovery";
pub const CONSTRUCT_COMPLETED_RUN_DIRECTLY: &str = "construct_completed_run_directly";
pub const CONSTRUCT_VALIDATED_PLAN_DIRECTLY: &str = "construct_validated_plan_directly";
pub const MERGE_REJECTED_VALIDATION: &str = "merge_rejected_validation";
pub const BASELINE_WITHOUT_MERGE: &str = "baseline_without_merge";
pub const COMPLETE_RUN_BEFORE_RUNNING: &str = "complete_run_before_running";
pub const VALIDATION_REJECTS_UNCLAIMED_FILES: &str = "validation_rejects_unclaimed_files";
pub const RETRY_COMPLETED_RUN: &str = "retry_completed_run";
pub const RETRY_LINEAGE_FROM_FAILED: &str = "retry_lineage_from_failed";
pub const RETRY_RESPECTS_MAX_RETRIES: &str = "retry_respects_max_retries";
pub const DAG_KERNEL_SERIAL_MERGE_SCAN: &str = "dag_kernel_serial_merge_scan";
pub const DAG_PLAN_CLAIMS_TRAVEL_TO_MERGE: &str = "dag_plan_claims_travel_to_merge";
pub const DAG_PLAN_REJECTS_CONFLICTING_CLAIMS: &str = "dag_plan_rejects_conflicting_claims";
pub const DAG_KERNEL_REJECTS_RAW_CLAIM_BYPASS: &str = "dag_kernel_rejects_raw_claim_bypass";
pub const WAIT_DONE_REJECTS_KERNEL_TASK_STATE: &str = "wait_done_rejects_kernel_task_state";
pub const DAG_KERNEL_BINDS_TASK_PANES: &str = "dag_kernel_binds_task_panes";
pub const TASK_STATE_REJECTS_DEAD_VARIANTS: &str = "task_state_rejects_dead_variants";
pub const REVIEW_DONE_REJECTS_BOOLEAN_VERDICT_BAG: &str = "review_done_rejects_boolean_verdict_bag";
pub const MERGE_DONE_REJECTS_OPTIONAL_ERROR: &str = "merge_done_rejects_optional_error";
pub const CONSTRUCT_DEPOSIT_DIRECTLY: &str = "construct_deposit_directly";
pub const DEPOSIT_IDS_ARE_DERIVED: &str = "deposit_ids_are_derived";
pub const REQUIRED_PRESSURE_TESTS_ARE_REGISTERED: &str = "required_pressure_tests_are_registered";
pub const PRESSURE_TEST_REGISTRY_SELF_CONSISTENT: &str = "pressure_test_registry_self_consistent";
pub const FILE_CLAIM_PATHS_REJECT_ESCAPE_FORMS: &str = "file_claim_paths_reject_escape_forms";

pub fn pressure_tests() -> Vec<PressureTest> {
    vec![
        PressureTest {
            name: DISPATCH_UNVALIDATED_PLAN.to_owned(),
            claim: "only a validated plan can be dispatched".to_owned(),
            enforced_by: "tests/compile_fail/dispatch_unvalidated_plan.rs".to_owned(),
        },
        PressureTest {
            name: DISPATCH_TWICE.to_owned(),
            claim: "dispatch consumes a validated plan exactly once".to_owned(),
            enforced_by: "tests/compile_fail/dispatch_twice.rs".to_owned(),
        },
        PressureTest {
            name: CONSTRUCT_MERGE_FROM_OUTSIDE.to_owned(),
            claim: "only the settlement crate can construct a merge".to_owned(),
            enforced_by: "tests/compile_fail/construct_merge_from_distributary.rs".to_owned(),
        },
        PressureTest {
            name: CONSTRUCT_BASELINE_FROM_OUTSIDE.to_owned(),
            claim: "only the settlement crate can construct a baseline".to_owned(),
            enforced_by: "tests/compile_fail/construct_baseline_from_distributary.rs".to_owned(),
        },
        PressureTest {
            name: SKIP_INTENT_RECOVERY.to_owned(),
            claim: "claims cannot be declared before intent is recovered".to_owned(),
            enforced_by: "tests/compile_fail/skip_intent_recovery.rs".to_owned(),
        },
        PressureTest {
            name: CONSTRUCT_COMPLETED_RUN_DIRECTLY.to_owned(),
            claim: "completed runs cannot be fabricated outside the dispatcher".to_owned(),
            enforced_by: "tests/compile_fail/construct_completed_run_directly.rs".to_owned(),
        },
        PressureTest {
            name: CONSTRUCT_VALIDATED_PLAN_DIRECTLY.to_owned(),
            claim: "validated plans cannot be fabricated outside the dispatcher".to_owned(),
            enforced_by: "tests/compile_fail/construct_validated_plan_directly.rs".to_owned(),
        },
        PressureTest {
            name: MERGE_REJECTED_VALIDATION.to_owned(),
            claim: "only accepted validation can be merged".to_owned(),
            enforced_by: "tests/compile_fail/merge_rejected_validation.rs".to_owned(),
        },
        PressureTest {
            name: BASELINE_WITHOUT_MERGE.to_owned(),
            claim: "only a merge can be anchored as a baseline".to_owned(),
            enforced_by: "tests/compile_fail/baseline_without_merge.rs".to_owned(),
        },
        PressureTest {
            name: COMPLETE_RUN_BEFORE_RUNNING.to_owned(),
            claim: "a pending run cannot complete before it is running".to_owned(),
            enforced_by: "tests/compile_fail/complete_run_before_running.rs".to_owned(),
        },
        PressureTest {
            name: VALIDATION_REJECTS_UNCLAIMED_FILES.to_owned(),
            claim: "validation rejects deposits that touched files outside the plan's write-authorizing file claims".to_owned(),
            enforced_by: "watershed-tributary/tests/claims_integrity.rs".to_owned(),
        },
        PressureTest {
            name: RETRY_COMPLETED_RUN.to_owned(),
            claim: "completed runs cannot be retried".to_owned(),
            enforced_by: "tests/compile_fail/retry_completed_run.rs".to_owned(),
        },
        PressureTest {
            name: RETRY_LINEAGE_FROM_FAILED.to_owned(),
            claim: "retrying a failed run preserves work, records parent lineage, increments retry index, and derives a new run id".to_owned(),
            enforced_by: "watershed-distributary/tests/retry_lineage.rs".to_owned(),
        },
        PressureTest {
            name: RETRY_RESPECTS_MAX_RETRIES.to_owned(),
            claim: "retrying a failed run cannot exceed the policy retry budget".to_owned(),
            enforced_by: "watershed-distributary/tests/retry_budget.rs".to_owned(),
        },
        PressureTest {
            name: DAG_KERNEL_SERIAL_MERGE_SCAN.to_owned(),
            claim: "the DAG kernel performs one merge at a time by scanning topological order, while terminal failures do not block later mergeable tasks".to_owned(),
            enforced_by: "watershed-distributary/tests/dag_kernel.rs".to_owned(),
        },
        PressureTest {
            name: DAG_PLAN_CLAIMS_TRAVEL_TO_MERGE.to_owned(),
            claim: "a typed DAG plan carries task file claims into the kernel merge action that authorizes settlement validation".to_owned(),
            enforced_by: "watershed-distributary/tests/dag_plan.rs".to_owned(),
        },
        PressureTest {
            name: DAG_PLAN_REJECTS_CONFLICTING_CLAIMS.to_owned(),
            claim: "a typed DAG plan rejects independent tasks with overlapping write authority unless the overlapping claims are explicitly shared".to_owned(),
            enforced_by: "watershed-distributary/tests/dag_plan.rs".to_owned(),
        },
        PressureTest {
            name: DAG_KERNEL_REJECTS_RAW_CLAIM_BYPASS.to_owned(),
            claim: "raw DAG kernel construction requires file claims for every task and rejects independent overlapping write authority".to_owned(),
            enforced_by: "watershed-distributary/tests/dag_kernel.rs".to_owned(),
        },
        PressureTest {
            name: WAIT_DONE_REJECTS_KERNEL_TASK_STATE.to_owned(),
            claim: "worker wait completion events accept only worker outcomes, not internal kernel task states".to_owned(),
            enforced_by: "tests/compile_fail/wait_done_rejects_kernel_task_state.rs".to_owned(),
        },
        PressureTest {
            name: DAG_KERNEL_BINDS_TASK_PANES.to_owned(),
            claim: "the DAG kernel binds task pane identity at dispatch, rejects wait completion from mismatched panes, and carries the bound pane into review interrupts and merge actions".to_owned(),
            enforced_by: "watershed-distributary/tests/dag_kernel.rs".to_owned(),
        },
        PressureTest {
            name: TASK_STATE_REJECTS_DEAD_VARIANTS.to_owned(),
            claim: "the public DAG task state enum exposes only lifecycle states the kernel can actually enter".to_owned(),
            enforced_by: "tests/compile_fail/task_state_rejects_dead_variants.rs".to_owned(),
        },
        PressureTest {
            name: REVIEW_DONE_REJECTS_BOOLEAN_VERDICT_BAG.to_owned(),
            claim: "review completion events use a typed review outcome instead of a boolean, verdict string, and commit-count bag".to_owned(),
            enforced_by: "tests/compile_fail/review_done_rejects_boolean_verdict_bag.rs".to_owned(),
        },
        PressureTest {
            name: MERGE_DONE_REJECTS_OPTIONAL_ERROR.to_owned(),
            claim: "merge completion events use a typed merge outcome instead of an optional error field".to_owned(),
            enforced_by: "tests/compile_fail/merge_done_rejects_optional_error.rs".to_owned(),
        },
        PressureTest {
            name: CONSTRUCT_DEPOSIT_DIRECTLY.to_owned(),
            claim: "only watershed-distributary completed runs can construct authoritative Deposit records".to_owned(),
            enforced_by: "tests/compile_fail/construct_deposit_directly.rs".to_owned(),
        },
        PressureTest {
            name: DEPOSIT_IDS_ARE_DERIVED.to_owned(),
            claim: "authoritative Deposit ids are content-derived from the producing run id, summary, and sorted touched files".to_owned(),
            enforced_by: "watershed-distributary/tests/worker_lifecycle.rs".to_owned(),
        },
        PressureTest {
            name: REQUIRED_PRESSURE_TESTS_ARE_REGISTERED.to_owned(),
            claim: "compiled plan validation rejects policy-required pressure test names that are not registered".to_owned(),
            enforced_by: "watershed-distributary/tests/policy_pressure_tests.rs".to_owned(),
        },
        PressureTest {
            name: PRESSURE_TEST_REGISTRY_SELF_CONSISTENT.to_owned(),
            claim: "pressure-test registry names, claims, and enforcement paths are non-empty, unique, and resolvable".to_owned(),
            enforced_by: "watershed-contracts/src/lib.rs".to_owned(),
        },
        PressureTest {
            name: FILE_CLAIM_PATHS_REJECT_ESCAPE_FORMS.to_owned(),
            claim: "file-claim authority paths reject empty paths, absolute paths, parent traversal, and non-authority current-directory forms before authorizing writes".to_owned(),
            enforced_by: "watershed-contracts/src/lib.rs;watershed-distributary/tests/dag_plan.rs;watershed-tributary/tests/claims_integrity.rs".to_owned(),
        },
    ]
}

#[cfg(test)]
mod tests {
    use super::{pressure_tests, ClaimKind, FileClaim, FileClaimPathError};
    use std::collections::BTreeSet;
    use std::path::{Path, PathBuf};

    fn claim(path: &str, kind: ClaimKind) -> FileClaim {
        FileClaim {
            path: PathBuf::from(path),
            kind,
        }
    }

    #[test]
    fn claim_covers_exact_path_and_descendants_only() {
        let claim = claim("./src/", ClaimKind::Exclusive);

        assert_eq!(
            claim.normalized_path().expect("path should normalize"),
            "src"
        );
        assert!(claim.covers_path("src").expect("path should normalize"));
        assert!(claim
            .covers_path("src/lib.rs")
            .expect("path should normalize"));
        assert!(!claim
            .covers_path("srcibling/lib.rs")
            .expect("path should normalize"));
        assert!(!claim
            .covers_path("src2/lib.rs")
            .expect("path should normalize"));
    }

    #[test]
    fn write_authority_excludes_read_only_claims() {
        let read_only = claim("src", ClaimKind::ReadOnly);
        let exclusive = claim("src", ClaimKind::Exclusive);

        assert!(read_only
            .covers_path("src/lib.rs")
            .expect("path should normalize"));
        assert!(!read_only
            .grants_write_to("src/lib.rs")
            .expect("path should normalize"));
        assert!(exclusive
            .grants_write_to("src/lib.rs")
            .expect("path should normalize"));
    }

    #[test]
    fn claim_conflicts_match_write_authority_overlap() {
        let exclusive_dir = claim("src", ClaimKind::Exclusive);
        let exclusive_file = claim("src/lib.rs", ClaimKind::Exclusive);
        let read_only_file = claim("src/lib.rs", ClaimKind::ReadOnly);
        let shared_a = claim("src/lib.rs", ClaimKind::Shared);
        let shared_b = claim("./src/lib.rs", ClaimKind::Shared);

        assert!(exclusive_dir
            .conflicts_with(&exclusive_file)
            .expect("paths should normalize"));
        assert!(!exclusive_dir
            .conflicts_with(&read_only_file)
            .expect("paths should normalize"));
        assert!(!shared_a
            .conflicts_with(&shared_b)
            .expect("paths should normalize"));
        assert!(shared_a
            .conflicts_with(&exclusive_file)
            .expect("paths should normalize"));
    }

    #[test]
    fn file_claim_paths_reject_escape_forms() {
        assert!(matches!(
            FileClaim::normalize_path(" "),
            Err(FileClaimPathError::Empty)
        ));
        assert!(matches!(
            FileClaim::normalize_path("."),
            Err(FileClaimPathError::Empty)
        ));
        assert!(matches!(
            FileClaim::normalize_path("/tmp/outside.rs"),
            Err(FileClaimPathError::Absolute { .. })
        ));
        assert!(matches!(
            FileClaim::normalize_path("src/../outside.rs"),
            Err(FileClaimPathError::ParentTraversal { .. })
        ));

        assert_eq!(
            FileClaim::normalize_path("./src//lib.rs").expect("path should normalize"),
            "src/lib.rs"
        );
    }

    #[test]
    fn authority_checks_validate_paths_before_kind_shortcuts() {
        let invalid_read_only = claim("../outside.rs", ClaimKind::ReadOnly);
        let exclusive = claim("src/lib.rs", ClaimKind::Exclusive);
        let valid_read_only = claim("src/lib.rs", ClaimKind::ReadOnly);

        assert!(invalid_read_only.grants_write_to("src/lib.rs").is_err());
        assert!(invalid_read_only.conflicts_with(&exclusive).is_err());
        assert!(valid_read_only.grants_write_to("../outside.rs").is_err());
    }

    #[test]
    fn pressure_test_registry_is_self_consistent() {
        let workspace_root = Path::new(env!("CARGO_MANIFEST_DIR"))
            .parent()
            .expect("contracts crate should live under workspace root")
            .canonicalize()
            .expect("workspace root should resolve");
        let mut names = BTreeSet::new();

        for pressure_test in pressure_tests() {
            let trimmed_name = pressure_test.name.trim();
            assert!(
                !trimmed_name.is_empty(),
                "pressure test name must be non-empty"
            );
            assert_eq!(
                pressure_test.name, trimmed_name,
                "pressure test name '{}' must not have leading or trailing whitespace",
                pressure_test.name
            );
            assert!(
                names.insert(trimmed_name.to_owned()),
                "duplicate pressure test name '{}'",
                pressure_test.name
            );
            assert!(
                !pressure_test.claim.trim().is_empty(),
                "pressure test '{}' must have a non-empty claim",
                pressure_test.name
            );

            let enforcement_paths = pressure_test
                .enforced_by
                .split(';')
                .map(str::trim)
                .collect::<Vec<_>>();
            assert!(
                !enforcement_paths.is_empty(),
                "pressure test '{}' must name at least one enforcement path",
                pressure_test.name
            );

            for path in enforcement_paths {
                assert!(
                    !path.is_empty(),
                    "pressure test '{}' has an empty enforcement path",
                    pressure_test.name
                );
                let resolved_path =
                    workspace_root
                        .join(path)
                        .canonicalize()
                        .unwrap_or_else(|err| {
                            panic!(
                                "pressure test '{}' enforcement path '{}' does not resolve: {err}",
                                pressure_test.name, path
                            )
                        });
                assert!(
                    resolved_path.starts_with(&workspace_root),
                    "pressure test '{}' enforcement path '{}' resolves outside the workspace",
                    pressure_test.name,
                    path
                );
                assert!(
                    resolved_path.is_file(),
                    "pressure test '{}' enforcement path '{}' does not resolve to a file",
                    pressure_test.name,
                    path
                );
            }
        }
    }
}
