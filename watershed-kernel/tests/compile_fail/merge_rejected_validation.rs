use watershed_contracts::{Deposit, FileClaim};
use watershed_tributary::{merge, validate, Validation};

fn main() {
    let deposit = Deposit {
        run_id: "run-1".to_owned(),
        summary: String::new(),
        touched_files: Vec::new(),
    };
    let claims = Vec::<FileClaim>::new();
    let validation = validate(deposit, &claims);

    if let Validation::Rejected(rejected) = validation {
        let _merge = merge(rejected);
    }
}
