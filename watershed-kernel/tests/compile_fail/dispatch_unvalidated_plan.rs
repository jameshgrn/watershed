use watershed_distributary::{dispatch, Drafted, Plan};

fn main() {
    let plan = Plan::<Drafted>::draft();
    let _run = dispatch(plan);
}
