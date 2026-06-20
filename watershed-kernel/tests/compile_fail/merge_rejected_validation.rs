use watershed_tributary::{merge, RejectedValidation};

fn main() {
    let rejected = rejected();
    let _merge = merge(rejected);
}

fn rejected() -> RejectedValidation {
    panic!("compile-fail fixture is not executed")
}
