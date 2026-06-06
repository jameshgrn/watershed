use std::path::PathBuf;
use watershed_contracts::{
    ClaimKind, FileClaim, Policy, RecoveredIntent, DEPOSIT_IDS_ARE_DERIVED,
    REQUIRED_PRESSURE_TESTS_ARE_REGISTERED,
};
use watershed_distributary::{Compiled, Drafted, Plan, ValidationError};

fn compiled_plan() -> Plan<Compiled> {
    let intent = RecoveredIntent {
        goal: "validate pressure-test policy names".to_owned(),
        scope: vec!["policy".to_owned()],
        constraints: vec!["registry-backed".to_owned()],
        non_goals: Vec::new(),
    };
    let claims = vec![FileClaim {
        path: PathBuf::from("src/lib.rs"),
        kind: ClaimKind::Exclusive,
    }];

    Plan::<Drafted>::draft()
        .recover_intent(intent)
        .declare_claims(claims)
        .compile()
        .expect("claims should compile")
}

fn policy(required_pressure_tests: Vec<String>) -> Policy {
    Policy {
        require_claims: true,
        allow_shared_claims: false,
        max_retries: None,
        required_pressure_tests,
    }
}

#[test]
fn validation_accepts_registered_required_pressure_tests() {
    let validated = compiled_plan().validate(&policy(vec![
        DEPOSIT_IDS_ARE_DERIVED.to_owned(),
        REQUIRED_PRESSURE_TESTS_ARE_REGISTERED.to_owned(),
    ]));

    assert!(validated.is_ok());
}

#[test]
fn validation_rejects_unknown_required_pressure_test() {
    let err = compiled_plan()
        .validate(&policy(vec!["missing_pressure_test".to_owned()]))
        .expect_err("unknown required pressure-test names should be rejected");

    assert!(matches!(
        err,
        ValidationError::UnknownPressureTest { name } if name == "missing_pressure_test"
    ));
}
