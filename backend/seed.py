"""Create the Cyber Heist tables and insert fictional demo records.

Running this file twice does not duplicate rows. Existing usernames, mission
numbers, puzzle slots, progress rows, and attempt timestamps are left as they
are. Demo passwords are development-only. See README.md.

The plaintext puzzle answers below are used only to compute solution_hash.
They are not written to the database.
"""

from datetime import datetime

from sqlalchemy.orm import Session

from database import Base, SessionLocal, get_engine
from models import Mission, Puzzle, PuzzleAttempt, User, UserProgress
from security import hash_password, hash_solution

CATALOG_TIME = datetime(2026, 2, 1, 8, 0, 0)

# Development-only passwords. They are hashed before insert.
DEMO_USERS = [
    {
        "id": 1,
        "username": "nova.agent",
        "email": "nova.agent@example.com",
        "password": "dev-only-nova",
        "created_at": datetime(2026, 2, 1, 9, 0, 0),
    },
    {
        "id": 2,
        "username": "pixel.fox",
        "email": "pixel.fox@example.com",
        "password": "dev-only-pixel",
        "created_at": datetime(2026, 2, 1, 9, 15, 0),
    },
    {
        "id": 3,
        "username": "cipher.owl",
        "email": "cipher.owl@example.com",
        "password": "dev-only-cipher",
        "created_at": datetime(2026, 2, 1, 9, 30, 0),
    },
    {
        "id": 4,
        "username": "byte.lynx",
        "email": "byte.lynx@example.com",
        "password": "dev-only-byte",
        "created_at": datetime(2026, 2, 1, 9, 45, 0),
    },
    {
        "id": 5,
        "username": "glitch.moth",
        "email": "glitch.moth@example.com",
        "password": "dev-only-glitch",
        "created_at": datetime(2026, 2, 1, 10, 0, 0),
    },
]

# Hash once at import so repeated seeds and tests stay fast.
for _demo_user in DEMO_USERS:
    _demo_user["password_hash"] = hash_password(
        _demo_user["password"],
        salt=f"devsalt-{_demo_user['username']}",
    )

DEMO_MISSIONS = [
    {
        "id": 1,
        "title": "THE SETUP",
        "description": (
            "Investigate fictional leaked files and hidden clues to locate "
            "the first access point. This mission introduces encoding and "
            "digital forensics."
        ),
        "topic": "Encoding and Digital Forensics",
        "mission_order": 1,
        "is_mvp": True,
    },
    {
        "id": 2,
        "title": "THE PERIMETER",
        "description": (
            "Explore a simulated network and read sample web traffic to "
            "discover an access key. This mission introduces networking and HTTP."
        ),
        "topic": "Networking and HTTP",
        "mission_order": 2,
        "is_mvp": True,
    },
    {
        "id": 3,
        "title": "THE ENCRYPTION LAYER",
        "description": (
            "Decode a short cipher and compare a hash prefix to recover a "
            "hidden word. This mission introduces cryptography and hashing. "
            "It is planned after the first MVP."
        ),
        "topic": "Cryptography and Hashing",
        "mission_order": 3,
        "is_mvp": False,
    },
    {
        "id": 4,
        "title": "INSIDE THE SYSTEM",
        "description": (
            "Read fictional program logic and a small access policy. This "
            "mission introduces code analysis and access control. It is "
            "planned after the first MVP."
        ),
        "topic": "Code Analysis and Access Control",
        "mission_order": 4,
        "is_mvp": False,
    },
    {
        "id": 5,
        "title": "THE FINAL HEIST",
        "description": (
            "Combine tokens from earlier missions in a fictional multi-stage "
            "vault puzzle. This mission ties the story together."
        ),
        "topic": "Integrated Cybersecurity Challenges",
        "mission_order": 5,
        "is_mvp": True,
    },
]

