use std::path::PathBuf;
use watershed_contracts::{ClaimKind, FileClaim, Policy, RecoveredIntent};
use watershed_distributary::{collect, dispatch, Deposit, Drafted, Plan};
use watershed_tributary::{validate, Validation};

fn claim(path: &str, kind: ClaimKind) -> FileClaim {
    FileClaim {
        path: PathBuf::from(path),
        kind,
    }
}

fn deposit(summary: &str, touched_files: Vec<PathBuf>, claims: Vec<FileClaim>) -> Deposit {
    let intent = RecoveredIntent {
        goal: "produce a deposit for claims-integrity validation".to_owned(),
        scope: vec!["tributary validation".to_owned()],
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
        .compile()
        .expect("claims should compile")
        .validate(&policy)
        .expect("policy should validate");
    let completed = dispatch(plan).start().complete(summary, touched_files);
    let (deposit, _claims) = collect(completed);

    deposit
}

#[test]
fn rejects_deposit_touched_outside_write_authority() {
    let claims = vec![claim("a.rs", ClaimKind::Exclusive)];
    let deposit = deposit(
        "synthetic deposit",
        vec![PathBuf::from("b.rs")],
        claims.clone(),
    );

    let validation = validate(deposit, &claims);

    let Validation::Rejected(rejected) = validation else {
        panic!("deposit touching an unclaimed file should be rejected");
    };

    assert_eq!(
        rejected.reason(),
        "deposit touched file without write authority 'b.rs'"
    );
}

#[test]
fn accepts_deposit_touched_within_plan_claims() {
    let claims = vec![claim("a.rs", ClaimKind::Exclusive)];
    let deposit = deposit(
        "synthetic deposit",
        vec![PathBuf::from("a.rs")],
        claims.clone(),
    );

    let validation = validate(deposit, &claims);

    let Validation::Accepted(accepted) = validation else {
        panic!("deposit touching only claimed files should be accepted");
    };

    assert!(accepted.deposit().run_id().starts_with("run:"));
}

#[test]
fn accepts_deposit_touched_under_directory_write_claim() {
    let claims = vec![claim("src", ClaimKind::Exclusive)];
    let deposit = deposit(
        "synthetic deposit",
        vec![PathBuf::from("src/lib.rs")],
        claims.clone(),
    );

    let validation = validate(deposit, &claims);

    let Validation::Accepted(accepted) = validation else {
        panic!("directory claim should authorize descendant paths");
    };

    assert!(accepted.deposit().run_id().starts_with("run:"));
}

#[test]
fn rejects_deposit_touched_under_read_only_claim() {
    let claims = vec![claim("src", ClaimKind::ReadOnly)];
    let deposit = deposit(
        "synthetic deposit",
        vec![PathBuf::from("src/lib.rs")],
        claims.clone(),
    );

    let validation = validate(deposit, &claims);

    let Validation::Rejected(rejected) = validation else {
        panic!("read-only claim should not authorize touched files");
    };

    assert_eq!(
        rejected.reason(),
        "deposit touched file without write authority 'src/lib.rs'"
    );
}

#[test]
fn rejects_sibling_paths_outside_directory_claim() {
    let claims = vec![claim("src", ClaimKind::Exclusive)];
    let deposit = deposit(
        "synthetic deposit",
        vec![PathBuf::from("src2/lib.rs")],
        claims.clone(),
    );

    let validation = validate(deposit, &claims);

    let Validation::Rejected(rejected) = validation else {
        panic!("directory claim should not authorize sibling paths");
    };

    assert_eq!(
        rejected.reason(),
        "deposit touched file without write authority 'src2/lib.rs'"
    );
}

#[test]
fn rejects_deposit_touched_escape_path() {
    let claims = vec![claim("src", ClaimKind::Exclusive)];
    let deposit = deposit(
        "synthetic deposit",
        vec![PathBuf::from("src/../outside.rs")],
        claims.clone(),
    );

    let validation = validate(deposit, &claims);

    let Validation::Rejected(rejected) = validation else {
        panic!("parent traversal touched paths should be rejected");
    };

    assert_eq!(
        rejected.reason(),
        "deposit touched invalid file path 'src/../outside.rs': path must not contain parent traversal: src/../outside.rs"
    );
}
