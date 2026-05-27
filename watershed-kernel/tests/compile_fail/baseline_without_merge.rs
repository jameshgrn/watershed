use watershed_contracts::{Deposit, FileClaim};
use watershed_tributary::{baseline, validate, Validation};

fn main() {
    let deposit = Deposit {
        run_id: "run-1".to_owned(),
        summary: "synthetic deposit".to_owned(),
        touched_files: Vec::new(),
    };
    let claims = Vec::<FileClaim>::new();
    let validation = validate(deposit, &claims);

    if let Validation::Accepted(accepted) = validation {
        let _baseline = baseline(accepted);
    }
}
