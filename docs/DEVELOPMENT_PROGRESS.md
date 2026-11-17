# Cyber Heist development progress

Team 5: Ganga Nomika Mahesh, Eshita Srivastava, Sushma Meghana Karri

Course: CSE 4095 Agentic Programming

The Week 1/early Week 2 sections below are historical. See the current MVP update
and [API contract](API_CONTRACT.md) for implemented behavior.

## Current playable MVP

- Task 4 completed November 17, 2026: rebuilt the frontend with separate hash
  routes for mission control, login, registration, mission play, and leaderboard;
  shared lobby navigation and an interactive city map; a guest welcome screen;
  mission/leaderboard route guards; responsive dark styling; and one puzzle at
  a time with objective navigation and completion feedback. Ten Playwright tests
  pass on desktop/mobile with controlled API responses. Keyboard skip navigation,
  labels, offline retry, expiry, guest access, map selection, and overflow are covered; screenshots
  were visually reviewed at 1440px and 390px.
- Task 3 verified November 17, 2026: 33 backend tests pass. Additional regression
  coverage confirms partial-mission resume after logout/login, rejection of
  client-supplied scoring/identity/status fields, and isolation of another
  player's progress after correct answers and blocked attempts.
- Registration, bearer-token login/current-user/logout, and persisted 24-hour sessions.
- Mission dashboard, start/resume, puzzle forms, answer feedback, saved progress, and leaderboard.
- Server-side answer validation, one effective award per puzzle, and mission progression 1 -> 2 -> 5.
- Existing demo progress reconciles from solved puzzles; missions 3 and 4 stay previews.
- Startup creates the session table and seeds missing demo data without deleting player records.
- API tests cover the full game loop, wrong/repeated/concurrent answers, locked missions, validation, session expiry/revocation, and player isolation.
- Frontend browser layout and keyboard checks are recorded under Task 4 above.

This note covers the initial foundation for the Week 1 progress report and the early Week 2 prototype. It does not describe a finished game.

The slides and proposal sometimes say Flask. The implementation uses FastAPI, which is the stack named in the architecture and technology sections.

## Week 1: Planning and Setup

### Completed

- Game concept and technical architecture are recorded in the README: a browser escape-room, five missions, and a three-mission MVP.
- Repository layout is in place for FastAPI, SQLite, React, tests, and docs.
- SQLAlchemy models and `database/schema.sql` describe the same five tables: users, missions, puzzles, puzzle attempts, and user progress.
- Foreign keys, uniqueness rules, and allowed progress statuses are enforced.
- Demo data is loaded for five fictional players, all five missions, two puzzles per mission, sample attempts, and sample progress.
- Passwords and puzzle answers are stored as hashes. The API does not return those hashes.
- Leaderboard totals are calculated from attempts. They are not copied onto the user row.
- README, schema diagram, and this progress note are written.
- `.gitignore` excludes virtual environments, `node_modules`, environment files, and SQLite runtime files.

### Not part of Week 1

- The GitHub remote is not connected from this working copy. Commands for a new empty repository are in the README.
- Mission unlock rules are not settled. Sample progress includes one linear snapshot and one MVP-style snapshot. The application does not choose between them.

## Week 2: Frontend and Backend

### Completed in this early prototype

- React landing page with the Cyber Heist title, subtitle, short introduction, five mission cards, MVP markers, and a Begin Heist button labeled as a preview.
- The page requests `GET /api/missions` and falls back to the planned list if the API is off.
- FastAPI routes read SQLite:
  - `GET /api/health`
  - `GET /api/missions`
  - `GET /api/missions/{mission_id}`
  - `GET /api/leaderboard`
  - `GET /api/me/progress` with HTTP Basic for a demo account
- CORS is limited to the local Vite origins `http://localhost:5173` and `http://127.0.0.1:5173`.
- pytest covers database setup, seed counts, mission order, puzzle counts, foreign keys, unique usernames and emails, idempotent seeding, and the API routes above.
- The React production build is part of the local check (`npm run build`).

### Planned, not built yet

- Registration and login screens.
- A browser-friendly session or token. HTTP Basic is only a temporary way to read demo progress.
- Puzzle screens and a server route that checks answers. The browser must not send its own score.
- The final mission-unlock rule, then code that updates `user_progress` when a mission is completed.
- A leaderboard page. The API exists; the page does not.
- Playable flows for The Setup, The Perimeter, and The Final Heist.
- Hint cost, timers, and a command terminal. Those stay optional and are out of scope until the core loop works.

## What can be shown now

- The landing page and its preview button.
- Swagger docs at `/docs`.
- Mission JSON from the database, including which missions are in the MVP.
- A mission detail payload that includes puzzle instructions and omits solution hashes.
- A leaderboard computed from demo attempts.
- One demo player's saved mission statuses through `/api/me/progress`.

## What should not be claimed as done

- Players cannot solve puzzles in the browser.
- Players cannot register.
- The client cannot submit an answer or change a score.
- Missions do not unlock automatically.
- Missions 3 and 4 are stored and visible, but they are not a playable build target for the MVP yet.
