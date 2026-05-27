use std::collections::BTreeMap;
use std::path::PathBuf;

use watershed_contracts::{ClaimKind, FileClaim};

use watershed_distributary::dag::{
    topological_sort, DagAction, DagError, DagEvent, DagKernel, DagState, DispatchTask,
    GovernorAction, TaskDispatched, TaskGovernorResumed, TaskMergeDone, TaskMergeOutcome,
    TaskReviewDone, TaskReviewOutcome, TaskState, TaskWaitDone, TaskWaitOutcome,
};

fn dep_map<const N: usize>(spec: [(&str, &[&str]); N]) -> BTreeMap<String, Vec<String>> {
    spec.into_iter()
        .map(|(task, deps)| {
            (
                task.to_owned(),
                deps.iter().map(|dep| (*dep).to_owned()).collect(),
            )
        })
        .collect()
}

fn file_claim(path: &str) -> FileClaim {
    FileClaim {
        path: PathBuf::from(path),
        kind: ClaimKind::Exclusive,
    }
}

fn kernel<const N: usize>(spec: [(&str, &[&str]); N]) -> DagKernel {
    DagKernel::new(dep_map(spec)).expect("test DAG should be valid")
}

fn dispatched(slug: &str, pane: &str) -> DagEvent {
    DagEvent::TaskDispatched(TaskDispatched {
        task_slug: slug.to_owned(),
        pane_slug: pane.to_owned(),
    })
}

fn wait_done(slug: &str, pane: &str, outcome: TaskWaitOutcome) -> DagEvent {
    DagEvent::TaskWaitDone(TaskWaitDone {
        task_slug: slug.to_owned(),
        pane_slug: pane.to_owned(),
        outcome,
    })
}

fn review_done(slug: &str, outcome: TaskReviewOutcome) -> DagEvent {
    DagEvent::TaskReviewDone(TaskReviewDone {
        task_slug: slug.to_owned(),
        outcome,
    })
}

fn merge_done(slug: &str) -> DagEvent {
    DagEvent::TaskMergeDone(TaskMergeDone {
        task_slug: slug.to_owned(),
        outcome: TaskMergeOutcome::Merged,
    })
}

fn merge_failed(slug: &str) -> DagEvent {
    DagEvent::TaskMergeDone(TaskMergeDone {
        task_slug: slug.to_owned(),
        outcome: TaskMergeOutcome::Failed,
    })
}

fn governor_resumed(slug: &str, action: GovernorAction) -> DagEvent {
    DagEvent::TaskGovernorResumed(TaskGovernorResumed {
        task_slug: slug.to_owned(),
        action,
    })
}

fn has_dispatch(actions: &[DagAction], slug: &str) -> bool {
    actions.iter().any(|action| {
        matches!(
            action,
            DagAction::DispatchTask(DispatchTask { task_slug }) if task_slug == slug
        )
    })
}

fn has_review(actions: &[DagAction], slug: &str) -> bool {
    actions.iter().any(|action| {
        matches!(
            action,
            DagAction::ReviewTask(review) if review.task_slug == slug
        )
    })
}

fn review_pane<'a>(actions: &'a [DagAction], slug: &str) -> Option<&'a str> {
    actions.iter().find_map(|action| {
        if let DagAction::ReviewTask(review) = action {
            if review.task_slug == slug {
                return Some(review.pane_slug.as_str());
            }
        }

        None
    })
}

fn has_merge(actions: &[DagAction], slug: &str) -> bool {
    actions.iter().any(|action| {
        matches!(
            action,
            DagAction::MergeTask(merge) if merge.task_slug == slug
        )
    })
}

fn merge_pane<'a>(actions: &'a [DagAction], slug: &str) -> Option<&'a str> {
    actions.iter().find_map(|action| {
        if let DagAction::MergeTask(merge) = action {
            if merge.task_slug == slug {
                return Some(merge.pane_slug.as_str());
            }
        }

        None
    })
}

fn has_cleanup(actions: &[DagAction], slug: &str) -> bool {
    actions.iter().any(|action| {
        matches!(
            action,
            DagAction::CleanupTask(cleanup) if cleanup.task_slug == slug
        )
    })
}

fn has_interrupt(actions: &[DagAction], slug: &str, reason: &str) -> bool {
    actions.iter().any(|action| {
        matches!(
            action,
            DagAction::InterruptGovernor(interrupt)
                if interrupt.task_slug == slug && interrupt.reason == reason
        )
    })
}

