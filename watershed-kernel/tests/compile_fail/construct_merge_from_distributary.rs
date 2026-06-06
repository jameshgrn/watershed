use watershed_distributary::Deposit;
use watershed_tributary::Merge;

fn main() {
    let _merge = Merge {
        id: "merge:forged".to_owned(),
        validation_id: "validation:forged".to_owned(),
        deposit: deposit(),
    };
}

fn deposit() -> Deposit {
    panic!("compile-fail fixture is not executed")
}
