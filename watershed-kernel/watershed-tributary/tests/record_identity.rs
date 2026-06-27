use std::path::PathBuf;
use watershed_contracts::{
    ClaimKind, FileClaim, Policy, RecoveredIntent, VerificationSpec, DEPOSIT_IDS_ARE_DERIVED,
};
use watershed_distributary::{collect, dispatch, Deposit, Drafted, Plan};
use watershed_tributary::{baseline, merge, validate, Validation};

fn claim(path: &str, kind: ClaimKind) -> FileClaim {
    FileClaim {
        path: PathBuf::from(path),
        kind,
    }
}

fn verification() -> VerificationSpec {
    VerificationSpec {
        checks: vec![DEPOSIT_IDS_ARE_DERIVED.to_owned()],
    }
}

fn deposit(summary: &str, touched_files: Vec<PathBuf>, claims: Vec<FileClaim>) -> Deposit {
    let intent = RecoveredIntent {
        goal: "produce a deposit for record identity validation".to_owned(),
        scope: vec!["tributary identity".to_owned()],
        constraints: vec!["in-memory ceremony".to_owned()],
        non_goals: Vec::new(),
    };
    let policy = Policy {
        require_claims: true,
        allow_shared_claims: false,
        max_retries: None,
        required_pressure_tests: Vec::new(),
    };
    let plan = Plan::<Drafted>::draft()
        .recover_intent(intent)
        .declare_claims(claims)
        .declare_verification(verification())
        .compile()
        .expect("claims should compile")
        .validate(&policy)
        .expect("policy should validate");
    let completed = dispatch(plan).start().complete(summary, touched_files);
    let (deposit, _claims, _verification) = collect(completed);

    deposit
}

fn equivalent_deposits() -> (Deposit, Deposit) {
    let claims = vec![
        claim("a.rs", ClaimKind::Exclusive),
        claim("b.rs", ClaimKind::Exclusive),
    ];
    let first = deposit(
        "synthetic deposit",
        vec![PathBuf::from("a.rs"), PathBuf::from("b.rs")],
        claims.clone(),
    );
    let second = deposit(
        "synthetic deposit",
        vec![PathBuf::from("b.rs"), PathBuf::from("a.rs")],
        claims,
    );
    (first, second)
}

#[test]
fn accepted_validation_id_starts_with_validation_prefix() {
    let claims = vec![claim("a.rs", ClaimKind::Exclusive)];
    let deposit = deposit(
        "synthetic deposit",
        vec![PathBuf::from("a.rs")],
        claims.clone(),
    );

    let validation = validate(deposit, &claims, &verification());
    let Validation::Accepted(accepted) = validation else {
        panic!("deposit should be accepted");
    };

    assert!(
        accepted.id().starts_with("validation:"),
        "accepted validation id should start with 'validation:'"
    );
}

#[test]
fn accepted_validation_id_is_stable_for_equivalent_deposits() {
    let (first, second) = equivalent_deposits();
    assert_eq!(
        first.id(),
        second.id(),
        "equivalent deposits should have the same id"
    );

    let claims = vec![
        claim("a.rs", ClaimKind::Exclusive),
        claim("b.rs", ClaimKind::Exclusive),
    ];

    let first_validation = validate(first, &claims, &verification());
    let second_validation = validate(second, &claims, &verification());

    let Validation::Accepted(first_accepted) = first_validation else {
        panic!("first deposit should be accepted");
    };
    let Validation::Accepted(second_accepted) = second_validation else {
        panic!("second deposit should be accepted");
    };

    assert_eq!(
        first_accepted.id(),
        second_accepted.id(),
        "accepted validation ids should be stable for equivalent deposits"
    );
}

#[test]
fn rejected_validation_id_starts_with_validation_prefix() {
    let claims = vec![claim("a.rs", ClaimKind::Exclusive)];
    let deposit = deposit("", vec![PathBuf::from("a.rs")], claims.clone());

    let validation = validate(deposit, &claims, &verification());
    let Validation::Rejected(rejected) = validation else {
        panic!("deposit with empty summary should be rejected");
    };

    assert!(
        rejected.id().starts_with("validation:"),
        "rejected validation id should start with 'validation:'"
    );
}

