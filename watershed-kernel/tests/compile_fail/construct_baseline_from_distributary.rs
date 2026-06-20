use watershed_tributary::{Baseline, Merge};

fn main() {
    let merge = merge();
    let _baseline = Baseline {
        id: "baseline:forged".to_owned(),
        merge,
    };
}

fn merge() -> Merge {
    panic!("compile-fail fixture is not executed")
}
