use std::collections::{BTreeMap, BTreeSet};
use thiserror::Error;
use watershed_contracts::FileClaim;

/// Per-task lifecycle state for the pure DAG kernel.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TaskState {
    Pending,
    Active,
    Done,
    Failed,
    Reviewing,
    ReviewedPass,
    ReviewedFail,
    Merging,
    Merged,
    TimedOut,
    Closed,
    Abandoned,
    Skipped,
}

impl TaskState {
    pub fn as_str(self) -> &'static str {
        match self {
            TaskState::Pending => "pending",
            TaskState::Active => "active",
            TaskState::Done => "done",
            TaskState::Failed => "failed",
            TaskState::Reviewing => "reviewing",
            TaskState::ReviewedPass => "reviewed_pass",
            TaskState::ReviewedFail => "reviewed_fail",
            TaskState::Merging => "merging",
            TaskState::Merged => "merged",
            TaskState::TimedOut => "timed_out",
            TaskState::Closed => "closed",
            TaskState::Abandoned => "abandoned",
            TaskState::Skipped => "skipped",
        }
    }

    pub fn is_terminal(self) -> bool {
        matches!(
            self,
            TaskState::Merged
                | TaskState::Failed
                | TaskState::Skipped
                | TaskState::Abandoned
                | TaskState::TimedOut
        )
    }
}

impl std::fmt::Display for TaskState {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(self.as_str())
    }
}

/// Worker wait result reported by an effect runner.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TaskWaitOutcome {
    Done,
    Failed,
    TimedOut,
    Abandoned,
}

impl TaskWaitOutcome {
    pub fn as_str(self) -> &'static str {
        match self {
            TaskWaitOutcome::Done => "done",
            TaskWaitOutcome::Failed => "failed",
            TaskWaitOutcome::TimedOut => "timed_out",
            TaskWaitOutcome::Abandoned => "abandoned",
        }
    }
}

impl std::fmt::Display for TaskWaitOutcome {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(self.as_str())
    }
}

/// Aggregate DAG status derived from task states.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DagState {
    Idle,
    Running,
    Completed,
    Failed,
    Partial,
}

/// Kernel action requesting worker dispatch.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DispatchTask {
    pub task_slug: String,
}

/// Kernel action requesting review of worker output.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ReviewTask {
    pub task_slug: String,
    pub pane_slug: String,
}

/// Kernel action requesting serial merge of reviewed work.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MergeTask {
    pub task_slug: String,
    pub pane_slug: String,
    pub file_claims: Vec<FileClaim>,
}

/// Kernel action requesting cleanup for a terminal task.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CleanupTask {
    pub task_slug: String,
}

/// Kernel action handing an ambiguous failure back to the governor.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct InterruptGovernor {
    pub task_slug: String,
    pub pane_slug: String,
    pub reason: String,
}

/// Kernel action emitted when every task has reached a terminal state.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DagDone {
    pub status: DagState,
    pub merged: Vec<String>,
    pub failed: Vec<String>,
    pub skipped: Vec<String>,
    pub blocked: Vec<String>,
}

/// Typed output from the pure DAG kernel.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DagAction {
    DispatchTask(DispatchTask),
    ReviewTask(ReviewTask),
    MergeTask(MergeTask),
    CleanupTask(CleanupTask),
    InterruptGovernor(InterruptGovernor),
    DagDone(DagDone),
}

impl From<DispatchTask> for DagAction {
    fn from(action: DispatchTask) -> Self {
        Self::DispatchTask(action)
    }
}

impl From<ReviewTask> for DagAction {
    fn from(action: ReviewTask) -> Self {
        Self::ReviewTask(action)
    }
}

impl From<MergeTask> for DagAction {
    fn from(action: MergeTask) -> Self {
        Self::MergeTask(action)
    }
}

impl From<CleanupTask> for DagAction {
    fn from(action: CleanupTask) -> Self {
        Self::CleanupTask(action)
    }
}

impl From<InterruptGovernor> for DagAction {
    fn from(action: InterruptGovernor) -> Self {
        Self::InterruptGovernor(action)
    }
}

impl From<DagDone> for DagAction {
    fn from(action: DagDone) -> Self {
        Self::DagDone(action)
    }
}

