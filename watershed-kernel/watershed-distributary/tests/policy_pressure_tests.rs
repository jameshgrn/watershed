use std::path::PathBuf;
use watershed_contracts::{
    ClaimKind, FileClaim, Policy, RecoveredIntent, VerificationSpec, DEPOSIT_IDS_ARE_DERIVED,
    REQUIRED_PRESSURE_TESTS_ARE_REGISTERED,
};
use watershed_distributary::{Compiled, Drafted, Plan, ValidationError};

fn compiled_plan(checks: Vec<String>) -> Plan<Compiled> {
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
        .declare_verification(VerificationSpec { checks })
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
    let checks = vec![
        DEPOSIT_IDS_ARE_DERIVED.to_owned(),
        REQUIRED_PRESSURE_TESTS_ARE_REGISTERED.to_owned(),
    ];
    let validated = compiled_plan(checks.clone()).validate(&policy(checks));

    assert!(validated.is_ok());
}

#[test]
fn validation_rejects_unknown_required_pressure_test() {
    let err = compiled_plan(vec![DEPOSIT_IDS_ARE_DERIVED.to_owned()])
        .validate(&policy(vec!["missing_pressure_test".to_owned()]))
        .expect_err("unknown required pressure-test names should be rejected");

    assert!(matches!(
        err,
        ValidationError::UnknownPressureTest { name } if name == "missing_pressure_test"
    ));
}

#[test]
fn validation_rejects_empty_verification_spec() {
    let err = compiled_plan(Vec::new())
        .validate(&policy(Vec::new()))
        .expect_err("empty verification specs should be rejected");

    assert!(matches!(err, ValidationError::MissingVerificationChecks));
}

#[test]
fn validation_rejects_unknown_verification_check() {
    let err = compiled_plan(vec!["missing_pressure_test".to_owned()])
        .validate(&policy(Vec::new()))
        .expect_err("unknown verification checks should be rejected");

    assert!(matches!(
        err,
        ValidationError::UnknownVerificationCheck { name } if name == "missing_pressure_test"
    ));
}

#[test]
fn validation_rejects_required_check_missing_from_verification_spec() {
    let err = compiled_plan(vec![DEPOSIT_IDS_ARE_DERIVED.to_owned()])
        .validate(&policy(vec![
            REQUIRED_PRESSURE_TESTS_ARE_REGISTERED.to_owned()
        ]))
        .expect_err("policy-required checks must be declared by the plan");

    assert!(matches!(
        err,
        ValidationError::MissingRequiredVerification { name }
            if name == REQUIRED_PRESSURE_TESTS_ARE_REGISTERED
    ));
}