# answer is hashing input only. It is removed before the row is saved.
DEMO_PUZZLES = [
    {
        "id": 1,
        "mission_id": 1,
        "title": "Demo: Base64 Access Note",
        "description": "Demo puzzle. Decode one Base64 clue from a fictional note.",
        "puzzle_type": "encoding",
        "instructions": (
            "A fictional incident note contains this Base64 text: "
            "QUNDRVNTLVBPSU5ULUEx. Decode it and submit the plaintext exactly, "
            "using capital letters and hyphens."
        ),
        "answer": "ACCESS-POINT-A1",
        "points": 100,
        "puzzle_order": 1,
    },
    {
        "id": 2,
        "mission_id": 1,
        "title": "Demo: Phishing Sign",
        "description": "Demo puzzle. Name the suspicious sign in one fictional message.",
        "puzzle_type": "forensics",
        "instructions": (
            "Fictional message, not a real email. From security@uconn-help.example. "
            "Subject: Mailbox expires tonight. The link host is uconn-help.example, "
            "which is not the real university site. Which label fits this sign? "
            "A) LOOKALIKE-DOMAIN B) ENCRYPTED-ATTACHMENT C) MISSING-SUBJECT. "
            "Submit the label only."
        ),
        "answer": "LOOKALIKE-DOMAIN",
        "points": 80,
        "puzzle_order": 2,
    },
    {
        "id": 3,
        "mission_id": 2,
        "title": "Demo: Response Header",
        "description": "Demo puzzle. Read a simulated HTTP response from a fictional gate.",
        "puzzle_type": "http",
        "instructions": (
            "Simulated response only. No live server is contacted. "
            "Status line: HTTP/1.1 200 OK. Header: Content-Type: text/plain. "
            "Header: X-Access-Key: PERIM-KEY-17. Body: gate=closed. "
            "Submit the value of the X-Access-Key header."
        ),
        "answer": "PERIM-KEY-17",
        "points": 100,
        "puzzle_order": 1,
    },
    {
        "id": 4,
        "mission_id": 2,
        "title": "Demo: Request Log",
        "description": "Demo puzzle. Pick one line from a fictional request log.",
        "puzzle_type": "networking",
        "instructions": (
            "Simulated log from a fictional service: "
            "10:01 GET /health 200; 10:02 GET /status 200; 10:03 POST /login 401. "
            "Which request returned 200 and was not the health check? "
            "Submit the method and path, for example POST /login."
        ),
        "answer": "GET /status",
        "points": 90,
        "puzzle_order": 2,
    },
    {
        "id": 5,
        "mission_id": 3,
        "title": "Demo: Caesar Shift",
        "description": "Demo puzzle. Reverse a three-letter Caesar shift.",
        "puzzle_type": "cryptography",
        "instructions": (
            "The fictional ciphertext FDHVDU was shifted forward by 3 letters. "
            "Submit the original word in capital letters."
        ),
        "answer": "CAESAR",
        "points": 100,
        "puzzle_order": 1,
    },
    {
        "id": 6,
        "mission_id": 3,
        "title": "Demo: Hash Prefix",
        "description": "Demo puzzle. Match a short SHA-256 prefix to a candidate word.",
        "puzzle_type": "hashing",
        "instructions": (
            "A fictional vault label was hashed with SHA-256. The digest begins "
            "with e6f0a1fb. Candidates: lock, vault, key. Submit the matching "
            "word in lowercase. This compares a known prefix. It is not password cracking."
        ),
        "answer": "vault",
        "points": 120,
        "puzzle_order": 2,
    },
    {
        "id": 7,
        "mission_id": 4,
        "title": "Demo: Read the Check",
        "description": "Demo puzzle. Read a fictional authentication function.",
        "puzzle_type": "code-analysis",
        "instructions": (
            "This function is fictional and does not protect a real account. "
            "def allow_entry(pin): grant access only when pin equals 2468. "
            "What PIN does the function accept? Submit the digits only."
        ),
        "answer": "2468",
        "points": 100,
        "puzzle_order": 1,
    },
    {
        "id": 8,
        "mission_id": 4,
        "title": "Demo: Night Access Policy",
        "description": "Demo puzzle. Read a fictional access-control table.",
        "puzzle_type": "access-control",
        "instructions": (
            "Fictional policy. analyst: night access no. auditor: night access yes. "
            "guest: night access no. Which role is allowed night access? "
            "Submit the role name in lowercase."
        ),
        "answer": "auditor",
        "points": 90,
        "puzzle_order": 2,
    },
    {
        "id": 9,
        "mission_id": 5,
        "title": "Demo: Join the Tokens",
        "description": "Demo puzzle. Combine two tokens from earlier demo puzzles.",
        "puzzle_type": "integrated",
        "instructions": (
            "Take the plaintext from the Base64 access note and the X-Access-Key "
            "value from the simulated HTTP response. Join them with one hyphen, "
            "access note first. Example shape: FIRST-TOKEN-SECOND-TOKEN. "
            "The vault is fictional."
        ),
        "answer": "ACCESS-POINT-A1-PERIM-KEY-17",
        "points": 150,
        "puzzle_order": 1,
    },
    {
        "id": 10,
        "mission_id": 5,
        "title": "Demo: Careful Response",
        "description": "Demo puzzle. Choose a defensive order for a fictional incident.",
        "puzzle_type": "integrated",
        "instructions": (
            "A fictional lab machine shows unexpected files. Which label is the "
            "careful defensive order? A) ISOLATE-PRESERVE-REPORT "
            "B) DELETE-EVERYTHING-FIRST C) IGNORE-AND-CONTINUE. "
            "Submit the chosen label."
        ),
        "answer": "ISOLATE-PRESERVE-REPORT",
        "points": 150,
        "puzzle_order": 2,
    },
]

