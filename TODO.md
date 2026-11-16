# Cyber Heist TODO

Use [the API contract](docs/API_CONTRACT.md) when building either side. Checked
items exist in source; they do not imply this checkout has passed runtime checks.

## Foundation already present

- [x] FastAPI application, SQLite models, and repeatable demo seeding.
- [x] Mission list/detail, health, leaderboard, and demo progress endpoints.
- [x] React landing page loads live missions with an offline preview fallback.
- [x] Backend database/API tests.
- [x] One-command launcher: `python start.py` (Git Bash or PowerShell).

## 1. Agree on the contract and verify setup

- [ ] Review the proposed endpoints and fields in `docs/API_CONTRACT.md` together.
- [ ] Confirm MVP progression: proposed mission order 1 -> 2 -> 5; missions 3 and 4 remain previews.
- [ ] Confirm the proposed bearer-token authentication and validation limits.
- [ ] Verify `backend/requirements.txt` installs in a fresh environment; resolve any unavailable package names or versions.
- [ ] Run the launcher end to end; check both URLs and Ctrl+C cleanup.

## 2. Backend: authentication

- [ ] Add request/response schemas for registration, login, current user, and logout.
- [ ] Implement registration with unique username/email checks and random password salts.
- [ ] Create initial mission progress when a user registers, in the same transaction.
- [ ] Implement expiring, revocable bearer sessions and persistent session storage/migration.
- [ ] Implement login, current-user lookup, and logout; authenticate protected routes with the session.
- [ ] Replace demo HTTP Basic on progress after the frontend switches to bearer authentication.
- [ ] Test duplicate registration, invalid login, expired sessions, and logout revocation.

## 3. Backend: playable game loop

- [ ] Enforce the agreed mission access rules on the server.
- [ ] Add mission-start endpoint; allow resuming without resetting progress.
- [ ] Add per-puzzle solved progress so the browser can resume after refresh.
- [ ] Add answer-submission endpoint using the existing answer normalization/hash helper.
- [ ] Reject client-supplied user IDs, correctness flags, scores, and completion statuses.
- [ ] Save attempt, score effect, mission completion, and unlocks in one transaction.
- [ ] Ensure repeated/concurrent correct submissions cannot increase total score twice.
- [ ] Keep solutions, solution hashes, password hashes, and private account fields out of public responses.
- [ ] Test wrong/correct/repeated answers, locked missions, missing resources, and user isolation.
- [ ] Update CORS methods for POST when the mutation endpoints are added.

## 4. Frontend

- [ ] Create a shared API client for JSON, auth headers, errors, and session expiry.
- [ ] Add registration/login forms with pending, validation, and failure states.
- [ ] Add session-aware navigation and logout; keep bearer tokens in memory for the proposed MVP.
- [ ] Replace Begin Heist preview with login/start/resume navigation.
- [ ] Build mission dashboard using mission metadata plus the player's progress.
- [ ] Build mission/puzzle screens with answer submission and correct/incorrect feedback.
- [ ] Refresh progress and score after successful submissions; show unlock/completion feedback.
- [ ] Build leaderboard screen using the existing endpoint.
- [ ] Handle loading, empty results, API failure, locked missions, and expired sessions.
- [ ] Keep offline fallback cards as previews; never let them start or score a game.
- [ ] Check keyboard navigation, form labels, and mobile layout.

## 5. Integration and acceptance

- [ ] Register -> login -> start mission 1 -> wrong answer -> correct answers -> unlock mission 2.
- [ ] Complete mission 2 -> unlock mission 5 -> finish the MVP.
- [ ] Refresh, log in again if needed, and verify saved puzzle/mission progress.
- [ ] Verify repeat answers do not inflate leaderboard totals.
- [ ] Verify a second account cannot read or modify another player's progress.
- [ ] Run `python -m pytest` in `backend` and `npm run build` in `frontend`.
- [ ] Update README, progress notes, and contract to match the implemented behavior.

## Later

- [ ] Make missions 3 and 4 playable and revise progression deliberately.
- [ ] Decide whether hints, timers, a simulated terminal, or attempt history are needed.
- [ ] Plan deployment configuration, HTTPS, abuse controls, and production authentication before publishing.
