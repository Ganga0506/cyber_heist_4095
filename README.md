# Cyber Heist

Cyber Heist is a browser-based cybersecurity escape-room game for CSE 4095 Agentic Programming at UConn. Players register, investigate simulated threats, solve puzzles, earn points, and save progress. This repository includes a local playable MVP with registration, login, saved progress, puzzle submissions, and a leaderboard.

The game uses fictional clues and simulated systems only. It does not connect to or attack real computers.

## Team 5

- Ganga Nomika Mahesh
- Eshita Srivastava
- Sushma Meghana Karri

## Technology stack

Development references: [TODO list](TODO.md) and
[frontend/backend API contract](docs/API_CONTRACT.md). The contract describes the implemented API used by the frontend.
Use the [production security runbook](docs/PRODUCTION_SECURITY.md) for HTTPS,
Google sign-in, password recovery, MFA, and deployment verification.

- Frontend: React, JavaScript, HTML, CSS (Vite)
- Backend: Python, FastAPI
- Database: SQLite with SQLAlchemy
- Tests: pytest and Playwright
- Version control: GitHub

The proposal and one architecture slide mention Flask. The project is standardized on FastAPI.

## Missions

The story has five missions, in this order:

| Order | Mission | Topic | MVP |
| --- | --- | --- | --- |
| 1 | THE SETUP | Encoding and Digital Forensics | Yes |
| 2 | THE PERIMETER | Networking and HTTP | Yes |
| 3 | THE ENCRYPTION LAYER | Cryptography and Hashing | Later |
| 4 | INSIDE THE SYSTEM | Code Analysis and Access Control | Later |
| 5 | THE FINAL HEIST | Integrated Cybersecurity Challenges | Yes |

The first playable version focuses on The Setup, The Perimeter, and The Final Heist. All five missions are already stored so the later two are not forgotten.

MVP progression is 1 -> 2 -> 5. Solve every puzzle in a mission to unlock the next MVP mission. Missions 3 and 4 remain locked previews. Existing demo progress is reconciled from solved puzzles on login.

## Folder structure

```text
cyberheist/
  README.md
  .gitignore
  backend/
    main.py          FastAPI routes
    database.py      SQLite connection
    models.py        SQLAlchemy tables
    schemas.py       API response shapes
    security.py      password and answer hashing
    seed.py          create tables and demo data
    requirements.txt
    tests/
  database/
    schema.sql       executable table script
    seed.sql         executable demo data script
    schema_diagram.md
  frontend/          React app with separate pages and shared components
  docs/
    DEVELOPMENT_PROGRESS.md
```

The project folder is named `cyberheist`. That folder is the project root.

## Database tables

- `users`: player id, unique username, unique email, password hash, created time.
- `auth_sessions`: hashed bearer token, user id, and expiry; removed on logout.
- `missions`: title, description, topic, unique mission order, MVP flag, created time.
- `puzzles`: mission foreign key, prompt, puzzle type, instructions, solution hash, points, order within the mission.
- `puzzle_attempts`: user and puzzle foreign keys, whether the attempt was correct, points earned, attempt time.
- `user_progress`: one row per user and mission. Status is `locked`, `available`, `in_progress`, or `completed`.

Leaderboard scores are not stored on the user. `GET /api/leaderboard` adds up the best correct `points_earned` for each puzzle. A second correct attempt on the same puzzle does not increase the score.

`database/schema.sql` and `database/seed.sql` are executable SQLite scripts. They are source files maintained with the Python models, not dumps exported from a live database. The app itself creates the database through SQLAlchemy.

Password accounts use salted Argon2id. Existing PBKDF2-HMAC-SHA256 hashes
upgrade on successful login. Text puzzle answers use SHA-256 of the trimmed,
case-folded text.

SQLite foreign keys are turned on for every connection.

## Development-only demo accounts

These fictional players exist so the team can try `GET /api/me/progress`.
Log in through the local frontend with any of these accounts. The demo
hashes use a fixed salt so the SQL script and Python seed match. Production
uses a catalog-only seed and refuses databases containing demo accounts.

| Username | Email | Password |
| --- | --- | --- |
| nova.agent | nova.agent@example.com | dev-only-nova |
| pixel.fox | pixel.fox@example.com | dev-only-pixel |
| cipher.owl | cipher.owl@example.com | dev-only-cipher |
| byte.lynx | byte.lynx@example.com | dev-only-byte |
| glitch.moth | glitch.moth@example.com | dev-only-glitch |

## Start frontend and backend together

Install Python 3.11+ and Node.js first. From the project root in PowerShell:

```powershell
.\start.cmd
```

The launcher creates a backend virtual environment and installs missing dependencies
on the first run. It then starts both servers. Open http://localhost:5173 for the
frontend or http://127.0.0.1:8000/docs for the API. Press Ctrl+C to stop both.
The API automatically creates and seeds the SQLite database at startup.

