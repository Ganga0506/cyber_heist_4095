"""Exercise the complete browser API flow against an isolated database."""

from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor

import pytest

from gameplay import token_digest
from models import AuthSession, utc_now
from seed import DEMO_PUZZLES


def new_agent(client, name="fresh.agent"):
    body = {"username": name, "email": name + "@example.com", "password": "fresh-password-123"}
    response = client.post("/api/auth/register", json=body)
    assert response.status_code == 201, response.text
    assert set(response.json()) == {"id", "username"}
    response = client.post("/api/auth/login", json={"username": name, "password": body["password"]})
    assert response.status_code == 200, response.text
    return {"Authorization": "Bearer " + response.json()["access_token"]}


def test_full_mvp_loop_and_repeat_scoring(client):
    headers = new_agent(client)
    progress = client.get("/api/me/progress", headers=headers).json()
    assert progress["score"] == 0
    assert [m["status"] for m in progress["missions"]] == ["available", "locked", "locked", "locked", "locked"]
    assert client.get("/api/me", headers=headers).json()["username"] == "fresh.agent"
    assert client.get("/api/missions/2", headers=headers).status_code == 403
    assert client.post("/api/puzzles/1/attempts", headers=headers, json={"answer": "wrong"}).status_code == 409
    total = 0
    for mission_id, next_id in [(1, 2), (2, 5), (5, None)]:
        assert client.post(f"/api/missions/{mission_id}/start", headers=headers).status_code == 200
        detail = client.get(f"/api/missions/{mission_id}", headers=headers)
        assert detail.status_code == 200, detail.text
        for puzzle in detail.json()["puzzles"]:
            path = f"/api/puzzles/{puzzle['id']}/attempts"
            wrong = client.post(path, headers=headers, json={"answer": "definitely wrong"})
            assert wrong.status_code == 200, wrong.text
            assert wrong.json()["points_awarded"] == 0
            answer = next(p["answer"] for p in DEMO_PUZZLES if p["id"] == puzzle["id"])
            result = client.post(path, headers=headers, json={"answer": "  " + answer.upper() + "  "})
            assert result.status_code == 200, result.text
            assert result.json()["is_correct"]
            assert result.json()["points_awarded"] == puzzle["points"]
            total += puzzle["points"]
            repeat = client.post(path, headers=headers, json={"answer": answer}).json()
            assert repeat["already_solved"] and repeat["points_awarded"] == 0
            assert repeat["total_score"] == total
        assert result.json()["mission"]["status"] == "completed"
        assert result.json()["unlocked_mission_ids"] == ([next_id] if next_id else [])
        timestamp = result.json()["mission"]["completed_at"]
        assert timestamp.endswith("Z")
        resumed = client.post(f"/api/missions/{mission_id}/start", headers=headers).json()
        assert resumed["completed_at"] == timestamp
    score = next(r for r in client.get("/api/leaderboard").json()["entries"] if r["username"] == "fresh.agent")
    assert score["score"] == total and score["puzzles_solved"] == 6
    assert client.post("/api/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/me", headers=headers).status_code == 401
    login = client.post("/api/auth/login", json={"username": "fresh.agent", "password": "fresh-password-123"}).json()
    assert client.get("/api/me/progress", headers={"Authorization": "Bearer " + login["access_token"]}).json()["score"] == total


def test_validation_isolation_and_expiration(client, seeded_session):
    headers = new_agent(client)
    other = new_agent(client, "other.agent")
    assert client.post("/api/auth/register", json={"username": "FRESH.AGENT", "email": "different@example.com", "password": "fresh-password-123"}).status_code == 409
    assert client.post("/api/auth/register", json={"username": "bad name", "email": "bad", "password": "short"}).status_code == 422
    assert client.post("/api/auth/login", json={"username": "unknown", "password": "bad"}).status_code == 401
    assert client.get("/api/missions/1").status_code == 401
    assert client.post("/api/missions/3/start", headers=headers).status_code == 403
    assert client.post("/api/missions/999/start", headers=headers).status_code == 404
    assert client.post("/api/puzzles/999/attempts", headers=headers, json={"answer": "test"}).status_code == 404
    client.post("/api/missions/1/start", headers=headers)
    for body in [{"answer": "   "}, {"answer": "test", "score": 999}, {"answer": 123}]:
        assert client.post("/api/puzzles/1/attempts", headers=headers, json=body).status_code == 422
    assert client.get("/api/me/progress", headers=other).json()["missions"][0]["status"] == "available"
    token = headers["Authorization"].split()[1]
    stored = seeded_session.get(AuthSession, token_digest(token))
    stored.expires_at = utc_now() - timedelta(seconds=1)
    seeded_session.commit()
    assert client.get("/api/me", headers=headers).status_code == 401


