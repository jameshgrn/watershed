use std::path::PathBuf;
use watershed_contracts::{
    ClaimKind, FileClaim, Policy, RecoveredIntent, VerificationSpec, DEPOSIT_IDS_ARE_DERIVED,
};
use watershed_distributary::{dispatch, Drafted, Failed, Plan, Run, Validated};

fn validated_plan() -> Plan<Validated> {
    let intent = RecoveredIntent {
        goal: "retry failed work".to_owned(),
        scope: vec!["run state machine".to_owned()],
        constraints: vec!["same work only".to_owned()],
        non_goals: vec!["retry completed work".to_owned()],
    };
    let claims = vec![FileClaim {
        path: PathBuf::from("src/lib.rs"),
        kind: ClaimKind::Exclusive,
    }];
    let policy = Policy {
        require_claims: true,
        allow_shared_claims: false,
        max_retries: None,
        required_pressure_tests: Vec::new(),
    };

    Plan::<Drafted>::draft()
        .recover_intent(intent)
        .declare_claims(claims)
        .declare_verification(VerificationSpec {
            checks: vec![DEPOSIT_IDS_ARE_DERIVED.to_owned()],
        })
        .compile()
        .expect("claims should compile")
        .validate(&policy)
        .expect("policy should validate")
}

fn failed_run() -> Run<Failed> {
    dispatch(validated_plan()).start().fail("worker failed")
}

#[test]
fn failed_run_retries_as_pending_with_lineage() {
    let failed = failed_run();
    let parent_id = failed.id().to_owned();
    let parent_goal = failed.intent().goal.clone();
    let parent_scope = failed.intent().scope.clone();
    let parent_constraints = failed.intent().constraints.clone();
    let parent_non_goals = failed.intent().non_goals.clone();
    let parent_claim_path = failed.claims()[0].path.clone();

    assert!(failed.retried_from().is_none());
    assert_eq!(failed.retry_index(), 0);

    let retry = failed.retry().expect("unbounded policy should allow retry");

    assert_ne!(retry.id(), parent_id);
    assert_eq!(retry.retried_from(), Some(parent_id.as_str()));
    assert_eq!(retry.retry_index(), 1);
    assert_eq!(retry.intent().goal.as_str(), parent_goal.as_str());
    assert_eq!(retry.intent().scope.as_slice(), parent_scope.as_slice());
    assert_eq!(
        retry.intent().constraints.as_slice(),
        parent_constraints.as_slice()
    );
    assert_eq!(
        retry.intent().non_goals.as_slice(),
        parent_non_goals.as_slice()
    );
    assert_eq!(retry.claims().len(), 1);
    assert_eq!(
        retry.claims()[0].path.as_path(),
        parent_claim_path.as_path()
    );
    assert!(matches!(&retry.claims()[0].kind, ClaimKind::Exclusive));
}

#[test]
fn equivalent_failed_runs_produce_equivalent_retries() {
    let retry_a = failed_run()
        .retry()
        .expect("unbounded policy should allow retry");
    let retry_b = failed_run()
        .retry()
        .expect("unbounded policy should allow retry");

    assert_eq!(retry_a.retried_from(), retry_b.retried_from());
    assert_eq!(retry_a.retry_index(), retry_b.retry_index());
    assert_eq!(retry_a.id(), retry_b.id());
}

#[test]
fn retry_lineage_survives_completion() {
    let failed = failed_run();
    let parent_id = failed.id().to_owned();
    let completed = failed
        .retry()
        .expect("unbounded policy should allow retry")
        .start()
        .complete("synthetic deposit", vec![PathBuf::from("src/lib.rs")]);

    assert_eq!(completed.retried_from(), Some(parent_id.as_str()));
    assert_eq!(completed.retry_index(), 1);
    assert_ne!(completed.id(), parent_id);
}

#[test]
fn retry_chain_increments_from_each_failed_parent() {
    let first_failed = failed_run();
    let original_id = first_failed.id().to_owned();
    let first_retry = first_failed
        .retry()
        .expect("unbounded policy should allow retry");
    let first_retry_id = first_retry.id().to_owned();
    let failed_retry = first_retry.start().fail("retry failed");

    assert_eq!(failed_retry.retried_from(), Some(original_id.as_str()));
    assert_eq!(failed_retry.retry_index(), 1);

    let second_retry = failed_retry
        .retry()
        .expect("unbounded policy should allow retry");

    assert_eq!(second_retry.retried_from(), Some(first_retry_id.as_str()));
    assert_eq!(second_retry.retry_index(), 2);
    assert_ne!(second_retry.id(), original_id);
    assert_ne!(second_retry.id(), first_retry_id);
}
