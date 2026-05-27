use std::path::PathBuf;

use watershed_contracts::{ClaimKind, FileClaim, Policy, RecoveredIntent};
use watershed_distributary::dag::{
    DagAction, DagError, DagEvent, DagPlan, DagTask, TaskDispatched, TaskMergeDone, TaskReviewDone,
    TaskState, TaskWaitDone,
};
use watershed_distributary::{collect, dispatch, mock_worker, Drafted, Plan};
use watershed_tributary::{baseline, merge, validate, Validation};

fn file_claim(path: &str) -> FileClaim {
    FileClaim {
        path: PathBuf::from(path),
        kind: ClaimKind::Exclusive,
    }
}

fn claim(path: &str, kind: ClaimKind) -> FileClaim {
    FileClaim {
        path: PathBuf::from(path),
        kind,
    }
}

fn root_task() -> DagTask {
    DagTask::new("root", Vec::new(), vec![file_claim("src/root.rs")])
        .expect("root task should be valid")
}

fn task(slug: &str, depends_on: Vec<String>, path: &str) -> DagTask {
    DagTask::new(slug, depends_on, vec![file_claim(path)]).expect("task should be valid")
}

fn task_review_passed(slug: &str) -> DagEvent {
    DagEvent::TaskReviewDone(TaskReviewDone {
        task_slug: slug.to_owned(),
        passed: true,
        verdict: "ok".to_owned(),
        commit_count: 1,
    })
}

fn merge_claims(actions: &[DagAction], task_slug: &str) -> Vec<FileClaim> {
    actions
        .iter()
        .find_map(|action| {
            if let DagAction::MergeTask(merge) = action {
                if merge.task_slug == task_slug {
                    return Some(merge.file_claims.clone());
                }
            }

            None
        })
        .expect("review pass should emit merge action")
}

#[test]
fn dag_plan_rejects_unknown_dependencies() {
    let task = task("downstream", vec!["missing".to_owned()], "b.rs");

    let err = DagPlan::new(vec![task]).expect_err("unknown dependency should be rejected");

    assert!(matches!(
        err,
        DagError::UnknownDependency {
            task,
            dependency
        } if task == "downstream" && dependency == "missing"
    ));
}

#[test]
fn dag_task_rejects_missing_claims() {
    let err = DagTask::new("claimless", Vec::new(), Vec::new())
        .expect_err("claimless task should be rejected");

    assert!(matches!(
        err,
        DagError::MissingClaims { task } if task == "claimless"
    ));
}

#[test]
fn dag_task_rejects_empty_claim_paths() {
    let err = DagTask::new("empty-claim", Vec::new(), vec![file_claim(" ")])
        .expect_err("empty claim paths should be rejected");

    assert!(matches!(
        err,
        DagError::EmptyClaimPath { task } if task == "empty-claim"
    ));
}

#[test]
fn dag_plan_rejects_duplicate_task_slugs() {
    let err = DagPlan::new(vec![
        task("same", Vec::new(), "a.rs"),
        task("same", Vec::new(), "b.rs"),
    ])
    .expect_err("duplicate task slugs should be rejected");

    assert!(matches!(
        err,
        DagError::DuplicateTask { task } if task == "same"
    ));
}

#[test]
fn dag_plan_rejects_dependency_cycles() {
    let a = task("a", vec!["b".to_owned()], "a.rs");
    let b = task("b", vec!["a".to_owned()], "b.rs");

    let err = DagPlan::new(vec![a, b]).expect_err("cycle should be rejected");

    assert!(matches!(err, DagError::Cycle { .. }));
}

#[test]
fn dag_plan_rejects_independent_conflicting_claims() {
    let a = DagTask::new("a", Vec::new(), vec![file_claim("src/main.rs")])
        .expect("task should be valid");
    let b = DagTask::new("b", Vec::new(), vec![file_claim("./src/main.rs")])
        .expect("task should be valid");

    let err = DagPlan::new(vec![a, b]).expect_err("conflicting claims should be rejected");

    assert!(matches!(
        err,
        DagError::ConflictingClaims {
            left_task,
            left_path,
            right_task,
            right_path
        } if left_task == "a"
            && left_path == "src/main.rs"
            && right_task == "b"
            && right_path == "src/main.rs"
    ));
}

#[test]
fn dag_plan_rejects_independent_directory_claim_overlap() {
    let a = DagTask::new("a", Vec::new(), vec![file_claim("src")]).expect("task should be valid");
    let b = DagTask::new("b", Vec::new(), vec![file_claim("src/main.rs")])
        .expect("task should be valid");

    let err = DagPlan::new(vec![a, b]).expect_err("directory overlap should be rejected");

    assert!(matches!(err, DagError::ConflictingClaims { .. }));
}

