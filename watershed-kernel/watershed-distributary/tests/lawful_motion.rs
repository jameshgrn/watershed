use std::path::PathBuf;
use watershed_contracts::{
    pressure_tests, ClaimKind, FileClaim, Policy, RecoveredIntent, VerificationSpec,
};
use watershed_distributary::{collect, dispatch, mock_worker, Drafted, Plan};

#[test]
fn run_ceremony_produces_collectable_deposit() {
    let intent = RecoveredIntent {
        goal: "build a typed dispatcher kernel".to_owned(),
        scope: vec!["in-memory ceremony".to_owned()],
        constraints: vec!["no subprocesses".to_owned()],
        non_goals: vec!["registry persistence".to_owned()],
    };
    let claims = vec![FileClaim {
        path: PathBuf::from("watershed-distributary/src/lib.rs"),
        kind: ClaimKind::Exclusive,
    }];
    let required_pressure_tests = pressure_tests()
        .into_iter()
        .map(|pressure_test| pressure_test.name)
        .collect::<Vec<_>>();
    let policy = Policy {
        require_claims: true,
        allow_shared_claims: false,
        max_retries: None,
        required_pressure_tests: required_pressure_tests.clone(),
    };

    let plan = Plan::<Drafted>::draft()
        .recover_intent(intent)
        .declare_claims(claims)
        .declare_verification(VerificationSpec {
            checks: required_pressure_tests,
        })
        .compile()
        .expect("claims should compile")
        .validate(&policy)
        .expect("policy should validate");
    let pending = dispatch(plan);
    let run_id = pending.id().to_owned();
    let running = pending.start();
    let completed = mock_worker(running);
    let (deposit, claims, verification) = collect(completed);

    assert!(deposit.id().starts_with("deposit:"));
    assert_eq!(deposit.run_id(), run_id);
    assert_eq!(deposit.summary(), "synthetic deposit");
    assert_eq!(
        deposit.touched_files(),
        &[PathBuf::from("watershed-distributary/src/lib.rs")]
    );
    assert_eq!(claims.len(), 1);
    assert_eq!(
        verification.checks.len(),
        policy.required_pressure_tests.len()
    );
}
