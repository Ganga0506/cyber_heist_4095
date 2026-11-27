# Cyber Heist API contract

This is the implemented local MVP contract. All endpoints below are connected
to the React interface. FastAPI `/docs` and `/openapi.json` provide the executable
request/response schemas.

## Connection and conventions

- Backend development URL: `http://127.0.0.1:8000`.
- Frontend uses relative `/api/...` URLs; Vite proxies them to the backend.
- JSON request bodies use `Content-Type: application/json`.
- IDs and points are integers; booleans are JSON booleans. Mission IDs must come
  from the API; do not assume they equal `mission_order`.
- Successful reads return 200. Current lists are unpaginated.
- Never send passwords in query strings or return passwords, password hashes,
  solutions, or solution hashes. Only registration accepts an email;
  user responses below omit it.

## Endpoint inventory

| Method | Path | Status | Authentication | Frontend purpose |
| --- | --- | --- | --- | --- |
| GET | `/api/health` | Current | None | Connection check |
| GET | `/api/missions` | Current | None | Mission cards |
| GET | `/api/missions/{mission_id}` | Current | Bearer | Metadata and puzzle instructions |
| GET | `/api/leaderboard` | Current | None | Leaderboard |
| GET | `/api/me/progress` | Current | Bearer | Saved mission statuses |
| POST | `/api/auth/register` | Current | None | Create account |
| POST | `/api/auth/login` | Current | None | Create session |
| GET | `/api/me` | Current | Bearer | Identify signed-in player |
| POST | `/api/auth/logout` | Current | Bearer | Revoke session |
| POST | `/api/missions/{mission_id}/start` | Current | Bearer | Start/resume mission |
| POST | `/api/puzzles/{puzzle_id}/attempts` | Current | Bearer | Submit text answer for missions 2 and 5 |
| POST | `/api/puzzles/{puzzle_id}/code` | Current | Bearer | Save, run, or submit a Mission 1 expression |

Also current: `GET /` returns API name and health/docs links; `/docs` serves the
interactive reference. Separate puzzle-detail, score-update, and mission-complete
endpoints are unnecessary for this MVP: mission detail contains the puzzles and
the backend calculates scores and completion from submitted answers.

## Current response shapes

The notation below lists exact field names and types, rather than sample records.

```text
Health = { status: string, database: string }
MissionSummary = {
  id: integer, title: string, description: string, topic: string,
  mission_order: integer, is_mvp: boolean, puzzle_count: integer
}
PuzzlePublic = {
  id: integer, title: string, description: string, puzzle_type: string,
  instructions: string, points: integer, puzzle_order: integer
}
MissionDetail = MissionSummary + { puzzles: PuzzlePublic[] }
LeaderboardEntry = {
  rank: integer, username: string, score: integer, puzzles_solved: integer
}
Leaderboard = { scoring: string, entries: LeaderboardEntry[] }
ProgressItem = {
  mission_id: integer, title: string, mission_order: integer,
  status: "locked" | "available" | "in_progress" | "completed",
  completed_at: datetime-string | null, puzzles: PuzzleProgress[]
}
PuzzleProgress = { puzzle_id: integer, solved: boolean, points_earned: integer }
PlayerProgress = {
  username: string, missions: ProgressItem[], score: integer, puzzles_solved: integer
}
```

| Read | 200 body | Details/errors |
| --- | --- | --- |
| Health | `{"status":"ok","database":"connected"}` | 503: `{"detail":"Database unavailable"}` |
| Missions | `MissionSummary[]` | Ordered by `mission_order`; empty list allowed |
| Mission detail | `MissionDetail` | Puzzles ordered by `puzzle_order`; 404: `{"detail":"Mission not found"}` |
| Leaderboard | `Leaderboard` | Score descending, username ascending for ties; ranks are sequential starting at 1 |
| My progress | `PlayerProgress` | Ordered by mission order; 401 for missing/invalid bearer session |

Scores sum each player's best correct points per puzzle. Repeated correct
attempts do not add score. Protected routes require a bearer session; HTTP Basic
is no longer accepted. CORS permits GET/POST/OPTIONS from the two local
port-5173 origins. Progress timestamps use UTC with a `Z` suffix.

## Authentication contract

An opaque bearer token expires after 24 hours. The `auth_sessions` table stores
its hash, user ID, and expiry. Logout deletes the session. The frontend keeps
the token in memory; log in again after browser refresh. Game progress remains
in SQLite. Startup creates the new table without deleting existing game data.

Send `Authorization: Bearer <access_token>` on protected requests. Missing,
expired, revoked, or invalid tokens return 401. Logout revokes the token; the
frontend clears its local session even if the request fails. `GET /api/me/progress` uses the same bearer token.

```text
UserPublic = { id: integer, username: string }
Session = {
  access_token: string, token_type: "bearer", expires_in: 86400,
  user: UserPublic
}
```

| Endpoint | Request body | Success | Expected failures |
| --- | --- | --- | --- |
| Register | `{"username":"new.agent","email":"agent@example.com","password":"example-password"}` | 201 `UserPublic`; does not log in automatically | 409 duplicate username/email; 422 invalid fields |
| Login | `{"username":"new.agent","password":"example-password"}` | 200 `Session` | 401 invalid credentials; 422 invalid fields |
| Me | None | 200 `UserPublic` | 401 |
| Logout | None | 204, no body | 401 |

Validation: usernames are trimmed, case-insensitive unique, 3-32 ASCII
letters/digits/dots/underscores/hyphens; emails are trimmed, checked for a basic local@domain.tld shape, and
case-insensitive unique; passwords are 12-128 characters and are never trimmed.
Login uses the same username normalization. Account lookup checks case-insensitively; new usernames/emails are normalized
before storage. New accounts use random password salts.
Registration creates all mission progress rows atomically with the user.

