use watershed_contracts::Deposit;
use watershed_tributary::Merge;

fn main() {
    let deposit = Deposit {
        run_id: "run-1".to_owned(),
        summary: "synthetic deposit".to_owned(),
        touched_files: Vec::new(),
    };
    let _merge = Merge {
        id: "merge-run-1".to_owned(),
        deposit,
    };
}