#[test]
fn rejected_validation_id_is_stable_for_equivalent_rejections() {
    let claims = vec![claim("a.rs", ClaimKind::Exclusive)];
    let first = deposit("", vec![PathBuf::from("a.rs")], claims.clone());
    let second = deposit("", vec![PathBuf::from("a.rs")], claims.clone());

    let first_validation = validate(first, &claims, &verification());
    let second_validation = validate(second, &claims, &verification());

    let Validation::Rejected(first_rejected) = first_validation else {
        panic!("first empty-summary deposit should be rejected");
    };
    let Validation::Rejected(second_rejected) = second_validation else {
        panic!("second empty-summary deposit should be rejected");
    };

    assert!(
        first_rejected.id().starts_with("validation:"),
        "rejected validation id should start with 'validation:'"
    );
    assert_eq!(
        first_rejected.id(),
        second_rejected.id(),
        "rejected validation ids should be stable for equivalent rejected deposits"
    );
}

#[test]
fn merge_id_starts_with_merge_prefix() {
    let claims = vec![claim("a.rs", ClaimKind::Exclusive)];
    let deposit = deposit(
        "synthetic deposit",
        vec![PathBuf::from("a.rs")],
        claims.clone(),
    );

    let validation = validate(deposit, &claims, &verification());
    let Validation::Accepted(accepted) = validation else {
        panic!("deposit should be accepted");
    };

    let merged = merge(accepted);

    assert!(
        merged.id().starts_with("merge:"),
        "merge id should start with 'merge:'"
    );
}

#[test]
fn merge_id_cites_accepted_validation_id() {
    let claims = vec![claim("a.rs", ClaimKind::Exclusive)];
    let deposit = deposit(
        "synthetic deposit",
        vec![PathBuf::from("a.rs")],
        claims.clone(),
    );

    let validation = validate(deposit, &claims, &verification());
    let Validation::Accepted(accepted) = validation else {
        panic!("deposit should be accepted");
    };

    let accepted_id = accepted.id().to_owned();
    let merged = merge(accepted);

    assert_eq!(
        merged.validation_id(),
        accepted_id,
        "merge should cite the accepted validation id"
    );
}

#[test]
fn merge_id_is_stable_for_equivalent_validations() {
    let (first, second) = equivalent_deposits();
    let claims = vec![
        claim("a.rs", ClaimKind::Exclusive),
        claim("b.rs", ClaimKind::Exclusive),
    ];

    let first_validation = validate(first, &claims, &verification());
    let second_validation = validate(second, &claims, &verification());

    let Validation::Accepted(first_accepted) = first_validation else {
        panic!("first deposit should be accepted");
    };
    let Validation::Accepted(second_accepted) = second_validation else {
        panic!("second deposit should be accepted");
    };

    let first_merge = merge(first_accepted);
    let second_merge = merge(second_accepted);

    assert_eq!(
        first_merge.id(),
        second_merge.id(),
        "merge ids should be stable for equivalent validations"
    );
}

#[test]
fn baseline_id_starts_with_baseline_prefix() {
    let claims = vec![claim("a.rs", ClaimKind::Exclusive)];
    let deposit = deposit(
        "synthetic deposit",
        vec![PathBuf::from("a.rs")],
        claims.clone(),
    );

    let validation = validate(deposit, &claims, &verification());
    let Validation::Accepted(accepted) = validation else {
        panic!("deposit should be accepted");
    };

    let merged = merge(accepted);
    let anchored = baseline(merged);

    assert!(
        anchored.id().starts_with("baseline:"),
        "baseline id should start with 'baseline:'"
    );
}

#[test]
fn baseline_id_is_stable_for_equivalent_merges() {
    let (first, second) = equivalent_deposits();
    let claims = vec![
        claim("a.rs", ClaimKind::Exclusive),
        claim("b.rs", ClaimKind::Exclusive),
    ];

    let first_validation = validate(first, &claims, &verification());
    let second_validation = validate(second, &claims, &verification());

    let Validation::Accepted(first_accepted) = first_validation else {
        panic!("first deposit should be accepted");
    };
    let Validation::Accepted(second_accepted) = second_validation else {
        panic!("second deposit should be accepted");
    };

    let first_merge = merge(first_accepted);
    let second_merge = merge(second_accepted);

    let first_baseline = baseline(first_merge);
    let second_baseline = baseline(second_merge);

    assert_eq!(
        first_baseline.id(),
        second_baseline.id(),
        "baseline ids should be stable for equivalent merges"
    );
}
