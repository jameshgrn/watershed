use watershed_distributary::dag::TaskMergeDone;

fn main() {
    let _event = TaskMergeDone {
        task_slug: "task".to_owned(),
        error: None,
    };
}
