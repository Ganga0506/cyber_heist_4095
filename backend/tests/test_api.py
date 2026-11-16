"""API tests against a temporary seeded database."""

PROTECTED_KEYS = {"password", "password_hash", "solution_hash", "email"}


def _walk(value):
    if isinstance(value, dict):
        for key, child in value.items():
            assert key not in PROTECTED_KEYS
            _walk(child)
    elif isinstance(value, list):
        for child in value:
            _walk(child)


def _secret_values(session):
    from models import Puzzle, User

    hashes = [row[0] for row in session.query(User.password_hash).all()]
    hashes.extend(row[0] for row in session.query(Puzzle.solution_hash).all())
    emails = [row[0] for row in session.query(User.email).all()]
    return hashes, emails


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}


def test_mission_list_comes_from_the_database(client):
    response = client.get("/api/missions")
    assert response.status_code == 200
    payload = response.json()
    assert [mission["title"] for mission in payload] == [
        "THE SETUP",
        "THE PERIMETER",
        "THE ENCRYPTION LAYER",
        "INSIDE THE SYSTEM",
        "THE FINAL HEIST",
    ]
    assert [mission["mission_order"] for mission in payload] == [1, 2, 3, 4, 5]
    assert [mission["is_mvp"] for mission in payload] == [True, True, False, False, True]
    assert all(mission["puzzle_count"] >= 2 for mission in payload)


def test_mission_detail_hides_the_solution(client, auth_headers):
    response = client.get("/api/missions/1", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["title"] == "THE SETUP"
    assert len(payload["puzzles"]) >= 2
    assert payload["puzzles"][0]["instructions"]
    assert "solution_hash" not in payload["puzzles"][0]
    _walk(payload)


def test_missing_mission_returns_404(client, auth_headers):
    response = client.get("/api/missions/99", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Mission not found"


def test_leaderboard_uses_best_correct_attempt(client):
    response = client.get("/api/leaderboard")
    assert response.status_code == 200
    payload = response.json()
    assert "puzzle_attempts" in payload["scoring"]
    by_name = {entry["username"]: entry for entry in payload["entries"]}

    # glitch solved four distinct puzzles: 100 + 80 + 100 + 150.
    assert by_name["glitch.moth"]["score"] == 430
    assert by_name["glitch.moth"]["puzzles_solved"] == 4
    # pixel solved the four Setup and Perimeter puzzles: 100 + 80 + 100 + 90.
    assert by_name["pixel.fox"]["score"] == 370
    assert by_name["pixel.fox"]["puzzles_solved"] == 4
    # nova has two correct attempts on puzzle 1. The score counts that puzzle once.
    assert by_name["nova.agent"]["score"] == 280
    assert by_name["nova.agent"]["puzzles_solved"] == 3
    assert by_name["byte.lynx"]["score"] == 0
    assert by_name["cipher.owl"]["score"] == 0
    assert [entry["username"] for entry in payload["entries"]] == [
        "glitch.moth",
        "pixel.fox",
        "nova.agent",
        "byte.lynx",
        "cipher.owl",
    ]
    assert [entry["rank"] for entry in payload["entries"]] == [1, 2, 3, 4, 5]


def test_responses_do_not_reveal_protected_data(client, seeded_session, auth_headers):
    hashes, emails = _secret_values(seeded_session)
    paths = [
        "/api/health",
        "/api/missions",
        "/api/missions/1",
        "/api/leaderboard",
    ]
    for path in paths:
        response = client.get(path, headers=auth_headers)
        assert response.status_code == 200
        body = response.text
        for secret in hashes:
            assert secret not in body
        for email in emails:
            assert email not in body
        _walk(response.json())

    progress = client.get("/api/me/progress", headers=auth_headers)
    assert progress.status_code == 200
    for secret in hashes:
        assert secret not in progress.text
    for email in emails:
        assert email not in progress.text
    _walk(progress.json())


def test_progress_requires_a_bearer_session(client, auth_headers):
    missing = client.get("/api/me/progress")
    assert missing.status_code == 401

    wrong = client.get("/api/me/progress", auth=("nova.agent", "wrong-password"))
    assert wrong.status_code == 401

    ok = client.get("/api/me/progress", headers=auth_headers)
    assert ok.status_code == 200
    payload = ok.json()
    assert payload["username"] == "nova.agent"
    assert [item["status"] for item in payload["missions"]] == [
        "completed",
        "in_progress",
        "locked",
        "locked",
        "locked",
    ]
    assert "email" not in payload
    assert "password_hash" not in payload


def test_cors_allows_only_local_frontend_origins(client):
    allowed = client.get("/api/health", headers={"Origin": "http://localhost:5173"})
    assert allowed.headers.get("access-control-allow-origin") == "http://localhost:5173"

    other_local = client.get(
        "/api/health",
        headers={"Origin": "http://127.0.0.1:5173"},
    )
    assert other_local.headers.get("access-control-allow-origin") == "http://127.0.0.1:5173"

    blocked = client.get("/api/health", headers={"Origin": "https://example.com"})
    assert blocked.headers.get("access-control-allow-origin") is None