def test_cors_accepts_post(client):
    response = client.options("/api/auth/login", headers={
        "Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type,authorization",
    })
    assert response.status_code == 200


def test_simultaneous_correct_answers_award_once(client):
    headers = new_agent(client)
    client.post("/api/missions/1/start", headers=headers)
    answer = next(p["answer"] for p in DEMO_PUZZLES if p["id"] == 1)
    def submit(_):
        return client.post("/api/puzzles/1/attempts", headers=headers, json={"answer": answer})
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(submit, range(2)))
    assert all(r.status_code == 200 for r in responses)
    assert sorted(r.json()["points_awarded"] for r in responses) == [0, 100]
    assert client.get("/api/me/progress", headers=headers).json()["score"] == 100


@pytest.mark.parametrize("field,value", [
    ("user_id", 1), ("is_correct", True), ("score", 99999),
    ("points_awarded", 99999), ("status", "completed"),
])
def test_attempt_rejects_client_controlled_game_state(client, field, value):
    headers = new_agent(client)
    client.post("/api/missions/1/start", headers=headers)
    answer = next(p["answer"] for p in DEMO_PUZZLES if p["id"] == 1)
    response = client.post("/api/puzzles/1/attempts", headers=headers,
                           json={"answer": answer, field: value})
    assert response.status_code == 422
    progress = client.get("/api/me/progress", headers=headers).json()
    assert progress["score"] == 0
    assert not any(p["solved"] for p in progress["missions"][0]["puzzles"])
    assert progress["missions"][1]["status"] == "locked"


def test_partial_mission_survives_logout_and_resume(client):
    headers = new_agent(client)
    client.post("/api/missions/1/start", headers=headers)
    answer = next(p["answer"] for p in DEMO_PUZZLES if p["id"] == 1)
    response = client.post("/api/puzzles/1/attempts", headers=headers, json={"answer": answer})
    assert response.status_code == 200
    before = client.get("/api/me/progress", headers=headers).json()
    assert before["missions"][0]["status"] == "in_progress"
    assert [p["solved"] for p in before["missions"][0]["puzzles"]] == [True, False]
    assert client.post("/api/auth/logout", headers=headers).status_code == 204
    login = client.post("/api/auth/login", json={
        "username": "fresh.agent", "password": "fresh-password-123",
    }).json()
    headers = {"Authorization": "Bearer " + login["access_token"]}
    resumed = client.post("/api/missions/1/start", headers=headers)
    assert resumed.status_code == 200
    assert resumed.json() == before["missions"][0]
    assert client.get("/api/me/progress", headers=headers).json() == before


def test_answers_and_locked_attempts_preserve_other_player_progress(client):
    headers = new_agent(client)
    other = new_agent(client, "other.agent")
    other_before = client.get("/api/me/progress", headers=other).json()
    client.post("/api/missions/1/start", headers=headers)
    for puzzle in (p for p in DEMO_PUZZLES if p["mission_id"] == 1):
        response = client.post(f"/api/puzzles/{puzzle['id']}/attempts", headers=headers,
                               json={"answer": puzzle["answer"]})
        assert response.status_code == 200
    assert client.get("/api/me/progress", headers=headers).json()["missions"][1]["status"] == "available"
    locked_puzzle = next(p for p in DEMO_PUZZLES if p["mission_id"] == 2)
    response = client.post(f"/api/puzzles/{locked_puzzle['id']}/attempts", headers=other,
                           json={"answer": locked_puzzle["answer"]})
    assert response.status_code == 403
    assert client.get("/api/me/progress", headers=other).json() == other_before
