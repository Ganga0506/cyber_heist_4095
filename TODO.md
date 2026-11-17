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

## 6. Interactive coding and learning progression (start with round 1 / mission 1)

Planned enhancement: make puzzles hands-on coding lessons with visible learning
progress, rather than relying on question-and-answer submissions. Deliver this
experience for mission 1 first, then extend it to later missions.

- [ ] Define a learning objective for each round 1 puzzle and sequence challenges from guided examples to independent coding.
- [ ] Redesign round 1 puzzles around writing, editing, debugging, and testing code; for example, decode an encoded clue with a program or inspect fictional evidence with a small script.
- [ ] Add short interactive explanations, starter code, and step-by-step hints that help players understand the concept and improve their solution.
- [ ] Explore an in-game code editor and compiler/interpreter so players can run and test code without leaving the mission; choose an initial language and execution approach.
- [ ] If code execution is adopted, isolate it from the game server and player data, with execution time/resource limits and a way to stop runaway code.
- [ ] Show input/output, compiler or runtime errors, and test-case results with actionable feedback so players can experiment and retry.
- [ ] Validate code against meaningful test cases instead of checking only a final text answer; keep scoring and unlock decisions on the server.
- [ ] Track and save code drafts, completed learning steps, and concepts practiced so players can resume and see their learning progress.
- [ ] Add a brief explanation after each solved puzzle and a round 1 recap of what the player learned, with an option to replay and practice.
- [ ] Verify round 1 end to end: learn a concept -> edit code -> run tests -> understand feedback -> improve the solution -> complete the challenge and unlock the next step.

## Later

- [ ] Make missions 3 and 4 playable and revise progression deliberately.
- [ ] Decide whether hints, timers, a simulated terminal, or attempt history are needed.
- [ ] Plan deployment configuration, HTTPS, abuse controls, and production authentication before publishing.
