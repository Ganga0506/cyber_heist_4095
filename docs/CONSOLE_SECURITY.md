# Console security

Mission 1 runs a small, server-defined expression language over fictional lesson
inputs. The accepted grammar is text and Boolean literals, the lesson's exact
input names, equality, and one explicitly approved text function per lesson.
Output, including decoded markup-like text, is data rendered through React text
nodes. The evaluator receives only fixture values. Draft storage, identity,
test comparison, scoring, and mission unlocks stay in the game API.

## Threat model and enforcement

| Threat | Control |
| --- | --- |
| User input reaching executable or privileged capabilities | Parse and validate the complete tree before interpreting it. Dispatch only the approved functions on strings and reject unsupported syntax and identifiers. The evaluator has no interfaces for files, processes, network, imports, or player data. |
| Resource exhaustion | Limit source to 512 characters and 1,024 UTF-8 bytes, the accepted tree to 48 expression nodes and 12 levels, and each text value to 512 UTF-8 bytes. The server supplies at most five test fixtures. Check a shared 50 ms monotonic deadline at validation and evaluation steps. |
| Repeated or simultaneous jobs | Admit 30 console requests per account per minute, one active request per account, and four active requests per API process. Bound the account bucket table to 2,048 entries and reject excess work. Production also applies the existing request-body and per-IP guards. |
| Cross-player access or score manipulation | Bind drafts to the authenticated account and puzzle. Use server-provided tests and existing transactional scoring. Timeouts and unexpected evaluator errors roll back pending work. |
| Output injection or sensitive logs | Render output as text and use fixed diagnostic messages. Emit aggregate policy warnings and fixed failure categories without source, output, account IDs, or credentials. |

The deadline is cooperative. Fixed inputs, bounded primitive operations, and a
grammar without loops or dynamic dispatch bound the work between checks. There
is no child process or runtime job to cancel. Admission is per process, so edge
quotas are still required for multi-worker or public deployments. The interpreter
shares the API process, and this design relies on its small trusted
implementation and the Python parser.

## Operator drill

1. Set `CYBERHEIST_CONSOLE_MODE=disabled` through deployment configuration
   and restart API workers. Runs and submissions return 503. Players can
   still save bounded drafts. An unknown mode rejects all console actions.
2. Confirm that a recorded draft and score remain intact after a rejected run.
   Check the security log route for `console_policy_rejections` and
   `console_evaluation_stopped`. Configure staging alerts for bursts of
   policy rejections and any unexpected evaluator failure.
3. Restore `CYBERHEIST_CONSOLE_MODE=simulation`, restart workers, and confirm
   that drafting, practice, and server scoring work. Regression tests cover
   the switch and failure behavior. Live alert and restart validation belongs
   to the Phase 7 staging drill.

## Gate for broader execution

The simulation design is the only runtime in this release. Before approving
a broader runtime, require a revised threat model and an independent review
covering sandbox escape, data exfiltration, cross-player access, resource
exhaustion, and infrastructure compromise. Require independently verified
disposable isolation away from the API, no credentials or host mounts,
default-deny networking, an unprivileged identity and restricted system calls,
and a read-only runtime. Set enforced CPU, memory, process, disk, output, and
wall-clock limits with whole-job termination on timeout or cancellation.
Record evidence from isolation and failure drills, and keep simulation in
effect until the review accepts the residual risk.