# user_id, puzzle_id, is_correct, points_earned, attempted_at
# nova solves puzzle 1 twice so the leaderboard can show that repeats do not stack.
DEMO_ATTEMPTS = [
    (1, 1, True, 100, datetime(2026, 3, 1, 10, 0, 0)),
    (1, 1, True, 100, datetime(2026, 3, 1, 10, 5, 0)),
    (1, 2, True, 80, datetime(2026, 3, 1, 10, 10, 0)),
    (1, 3, False, 0, datetime(2026, 3, 1, 11, 0, 0)),
    (1, 3, True, 100, datetime(2026, 3, 1, 11, 6, 0)),
    (2, 1, True, 100, datetime(2026, 3, 2, 9, 0, 0)),
    (2, 2, True, 80, datetime(2026, 3, 2, 9, 20, 0)),
    (2, 3, True, 100, datetime(2026, 3, 2, 10, 0, 0)),
    (2, 4, True, 90, datetime(2026, 3, 2, 10, 30, 0)),
    (3, 1, False, 0, datetime(2026, 3, 3, 12, 0, 0)),
    (4, 1, False, 0, datetime(2026, 3, 4, 15, 0, 0)),
    (4, 2, False, 0, datetime(2026, 3, 4, 15, 12, 0)),
    (5, 1, True, 100, datetime(2026, 3, 5, 8, 0, 0)),
    (5, 2, True, 80, datetime(2026, 3, 5, 8, 25, 0)),
    (5, 3, True, 100, datetime(2026, 3, 5, 8, 40, 0)),
    (5, 9, True, 150, datetime(2026, 3, 5, 9, 10, 0)),
]

# Sample snapshots only. The app does not enforce an unlock rule yet.
# pixel.fox has mission 3 available after mission 2, which illustrates a 1-to-5 path.
# glitch.moth has mission 5 in progress while missions 3 and 4 stay locked,
# which illustrates one possible MVP path. Neither pattern is final.
DEMO_PROGRESS = [
    (1, 1, "completed", datetime(2026, 3, 1, 10, 10, 0)),
    (1, 2, "in_progress", None),
    (1, 3, "locked", None),
    (1, 4, "locked", None),
    (1, 5, "locked", None),
    (2, 1, "completed", datetime(2026, 3, 2, 9, 20, 0)),
    (2, 2, "completed", datetime(2026, 3, 2, 10, 30, 0)),
    (2, 3, "available", None),
    (2, 4, "locked", None),
    (2, 5, "locked", None),
    (3, 1, "available", None),
    (3, 2, "locked", None),
    (3, 3, "locked", None),
    (3, 4, "locked", None),
    (3, 5, "locked", None),
    (4, 1, "in_progress", None),
    (4, 2, "locked", None),
    (4, 3, "locked", None),
    (4, 4, "locked", None),
    (4, 5, "locked", None),
    (5, 1, "completed", datetime(2026, 3, 5, 8, 25, 0)),
    (5, 2, "completed", datetime(2026, 3, 5, 8, 40, 0)),
    (5, 3, "locked", None),
    (5, 4, "locked", None),
    (5, 5, "in_progress", None),
]


