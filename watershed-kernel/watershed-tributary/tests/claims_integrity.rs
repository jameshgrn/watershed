use std::path::PathBuf;
use watershed_contracts::{ClaimKind, Deposit, FileClaim};
use watershed_tributary::{validate, Validation};

#[test]
fn rejects_deposit_touched_outside_plan_claims() {
    let deposit = Deposit {
        run_id: "run-1".to_owned(),
        summary: "synthetic deposit".to_owned(),
        touched_files: vec![PathBuf::from("b.rs")],
    };
    let claims = vec![FileClaim {
        path: PathBuf::from("a.rs"),
        kind: ClaimKind::Exclusive,
    }];

    let validation = validate(deposit, &claims);

    let Validation::Rejected(rejected) = validation else {
        panic!("deposit touching an unclaimed file should be rejected");
    };

    assert_eq!(rejected.reason(), "deposit touched unclaimed file 'b.rs'");
}

#[test]
fn accepts_deposit_touched_within_plan_claims() {
    let deposit = Deposit {
        run_id: "run-1".to_owned(),
        summary: "synthetic deposit".to_owned(),
        touched_files: vec![PathBuf::from("a.rs")],
    };
    let claims = vec![FileClaim {
        path: PathBuf::from("a.rs"),
        kind: ClaimKind::Exclusive,
    }];

    let validation = validate(deposit, &claims);

    let Validation::Accepted(accepted) = validation else {
        panic!("deposit touching only claimed files should be accepted");
    };

    assert_eq!(accepted.deposit().run_id, "run-1");
}
