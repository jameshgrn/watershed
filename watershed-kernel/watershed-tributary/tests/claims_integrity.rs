use std::path::PathBuf;
use watershed_contracts::{ClaimKind, Deposit, FileClaim};
use watershed_tributary::{validate, Validation};

fn claim(path: &str, kind: ClaimKind) -> FileClaim {
    FileClaim {
        path: PathBuf::from(path),
        kind,
    }
}

#[test]
fn rejects_deposit_touched_outside_write_authority() {
    let deposit = Deposit {
        run_id: "run-1".to_owned(),
        summary: "synthetic deposit".to_owned(),
        touched_files: vec![PathBuf::from("b.rs")],
    };
    let claims = vec![claim("a.rs", ClaimKind::Exclusive)];

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
    let deposit = Deposit {
        run_id: "run-1".to_owned(),
        summary: "synthetic deposit".to_owned(),
        touched_files: vec![PathBuf::from("a.rs")],
    };
    let claims = vec![claim("a.rs", ClaimKind::Exclusive)];

    let validation = validate(deposit, &claims);

    let Validation::Accepted(accepted) = validation else {
        panic!("deposit touching only claimed files should be accepted");
    };

    assert_eq!(accepted.deposit().run_id, "run-1");
}

#[test]
fn accepts_deposit_touched_under_directory_write_claim() {
    let deposit = Deposit {
        run_id: "run-1".to_owned(),
        summary: "synthetic deposit".to_owned(),
        touched_files: vec![PathBuf::from("src/lib.rs")],
    };
    let claims = vec![claim("src", ClaimKind::Exclusive)];

    let validation = validate(deposit, &claims);

    let Validation::Accepted(accepted) = validation else {
        panic!("directory claim should authorize descendant paths");
    };

    assert_eq!(accepted.deposit().run_id, "run-1");
}

#[test]
fn rejects_deposit_touched_under_read_only_claim() {
    let deposit = Deposit {
        run_id: "run-1".to_owned(),
        summary: "synthetic deposit".to_owned(),
        touched_files: vec![PathBuf::from("src/lib.rs")],
    };
    let claims = vec![claim("src", ClaimKind::ReadOnly)];

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
    let deposit = Deposit {
        run_id: "run-1".to_owned(),
        summary: "synthetic deposit".to_owned(),
        touched_files: vec![PathBuf::from("src2/lib.rs")],
    };
    let claims = vec![claim("src", ClaimKind::Exclusive)];

    let validation = validate(deposit, &claims);

    let Validation::Rejected(rejected) = validation else {
        panic!("directory claim should not authorize sibling paths");
    };

    assert_eq!(
        rejected.reason(),
        "deposit touched file without write authority 'src2/lib.rs'"
    );
}
