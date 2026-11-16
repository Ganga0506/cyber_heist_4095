# Cyber Heist API contract

This file is the shared frontend/backend reference. **Current** describes code
that exists. **Proposed** describes the next MVP implementation, not working
routes. Review proposed choices before implementing them. FastAPI's `/docs` and
`/openapi.json` describe only the currently implemented API.

## Connection and conventions

- Backend development URL: `http://127.0.0.1:8000`.
- Frontend uses relative `/api/...` URLs; Vite proxies them to the backend.
- JSON request bodies use `Content-Type: application/json`.
- IDs and points are integers; booleans are JSON booleans. Mission IDs must come
  from the API; do not assume they equal `mission_order`.
- Successful reads return 200. Current lists are unpaginated.
- Never send passwords in query strings or return passwords, password hashes,
  solutions, or solution hashes. Only registration accepts an email; proposed
  user responses below omit it.

## Endpoint inventory

| Method | Path | Status | Authentication | Frontend purpose |
| --- | --- | --- | --- | --- |
| GET | `/api/health` | Current | None | Connection check |
| GET | `/api/missions` | Current | None | Mission cards |
| GET | `/api/missions/{mission_id}` | Current | None | Metadata and puzzle instructions |
| GET | `/api/leaderboard` | Current | None | Leaderboard |
| GET | `/api/me/progress` | Current | Demo HTTP Basic | Saved mission statuses |
| POST | `/api/auth/register` | Proposed | None | Create account |
| POST | `/api/auth/login` | Proposed | None | Create session |
| GET | `/api/me` | Proposed | Bearer | Identify signed-in player |
| POST | `/api/auth/logout` | Proposed | Bearer | Revoke session |
| POST | `/api/missions/{mission_id}/start` | Proposed | Bearer | Start/resume mission |
| POST | `/api/puzzles/{puzzle_id}/attempts` | Proposed | Bearer | Submit answer |

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
  completed_at: datetime-string | null
}
PlayerProgress = { username: string, missions: ProgressItem[] }
```

| Read | 200 body | Details/errors |
| --- | --- | --- |
| Health | `{"status":"ok","database":"connected"}` | 503: `{"detail":"Database unavailable"}` |
| Missions | `MissionSummary[]` | Ordered by `mission_order`; empty list allowed |
| Mission detail | `MissionDetail` | Puzzles ordered by `puzzle_order`; 404: `{"detail":"Mission not found"}` |
| Leaderboard | `Leaderboard` | Score descending, username ascending for ties; ranks are sequential starting at 1 |
| My progress | `PlayerProgress` | Ordered by mission order; 401 for missing/invalid Basic credentials |

Current progress authentication is `Authorization: Basic <base64(username:password)>`
using README demo accounts. Invalid supplied credentials return
`{"detail":"Invalid username or password"}` and `WWW-Authenticate: Basic`.
Missing credentials are handled by FastAPI's HTTP Basic dependency.

Current scores sum each user's best correct points per puzzle; repeated correct
attempts do not add extra score. Current mission detail is public and does not
enforce locks. Current timestamps represent UTC but may lack an explicit timezone
suffix. Current CORS permits only local port-5173 origins, GET/OPTIONS, and
Authorization/Content-Type headers.

## Proposed authentication contract

Use an opaque bearer token with a 24-hour expiry, stored server-side as a hash
with user ID, expiration, and revocation state. This requires new session storage;
it is not in the existing five-table model. Login after refresh is acceptable for
the initial MVP: the frontend keeps the token in memory and game progress stays
in SQLite. A persistent browser session can be designed separately later.

Send `Authorization: Bearer <access_token>` on protected requests. Missing,
expired, revoked, or invalid tokens return 401. Logout revokes the token; the
frontend clears its local session even if the request fails. Switch
`GET /api/me/progress` from Basic to bearer in the same integration change.

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

Proposed validation: usernames are trimmed, case-insensitive unique, 3-32 ASCII
letters/digits/dots/underscores/hyphens; emails are trimmed, validated, and
case-insensitive unique; passwords are 12-128 characters and are never trimmed.
Login uses the same username normalization. Existing account lookup/uniqueness
must be migrated to honor these rules. Use random password salts for new users.
Registration creates all mission progress rows atomically with the user.

## Proposed mission and puzzle contract

Proposed MVP sequence is **mission orders 1 -> 2 -> 5**, subject to team agreement.
New players start with mission 1 available and the rest locked. Missions 3 and 4
stay visible as previews. Completing all puzzles in a mission unlocks the next
MVP mission. There are no hint deductions, time bonuses, or puzzle-order locks.
Existing demo progress must be reconciled with this rule before enforcing it.

Keep mission summaries public. Change mission detail to require bearer auth and
return 403 for locked missions, including preview missions. This is a deliberate
change from its current public behavior. A player's progress is always derived
from their token, never a client-supplied user ID.

Extend `PlayerProgress` with `score: integer` and `puzzles_solved: integer`.
Extend every `ProgressItem` with `puzzles: PuzzleProgress[]`, where:

```text
PuzzleProgress = { puzzle_id: integer, solved: boolean, points_earned: integer }
```

`points_earned` is the best correct award for that puzzle, or zero. Return all
mission statuses, but return an empty puzzle progress list for locked missions.
Use UTC RFC 3339 timestamps ending in `Z` for future responses. Keep the existing
mission and puzzle metadata fields unchanged.

### Start/resume mission

`POST /api/missions/{mission_id}/start` has no body. Return 200 with the extended
`ProgressItem`. An available mission becomes `in_progress`; starting an
in-progress or completed mission returns its current progress without resetting
anything. Return 401 for invalid authentication, 403 for locked/non-MVP missions,
404 for an unknown mission, and 422 for an invalid path ID.

### Submit answer

`POST /api/puzzles/{puzzle_id}/attempts` accepts only:

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

Keep FastAPI's existing error convention for current and proposed routes:

```json
{"detail":"Human-readable error message"}
```

Validation errors use FastAPI's `{"detail":[...]}` shape with field locations and
messages. The frontend must handle both a string and an array; do not assume all
errors have the same detail type. Unexpected failures return a generic 500
without internal traces. Proposed auth failures use `WWW-Authenticate: Bearer`.

| Screen/action | Calls |
| --- | --- |
| Landing page | GET missions; fallback is preview only |
| Register | POST register, then show login |
| Login | POST login, then GET me/progress |
| Dashboard | GET missions + GET me/progress |
| Open/start/resume mission | POST mission/start, then GET mission detail |
| Submit puzzle answer | POST puzzle/attempts, then refresh me/progress |
| Leaderboard | GET leaderboard; refresh after scoring if visible |
| Logout | POST logout, clear token and private UI state |

Disable duplicate submission buttons while a request is pending. On a network
failure, refresh progress before assuming an answer was not saved. On 401,
clear the session and show login; on 403, refresh progress and explain the lock.
Use backend-provided correctness, status, and scores for all gameplay decisions.

## Coordinating changes

Implement proposed schemas and backend behavior with tests, then wire the
frontend to them. Update this document and TODO statuses in the same change.
Update CORS to allow POST when introducing these routes. Keep optional features
(hints, timers, terminal, attempt-history APIs) outside this MVP contract until
their behavior is agreed.
