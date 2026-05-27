use watershed_contracts::Deposit;
use watershed_distributary::{Completed, Run};

fn main() {
    let deposit = Deposit {
        run_id: "run-1".to_owned(),
        summary: "synthetic deposit".to_owned(),
        touched_files: Vec::new(),
    };
    let completed = Completed { deposit };
    let _run = Run::<Completed> {
        state: completed,
    };
}
