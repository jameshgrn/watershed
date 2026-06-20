use watershed_tributary::{baseline, AcceptedValidation};

fn main() {
    let accepted = accepted();
    let _baseline = baseline(accepted);
}

fn accepted() -> AcceptedValidation {
    panic!("compile-fail fixture is not executed")
}
