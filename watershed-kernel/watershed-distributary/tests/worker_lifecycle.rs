use std::path::PathBuf;
use watershed_contracts::{ClaimKind, FileClaim, Policy, RecoveredIntent};
use watershed_distributary::{collect, dispatch, mock_worker, Drafted, Plan, Validated};

fn validated_plan() -> Plan<Validated> {
    let intent = RecoveredIntent {
        goal: "prove worker lifecycle".to_owned(),
        scope: vec!["run state machine".to_owned()],
        constraints: vec!["in memory".to_owned()],
        non_goals: Vec::new(),
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
        .compile()
        .expect("claims should compile")
        .validate(&policy)
        .expect("policy should validate")
}

#[test]
fn pending_run_starts_before_completion() {
    let pending = dispatch(validated_plan());
    let run_id = pending.id().to_owned();
    let running = pending.start();
    let completed = mock_worker(running);

    assert_eq!(completed.id(), run_id);
}

#[test]
fn running_run_can_fail() {
    let failed = dispatch(validated_plan()).start().fail("worker failed");

    assert_eq!(failed.reason(), "worker failed");
}

#[test]
fn completed_runs_derive_stable_deposit_ids() {
    let first = dispatch(validated_plan()).start().complete(
        "synthetic deposit",
        vec![PathBuf::from("./b.rs"), PathBuf::from("a.rs")],
    );
    let second = dispatch(validated_plan()).start().complete(
        "synthetic deposit",
        vec![PathBuf::from("b.rs"), PathBuf::from("./a.rs")],
    );
    let (first_deposit, _first_claims) = collect(first);
    let (second_deposit, _second_claims) = collect(second);

    assert_eq!(first_deposit.id(), second_deposit.id());
    assert_eq!(
        first_deposit.touched_files(),
        &[PathBuf::from("a.rs"), PathBuf::from("b.rs")]
    );
    assert!(first_deposit.id().starts_with("deposit:"));
}
