pub mod dag;

use sha2::{Digest, Sha256};
use std::path::PathBuf;
use thiserror::Error;
use watershed_contracts::{ClaimKind, Deposit, FileClaim, Policy, RecoveredIntent};

mod sealed {
    pub trait Sealed {}
}

/// Marker trait for legal plan states.
pub trait PlanState: sealed::Sealed {}

/// A plan whose intent has not yet been recovered.
#[derive(Debug, Clone)]
pub struct Drafted;

/// A plan whose structured intent has been recovered.
#[derive(Debug, Clone)]
pub struct IntentRecovered {
    intent: RecoveredIntent,
}

/// A plan whose file claims have been declared.
#[derive(Debug, Clone)]
pub struct ClaimsDeclared {
    intent: RecoveredIntent,
    claims: Vec<FileClaim>,
}

/// A plan that has passed compilation checks.
#[derive(Debug, Clone)]
pub struct Compiled {
    intent: RecoveredIntent,
    claims: Vec<FileClaim>,
}

/// A plan that has passed policy validation and may be dispatched.
#[derive(Debug, Clone)]
pub struct Validated {
    intent: RecoveredIntent,
    claims: Vec<FileClaim>,
    max_retries: Option<u32>,
}

impl sealed::Sealed for Drafted {}
impl sealed::Sealed for IntentRecovered {}
impl sealed::Sealed for ClaimsDeclared {}
impl sealed::Sealed for Compiled {}
impl sealed::Sealed for Validated {}

impl PlanState for Drafted {}
impl PlanState for IntentRecovered {}
impl PlanState for ClaimsDeclared {}
impl PlanState for Compiled {}
impl PlanState for Validated {}

/// Typed plan that can only move forward through its state ceremony.
#[derive(Debug)]
pub struct Plan<S: PlanState> {
    state: S,
}

impl Plan<Drafted> {
    pub fn draft() -> Self {
        Self { state: Drafted }
    }

    pub fn recover_intent(self, intent: RecoveredIntent) -> Plan<IntentRecovered> {
        Plan {
            state: IntentRecovered { intent },
        }
    }
}

impl Plan<IntentRecovered> {
    pub fn intent(&self) -> &RecoveredIntent {
        &self.state.intent
    }

    pub fn declare_claims(self, claims: Vec<FileClaim>) -> Plan<ClaimsDeclared> {
        let IntentRecovered { intent } = self.state;
        Plan {
            state: ClaimsDeclared { intent, claims },
        }
    }
}

impl Plan<ClaimsDeclared> {
    pub fn intent(&self) -> &RecoveredIntent {
        &self.state.intent
    }

    pub fn claims(&self) -> &[FileClaim] {
        &self.state.claims
    }

    pub fn compile(self) -> Result<Plan<Compiled>, CompileError> {
        let ClaimsDeclared { intent, claims } = self.state;

        if claims.is_empty() {
            return Err(CompileError::MissingClaims);
        }

        Ok(Plan {
            state: Compiled { intent, claims },
        })
    }
}

impl Plan<Compiled> {
    pub fn intent(&self) -> &RecoveredIntent {
        &self.state.intent
    }

    pub fn claims(&self) -> &[FileClaim] {
        &self.state.claims
    }

    pub fn validate(self, policy: &Policy) -> Result<Plan<Validated>, ValidationError> {
        let Compiled { intent, claims } = self.state;

        if policy.require_claims && claims.is_empty() {
            return Err(ValidationError::MissingClaims);
        }

        if !policy.allow_shared_claims
            && claims
                .iter()
                .any(|claim| matches!(claim.kind, ClaimKind::Shared))
        {
            return Err(ValidationError::SharedClaimsForbidden);
        }

        Ok(Plan {
            state: Validated {
                intent,
                claims,
                max_retries: policy.max_retries,
            },
        })
    }
}

impl Plan<Validated> {
    pub fn intent(&self) -> &RecoveredIntent {
        &self.state.intent
    }

    pub fn claims(&self) -> &[FileClaim] {
        &self.state.claims
    }
}

/// Errors raised while compiling a claims-declared plan.
#[derive(Debug, Error)]
pub enum CompileError {
    #[error("cannot compile a plan with no file claims")]
    MissingClaims,
}

/// Errors raised while validating a compiled plan against policy.
#[derive(Debug, Error)]
pub enum ValidationError {
    #[error("policy requires at least one file claim")]
    MissingClaims,
    #[error("policy forbids shared file claims")]
    SharedClaimsForbidden,
}

/// Errors raised while retrying a failed run.
#[derive(Debug, Error)]
pub enum RetryError {
    #[error(
        "retry budget exhausted: current retry index {current} reached policy max_retries {budget}"
    )]
    BudgetExhausted { current: u32, budget: u32 },
}

/// Marker trait for legal run states.
pub trait RunState: sealed::Sealed {}

/// A dispatched run waiting for a worker.
#[derive(Debug, Clone)]
pub struct Pending {
    _private: (),
}

/// A run currently held by a worker.
#[derive(Debug, Clone)]
pub struct Running {
    _private: (),
}

/// A run completed by a worker.
#[derive(Debug, Clone)]
pub struct Completed {
    deposit: Deposit,
}

