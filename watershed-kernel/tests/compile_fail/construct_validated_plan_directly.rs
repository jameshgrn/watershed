use watershed_contracts::RecoveredIntent;
use watershed_distributary::{Plan, Validated};

fn main() {
    let validated = Validated {
        intent: RecoveredIntent {
            goal: "skip ceremony".to_owned(),
            scope: Vec::new(),
            constraints: Vec::new(),
            non_goals: Vec::new(),
        },
        claims: Vec::new(),
        max_retries: None,
    };
    let _plan = Plan::<Validated> {
        state: validated,
    };
}
