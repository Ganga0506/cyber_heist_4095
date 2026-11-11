# Cyber Heist schema

The application stores accounts, missions, puzzles, attempts, and mission
progress. Leaderboard totals are not a table. They are calculated from
correct rows in `puzzle_attempts`, keeping only the best score for each
player on each puzzle.

`schema.sql` and `seed.sql` are executable SQLite scripts. They match the
SQLAlchemy models in `backend/models.py`. The running app creates and fills
the database through SQLAlchemy (`python seed.py`). You can also apply the
SQL files with the `sqlite3` command. They are maintained source files, not
exports taken from a live database file.

```mermaid
erDiagram
    USERS ||--o{ PUZZLE_ATTEMPTS : submits
    USERS ||--o{ USER_PROGRESS : has
    MISSIONS ||--o{ PUZZLES : contains
    MISSIONS ||--o{ USER_PROGRESS : tracks
    PUZZLES ||--o{ PUZZLE_ATTEMPTS : receives

    USERS {
        int id PK
        string username UK
        string email UK
        string password_hash
        datetime created_at
    }

    MISSIONS {
        int id PK
        string title
        string description
        string topic
        int mission_order UK
        bool is_mvp
        datetime created_at
    }

    PUZZLES {
        int id PK
        int mission_id FK
        string title
        string description
        string puzzle_type
        string instructions
        string solution_hash
        int points
        int puzzle_order
    }

    PUZZLE_ATTEMPTS {
        int id PK
        int user_id FK
        int puzzle_id FK
        bool is_correct
        int points_earned
        datetime attempted_at
    }

    USER_PROGRESS {
        int id PK
        int user_id FK
        int mission_id FK
        string status
        datetime completed_at
    }
```

Notes:

- `PUZZLES` has a unique pair of `mission_id` and `puzzle_order`.
- `USER_PROGRESS` has a unique pair of `user_id` and `mission_id`.
- `status` is one of `locked`, `available`, `in_progress`, or `completed`.
- `solution_hash` is a SHA-256 digest. The answer text is not stored.
- `password_hash` is a PBKDF2 hash. The password text is not stored.
- Foreign keys are enforced with `PRAGMA foreign_keys = ON`.
- Deleting a mission that still has puzzles is rejected. The same is true for users or puzzles that still have attempts or progress rows.
- Mission unlock order is not represented by an extra table. Sample progress rows are snapshots, and the real unlock rule is still an open design choice.
