# Cyber Heist TODO

Use [the API contract](docs/API_CONTRACT.md) when building either side. Checked
items are implemented. API integration tests exercise the checked game flows;
manual browser/keyboard/mobile acceptance remains below.

## Foundation already present

- [x] FastAPI application, SQLite models, and repeatable demo seeding.
- [x] Mission list/detail, health, leaderboard, and demo progress endpoints.
- [x] React mission dashboard loads live records and reports connection failures.
- [x] Backend database/API tests.
- [x] One-command launcher: `python start.py` (Git Bash or PowerShell).

## 1. Agree on the contract and verify setup

- [ ] Review the implemented endpoints and fields in `docs/API_CONTRACT.md` together.
- [x] Implement the documented MVP default: mission order 1 -> 2 -> 5; missions 3 and 4 remain previews.
- [x] Implement the documented bearer-token authentication and validation limits.
- [ ] Verify `backend/requirements.txt` installs in a fresh environment; resolve any unavailable package names or versions.
- [ ] Run the launcher end to end; check both URLs and Ctrl+C cleanup.

## 2. Backend: authentication

- [x] Add request/response schemas for registration, login, current user, and logout (204 has no body).
- [x] Implement registration with unique username/email checks and random password salts.
- [x] Create initial mission progress when a user registers, in the same transaction.
- [x] Implement expiring, revocable bearer sessions and persistent session storage/migration.
- [x] Implement login, current-user lookup, and logout; authenticate protected routes with the session.
- [x] Replace demo HTTP Basic on progress after the frontend switches to bearer authentication.
- [x] Test duplicate registration, invalid login, expired sessions, and logout revocation.

## 3. Backend: playable game loop

Verified November 17, 2026: all items below are implemented. The backend suite
passes 33 tests, including partial-mission resume after logout/login, rejection
of client-controlled game state, player isolation, and concurrent scoring.

- [x] Enforce the agreed mission access rules on the server.
- [x] Add mission-start endpoint; allow resuming without resetting progress.
- [x] Add per-puzzle solved progress so the browser can resume after refresh.
- [x] Add answer-submission endpoint using the existing answer normalization/hash helper.
- [x] Reject client-supplied user IDs, correctness flags, scores, and completion statuses.
- [x] Save attempt, score effect, mission completion, and unlocks in one transaction.
- [x] Ensure repeated/concurrent correct submissions cannot increase total score twice.
- [x] Keep solutions, solution hashes, password hashes, and private account fields out of public responses.
- [x] Test wrong/correct/repeated answers, locked missions, missing resources, and user isolation.
- [x] Update CORS methods for POST when the mutation endpoints are added.

## 4. Frontend

Completed November 17, 2026: separate dashboard, login, registration, mission,
and leaderboard routes with a shared game lobby and interactive mission map.
Guests see a welcome screen; mission and leaderboard pages require login in the
frontend. Ten Playwright browser tests
pass across desktop and mobile using controlled API responses; screenshots were
reviewed at 1440px and 390px. Browser tests cover gameplay feedback, completion,
registration, logout, locked access, session expiry, offline retry, form labels,
keyboard skip navigation, guest route guards, map selection, and horizontal overflow.

- [x] Create a shared API client for JSON, auth headers, errors, and session expiry.
- [x] Add registration/login forms with pending, validation, and failure states.
- [x] Add session-aware navigation and logout; keep bearer tokens in memory for the proposed MVP.
- [x] Replace Begin Heist preview with login/start/resume navigation.
- [x] Build mission dashboard using mission metadata plus the player's progress.
- [x] Build mission/puzzle screens with answer submission and correct/incorrect feedback.
- [x] Refresh progress and score after successful submissions; show unlock/completion feedback.
- [x] Build leaderboard screen using the existing endpoint.
- [x] Handle loading, empty results, API failure, locked missions, and expired sessions.
- [x] Show a connection error and retry action when offline; gameplay requires the API.
- [x] Check keyboard navigation, form labels, and mobile layout.

## 5. Integration and acceptance

- [x] Register -> login -> start mission 1 -> wrong answer -> correct answers -> unlock mission 2.
- [x] Complete mission 2 -> unlock mission 5 -> finish the MVP.
- [x] Refresh, log in again if needed, and verify saved puzzle/mission progress.
- [x] Verify repeat answers do not inflate leaderboard totals.
- [x] Verify a second account cannot read or modify another player's progress.
- [x] Run `python -m pytest` in `backend` (26 passed) and `npm run build` in `frontend`.
- [x] Update README, progress notes, and contract to match the implemented behavior.

## 6. Interactive coding and learning progression (Mission 1)

- [x] Sequence lessons from guided Base64 decoding to independent domain comparison.
- [x] Let players edit Python expressions, debug failed tests, and retry with fictional evidence.
- [x] Provide learning objectives, concept explanations, starter code, and progressive hints.
- [x] Add an in-game editor and a bounded interpreter for a small Python expression subset.
- [x] Restrict the interpreter to lesson inputs and predefined functions, with source and syntax limits. Expressions have no access to files, network, processes, or player records and cannot use loops.
- [x] Show test inputs, expected and actual outputs, and syntax or evaluation errors.
- [x] Check additional cases on submission and apply scoring and unlocks on the server.
- [x] Save per-account drafts and track learned concepts through solved lessons.
- [x] Show solved-lesson explanations and a mission recap, with replay from starter code.
- [x] Verify editing, failed tests, draft resume, successful submissions, and Mission 2 unlock through automated tests.

## 7. Production security

- [ ] Define the threat model, prioritize controls by risk, and set release criteria based on verified mitigations and documented residual risks.
- [ ] Add Google sign-in using OpenID Connect with authorization code and PKCE. Validate issuer, audience, signature, expiration, state, and nonce. Define secure account linking and recovery.
- [ ] Review existing password hashing and plan a migration to a tuned, salted Argon2id configuration with rehash on login. Add breached-password screening, secure password recovery, and optional MFA.
- [ ] Harden session expiration, rotation, and revocation. Review token storage and apply Secure, HttpOnly, and SameSite settings plus CSRF protection wherever cookies authenticate requests.
- [ ] Audit server-side ownership and authorization on every protected endpoint, including drafts, scores, and mission unlocks. Test cross-account access and privilege escalation.
- [ ] Prevent SQL, command, and template injection through parameterized queries, strict input schemas, and avoidance of shell and dynamic evaluation. Verify with defensive regression tests.
- [ ] Protect against cross-site scripting with context-aware output encoding, safe rendering, sanitization where rich text is needed, and a restrictive Content Security Policy.
- [ ] Review SSRF, path traversal, unsafe uploads, and open redirects wherever features accept URLs, paths, files, or redirect destinations.
- [ ] Require HTTPS, configure HSTS and other browser security headers, and restrict CORS to approved origins.
- [ ] Limit login and recovery abuse, automated submissions, request sizes, and resource consumption using rate limits, quotas, and timeouts.
- [ ] Protect production secrets and private data using least privilege, secret rotation, retention limits, and tested backups and restores.
- [ ] Scan dependencies and secrets in CI, patch promptly, and review production build and deployment settings.
- [ ] Add security event logging and alerting with sensitive data redacted. Document incident response and verify controls through recurring security tests and review.

## Later

- [ ] Make missions 3 and 4 playable and revise progression deliberately.
- [ ] Decide whether hints, timers, a simulated terminal, or attempt history are needed.
- [ ] Plan deployment configuration, HTTPS, abuse controls, and production authentication before publishing.
