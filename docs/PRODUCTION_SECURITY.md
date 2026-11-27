# Production security and release checks

## Threat model

The public browser, API, identity callback, recovery email, and lesson inputs
cross separate trust boundaries. Treat every client value as untrusted.
Protect account credentials, session and recovery tokens, private drafts,
scores, and database backups. The game exposes public usernames and scores.

| Priority | Threat | Control |
| --- | --- | --- |
| Critical | Account takeover, callback replay, credential stuffing | Argon2id, breached-password corpus, rate limits, optional TOTP, one-time recovery links, Google state/nonce and PKCE, hashed bearer sessions |
| Critical | Injection or cross-account reads and score manipulation | Strict request schemas, bound queries, per-account authorization, server-authoritative scoring, restricted lesson expressions |
| High | Cross-site scripting, request forgery, or interception | React text rendering, CSP and TLS at the proxy, strict same-origin cookie exchange, secure temporary cookies |
| High | Availability loss or data exposure | Bounded requests and concurrent authentication, restricted service identities and egress, private verified backups, dependency scans, and operational alerts |

The application rate limiter is local to each process and IP-based. Distributed
traffic and multiple instances require limits at the edge. Argon2id is currently
configured for 64 MiB, three passes, and one lane. Measure login latency and
memory use under load on the deployment host. Browser bearer tokens are
in memory and remain exposed to any script that executes in the page origin.
Mailbox or Google account compromise can also compromise the corresponding
account. Google account recovery and MFA are managed by Google. Password
accounts can enroll an authenticator, and email password recovery preserves
an enrolled factor. Authenticator codes remain susceptible to phishing, and
players need a backup code if they lose the authenticator.
Never link an existing account from an email match alone. A future linking
flow must require fresh proof of control of both accounts.

The API has no URL-fetch, file-upload, or user-supplied filesystem endpoints.
Google requests use fixed provider URLs and disable redirects. SMTP and database
destinations are controlled by operator configuration. Keep Phase 8's broader
execution approval independent of these release criteria.

## Deploy and verify

1. Use a fresh dedicated database path with environment variables
   `CYBERHEIST_ENV=production`, `CYBERHEIST_PUBLIC_ORIGIN=https://game.example`,
   and an explicit persistent SQLite `DATABASE_URL`. Use a distinct service
   identity with read/write access to that database directory only. Production
   refuses an existing database with development account email addresses and
   seeds only mission content.
2. Give the API read-only access to a vetted, regularly refreshed
   `CYBERHEIST_BREACHED_PASSWORD_DB`. This SQLite file must contain
   `breached_passwords(digest TEXT PRIMARY KEY)` populated with uppercase
   SHA-1 digests from the corpus. SHA-1 is used for corpus lookup only. Store
   live password verifiers with Argon2id. Production startup and registration
   fail closed when the corpus is unavailable.
3. Configure an OAuth web client with the exact redirect URI
   `https://game.example/api/auth/google/callback`. Give the API
   `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` via secret storage and build
   React with `VITE_GOOGLE_SIGN_IN=1`. Verify a real sign-in, logout, state
   expiry, and account collision on staging. Provider verification follows
   [Google OpenID Connect](https://developers.google.com/identity/openid-connect/openid-connect).
4. For email recovery, configure `SMTP_HOST`, `SMTP_FROM`, `SMTP_USER`, and
   `SMTP_PASSWORD` with an implicit TLS SMTP service on port 465. Build React
   with `VITE_PASSWORD_RECOVERY=1`. Test actual delivery without link tracking,
   expiry, single use, and session revocation in staging.
   For optional MFA, set `CYBERHEIST_MFA_KEYS` to a Fernet key stored in the
   secret manager and build the frontend with `VITE_MFA=1`. Verify enrollment,
   replay rejection, and backup-code use in staging. The API accepts a
   comma-separated list of keys with the active key first for staged rotation.
   Retain previous keys in protected storage until affected enrollments are
   replaced, including for retained database snapshots.
5. Build and serve the production frontend at the same origin as the API.
   Set `CYBERHEIST_HOST` and `CYBERHEIST_WEB_ROOT` for the example
   `deploy/Caddyfile`. Run Uvicorn on loopback behind that proxy using
   `uvicorn main:app --host 127.0.0.1 --port 8000 --proxy-headers --forwarded-allow-ips 127.0.0.1 --no-access-log`.
   Restrict API ingress to the proxy. Avoid logging callback query strings,
   request bodies, cookies, or authorization headers at every layer. Test
   redirects, certificate renewal, CSP and HSTS on the frontend, and API
   origin restrictions through the actual proxy. Configure host-wide and
   edge limits before public exposure.
6. Gate releases on backend and browser tests and passing dependency and
   history scans. Verify the production configuration and run restore and
   incident drills in staging. Record the chosen data retention policy,
   alert owners, residual risks, and approval before opening public access.

## Data protection and incident response

- Keep secrets out of settings bundled into the browser. Rotate the Google
  and SMTP credentials through the provider and secret manager, then redeploy
  and verify sign-in or delivery. Restrict outbound access to approved provider
  destinations. Keep database and backup volumes encrypted and private.
- Use a private backup destination and copy a consistent snapshot with
  `python backend/snapshot.py /path/to/live.db /private/new-backup.db`.
  Restore to a fresh database path using the same command with the snapshot
  as source. The tool checks integrity and refuses to overwrite files.
  Periodically restore and verify sign-in, drafts, and scores using an
  isolated environment. Revoke all restored bearer sessions and discard
  pending Google and recovery transactions before promoting a restored copy.
- Define deletion windows for account data, backups, and logs before launch.
  Expire backups through the storage lifecycle policy, and include pending
  authentication transactions in database maintenance. Exclude player drafts
  and secrets from incident tickets.
- Route security events to restricted logging, then alert on bursts of
  rejected requests and authentication failures, missing password screening,
  or recovery delivery failures. Assign an on-call owner and test alert
  delivery. Aggregate allowed traffic and health at the edge without logging
  sensitive URLs or payloads.
- In an incident, disable the affected sign-in method or restrict service
  at the edge, revoke affected sessions, rotate exposed credentials, scope
  exposure using redacted events, restore from a verified snapshot if needed,
  and record the decision and evidence before reopening traffic.