/// Runner event acknowledging a worker dispatch.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TaskDispatched {
    pub task_slug: String,
    pub pane_slug: String,
}

/// Runner event reporting that a worker wait completed.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TaskWaitDone {
    pub task_slug: String,
    pub pane_slug: String,
    pub outcome: TaskWaitOutcome,
}

/// Runner event reporting review outcome.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TaskReviewDone {
    pub task_slug: String,
    pub passed: bool,
    pub verdict: String,
    pub commit_count: u32,
}

/// Runner event reporting merge outcome.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TaskMergeDone {
    pub task_slug: String,
    pub error: Option<String>,
}

/// Governor decision after an interrupted task.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum GovernorAction {
    Retry,
    Fail,
    Skip,
}

/// Typed input to the pure DAG kernel.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DagEvent {
    TaskDispatched(TaskDispatched),
    TaskWaitDone(TaskWaitDone),
    TaskReviewDone(TaskReviewDone),
    TaskMergeDone(TaskMergeDone),
    TaskGovernorResumed(TaskGovernorResumed),
}

/// Runner event carrying a governor decision back to the kernel.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TaskGovernorResumed {
    pub task_slug: String,
    pub action: GovernorAction,
}

/// Serializable snapshot of pure kernel state.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DagSnapshot {
    pub task_states: BTreeMap<String, TaskState>,
    pub task_panes: BTreeMap<String, String>,
    pub merge_order: Vec<String>,
}

/// Structural errors in a DAG definition.
#[derive(Debug, Error, PartialEq, Eq)]
pub enum DagError {
    #[error("task '{task}' depends on unknown task '{dependency}'")]
    UnknownDependency { task: String, dependency: String },
    #[error("task_files contains unknown task '{task}'")]
    UnknownTaskFiles { task: String },
    #[error("dependency cycle detected at task '{task}'")]
    Cycle { task: String },
    #[error("DAG task slug cannot be empty")]
    EmptyTaskSlug,
    #[error("DAG task '{task}' has an empty dependency slug")]
    EmptyDependency { task: String },
    #[error("DAG task '{task}' must declare at least one file claim")]
    MissingClaims { task: String },
    #[error("DAG task '{task}' has an empty file claim path")]
    EmptyClaimPath { task: String },
    #[error("duplicate DAG task '{task}'")]
    DuplicateTask { task: String },
    #[error(
        "independent DAG tasks '{left_task}' and '{right_task}' have conflicting file claims: '{left_path}' overlaps '{right_path}'"
    )]
    ConflictingClaims {
        left_task: String,
        left_path: String,
        right_task: String,
        right_path: String,
    },
}

/// A task declaration before the DAG becomes executable kernel state.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DagTask {
    slug: String,
    depends_on: Vec<String>,
    claims: Vec<FileClaim>,
}

impl DagTask {
    pub fn new(
        slug: impl Into<String>,
        depends_on: Vec<String>,
        claims: Vec<FileClaim>,
    ) -> Result<Self, DagError> {
        let slug = slug.into();
        if slug.trim().is_empty() {
            return Err(DagError::EmptyTaskSlug);
        }

        if depends_on
            .iter()
            .any(|dependency| dependency.trim().is_empty())
        {
            return Err(DagError::EmptyDependency { task: slug });
        }

        if claims.is_empty() {
            return Err(DagError::MissingClaims { task: slug });
        }

        if claims
            .iter()
            .any(|claim| claim.normalized_path().is_empty())
        {
            return Err(DagError::EmptyClaimPath { task: slug });
        }

        Ok(Self {
            slug,
            depends_on,
            claims,
        })
    }

    pub fn slug(&self) -> &str {
        &self.slug
    }

    pub fn depends_on(&self) -> &[String] {
        &self.depends_on
    }

    pub fn claims(&self) -> &[FileClaim] {
        &self.claims
    }
}

/// Typed DAG declaration that compiles into the pure kernel.
#[derive(Debug, Clone)]
pub struct DagPlan {
    tasks: BTreeMap<String, DagTask>,
}

