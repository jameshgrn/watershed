use watershed_contracts::FileClaim;
use watershed_distributary::{Drafted, Plan};

fn main() {
    let _plan = Plan::<Drafted>::draft().declare_claims(Vec::<FileClaim>::new());
}