fn interrupt_pane<'a>(actions: &'a [DagAction], slug: &str, reason: &str) -> Option<&'a str> {
    actions.iter().find_map(|action| {
        if let DagAction::InterruptGovernor(interrupt) = action {
            if interrupt.task_slug == slug && interrupt.reason == reason {
                return Some(interrupt.pane_slug.as_str());
            }
        }

        None
    })
}

fn dag_done(actions: &[DagAction]) -> Option<&watershed_distributary::dag::DagDone> {
    actions.iter().find_map(|action| {
        if let DagAction::DagDone(done) = action {
            Some(done)
        } else {
            None
        }
    })
}

fn position(order: &[String], slug: &str) -> usize {
    order
        .iter()
        .position(|candidate| candidate == slug)
        .expect("task should be present in topological order")
}

fn drive_happy(kernel: &mut DagKernel, slug: &str) -> Vec<DagAction> {
    let pane = format!("p-{slug}");
    let mut actions = Vec::new();
    actions.extend(kernel.handle(dispatched(slug, &pane)));
    actions.extend(kernel.handle(wait_done(slug, &pane, TaskWaitOutcome::Done)));
    actions.extend(kernel.handle(review_done(slug, TaskReviewOutcome::Passed)));
    actions.extend(kernel.handle(merge_done(slug)));
    actions
}

#[test]
fn topo_sort_is_deterministic_and_detects_cycles() {
    let deps = dep_map([("d", &["b", "c"]), ("b", &["a"]), ("c", &["a"]), ("a", &[])]);
    let order = topological_sort(&deps).expect("diamond should sort");

    assert!(position(&order, "a") < position(&order, "b"));
    assert!(position(&order, "a") < position(&order, "c"));
    assert!(position(&order, "b") < position(&order, "d"));
    assert!(position(&order, "c") < position(&order, "d"));
    assert_eq!(order, topological_sort(&deps).expect("sort should repeat"));

    let err = topological_sort(&dep_map([("a", &["b"]), ("b", &["a"])]))
        .expect_err("cycle should be rejected");
    assert!(matches!(err, DagError::Cycle { .. }));
}

#[test]
fn raw_kernel_definition_rejects_empty_task_identity() {
    let empty_task =
        DagKernel::new(dep_map([("", &[])])).expect_err("empty task slug should be rejected");
    assert!(matches!(empty_task, DagError::EmptyTaskSlug));

    let empty_dependency = DagKernel::new(dep_map([("a", &[""])]))
        .expect_err("empty dependency slug should be rejected");
    assert!(matches!(
        empty_dependency,
        DagError::EmptyDependency { task } if task == "a"
    ));
}

#[test]
fn raw_kernel_task_files_reject_invalid_claim_shape() {
    let deps = dep_map([("a", &[])]);

    let missing_claims =
        DagKernel::with_task_files(deps.clone(), BTreeMap::from([("a".to_owned(), Vec::new())]))
            .expect_err("empty task file claim set should be rejected");
    assert!(matches!(
        missing_claims,
        DagError::MissingClaims { task } if task == "a"
    ));

    let empty_path = DagKernel::with_task_files(
        deps,
        BTreeMap::from([("a".to_owned(), vec![file_claim(" ")])]),
    )
    .expect_err("empty task file claim path should be rejected");
    assert!(matches!(
        empty_path,
        DagError::EmptyClaimPath { task } if task == "a"
    ));
}

#[test]
fn start_dispatches_only_dependency_roots() {
    let kernel = kernel([("a", &[]), ("b", &["a"]), ("c", &[])]);

    let actions = kernel.start();

    assert!(has_dispatch(&actions, "a"));
    assert!(has_dispatch(&actions, "c"));
    assert!(!has_dispatch(&actions, "b"));
    assert_eq!(kernel.status(), DagState::Idle);
}

#[test]
fn single_task_happy_path_finishes_the_dag() {
    let mut kernel = kernel([("a", &[])]);
    kernel.start();

    let actions = kernel.handle(dispatched("a", "p-a"));
    assert_eq!(kernel.task_state("a"), Some(TaskState::Active));
    assert!(actions.is_empty());
    assert_eq!(
        kernel.snapshot().task_panes.get("a").map(String::as_str),
        Some("p-a")
    );

    let actions = kernel.handle(wait_done("a", "p-a", TaskWaitOutcome::Done));
    assert_eq!(kernel.task_state("a"), Some(TaskState::Reviewing));
    assert!(has_review(&actions, "a"));
    assert_eq!(review_pane(&actions, "a"), Some("p-a"));

    let actions = kernel.handle(review_done("a", TaskReviewOutcome::Passed));
    assert_eq!(kernel.task_state("a"), Some(TaskState::Merging));
    assert!(has_merge(&actions, "a"));
    assert_eq!(merge_pane(&actions, "a"), Some("p-a"));

    let actions = kernel.handle(merge_done("a"));
    assert_eq!(kernel.task_state("a"), Some(TaskState::Merged));
    assert!(kernel.done());
    assert_eq!(kernel.status(), DagState::Completed);

    let done = dag_done(&actions).expect("done action should be emitted");
    assert_eq!(done.merged, vec!["a"]);
    assert!(done.failed.is_empty());
    assert!(done.skipped.is_empty());
}

