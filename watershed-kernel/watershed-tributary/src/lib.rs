use watershed_contracts::{Deposit, FileClaim};

/// Result of validating a collected deposit.
#[derive(Debug, Clone)]
pub enum Validation {
    Accepted(AcceptedValidation),
    Rejected(RejectedValidation),
}

/// A deposit that passed settlement validation.
#[derive(Debug, Clone)]
pub struct AcceptedValidation {
    deposit: Deposit,
}

/// A deposit that failed settlement validation.
#[derive(Debug, Clone)]
pub struct RejectedValidation {
    deposit: Deposit,
    reason: String,
}

/// Accepted work prepared for baseline anchoring.
#[derive(Debug, Clone)]
pub struct Merge {
    id: String,
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
        Self { deposit }
    }

    pub fn deposit(&self) -> &Deposit {
        &self.deposit
    }
}

impl RejectedValidation {
    pub(crate) fn new(deposit: Deposit, reason: String) -> Self {
        Self { deposit, reason }
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
        let id = format!("merge-{}", accepted.deposit.run_id);
        Self {
            id,
            deposit: accepted.deposit,
        }
    }

    pub fn id(&self) -> &str {
        &self.id
    }

    pub fn deposit(&self) -> &Deposit {
        &self.deposit
    }
}

impl Baseline {
    pub(crate) fn new(merge: Merge) -> Self {
        let id = format!("baseline-{}", merge.id);
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
    if deposit.summary.is_empty() {
        return Validation::Rejected(RejectedValidation::new(
            deposit,
            "deposit summary is empty".to_owned(),
        ));
    }

    if let Some(unclaimed_path) = deposit.touched_files.iter().find(|touched_path| {
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
