use watershed_distributary::{Completed, Deposit, Run};

fn main() {
    let completed = Completed { deposit: deposit() };
    let _run = Run::<Completed> {
        state: completed,
    };
}

fn deposit() -> Deposit {
    panic!("compile-fail fixture is not executed")
}
