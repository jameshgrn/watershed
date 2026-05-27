use schemars::JsonSchema;
use serde::{Deserialize, Serialize};
use std::path::{Path, PathBuf};
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
    /// Returns the path form used when comparing claim authority.
    pub fn normalized_path(&self) -> String {
        normalize_claim_path(&self.path)
    }

    /// Returns whether this claim's path authority covers `path`.
    pub fn covers_path(&self, path: impl AsRef<Path>) -> bool {
        path_covers(
            &self.normalized_path(),
            &normalize_claim_path(path.as_ref()),
        )
    }

    /// Returns whether this claim grants write authority for `path`.
    pub fn grants_write_to(&self, path: impl AsRef<Path>) -> bool {
        !matches!(self.kind, ClaimKind::ReadOnly) && self.covers_path(path)
    }

    /// Returns whether this claim and `other` cannot legally run independently.
    pub fn conflicts_with(&self, other: &FileClaim) -> bool {
        if matches!(self.kind, ClaimKind::ReadOnly)
            || matches!(other.kind, ClaimKind::ReadOnly)
            || matches!(
                (&self.kind, &other.kind),
                (ClaimKind::Shared, ClaimKind::Shared)
            )
        {
            return false;
        }

        path_covers(&self.normalized_path(), &other.normalized_path())
            || path_covers(&other.normalized_path(), &self.normalized_path())
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

/// A named compile-time invariant and the test that enforces it.
#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
pub struct PressureTest {
    pub name: String,
    pub claim: String,
    pub enforced_by: String,
}

/// Typed output collected from a completed run.
#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
pub struct Deposit {
    pub run_id: String,
    pub summary: String,
    pub touched_files: Vec<PathBuf>,
}

/// Errors raised while handling shared contract data.
#[derive(Debug, Error)]
pub enum ContractError {
    #[error("invalid contract data: {reason}")]
    InvalidData { reason: String },
}

fn normalize_claim_path(path: &Path) -> String {
    path.to_string_lossy()
        .trim()
        .trim_start_matches("./")
        .trim_end_matches('/')
        .to_owned()
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
pub const WAIT_DONE_REJECTS_KERNEL_TASK_STATE: &str = "wait_done_rejects_kernel_task_state";
pub const DAG_KERNEL_BINDS_TASK_PANES: &str = "dag_kernel_binds_task_panes";

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
            name: WAIT_DONE_REJECTS_KERNEL_TASK_STATE.to_owned(),
            claim: "worker wait completion events accept only worker outcomes, not internal kernel task states".to_owned(),
            enforced_by: "tests/compile_fail/wait_done_rejects_kernel_task_state.rs".to_owned(),
        },
        PressureTest {
            name: DAG_KERNEL_BINDS_TASK_PANES.to_owned(),
            claim: "the DAG kernel binds task pane identity at dispatch, rejects wait completion from mismatched panes, and carries the bound pane into review interrupts and merge actions".to_owned(),
            enforced_by: "watershed-distributary/tests/dag_kernel.rs".to_owned(),
        },
    ]
}

#[cfg(test)]
mod tests {
    use super::{ClaimKind, FileClaim};
    use std::path::PathBuf;

    fn claim(path: &str, kind: ClaimKind) -> FileClaim {
        FileClaim {
            path: PathBuf::from(path),
            kind,
        }
    }

    #[test]
    fn claim_covers_exact_path_and_descendants_only() {
        let claim = claim("./src/", ClaimKind::Exclusive);

        assert_eq!(claim.normalized_path(), "src");
        assert!(claim.covers_path("src"));
        assert!(claim.covers_path("src/lib.rs"));
        assert!(!claim.covers_path("srcibling/lib.rs"));
        assert!(!claim.covers_path("src2/lib.rs"));
    }

    #[test]
    fn write_authority_excludes_read_only_claims() {
        let read_only = claim("src", ClaimKind::ReadOnly);
        let exclusive = claim("src", ClaimKind::Exclusive);

        assert!(read_only.covers_path("src/lib.rs"));
        assert!(!read_only.grants_write_to("src/lib.rs"));
        assert!(exclusive.grants_write_to("src/lib.rs"));
    }

    #[test]
    fn claim_conflicts_match_write_authority_overlap() {
        let exclusive_dir = claim("src", ClaimKind::Exclusive);
        let exclusive_file = claim("src/lib.rs", ClaimKind::Exclusive);
        let read_only_file = claim("src/lib.rs", ClaimKind::ReadOnly);
        let shared_a = claim("src/lib.rs", ClaimKind::Shared);
        let shared_b = claim("./src/lib.rs", ClaimKind::Shared);

        assert!(exclusive_dir.conflicts_with(&exclusive_file));
        assert!(!exclusive_dir.conflicts_with(&read_only_file));
        assert!(!shared_a.conflicts_with(&shared_b));
        assert!(shared_a.conflicts_with(&exclusive_file));
    }
}
