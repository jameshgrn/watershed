# Design Debt

2026-05-22: WorkClass-in-Plan is deferred until policy consumes it. Promote when a transition uses `WorkClass` to gate or branch behavior.

2026-05-22: VerificationSpec-in-Plan is deferred until validation consumes it. Promote via a `declare_verification` transition when tributary validation actually checks against `VerificationSpec`.

2026-05-22: RollbackSpec-in-Plan is deferred. It likely belongs near settlement or dispatch safety. Promote when a real rollback path is added.