#[test]
fn dag_plan_allows_dependent_claim_overlap() {
    let a = DagTask::new("a", Vec::new(), vec![file_claim("src/main.rs")])
        .expect("task should be valid");
    let b = DagTask::new("b", vec!["a".to_owned()], vec![file_claim("src/main.rs")])
        .expect("task should be valid");

    let plan = DagPlan::new(vec![a, b]).expect("dependent overlap should be serializable");

    assert_eq!(plan.tasks().len(), 2);
}

#[test]
fn dag_plan_allows_read_only_and_shared_claim_overlap() {
    let reader = DagTask::new(
        "reader",
        Vec::new(),
        vec![claim("src/main.rs", ClaimKind::ReadOnly)],
    )
    .expect("task should be valid");
    let writer = DagTask::new(
        "writer",
        Vec::new(),
        vec![claim("src/main.rs", ClaimKind::Exclusive)],
    )
    .expect("task should be valid");
    let shared_a = DagTask::new(
        "shared-a",
        Vec::new(),
        vec![claim("src/lib.rs", ClaimKind::Shared)],
    )
    .expect("task should be valid");
    let shared_b = DagTask::new(
        "shared-b",
        Vec::new(),
        vec![claim("src/lib.rs", ClaimKind::Shared)],
    )
    .expect("task should be valid");

    let plan = DagPlan::new(vec![reader, writer, shared_a, shared_b])
        .expect("read-only and shared overlaps should be legal");

    assert_eq!(plan.tasks().len(), 4);
}

#[test]
fn dag_plan_compiles_claims_into_merge_actions() {
    let root = root_task();
    let downstream = task("downstream", vec!["root".to_owned()], "src/downstream.rs");
    let plan = DagPlan::new(vec![downstream, root]).expect("DAG plan should be valid");
    let mut kernel = plan.compile_kernel().expect("kernel should compile");

    assert_eq!(
        kernel.merge_order(),
        &["root".to_owned(), "downstream".to_owned()]
    );

    kernel.handle(DagEvent::TaskDispatched(TaskDispatched {
        task_slug: "root".to_owned(),
        pane_slug: "p-root".to_owned(),
    }));
    kernel.handle(DagEvent::TaskWaitDone(TaskWaitDone {
        task_slug: "root".to_owned(),
        pane_slug: "p-root".to_owned(),
        task_state: TaskState::Done,
    }));

    let actions = kernel.handle(task_review_passed("root"));
    let claims = merge_claims(&actions, "root");

    assert_eq!(claims, vec![file_claim("src/root.rs")]);
}

#[test]
fn dag_dispatch_feeds_existing_plan_run_settlement_ceremony() {
    let plan = DagPlan::new(vec![root_task()]).expect("DAG plan should be valid");
    let mut kernel = plan.compile_kernel().expect("kernel should compile");

    let dispatch_actions = kernel.start();
    assert!(dispatch_actions.iter().any(|action| {
        matches!(
            action,
            DagAction::DispatchTask(dispatch) if dispatch.task_slug == "root"
        )
    }));

    let task = plan.task("root").expect("root task should exist");
    let policy = Policy {
        require_claims: true,
        allow_shared_claims: false,
        max_retries: None,
        required_pressure_tests: Vec::new(),
    };
    let intent = RecoveredIntent {
        goal: "drive a DAG task through the run ceremony".to_owned(),
        scope: vec![task.slug().to_owned()],
        constraints: vec!["pure kernel emits actions only".to_owned()],
        non_goals: vec!["real worker dispatch".to_owned()],
    };

    let plan = Plan::<Drafted>::draft()
        .recover_intent(intent)
        .declare_claims(task.claims().to_vec())
        .compile()
        .expect("task claims should compile")
        .validate(&policy)
        .expect("policy should validate");
    let pending = dispatch(plan);
    let completed = mock_worker(pending.start());
    let (deposit, _dispatch_claims) = collect(completed);

    kernel.handle(DagEvent::TaskDispatched(TaskDispatched {
        task_slug: "root".to_owned(),
        pane_slug: "p-root".to_owned(),
    }));
    kernel.handle(DagEvent::TaskWaitDone(TaskWaitDone {
        task_slug: "root".to_owned(),
        pane_slug: "p-root".to_owned(),
        task_state: TaskState::Done,
    }));
    let merge_actions = kernel.handle(task_review_passed("root"));
    let merge_claims = merge_claims(&merge_actions, "root");

    let accepted = match validate(deposit, &merge_claims) {
        Validation::Accepted(accepted) => accepted,
        Validation::Rejected(rejected) => {
            panic!("deposit was rejected: {}", rejected.reason());
        }
    };
    let baseline = baseline(merge(accepted));

    assert!(baseline.id().starts_with("baseline-merge-run:"));

    let done_actions = kernel.handle(DagEvent::TaskMergeDone(TaskMergeDone {
        task_slug: "root".to_owned(),
        error: None,
    }));
    assert!(done_actions
        .iter()
        .any(|action| matches!(action, DagAction::DagDone(done) if done.merged == ["root"])));
}
