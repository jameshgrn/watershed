use watershed_distributary::dag::TaskReviewDone;

fn main() {
    let _event = TaskReviewDone {
        task_slug: "task".to_owned(),
        passed: true,
        verdict: "ok".to_owned(),
        commit_count: 1,
    };
}