impl DagPlan {
    pub fn new(tasks: Vec<DagTask>) -> Result<Self, DagError> {
        let mut task_map = BTreeMap::new();

        for task in tasks {
            let slug = task.slug.clone();
            if task_map.insert(slug.clone(), task).is_some() {
                return Err(DagError::DuplicateTask { task: slug });
            }
        }

        let plan = Self { tasks: task_map };
        let deps = plan.deps();
        topological_sort(&deps)?;
        validate_claim_conflicts(&plan.tasks, &deps)?;

        Ok(plan)
    }

    pub fn task(&self, task_slug: &str) -> Option<&DagTask> {
        self.tasks.get(task_slug)
    }

    pub fn tasks(&self) -> &BTreeMap<String, DagTask> {
        &self.tasks
    }

    pub fn compile_kernel(&self) -> Result<DagKernel, DagError> {
        DagKernel::with_task_files(self.deps(), self.task_files())
    }

    fn deps(&self) -> BTreeMap<String, Vec<String>> {
        self.tasks
            .iter()
            .map(|(slug, task)| (slug.clone(), task.depends_on.clone()))
            .collect()
    }

    fn task_files(&self) -> BTreeMap<String, Vec<FileClaim>> {
        self.tasks
            .iter()
            .map(|(slug, task)| (slug.clone(), task.claims.clone()))
            .collect()
    }
}

/// Pure, deterministic state machine for dispatch DAG lifecycle.
///
/// The kernel owns no I/O and no worker execution. It maps `(state, event)` to
/// `(new_state, actions)`, with serial topological merge and failure cascade.
#[derive(Debug, Clone)]
pub struct DagKernel {
    deps: BTreeMap<String, Vec<String>>,
    task_files: BTreeMap<String, Vec<FileClaim>>,
    task_states: BTreeMap<String, TaskState>,
    task_panes: BTreeMap<String, String>,
    merge_order: Vec<String>,
}

impl DagKernel {
    pub fn new(deps: BTreeMap<String, Vec<String>>) -> Result<Self, DagError> {
        Self::with_task_files(deps, BTreeMap::new())
    }

    pub fn with_task_files(
        deps: BTreeMap<String, Vec<String>>,
        task_files: BTreeMap<String, Vec<FileClaim>>,
    ) -> Result<Self, DagError> {
        validate_task_files(&deps, &task_files)?;
        let merge_order = topological_sort(&deps)?;
        let task_states = deps
            .keys()
            .map(|slug| (slug.clone(), TaskState::Pending))
            .collect();

        Ok(Self {
            deps,
            task_files,
            task_states,
            task_panes: BTreeMap::new(),
            merge_order,
        })
    }

    pub fn done(&self) -> bool {
        self.task_states.values().all(|state| state.is_terminal())
    }

    pub fn status(&self) -> DagState {
        if self
            .task_states
            .values()
            .all(|state| *state == TaskState::Pending)
        {
            return DagState::Idle;
        }

        if !self.done() {
            return DagState::Running;
        }

        let has_bad_terminal = self.task_states.values().any(|state| {
            matches!(
                state,
                TaskState::Failed | TaskState::Abandoned | TaskState::TimedOut
            )
        });
        let has_merged = self
            .task_states
            .values()
            .any(|state| *state == TaskState::Merged);

        if has_bad_terminal {
            if has_merged {
                DagState::Partial
            } else {
                DagState::Failed
            }
        } else {
            DagState::Completed
        }
    }

    pub fn task_state(&self, task_slug: &str) -> Option<TaskState> {
        self.task_states.get(task_slug).copied()
    }

    pub fn task_states(&self) -> &BTreeMap<String, TaskState> {
        &self.task_states
    }

    pub fn merge_order(&self) -> &[String] {
        &self.merge_order
    }

    pub fn snapshot(&self) -> DagSnapshot {
        DagSnapshot {
            task_states: self.task_states.clone(),
            task_panes: self.task_panes.clone(),
            merge_order: self.merge_order.clone(),
        }
    }

    pub fn start(&self) -> Vec<DagAction> {
        self.schedule()
    }

    pub fn handle(&mut self, event: DagEvent) -> Vec<DagAction> {
        let was_done = self.done();
        let mut actions = match event {
            DagEvent::TaskDispatched(event) => self.on_dispatched(event),
            DagEvent::TaskWaitDone(event) => self.on_wait_done(event),
            DagEvent::TaskReviewDone(event) => self.on_review_done(event),
            DagEvent::TaskMergeDone(event) => self.on_merge_done(event),
            DagEvent::TaskGovernorResumed(event) => self.on_governor_resumed(event),
        };

        if !was_done && self.done() {
            actions.push(self.summary().into());
        }

        actions
    }

