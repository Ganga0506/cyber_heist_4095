# Cyber Heist

Cyber Heist is a browser-based cybersecurity escape-room game for CSE 4095 Agentic Programming at UConn. Players register, investigate simulated threats, solve puzzles, earn points, and save progress. This repository is the Week 1 foundation and an early Week 2 prototype. It is not the finished game.

The game uses fictional clues and simulated systems only. It does not connect to or attack real computers.

## Team 5

- Ganga Nomika Mahesh
- Eshita Srivastava
- Sushma Meghana Karri

## Technology stack

- Frontend: React, JavaScript, HTML, CSS (Vite)
- Backend: Python, FastAPI
- Database: SQLite with SQLAlchemy
- Tests: pytest
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

Mission unlock rules are not final. The proposal describes finishing one mission to open the next. The architecture notes say the MVP connects missions 1, 2, and 5. Sample progress rows show both ideas. The app does not enforce either rule yet.

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
  frontend/          React landing page
  docs/
    DEVELOPMENT_PROGRESS.md
```

The project folder is named `cyberheist`. That folder is the project root.

## Database tables

- `users`: player id, unique username, unique email, password hash, created time.
- `missions`: title, description, topic, unique mission order, MVP flag, created time.
- `puzzles`: mission foreign key, prompt, puzzle type, instructions, solution hash, points, order within the mission.
- `puzzle_attempts`: user and puzzle foreign keys, whether the attempt was correct, points earned, attempt time.
- `user_progress`: one row per user and mission. Status is `locked`, `available`, `in_progress`, or `completed`.

Leaderboard scores are not stored on the user. `GET /api/leaderboard` adds up the best correct `points_earned` for each puzzle. A second correct attempt on the same puzzle does not increase the score.

`database/schema.sql` and `database/seed.sql` are executable SQLite scripts. They are source files maintained with the Python models, not dumps exported from a live database. The app itself creates the database through SQLAlchemy.

Passwords and puzzle answers are not stored as plaintext. Passwords use PBKDF2-HMAC-SHA256. Answers use SHA-256 of the trimmed, case-folded text.

SQLite foreign keys are turned on for every connection.

## Development-only demo accounts

These fictional players exist so the team can try `GET /api/me/progress`. They are not production credentials. Do not reuse the passwords anywhere else. The demo hashes use a fixed salt so the SQL script and the Python seed match. Replace that approach before any real deployment.

| Username | Email | Password |
| --- | --- | --- |
| nova.agent | nova.agent@example.com | dev-only-nova |
| pixel.fox | pixel.fox@example.com | dev-only-pixel |
| cipher.owl | cipher.owl@example.com | dev-only-cipher |
| byte.lynx | byte.lynx@example.com | dev-only-byte |
| glitch.moth | glitch.moth@example.com | dev-only-glitch |

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
curl http://127.0.0.1:8000/api/missions/1
curl http://127.0.0.1:8000/api/leaderboard
curl -u nova.agent:dev-only-nova http://127.0.0.1:8000/api/me/progress
```

CORS allows only `http://localhost:5173` and `http://127.0.0.1:5173`.

The API does not accept puzzle answers and does not let the browser set a score.

## Frontend

From the `frontend` directory:

```bash
npm install
npm run dev
```

Open [http://127.0.0.1:5173](http://127.0.0.1:5173). The dev server proxies `/api` to FastAPI on port 8000. Start the API first if you want the page to load live mission records. The landing page still shows the five planned missions when the API is off.

The Begin Heist button is a preview. Login and puzzle play are not built yet.

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

## Check the demo records

From the `backend` directory, after seeding:

```bash
sqlite3 cyberheist.db "SELECT COUNT(*) AS users FROM users;"
sqlite3 cyberheist.db "SELECT mission_order, title, is_mvp FROM missions ORDER BY mission_order;"
sqlite3 cyberheist.db "SELECT mission_id, COUNT(*) FROM puzzles GROUP BY mission_id;"
sqlite3 cyberheist.db "SELECT COUNT(*) AS attempts FROM puzzle_attempts;"
sqlite3 cyberheist.db "SELECT status, COUNT(*) FROM user_progress GROUP BY status;"
```

Expected counts: 5 users, 5 missions, 10 puzzles, 16 attempts, 25 progress rows.

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