def _stamp(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S")


def _quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def init_db() -> None:
    """Create any missing tables. Does not insert demo rows."""
    get_engine()
    Base.metadata.create_all(bind=get_engine())


def seed(session: Session) -> None:
    """Insert demo rows that are not already present."""
    for row in DEMO_USERS:
        exists = session.query(User).filter_by(username=row["username"]).one_or_none()
        if exists is None:
            session.add(
                User(
                    id=row["id"],
                    username=row["username"],
                    email=row["email"],
                    password_hash=row["password_hash"],
                    created_at=row["created_at"],
                )
            )
    session.flush()

    for row in DEMO_MISSIONS:
        exists = (
            session.query(Mission)
            .filter_by(mission_order=row["mission_order"])
            .one_or_none()
        )
        if exists is None:
            session.add(
                Mission(
                    id=row["id"],
                    title=row["title"],
                    description=row["description"],
                    topic=row["topic"],
                    mission_order=row["mission_order"],
                    is_mvp=row["is_mvp"],
                    created_at=CATALOG_TIME,
                )
            )
    session.flush()

    for row in DEMO_PUZZLES:
        exists = (
            session.query(Puzzle)
            .filter_by(mission_id=row["mission_id"], puzzle_order=row["puzzle_order"])
            .one_or_none()
        )
        if exists is None:
            session.add(
                Puzzle(
                    id=row["id"],
                    mission_id=row["mission_id"],
                    title=row["title"],
                    description=row["description"],
                    puzzle_type=row["puzzle_type"],
                    instructions=row["instructions"],
                    solution_hash=hash_solution(row["answer"]),
                    points=row["points"],
                    puzzle_order=row["puzzle_order"],
                )
            )
    session.flush()

    for user_id, mission_id, status, completed_at in DEMO_PROGRESS:
        exists = (
            session.query(UserProgress)
            .filter_by(user_id=user_id, mission_id=mission_id)
            .one_or_none()
        )
        if exists is None:
            session.add(
                UserProgress(
                    user_id=user_id,
                    mission_id=mission_id,
                    status=status,
                    completed_at=completed_at,
                )
            )
    session.flush()

    for user_id, puzzle_id, is_correct, points_earned, attempted_at in DEMO_ATTEMPTS:
        exists = (
            session.query(PuzzleAttempt)
            .filter_by(
                user_id=user_id,
                puzzle_id=puzzle_id,
                attempted_at=attempted_at,
            )
            .one_or_none()
        )
        if exists is None:
            session.add(
                PuzzleAttempt(
                    user_id=user_id,
                    puzzle_id=puzzle_id,
                    is_correct=is_correct,
                    points_earned=points_earned,
                    attempted_at=attempted_at,
                )
            )

    session.commit()


def render_seed_sql() -> str:
    """Build database/seed.sql from the same records seed() inserts."""
    lines = [
        "-- Executable demo data for Cyber Heist.",
        "-- This is a source script, not a dump of a live database.",
        "-- It inserts the same fictional records as backend/seed.py.",
        "-- Running it again does not add duplicate rows.",
        "--",
        "-- Demo passwords are development-only and are stored as",
        "-- PBKDF2-HMAC-SHA256 hashes. See README.md.",
        "-- Puzzle answers are stored only as SHA-256 hashes.",
        "",
        "PRAGMA foreign_keys = ON;",
        "",
        "-- Fictional demo players",
    ]

    for row in DEMO_USERS:
        lines.extend(
            [
                "INSERT INTO users (id, username, email, password_hash, created_at)",
                "SELECT "
                f"{row['id']}, {_quote(row['username'])}, {_quote(row['email'])}, "
                f"{_quote(row['password_hash'])}, {_quote(_stamp(row['created_at']))}",
                f"WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = {_quote(row['username'])});",
                "",
            ]
        )

    lines.append("-- Five missions. is_mvp = 1 marks the first playable subset.")
    for row in DEMO_MISSIONS:
        lines.extend(
            [
                "INSERT INTO missions (id, title, description, topic, mission_order, is_mvp, created_at)",
                "SELECT "
                f"{row['id']}, {_quote(row['title'])}, {_quote(row['description'])}, "
                f"{_quote(row['topic'])}, {row['mission_order']}, "
                f"{1 if row['is_mvp'] else 0}, {_quote(_stamp(CATALOG_TIME))}",
                "WHERE NOT EXISTS ("
                f"SELECT 1 FROM missions WHERE mission_order = {row['mission_order']}"
                ");",
                "",
            ]
        )

    lines.append("-- Two demo puzzles for every mission.")
    for row in DEMO_PUZZLES:
        lines.extend(
            [
                "INSERT INTO puzzles "
                "(id, mission_id, title, description, puzzle_type, instructions, "
                "solution_hash, points, puzzle_order)",
                "SELECT "
                f"{row['id']}, {row['mission_id']}, {_quote(row['title'])}, "
                f"{_quote(row['description'])}, {_quote(row['puzzle_type'])}, "
                f"{_quote(row['instructions'])}, {_quote(hash_solution(row['answer']))}, "
                f"{row['points']}, {row['puzzle_order']}",
                "WHERE NOT EXISTS ("
                "SELECT 1 FROM puzzles "
                f"WHERE mission_id = {row['mission_id']} AND puzzle_order = {row['puzzle_order']}"
                ");",
                "",
            ]
        )

    lines.extend(
        [
            "-- Sample progress. These statuses are hand-written snapshots.",
            "-- They are not produced by a finished unlock rule.",
            "-- One sample follows mission order. Another leaves missions 3 and 4",
            "-- locked while mission 5 is in progress. The team still needs to",
            "-- choose the real rule.",
        ]
    )
    for user_id, mission_id, status, completed_at in DEMO_PROGRESS:
        completed_sql = "NULL" if completed_at is None else _quote(_stamp(completed_at))
        lines.extend(
            [
                "INSERT INTO user_progress (user_id, mission_id, status, completed_at)",
                f"SELECT {user_id}, {mission_id}, {_quote(status)}, {completed_sql}",
                "WHERE NOT EXISTS ("
                "SELECT 1 FROM user_progress "
                f"WHERE user_id = {user_id} AND mission_id = {mission_id}"
                ");",
                "",
            ]
        )

    lines.extend(
        [
            "-- Sample attempts. Player 1 submits a correct answer for puzzle 1 twice.",
            "-- Leaderboard scoring keeps the best correct attempt per puzzle.",
        ]
    )
    for user_id, puzzle_id, is_correct, points_earned, attempted_at in DEMO_ATTEMPTS:
        stamp = _quote(_stamp(attempted_at))
        lines.extend(
            [
                "INSERT INTO puzzle_attempts "
                "(user_id, puzzle_id, is_correct, points_earned, attempted_at)",
                "SELECT "
                f"{user_id}, {puzzle_id}, {1 if is_correct else 0}, {points_earned}, {stamp}",
                "WHERE NOT EXISTS ("
                "SELECT 1 FROM puzzle_attempts "
                f"WHERE user_id = {user_id} AND puzzle_id = {puzzle_id} "
                f"AND attempted_at = {stamp}"
                ");",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    init_db()
    session = SessionLocal()
    try:
        seed(session)
        print("Cyber Heist demo database is ready.")
        print(f"location: {get_engine().url}")
        print(f"users: {session.query(User).count()}")
        print(f"missions: {session.query(Mission).count()}")
        print(f"puzzles: {session.query(Puzzle).count()}")
        print(f"puzzle_attempts: {session.query(PuzzleAttempt).count()}")
        print(f"user_progress: {session.query(UserProgress).count()}")
        print("Demo passwords are documented in README.md. They are development-only.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