#[test]
fn wait_done_must_match_dispatched_pane() {
    let mut kernel = kernel([("a", &[])]);
    kernel.start();
    kernel.handle(dispatched("a", "p-a"));

    let wrong_pane = kernel.handle(wait_done("a", "p-other", TaskWaitOutcome::Done));

    assert_eq!(kernel.task_state("a"), Some(TaskState::Active));
    assert!(wrong_pane.is_empty());

    let correct_pane = kernel.handle(wait_done("a", "p-a", TaskWaitOutcome::Done));

    assert_eq!(kernel.task_state("a"), Some(TaskState::Reviewing));
    assert_eq!(review_pane(&correct_pane, "a"), Some("p-a"));
}

#[test]
fn merged_dependency_unblocks_downstream_dispatch() {
    let mut kernel = kernel([("a", &[]), ("b", &["a"]), ("c", &["b"])]);
    kernel.start();

    let actions = drive_happy(&mut kernel, "a");

    assert!(has_dispatch(&actions, "b"));
    assert!(!has_dispatch(&actions, "c"));
}

#[test]
fn parallel_reviews_merge_one_at_a_time_in_topological_order() {
    let mut kernel = kernel([("a", &[]), ("b", &[])]);
    kernel.start();
    kernel.handle(dispatched("a", "p-a"));
    kernel.handle(dispatched("b", "p-b"));
    kernel.handle(wait_done("a", "p-a", TaskWaitOutcome::Done));
    kernel.handle(wait_done("b", "p-b", TaskWaitOutcome::Done));

    let first = kernel.handle(review_done("a", TaskReviewOutcome::Passed));
    let second = kernel.handle(review_done("b", TaskReviewOutcome::Passed));

    assert!(has_merge(&first, "a"));
    assert_eq!(merge_pane(&first, "a"), Some("p-a"));
    assert!(!has_merge(&second, "b"));
    assert_eq!(kernel.task_state("a"), Some(TaskState::Merging));
    assert_eq!(kernel.task_state("b"), Some(TaskState::ReviewedPass));

    let after_first_merge = kernel.handle(merge_done("a"));

    assert!(has_merge(&after_first_merge, "b"));
    assert_eq!(merge_pane(&after_first_merge, "b"), Some("p-b"));
    assert_eq!(kernel.task_state("b"), Some(TaskState::Merging));
}

#[test]
fn terminal_failure_does_not_block_later_mergeable_task() {
    let mut kernel = kernel([("a", &[]), ("b", &[])]);
    kernel.start();
    kernel.handle(dispatched("a", "p-a"));
    kernel.handle(dispatched("b", "p-b"));
    kernel.handle(wait_done("a", "p-a", TaskWaitOutcome::Done));
    kernel.handle(wait_done("b", "p-b", TaskWaitOutcome::Done));

    let fail_actions = kernel.handle(review_done("a", TaskReviewOutcome::Rejected));
    assert_eq!(kernel.task_state("a"), Some(TaskState::Failed));
    assert!(has_cleanup(&fail_actions, "a"));

    let pass_actions = kernel.handle(review_done("b", TaskReviewOutcome::Passed));

    assert_eq!(kernel.task_state("b"), Some(TaskState::Merging));
    assert!(has_merge(&pass_actions, "b"));
}

#[test]
fn in_progress_task_blocks_later_mergeable_task() {
    let mut kernel = kernel([("a", &[]), ("b", &[])]);
    kernel.start();
    kernel.handle(dispatched("a", "p-a"));
    kernel.handle(dispatched("b", "p-b"));
    kernel.handle(wait_done("b", "p-b", TaskWaitOutcome::Done));

    let actions = kernel.handle(review_done("b", TaskReviewOutcome::Passed));

    assert_eq!(kernel.task_state("a"), Some(TaskState::Active));
    assert_eq!(kernel.task_state("b"), Some(TaskState::ReviewedPass));
    assert!(!has_merge(&actions, "b"));
}

