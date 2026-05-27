use std::path::PathBuf;
use watershed_contracts::{ClaimKind, FileClaim, Policy, RecoveredIntent};
use watershed_distributary::{dispatch, Drafted, Failed, Plan, RetryError, Run, Validated};

fn validated_plan(max_retries: Option<u32>) -> Plan<Validated> {
    let intent = RecoveredIntent {
        goal: "bound retry depth".to_owned(),
        scope: vec!["run state machine".to_owned()],
        constraints: vec!["policy budget travels with work".to_owned()],
        non_goals: vec!["plan-declared retry checks".to_owned()],
    };
    let claims = vec![FileClaim {
        path: PathBuf::from("src/lib.rs"),
        kind: ClaimKind::Exclusive,
    }];
    let policy = Policy {
        require_claims: true,
        allow_shared_claims: false,
        max_retries,
        required_pressure_tests: Vec::new(),
    };

    Plan::<Drafted>::draft()
        .recover_intent(intent)
        .declare_claims(claims)
        .compile()
        .expect("claims should compile")
        .validate(&policy)
        .expect("policy should validate")
}

fn failed_run(max_retries: Option<u32>) -> Run<Failed> {
    dispatch(validated_plan(max_retries))
        .start()
        .fail("worker failed")
}

#[test]
fn retry_succeeds_while_current_index_is_below_budget() {
    let first_failed = failed_run(Some(2));
    let first_retry = first_failed
        .retry()
        .expect("retry index 0 should be below budget 2");
    let first_retry_id = first_retry.id().to_owned();
    let failed_retry = first_retry.start().fail("retry failed");

    assert_eq!(failed_retry.retry_index(), 1);

    let second_retry = failed_retry
        .retry()
        .expect("retry index 1 should be below budget 2");

    assert_eq!(second_retry.retried_from(), Some(first_retry_id.as_str()));
    assert_eq!(second_retry.retry_index(), 2);
}

#[test]
fn retry_is_refused_when_current_index_reaches_budget() {
    let failed_retry = failed_run(Some(1))
        .retry()
        .expect("retry index 0 should be below budget 1")
        .start()
        .fail("retry failed");

    let err = failed_retry
        .retry()
        .expect_err("retry index 1 should reach budget 1");

    assert!(matches!(
        err,
        RetryError::BudgetExhausted {
            current: 1,
            budget: 1
        }
    ));
}

#[test]
fn zero_retry_budget_refuses_the_first_retry() {
    let err = failed_run(Some(0))
        .retry()
        .expect_err("retry index 0 should reach budget 0");

    assert!(matches!(
        err,
        RetryError::BudgetExhausted {
            current: 0,
            budget: 0
        }
    ));
}

#[test]
fn unbounded_retry_budget_allows_descendant_retries() {
    let mut failed = failed_run(None);

    for expected_retry_index in 1..=5 {
        let retry = failed
            .retry()
            .expect("unbounded policy should keep allowing retries");

        assert_eq!(retry.retry_index(), expected_retry_index);

        failed = retry.start().fail("retry failed");
    }
}

#[test]
fn retry_budget_is_not_part_of_run_identity() {
    let bounded_retry = failed_run(Some(2))
        .retry()
        .expect("bounded policy should allow first retry");
    let unbounded_retry = failed_run(None)
        .retry()
        .expect("unbounded policy should allow first retry");

    assert_eq!(bounded_retry.retried_from(), unbounded_retry.retried_from());
    assert_eq!(bounded_retry.retry_index(), unbounded_retry.retry_index());
    assert_eq!(bounded_retry.id(), unbounded_retry.id());
}
