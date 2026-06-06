use sha2::{Digest, Sha256};
use watershed_contracts::FileClaim;
use watershed_distributary::Deposit;

/// Result of validating a collected deposit.
#[derive(Debug, Clone)]
pub enum Validation {
    Accepted(AcceptedValidation),
    Rejected(RejectedValidation),
}

/// A deposit that passed settlement validation.
#[derive(Debug, Clone)]
pub struct AcceptedValidation {
    id: String,
    deposit: Deposit,
}

/// A deposit that failed settlement validation.
#[derive(Debug, Clone)]
pub struct RejectedValidation {
    id: String,
    deposit: Deposit,
    reason: String,
}

/// Accepted work prepared for baseline anchoring.
#[derive(Debug, Clone)]
pub struct Merge {
    id: String,
    validation_id: String,
    deposit: Deposit,
}

/// Settled baseline produced from a merge.
#[derive(Debug, Clone)]
pub struct Baseline {
    id: String,
    merge: Merge,
}

impl AcceptedValidation {
    pub(crate) fn new(deposit: Deposit) -> Self {
        let id = derive_validation_id(deposit.id(), "accepted", "");
        Self { id, deposit }
    }

    pub fn id(&self) -> &str {
        &self.id
    }

    pub fn deposit(&self) -> &Deposit {
        &self.deposit
    }
}

impl RejectedValidation {
    pub(crate) fn new(deposit: Deposit, reason: String) -> Self {
        let id = derive_validation_id(deposit.id(), "rejected", &reason);
        Self {
            id,
            deposit,
            reason,
        }
    }

    pub fn id(&self) -> &str {
        &self.id
    }

    pub fn deposit(&self) -> &Deposit {
        &self.deposit
    }

    pub fn reason(&self) -> &str {
        &self.reason
    }
}

impl Merge {
    pub(crate) fn new(accepted: AcceptedValidation) -> Self {
        let id = derive_merge_id(accepted.deposit.id(), accepted.id());
        let validation_id = accepted.id;
        Self {
            id,
            validation_id,
            deposit: accepted.deposit,
        }
    }

    pub fn id(&self) -> &str {
        &self.id
    }

    pub fn deposit(&self) -> &Deposit {
        &self.deposit
    }

    pub fn validation_id(&self) -> &str {
        &self.validation_id
    }
}

impl Baseline {
    pub(crate) fn new(merge: Merge) -> Self {
        let id = derive_baseline_id(merge.id());
        Self { id, merge }
    }

    pub fn id(&self) -> &str {
        &self.id
    }

    pub fn merge(&self) -> &Merge {
        &self.merge
    }
}

pub fn validate(deposit: Deposit, claims: &[FileClaim]) -> Validation {
    if deposit.summary().is_empty() {
        return Validation::Rejected(RejectedValidation::new(
            deposit,
            "deposit summary is empty".to_owned(),
        ));
    }

    if let Some(unclaimed_path) = deposit.touched_files().iter().find(|touched_path| {
        !claims
            .iter()
            .any(|claim| claim.grants_write_to(touched_path.as_path()))
    }) {
        let reason = format!(
            "deposit touched file without write authority '{}'",
            unclaimed_path.display()
        );

        return Validation::Rejected(RejectedValidation::new(deposit, reason));
    }

    Validation::Accepted(AcceptedValidation::new(deposit))
}

pub fn merge(accepted: AcceptedValidation) -> Merge {
    Merge::new(accepted)
}

pub fn baseline(merge: Merge) -> Baseline {
    Baseline::new(merge)
}

fn derive_validation_id(deposit_id: &str, verdict: &str, reason: &str) -> String {
    derive_tagged_id(
        "validation:",
        serde_json::json!({
            "deposit_id": deposit_id,
            "verdict": verdict,
            "reason": reason,
        }),
    )
}

fn derive_merge_id(deposit_id: &str, validation_id: &str) -> String {
    derive_tagged_id(
        "merge:",
        serde_json::json!({
            "deposit_id": deposit_id,
            "validation_id": validation_id,
        }),
    )
}

fn derive_baseline_id(merge_id: &str) -> String {
    derive_tagged_id(
        "baseline:",
        serde_json::json!({
            "merge_id": merge_id,
        }),
    )
}

fn derive_tagged_id(tag: &str, payload: serde_json::Value) -> String {
    let serialized = serde_json::to_vec(&payload)
        .expect("tributary identity serialization should be infallible");
    let mut hasher = Sha256::new();
    hasher.update(tag.as_bytes());
    hasher.update(serialized);
    let digest = hasher.finalize();

    format!("{tag}{digest:x}")
}
