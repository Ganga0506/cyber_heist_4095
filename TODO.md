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
- [ ] Check keyboard navigation, form labels, and mobile layout.

## 5. Integration and acceptance

- [x] Register -> login -> start mission 1 -> wrong answer -> correct answers -> unlock mission 2.
- [x] Complete mission 2 -> unlock mission 5 -> finish the MVP.
- [x] Refresh, log in again if needed, and verify saved puzzle/mission progress.
- [x] Verify repeat answers do not inflate leaderboard totals.
- [x] Verify a second account cannot read or modify another player's progress.
- [x] Run `python -m pytest` in `backend` (26 passed) and `npm run build` in `frontend`.
- [x] Update README, progress notes, and contract to match the implemented behavior.

## Later

- [ ] Make missions 3 and 4 playable and revise progression deliberately.
- [ ] Decide whether hints, timers, a simulated terminal, or attempt history are needed.
- [ ] Plan deployment configuration, HTTPS, abuse controls, and production authentication before publishing.