## Mission and puzzle contract

MVP sequence is **mission orders 1 -> 2 -> 5**.
New players start with mission 1 available and the rest locked. Missions 3 and 4
stay visible as previews. Completing all puzzles in a mission unlocks the next
MVP mission. There are no hint deductions, time bonuses, or puzzle-order locks.
Demo progress is reconciled from solved puzzles on login and progress reads.

Mission summaries remain public. Mission detail requires bearer auth and
returns 403 for locked missions, including preview missions. A player's progress is always derived
from their token, never a client-supplied user ID.

`PlayerProgress` includes `score: integer` and `puzzles_solved: integer`.
Every `ProgressItem` includes `puzzles: PuzzleProgress[]`, where:

```text
PuzzleProgress = { puzzle_id: integer, solved: boolean, points_earned: integer }
```

`points_earned` is the best correct award for that puzzle, or zero. Return all
mission statuses, but return an empty puzzle progress list for locked missions.
Progress responses use UTC RFC 3339 timestamps ending in `Z`. Mission and puzzle metadata fields retain their original names.

### Start/resume mission

`POST /api/missions/{mission_id}/start` has no body. Return 200 with the extended
`ProgressItem`. An available mission becomes `in_progress`; starting an
in-progress or completed mission returns its current progress without resetting
anything. Return 401 for invalid authentication, 403 for locked/non-MVP missions,
404 for an unknown mission, and 422 for an invalid path ID.

### Submit answer

`POST /api/puzzles/{puzzle_id}/attempts` accepts only the following body. Mission 1 uses the coding endpoint below.

```json
{"answer":"the player's answer"}
```

The answer must be a string of 1-4096 characters and nonempty after trimming.
Normalize with the existing `strip().casefold()` hash helper. Require an
`in_progress` or `completed` parent mission; return 409 if an available mission
has not been started. A wrong answer is a successful request with
`is_correct: false`, not an HTTP error.

200 response shape:

```text
{
  attempt_id: integer,
  puzzle_id: integer,
  is_correct: boolean,
  already_solved: boolean,
  points_awarded: integer,
  total_score: integer,
  mission: ProgressItem,
  unlocked_mission_ids: integer[]
}
```

Here `mission` is the extended progress item. `already_solved` describes the
puzzle before this attempt. The first correct submission awards the puzzle's
configured points. Wrong or repeated submissions award zero additional points;
an incorrect retry never removes prior progress. `unlocked_mission_ids` lists
only missions newly unlocked by this request, otherwise `[]`.

Record the attempt and update completion/unlocks atomically. Completion happens
only when every puzzle in the mission is solved; set `completed_at` once and
preserve it on retries. A concurrent/retried correct answer must not duplicate
the effective award. Leaderboard aggregation must remain consistent with the
current best-per-puzzle scoring rule.

Expected errors: 401 unauthenticated, 403 locked/non-MVP parent mission, 404
unknown puzzle, 409 mission not started, 422 invalid answer/path/body. Reject
extra mutation fields such as `score`, `user_id`, or `is_correct` with 422.

## Errors and frontend behavior

Keep FastAPI's existing error convention for all routes:

```json
{"detail":"Human-readable error message"}
```

Validation errors use FastAPI's `{"detail":[...]}` shape with field locations and
messages. The frontend must handle both a string and an array; do not assume all
errors have the same detail type. Unexpected failures return a generic 500
without internal traces. Authentication failures use `WWW-Authenticate: Bearer`.

| Screen/action | Calls |
| --- | --- |
| Landing page | GET health + GET missions + GET leaderboard; show connection errors |
| Register | POST register, then show login |
| Login | POST login, then GET me/progress |
| Dashboard | GET missions + GET me/progress |
| Open/start/resume mission | POST mission/start, then GET mission detail |
| Submit puzzle | POST puzzle/code for Mission 1 or puzzle/attempts for later missions, then refresh me/progress |
| Leaderboard | GET leaderboard; refresh after scoring if visible |
| Logout | POST logout, clear token and private UI state |

Disable duplicate submission buttons while a request is pending. On a network
failure, refresh progress before assuming an answer was not saved. On 401,
clear the session and show login; on 403, refresh progress and explain the lock.
Use backend-provided correctness, status, and scores for all gameplay decisions.

## Coordinating changes

Keep schemas, backend tests, frontend calls, this document, and TODO statuses
in sync when changing a route. Keep optional features
(hints, timers, terminal, attempt-history APIs) outside this MVP contract until
their behavior is agreed.

## Mission 1 coding lessons

Mission details include a `lesson` object for each Mission 1 puzzle with its title,
concept, objective, explanation, starter expression, hints, and recap. Authenticated
puzzle progress includes a nullable `draft` field for the signed-in player.

Send `{"action":"save|run|submit","code":"..."}` to the coding endpoint with one
action from the list and up to 512 characters of source. Start the mission first
and solve earlier lessons in order. All three actions save the draft. Save returns
`{"saved":true}`. Run returns `passed`, `error`, and public test cases with inputs,
expected output, and actual output or an error. Submit also checks additional
cases on the server and returns the usual scoring result under `attempt`. Running
tests after completion allows practice without affecting score.

The interpreter accepts a small Python expression subset with lesson inputs,
text and Boolean literals, equality, and the predefined `decode64` and `lower`
functions. It evaluates the permitted syntax with fixed limits on source length
and expression size, without executing arbitrary Python.