    fn on_dispatched(&mut self, event: TaskDispatched) -> Vec<DagAction> {
        if self.task_states.get(&event.task_slug) != Some(&TaskState::Pending) {
            return Vec::new();
        }

        self.task_panes
            .insert(event.task_slug.clone(), event.pane_slug);
        self.task_states.insert(event.task_slug, TaskState::Active);
        Vec::new()
    }

    fn on_wait_done(&mut self, event: TaskWaitDone) -> Vec<DagAction> {
        if self.task_states.get(&event.task_slug) != Some(&TaskState::Active) {
            return Vec::new();
        }

        let Some(pane_slug) = self.task_panes.get(&event.task_slug).cloned() else {
            return Vec::new();
        };
        if pane_slug != event.pane_slug {
            return Vec::new();
        }

        match event.outcome {
            TaskWaitOutcome::Done => {
                self.task_states
                    .insert(event.task_slug.clone(), TaskState::Reviewing);
                vec![ReviewTask {
                    task_slug: event.task_slug,
                    pane_slug,
                }
                .into()]
            }
            TaskWaitOutcome::Abandoned => self.on_terminal_wait(event, TaskState::Abandoned),
            TaskWaitOutcome::TimedOut => self.on_terminal_wait(event, TaskState::TimedOut),
            TaskWaitOutcome::Failed => vec![InterruptGovernor {
                task_slug: event.task_slug,
                pane_slug,
                reason: event.outcome.to_string(),
            }
            .into()],
        }
    }

    fn on_terminal_wait(&mut self, event: TaskWaitDone, task_state: TaskState) -> Vec<DagAction> {
        self.task_states.insert(event.task_slug.clone(), task_state);
        self.cascade_failure(&event.task_slug);

        let mut actions: Vec<DagAction> = vec![CleanupTask {
            task_slug: event.task_slug,
        }
        .into()];
        actions.extend(self.try_merge());
        actions.extend(self.schedule());
        actions
    }

    fn on_review_done(&mut self, event: TaskReviewDone) -> Vec<DagAction> {
        if self.task_states.get(&event.task_slug) != Some(&TaskState::Reviewing) {
            return Vec::new();
        }

        if event.passed {
            self.task_states
                .insert(event.task_slug, TaskState::ReviewedPass);
            return self.try_merge();
        }

        if event.verdict == "read_scope_violation" {
            let pane_slug = self
                .task_panes
                .get(&event.task_slug)
                .cloned()
                .expect("reviewing task has an assigned pane");
            self.task_states
                .insert(event.task_slug.clone(), TaskState::Failed);
            return vec![InterruptGovernor {
                task_slug: event.task_slug,
                pane_slug,
                reason: "read_scope_violation".to_owned(),
            }
            .into()];
        }

        self.task_states
            .insert(event.task_slug.clone(), TaskState::Failed);
        self.cascade_failure(&event.task_slug);

        let mut actions: Vec<DagAction> = vec![CleanupTask {
            task_slug: event.task_slug,
        }
        .into()];
        actions.extend(self.try_merge());
        actions.extend(self.schedule());
        actions
    }

    fn on_merge_done(&mut self, event: TaskMergeDone) -> Vec<DagAction> {
        if self.task_states.get(&event.task_slug) != Some(&TaskState::Merging) {
            return Vec::new();
        }

        if event.error.is_some() {
            self.task_states
                .insert(event.task_slug.clone(), TaskState::Failed);
            self.cascade_failure(&event.task_slug);
        } else {
            self.task_states.insert(event.task_slug, TaskState::Merged);
        }

        let mut actions = self.try_merge();
        actions.extend(self.schedule());
        actions
    }

