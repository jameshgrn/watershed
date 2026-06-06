use std::path::PathBuf;
use watershed_distributary::Deposit;

fn main() {
    let _deposit = Deposit::new("run-1", "synthetic deposit", Vec::<PathBuf>::new());
}
