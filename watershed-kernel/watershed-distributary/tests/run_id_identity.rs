use std::path::PathBuf;
use watershed_contracts::{
    ClaimKind, FileClaim, Policy, RecoveredIntent, VerificationSpec, DEPOSIT_IDS_ARE_DERIVED,
    REQUIRED_PRESSURE_TESTS_ARE_REGISTERED,
};
use watershed_distributary::{derive_run_id, dispatch, Drafted, Plan, Validated};

fn validated_plan(goal: &str, path: &str, kind: ClaimKind) -> Plan<Validated> {
    validated_plan_with_checks(goal, path, kind, vec![DEPOSIT_IDS_ARE_DERIVED.to_owned()])
}

fn validated_plan_with_checks(
    goal: &str,
    path: &str,
    kind: ClaimKind,
    checks: Vec<String>,
) -> Plan<Validated> {
    let intent = RecoveredIntent {
        goal: goal.to_owned(),
        scope: vec!["dispatch identity".to_owned()],
        constraints: vec!["content-derived".to_owned()],
        non_goals: vec!["assigned identifiers".to_owned()],
    };
    let claims = vec![FileClaim {
        path: PathBuf::from(path),
        kind,
    }];
    let policy = Policy {
        require_claims: true,
        allow_shared_claims: false,
        max_retries: None,
        required_pressure_tests: vec![],
    };

    Plan::<Drafted>::draft()
        .recover_intent(intent)
        .declare_claims(claims)
        .declare_verification(VerificationSpec { checks })
        .compile()
        .expect("claims should compile")
        .validate(&policy)
        .expect("policy should validate")
}

#[test]
fn equivalent_dispatches_produce_equal_run_ids() {
    let run_a = dispatch(validated_plan(
        "derive run id",
        "./a.rs",
        ClaimKind::Exclusive,
    ));
    let run_b = dispatch(validated_plan(
        "derive run id",
        "a.rs",
        ClaimKind::Exclusive,
    ));

    assert_eq!(run_a.id(), run_b.id());
    assert_eq!(run_a.claims()[0].path, PathBuf::from("a.rs"));
    assert_eq!(
        derive_run_id(
            run_a.intent(),
            &[FileClaim {
                path: PathBuf::from("./a.rs"),
                kind: ClaimKind::Exclusive,
            }],
            run_a.verification(),
            None,
            0,
        ),
        derive_run_id(
            run_a.intent(),
            &[FileClaim {
                path: PathBuf::from("a.rs"),
                kind: ClaimKind::Exclusive,
            }],
            run_a.verification(),
            None,
            0,
        )
    );
}

#[test]
fn differing_intents_produce_different_run_ids() {
    let run_a = dispatch(validated_plan(
        "derive run id",
        "a.rs",
        ClaimKind::Exclusive,
    ));
    let run_b = dispatch(validated_plan(
        "derive another run id",
        "a.rs",
        ClaimKind::Exclusive,
    ));

    assert_ne!(run_a.id(), run_b.id());
}

#[test]
fn differing_claims_produce_different_run_ids() {
    let run_a = dispatch(validated_plan(
        "derive run id",
        "a.rs",
        ClaimKind::Exclusive,
    ));
    let run_b = dispatch(validated_plan("derive run id", "b.rs", ClaimKind::ReadOnly));

    assert_ne!(run_a.id(), run_b.id());
}

#[test]
fn differing_verification_specs_produce_different_run_ids() {
    let run_a = dispatch(validated_plan_with_checks(
        "derive run id",
        "a.rs",
        ClaimKind::Exclusive,
        vec![DEPOSIT_IDS_ARE_DERIVED.to_owned()],
    ));
    let run_b = dispatch(validated_plan_with_checks(
        "derive run id",
        "a.rs",
        ClaimKind::Exclusive,
        vec![REQUIRED_PRESSURE_TESTS_ARE_REGISTERED.to_owned()],
    ));

    assert_ne!(run_a.id(), run_b.id());
}

#[test]
fn retry_lineage_changes_run_id() {
    let plan = validated_plan("derive run id", "a.rs", ClaimKind::Exclusive);
    let original = derive_run_id(plan.intent(), plan.claims(), plan.verification(), None, 0);
    let retry = derive_run_id(
        plan.intent(),
        plan.claims(),
        plan.verification(),
        Some(original.as_str()),
        1,
    );

    assert_ne!(original, retry);
}

#[test]
fn equivalent_retry_lineage_produces_equal_run_ids() {
    let plan = validated_plan("derive run id", "a.rs", ClaimKind::Exclusive);
    let retry_a = derive_run_id(
        plan.intent(),
        plan.claims(),
        plan.verification(),
        Some("run:parent"),
        1,
    );
    let retry_b = derive_run_id(
        plan.intent(),
        plan.claims(),
        plan.verification(),
        Some("run:parent"),
        1,
    );

    assert_eq!(retry_a, retry_b);
}

#[test]
fn differing_retry_index_produces_different_run_ids() {
    let plan = validated_plan("derive run id", "a.rs", ClaimKind::Exclusive);
    let retry_a = derive_run_id(
        plan.intent(),
        plan.claims(),
        plan.verification(),
        Some("run:parent"),
        1,
    );
    let retry_b = derive_run_id(
        plan.intent(),
        plan.claims(),
        plan.verification(),
        Some("run:parent"),
        2,
    );

    assert_ne!(retry_a, retry_b);
}