    fn on_governor_resumed(&mut self, event: TaskGovernorResumed) -> Vec<DagAction> {
        let Some(current) = self.task_states.get(&event.task_slug).copied() else {
            return Vec::new();
        };

        if !matches!(
            current,
            TaskState::Pending
                | TaskState::Active
                | TaskState::Failed
                | TaskState::Abandoned
                | TaskState::TimedOut
                | TaskState::Skipped
        ) {
            return Vec::new();
        }

        match event.action {
            GovernorAction::Retry => {
                self.task_states.insert(event.task_slug, TaskState::Pending);
                self.schedule()
            }
            GovernorAction::Skip => {
                self.task_states
                    .insert(event.task_slug.clone(), TaskState::Skipped);
                self.cascade_failure(&event.task_slug);

                let mut actions: Vec<DagAction> = vec![CleanupTask {
                    task_slug: event.task_slug,
                }
                .into()];
                actions.extend(self.try_merge());
                actions.extend(self.schedule());
                actions
            }
            GovernorAction::Fail => {
                self.task_states
                    .insert(event.task_slug.clone(), TaskState::Failed);
                self.cascade_failure(&event.task_slug);

                let mut actions: Vec<DagAction> = vec![CleanupTask {
                    task_slug: event.task_slug,
                }
                .into()];
                actions.extend(self.try_merge());
                actions.extend(self.schedule());
                actions
            }
        }
    }

    fn cascade_failure(&mut self, failed_slug: &str) {
        let mut blocked = BTreeSet::new();
        let mut changed = true;

        while changed {
            changed = false;
            for (slug, state) in &self.task_states {
                if *state != TaskState::Pending || blocked.contains(slug) {
                    continue;
                }

                let deps = self.deps.get(slug).expect("kernel deps are validated");
                let directly_blocked = deps.iter().any(|dep| dep == failed_slug);
                let transitively_blocked = deps.iter().any(|dep| blocked.contains(dep));

                if directly_blocked || transitively_blocked {
                    blocked.insert(slug.clone());
                    changed = true;
                }
            }
        }

        for slug in blocked {
            self.task_states.insert(slug, TaskState::Skipped);
        }
    }

    fn schedule(&self) -> Vec<DagAction> {
        self.task_states
            .iter()
            .filter_map(|(slug, state)| {
                if *state != TaskState::Pending {
                    return None;
                }

                let deps = self.deps.get(slug).expect("kernel deps are validated");
                if deps
                    .iter()
                    .all(|dep| self.task_states.get(dep).copied() == Some(TaskState::Merged))
                {
                    Some(
                        DispatchTask {
                            task_slug: slug.clone(),
                        }
                        .into(),
                    )
                } else {
                    None
                }
            })
            .collect()
    }

    fn try_merge(&mut self) -> Vec<DagAction> {
        if self
            .task_states
            .values()
            .any(|state| *state == TaskState::Merging)
        {
            return Vec::new();
        }

        for slug in &self.merge_order {
            let state = self
                .task_states
                .get(slug)
                .copied()
                .expect("merge order only contains declared tasks");

            if state == TaskState::ReviewedPass {
                let pane_slug = self
                    .task_panes
                    .get(slug)
                    .cloned()
                    .expect("reviewed task has an assigned pane");
                self.task_states.insert(slug.clone(), TaskState::Merging);
                return vec![MergeTask {
                    task_slug: slug.clone(),
                    pane_slug,
                    file_claims: self.task_files.get(slug).cloned().unwrap_or_default(),
                }
                .into()];
            }

            if state.is_terminal() {
                continue;
            }

            return Vec::new();
        }

        Vec::new()
    }

    fn summary(&self) -> DagDone {
        let slugs_with_state = |target| {
            self.task_states
                .iter()
                .filter_map(|(slug, state)| {
                    if *state == target {
                        Some(slug.clone())
                    } else {
                        None
                    }
                })
                .collect()
        };

        DagDone {
            status: self.status(),
            merged: slugs_with_state(TaskState::Merged),
            failed: slugs_with_state(TaskState::Failed),
            skipped: slugs_with_state(TaskState::Skipped),
            blocked: Vec::new(),
        }
    }
}

pub fn topological_sort(deps: &BTreeMap<String, Vec<String>>) -> Result<Vec<String>, DagError> {
    validate_deps(deps)?;

    let mut order = Vec::new();
    let mut marks = BTreeMap::new();

    for node in deps.keys() {
        visit(node, deps, &mut marks, &mut order)?;
    }

    Ok(order)
}

