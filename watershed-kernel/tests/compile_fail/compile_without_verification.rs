use std::path::PathBuf;
use watershed_contracts::{ClaimKind, FileClaim, RecoveredIntent};
use watershed_distributary::{Drafted, Plan};

fn main() {
    let intent = RecoveredIntent {
        goal: "prove verification is declared before compile".to_owned(),
        scope: vec!["compile-fail test".to_owned()],
        constraints: Vec::new(),
        non_goals: Vec::new(),
    };
    let claims = vec![FileClaim {
        path: PathBuf::from("src/lib.rs"),
        kind: ClaimKind::Exclusive,
    }];

    let _compiled = Plan::<Drafted>::draft()
        .recover_intent(intent)
        .declare_claims(claims)
        .compile();
}