#[test]
fn merge_failure_cascades_to_pending_dependents_but_not_independent_active_work() {
    let mut kernel = kernel([("a", &[]), ("b", &["a"]), ("c", &[])]);
    kernel.start();
    kernel.handle(dispatched("a", "p-a"));
    kernel.handle(dispatched("c", "p-c"));
    kernel.handle(wait_done("a", "p-a", TaskWaitOutcome::Done));
    kernel.handle(review_done("a", TaskReviewOutcome::Passed));

    let actions = kernel.handle(merge_failed("a"));

    assert_eq!(kernel.task_state("a"), Some(TaskState::Failed));
    assert_eq!(kernel.task_state("b"), Some(TaskState::Skipped));
    assert_eq!(kernel.task_state("c"), Some(TaskState::Active));
    assert!(!has_cleanup(&actions, "a"));
}

#[test]
fn terminal_worker_wait_outcomes_cleanup_and_skip_pending_dependents() {
    for (outcome, terminal_state) in [
        (TaskWaitOutcome::TimedOut, TaskState::TimedOut),
        (TaskWaitOutcome::Abandoned, TaskState::Abandoned),
    ] {
        let mut kernel = kernel([("a", &[]), ("b", &["a"]), ("c", &[])]);
        kernel.start();
        kernel.handle(dispatched("a", "p-a"));
        kernel.handle(dispatched("c", "p-c"));

        let actions = kernel.handle(wait_done("a", "p-a", outcome));

        assert_eq!(kernel.task_state("a"), Some(terminal_state));
        assert_eq!(kernel.task_state("b"), Some(TaskState::Skipped));
        assert_eq!(kernel.task_state("c"), Some(TaskState::Active));
        assert!(has_cleanup(&actions, "a"));
        assert!(!has_interrupt(&actions, "a", &outcome.to_string()));
    }
}

#[test]
fn governor_retry_resets_interrupted_active_task() {
    let mut kernel = kernel([("a", &[])]);
    kernel.start();
    kernel.handle(dispatched("a", "p-a"));

    let interrupt = kernel.handle(wait_done("a", "p-a", TaskWaitOutcome::Failed));
    assert!(has_interrupt(&interrupt, "a", "failed"));
    assert_eq!(interrupt_pane(&interrupt, "a", "failed"), Some("p-a"));
    assert_eq!(kernel.task_state("a"), Some(TaskState::Active));

    let actions = kernel.handle(governor_resumed("a", GovernorAction::Retry));

    assert_eq!(kernel.task_state("a"), Some(TaskState::Pending));
    assert!(has_dispatch(&actions, "a"));
}

#[test]
fn governor_resume_cannot_unmerge_task() {
    let mut kernel = kernel([("a", &[])]);
    kernel.start();
    drive_happy(&mut kernel, "a");

    let actions = kernel.handle(governor_resumed("a", GovernorAction::Retry));

    assert_eq!(kernel.task_state("a"), Some(TaskState::Merged));
    assert!(actions.is_empty());
    assert!(!has_dispatch(&actions, "a"));
}

#[test]
fn skip_cascades_to_dependents_and_appears_in_done_summary() {
    let mut kernel = kernel([("a", &[]), ("b", &["a"])]);
    kernel.start();
    kernel.handle(dispatched("a", "p-a"));
    kernel.handle(wait_done("a", "p-a", TaskWaitOutcome::Failed));

    let actions = kernel.handle(governor_resumed("a", GovernorAction::Skip));

    assert_eq!(kernel.task_state("a"), Some(TaskState::Skipped));
    assert_eq!(kernel.task_state("b"), Some(TaskState::Skipped));
    assert!(kernel.done());

    let done = dag_done(&actions).expect("skip should finish the DAG");
    assert_eq!(done.skipped, vec!["a", "b"]);
}

#[test]
fn read_scope_violation_interrupts_without_skipping_dependents() {
    let mut kernel = kernel([("a", &[]), ("b", &["a"])]);
    kernel.start();
    kernel.handle(dispatched("a", "p-a"));
    kernel.handle(wait_done("a", "p-a", TaskWaitOutcome::Done));

    let actions = kernel.handle(review_done("a", TaskReviewOutcome::ReadScopeViolation));

    assert_eq!(kernel.task_state("a"), Some(TaskState::Failed));
    assert_eq!(kernel.task_state("b"), Some(TaskState::Pending));
    assert!(has_interrupt(&actions, "a", "read_scope_violation"));
    assert_eq!(
        interrupt_pane(&actions, "a", "read_scope_violation"),
        Some("p-a")
    );
}