fn validate_deps(deps: &BTreeMap<String, Vec<String>>) -> Result<(), DagError> {
    for (task, task_deps) in deps {
        if task.trim().is_empty() {
            return Err(DagError::EmptyTaskSlug);
        }

        for dependency in task_deps {
            if dependency.trim().is_empty() {
                return Err(DagError::EmptyDependency { task: task.clone() });
            }

            if !deps.contains_key(dependency) {
                return Err(DagError::UnknownDependency {
                    task: task.clone(),
                    dependency: dependency.clone(),
                });
            }
        }
    }

    Ok(())
}

fn validate_task_files(
    deps: &BTreeMap<String, Vec<String>>,
    task_files: &BTreeMap<String, Vec<FileClaim>>,
) -> Result<(), DagError> {
    for (task, claims) in task_files {
        if !deps.contains_key(task) {
            return Err(DagError::UnknownTaskFiles { task: task.clone() });
        }

        if claims.is_empty() {
            return Err(DagError::MissingClaims { task: task.clone() });
        }

        if claims
            .iter()
            .any(|claim| claim.normalized_path().is_empty())
        {
            return Err(DagError::EmptyClaimPath { task: task.clone() });
        }
    }

    Ok(())
}

fn validate_claim_conflicts(
    tasks: &BTreeMap<String, DagTask>,
    deps: &BTreeMap<String, Vec<String>>,
) -> Result<(), DagError> {
    let slugs = tasks.keys().collect::<Vec<_>>();

    for (index, left_slug) in slugs.iter().enumerate() {
        for right_slug in slugs.iter().skip(index + 1) {
            if !tasks_are_independent(left_slug, right_slug, deps) {
                continue;
            }

            if let Some(conflict) =
                first_claim_conflict(&tasks[*left_slug].claims, &tasks[*right_slug].claims)
            {
                return Err(DagError::ConflictingClaims {
                    left_task: (*left_slug).clone(),
                    left_path: conflict.left_path,
                    right_task: (*right_slug).clone(),
                    right_path: conflict.right_path,
                });
            }
        }
    }

    Ok(())
}

fn tasks_are_independent(
    left_slug: &str,
    right_slug: &str,
    deps: &BTreeMap<String, Vec<String>>,
) -> bool {
    !depends_on_transitively(left_slug, right_slug, deps)
        && !depends_on_transitively(right_slug, left_slug, deps)
}

fn depends_on_transitively(
    task_slug: &str,
    dependency_slug: &str,
    deps: &BTreeMap<String, Vec<String>>,
) -> bool {
    let mut seen = BTreeSet::new();
    let mut stack = deps
        .get(task_slug)
        .expect("kernel deps are validated")
        .iter()
        .collect::<Vec<_>>();

    while let Some(candidate) = stack.pop() {
        if candidate == dependency_slug {
            return true;
        }

        if !seen.insert(candidate) {
            continue;
        }

        stack.extend(deps.get(candidate).expect("kernel deps are validated"));
    }

    false
}

struct ClaimConflict {
    left_path: String,
    right_path: String,
}

fn first_claim_conflict(
    left_claims: &[FileClaim],
    right_claims: &[FileClaim],
) -> Option<ClaimConflict> {
    for left_claim in left_claims {
        for right_claim in right_claims {
            if left_claim.conflicts_with(right_claim) {
                return Some(ClaimConflict {
                    left_path: left_claim.normalized_path(),
                    right_path: right_claim.normalized_path(),
                });
            }
        }
    }

    None
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum VisitMark {
    Visiting,
    Visited,
}

fn visit(
    node: &str,
    deps: &BTreeMap<String, Vec<String>>,
    marks: &mut BTreeMap<String, VisitMark>,
    order: &mut Vec<String>,
) -> Result<(), DagError> {
    match marks.get(node) {
        Some(VisitMark::Visiting) => {
            return Err(DagError::Cycle {
                task: node.to_owned(),
            });
        }
        Some(VisitMark::Visited) => return Ok(()),
        None => {}
    }

    marks.insert(node.to_owned(), VisitMark::Visiting);

    for dependency in deps.get(node).expect("kernel deps are validated") {
        visit(dependency, deps, marks, order)?;
    }

    marks.insert(node.to_owned(), VisitMark::Visited);
    order.push(node.to_owned());

    Ok(())
}
