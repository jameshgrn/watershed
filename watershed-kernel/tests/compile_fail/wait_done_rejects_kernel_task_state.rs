use watershed_distributary::dag::{TaskState, TaskWaitDone};

fn main() {
    let _event = TaskWaitDone {
        task_slug: "task".to_owned(),
        pane_slug: "pane".to_owned(),
        outcome: TaskState::Merging,
    };
}