You can also run `python start.py` (including on macOS/Linux). After changing
dependency files, run `python start.py --install` to reinstall dependencies.
If installation fails, the launcher prints the error and stops; fix the reported
dependency issue and rerun the same command.

## Backend setup

Use Python 3.11 or newer. Run these commands from the `backend` directory.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python seed.py
```

`python seed.py` creates `backend/cyberheist.db` if needed and inserts the demo rows. Running it again does not duplicate records. The database file is gitignored.

Optional SQL path, from the project root:

```bash
sqlite3 backend/cyberheist.db < database/schema.sql
sqlite3 backend/cyberheist.db < database/seed.sql
```

If you change the demo records in `backend/seed.py`, regenerate the SQL script from the `backend` directory:

```bash
python -c "from seed import render_seed_sql; from pathlib import Path; Path('../database/seed.sql').write_text(render_seed_sql())"
```

## Run the API

From the `backend` directory, with the virtual environment active:

```bash
uvicorn main:app --reload
```

Open the interactive docs at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

Useful checks:

```bash
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/missions
curl http://127.0.0.1:8000/api/leaderboard
```

CORS allows only `http://localhost:5173` and `http://127.0.0.1:5173`.

Use the frontend or `/docs` to register, log in, start missions, and submit answers. Login returns a bearer token for protected routes. The backend calculates scores; the browser cannot set them.

## Frontend

From the `frontend` directory:

```bash
npm install
npm run dev
```

Open [http://127.0.0.1:5173](http://127.0.0.1:5173). The dev server proxies `/api` to FastAPI on port 8000. Start the API first. The page shows API connection errors and offers a Retry connection button when it is unavailable.

Guests see a welcome screen and login/registration links. After login, mission
control becomes an interactive city map: select a location to inspect its clues,
lock requirements, saved progress, and start/resume action. The map path follows
missions 1 -> 2 -> 5, with 3 and 4 shown as future districts. The leaderboard is
also available from the signed-in navigation. Direct links to missions or the
leaderboard show the login form for guests. Public API endpoints retain their
existing contract; the frontend does not request mission or leaderboard data
until login.

Pages use hash routes so navigation, direct links, and browser back/forward work
without server rewrite rules: `#/` (mission control), `#/login`, `#/register`,
`#/missions/1` (replace 1 with the mission ID), and `#/leaderboard`.
Page components live in `frontend/src/pages`; the shared navigation/layout and
interactive map live in `frontend/src/components`.

Log in with a demo account or register a new one, then start an available mission. Correct answers save progress and unlock the next MVP mission. Refreshing the browser requires logging in again; saved scores and progress persist.

To build the static files:

```bash
npm run build
```

## Tests

From the `backend` directory, with the virtual environment active:

```bash
python -m pytest
```

Tests use a temporary SQLite file. They do not read or write `backend/cyberheist.db`.

From the `frontend` directory, run `npm run test:ui` for ten Playwright browser
checks across desktop (1440px) and mobile (390px). The tests start their own Vite
server on port 5178 and use controlled API responses without changing player data.
They cover registration/login, puzzle feedback/completion, leaderboard/logout,
locked routes, session expiry, offline retry, keyboard skip navigation, labels,
guest route guards, map selection, and horizontal overflow. Welcome and map
screenshots are saved under `test-results/`.
Windows uses installed Microsoft Edge; other platforms use Chromium (install it
first with `npx playwright install chromium`). Set `PLAYWRIGHT_CHANNEL` to override
the browser channel.

## Check the demo records

From the `backend` directory, after seeding:

```bash
sqlite3 cyberheist.db "SELECT COUNT(*) AS users FROM users;"
sqlite3 cyberheist.db "SELECT mission_order, title, is_mvp FROM missions ORDER BY mission_order;"
sqlite3 cyberheist.db "SELECT mission_id, COUNT(*) FROM puzzles GROUP BY mission_id;"
sqlite3 cyberheist.db "SELECT COUNT(*) AS attempts FROM puzzle_attempts;"
sqlite3 cyberheist.db "SELECT status, COUNT(*) FROM user_progress GROUP BY status;"
```

Fresh seed counts: 5 users, 5 missions, 10 puzzles, 16 attempts, 25 progress rows. Registration and gameplay increase these counts.

## GitHub

This folder currently sits inside the `AgenticProgramming` Git repository. Do not run `git init` here unless the team wants a separate nested repository. The safer setup is to publish Cyber Heist from its own empty GitHub repository after moving or copying the project out of the parent repo.

From the project root of that separate copy:

```bash
git init
git add .
git status
git commit -m "Add the Week 1 Cyber Heist foundation and early API prototype."
git branch -M main
git remote add origin git@github.com:OWNER/cyber-heist.git
git push -u origin main
```

Create the empty GitHub repository first. Replace `OWNER/cyber-heist` with the real repository. Do not force-push. Do not commit `.env` files, virtual environments, `node_modules`, or `backend/cyberheist.db`.
