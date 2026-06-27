use std::path::PathBuf;
use watershed_contracts::{
    pressure_tests, ClaimKind, FileClaim, Policy, RecoveredIntent, VerificationSpec,
};
use watershed_distributary::{collect, dispatch, mock_worker, Drafted, Plan};
use watershed_tributary::{baseline, merge, validate, Validation};

#[test]
fn full_ceremony_produces_baseline() {
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
    let running = pending.start();
    let completed = mock_worker(running);
    let (deposit, claims, verification) = collect(completed);
    let accepted = match validate(deposit, &claims, &verification) {
        Validation::Accepted(accepted) => accepted,
        Validation::Rejected(rejected) => {
            panic!("deposit was rejected: {}", rejected.reason());
        }
    };
    let merged = merge(accepted);
    let anchored = baseline(merged);

    assert!(anchored.id().starts_with("baseline:"));
}
