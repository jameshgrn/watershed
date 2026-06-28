use std::path::PathBuf;
use watershed_contracts::{
    ClaimKind, FileClaim, Policy, RecoveredIntent, VerificationSpec, DEPOSIT_IDS_ARE_DERIVED,
};
use watershed_distributary::{dispatch, Drafted, Plan};

fn main() {
    let intent = RecoveredIntent {
        goal: "prove completed runs cannot retry".to_owned(),
        scope: vec!["compile-fail test".to_owned()],
        constraints: Vec::new(),
        non_goals: Vec::new(),
    };
    let claims = vec![FileClaim {
        path: PathBuf::from("src/lib.rs"),
        kind: ClaimKind::Exclusive,
    }];
    let policy = Policy {
        require_claims: true,
        allow_shared_claims: false,
        max_retries: None,
        required_pressure_tests: Vec::new(),
    };
    let completed = dispatch(
        Plan::<Drafted>::draft()
            .recover_intent(intent)
            .declare_claims(claims)
            .declare_verification(VerificationSpec {
                checks: vec![DEPOSIT_IDS_ARE_DERIVED.to_owned()],
            })
            .compile()
            .expect("compile")
            .validate(&policy)
            .expect("validate"),
    )
    .start()
    .complete(
        "synthetic deposit",
        vec![PathBuf::from("src/lib.rs")],
    );

    let _retry = completed.retry();
}