/// A run that failed before producing a deposit.
#[derive(Debug, Clone)]
pub struct Failed {
    reason: String,
}

impl sealed::Sealed for Pending {}
impl sealed::Sealed for Running {}
impl sealed::Sealed for Completed {}
impl sealed::Sealed for Failed {}

impl RunState for Pending {}
impl RunState for Running {}
impl RunState for Completed {}
impl RunState for Failed {}

/// Typed worker run whose state controls collection.
#[derive(Debug)]
pub struct Run<S: RunState> {
    id: String,
    intent: RecoveredIntent,
    claims: Vec<FileClaim>,
    retried_from: Option<String>,
    retry_index: u32,
    max_retries: Option<u32>,
    state: S,
}

impl<S: RunState> Run<S> {
    pub fn id(&self) -> &str {
        &self.id
    }

    pub fn intent(&self) -> &RecoveredIntent {
        &self.intent
    }

    pub fn claims(&self) -> &[FileClaim] {
        &self.claims
    }

    pub fn retried_from(&self) -> Option<&str> {
        self.retried_from.as_deref()
    }

    pub fn retry_index(&self) -> u32 {
        self.retry_index
    }
}

impl Run<Pending> {
    pub fn start(self) -> Run<Running> {
        let Run {
            id,
            intent,
            claims,
            retried_from,
            retry_index,
            max_retries,
            ..
        } = self;

        Run {
            id,
            intent,
            claims,
            retried_from,
            retry_index,
            max_retries,
            state: Running { _private: () },
        }
    }
}

impl Run<Running> {
    pub fn complete(
        self,
        summary: impl Into<String>,
        touched_files: Vec<PathBuf>,
    ) -> Run<Completed> {
        let Run {
            id,
            intent,
            claims,
            retried_from,
            retry_index,
            max_retries,
            ..
        } = self;
        let deposit = Deposit {
            run_id: id.clone(),
            summary: summary.into(),
            touched_files,
        };

        Run {
            id,
            intent,
            claims,
            retried_from,
            retry_index,
            max_retries,
            state: Completed { deposit },
        }
    }

    pub fn fail(self, reason: impl Into<String>) -> Run<Failed> {
        let Run {
            id,
            intent,
            claims,
            retried_from,
            retry_index,
            max_retries,
            ..
        } = self;

        Run {
            id,
            intent,
            claims,
            retried_from,
            retry_index,
            max_retries,
            state: Failed {
                reason: reason.into(),
            },
        }
    }
}

impl Run<Failed> {
    pub fn reason(&self) -> &str {
        &self.state.reason
    }

    pub fn retry(self) -> Result<Run<Pending>, RetryError> {
        let Run {
            id,
            intent,
            claims,
            retry_index,
            max_retries,
            ..
        } = self;

        if let Some(budget) = max_retries {
            if retry_index >= budget {
                return Err(RetryError::BudgetExhausted {
                    current: retry_index,
                    budget,
                });
            }
        }

        let retried_from = Some(id);
        let retry_index = retry_index
            .checked_add(1)
            .expect("retry_index exceeded u32::MAX; start a new dispatch instead of retrying");
        let id = derive_run_id(&intent, &claims, retried_from.as_deref(), retry_index);

        Ok(Run {
            id,
            intent,
            claims,
            retried_from,
            retry_index,
            max_retries,
            state: Pending { _private: () },
        })
    }
}

/// Computes the content-derived run_id from a dispatched plan's intent and claims.
/// The hash is strategy-tag-prefixed and stable across equivalent dispatches.
pub fn derive_run_id(
    intent: &RecoveredIntent,
    claims: &[FileClaim],
    retried_from: Option<&str>,
    retry_index: u32,
) -> String {
    let serialized_intent =
        serde_json::to_vec(intent).expect("RecoveredIntent serialization should be infallible");
    let serialized_claims =
        serde_json::to_vec(claims).expect("FileClaim serialization should be infallible");
    let serialized_retried_from = serde_json::to_vec(&retried_from)
        .expect("retry lineage serialization should be infallible");

    let mut hasher = Sha256::new();
    hasher.update(b"run:");
    hasher.update(serialized_intent);
    hasher.update(serialized_claims);
    hasher.update(serialized_retried_from);
    hasher.update(retry_index.to_be_bytes());
    let digest = hasher.finalize();

    format!("run:{digest:x}")
}

pub fn dispatch(plan: Plan<Validated>) -> Run<Pending> {
    let Validated {
        intent,
        claims,
        max_retries,
    } = plan.state;
    let run_id = derive_run_id(&intent, &claims, None, 0);
    Run {
        id: run_id,
        intent,
        claims,
        retried_from: None,
        retry_index: 0,
        max_retries,
        state: Pending { _private: () },
    }
}

pub fn mock_worker(run: Run<Running>) -> Run<Completed> {
    let touched_files = run
        .claims()
        .iter()
        .map(|claim| claim.path.clone())
        .collect::<Vec<_>>();

    run.complete("synthetic deposit", touched_files)
}

pub fn collect(run: Run<Completed>) -> (Deposit, Vec<FileClaim>) {
    let Run { claims, state, .. } = run;
    let Completed { deposit } = state;

    (deposit, claims)
}
