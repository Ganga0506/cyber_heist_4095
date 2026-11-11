-- Executable demo data for Cyber Heist.
-- This is a source script, not a dump of a live database.
-- It inserts the same fictional records as backend/seed.py.
-- Running it again does not add duplicate rows.
--
-- Demo passwords are development-only and are stored as
-- PBKDF2-HMAC-SHA256 hashes. See README.md.
-- Puzzle answers are stored only as SHA-256 hashes.

PRAGMA foreign_keys = ON;

-- Fictional demo players
INSERT INTO users (id, username, email, password_hash, created_at)
SELECT 1, 'nova.agent', 'nova.agent@example.com', 'pbkdf2_sha256$260000$devsalt-nova.agent$63b2bc1c7cdad6b282656596e45e17e68a0481866d31684bcb4760ecb5357509', '2026-02-01 09:00:00'
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'nova.agent');

INSERT INTO users (id, username, email, password_hash, created_at)
SELECT 2, 'pixel.fox', 'pixel.fox@example.com', 'pbkdf2_sha256$260000$devsalt-pixel.fox$dec37620139605f74570be89124db58272146c84128822c4de8eb8f866a9096a', '2026-02-01 09:15:00'
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'pixel.fox');

INSERT INTO users (id, username, email, password_hash, created_at)
SELECT 3, 'cipher.owl', 'cipher.owl@example.com', 'pbkdf2_sha256$260000$devsalt-cipher.owl$dcd21489c74a3899a7c2a03d9602e20bf94235ca1ea2b026038d44b3714b5c23', '2026-02-01 09:30:00'
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'cipher.owl');

INSERT INTO users (id, username, email, password_hash, created_at)
SELECT 4, 'byte.lynx', 'byte.lynx@example.com', 'pbkdf2_sha256$260000$devsalt-byte.lynx$5cd7f7629bdff3d46bbbe71d3c54d8f485d4c1b0b06e5dae9d741471af5b870d', '2026-02-01 09:45:00'
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'byte.lynx');

INSERT INTO users (id, username, email, password_hash, created_at)
SELECT 5, 'glitch.moth', 'glitch.moth@example.com', 'pbkdf2_sha256$260000$devsalt-glitch.moth$a80e51b926db5d6aeef9b74b5c69641e652316e94395d0b11d46c65825808552', '2026-02-01 10:00:00'
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'glitch.moth');

-- Five missions. is_mvp = 1 marks the first playable subset.
INSERT INTO missions (id, title, description, topic, mission_order, is_mvp, created_at)
SELECT 1, 'THE SETUP', 'Investigate fictional leaked files and hidden clues to locate the first access point. This mission introduces encoding and digital forensics.', 'Encoding and Digital Forensics', 1, 1, '2026-02-01 08:00:00'
WHERE NOT EXISTS (SELECT 1 FROM missions WHERE mission_order = 1);

INSERT INTO missions (id, title, description, topic, mission_order, is_mvp, created_at)
SELECT 2, 'THE PERIMETER', 'Explore a simulated network and read sample web traffic to discover an access key. This mission introduces networking and HTTP.', 'Networking and HTTP', 2, 1, '2026-02-01 08:00:00'
WHERE NOT EXISTS (SELECT 1 FROM missions WHERE mission_order = 2);

INSERT INTO missions (id, title, description, topic, mission_order, is_mvp, created_at)
SELECT 3, 'THE ENCRYPTION LAYER', 'Decode a short cipher and compare a hash prefix to recover a hidden word. This mission introduces cryptography and hashing. It is planned after the first MVP.', 'Cryptography and Hashing', 3, 0, '2026-02-01 08:00:00'
WHERE NOT EXISTS (SELECT 1 FROM missions WHERE mission_order = 3);

INSERT INTO missions (id, title, description, topic, mission_order, is_mvp, created_at)
SELECT 4, 'INSIDE THE SYSTEM', 'Read fictional program logic and a small access policy. This mission introduces code analysis and access control. It is planned after the first MVP.', 'Code Analysis and Access Control', 4, 0, '2026-02-01 08:00:00'
WHERE NOT EXISTS (SELECT 1 FROM missions WHERE mission_order = 4);

INSERT INTO missions (id, title, description, topic, mission_order, is_mvp, created_at)
SELECT 5, 'THE FINAL HEIST', 'Combine tokens from earlier missions in a fictional multi-stage vault puzzle. This mission ties the story together.', 'Integrated Cybersecurity Challenges', 5, 1, '2026-02-01 08:00:00'
WHERE NOT EXISTS (SELECT 1 FROM missions WHERE mission_order = 5);

-- Two demo puzzles for every mission.
INSERT INTO puzzles (id, mission_id, title, description, puzzle_type, instructions, solution_hash, points, puzzle_order)
SELECT 1, 1, 'Demo: Base64 Access Note', 'Demo puzzle. Decode one Base64 clue from a fictional note.', 'encoding', 'A fictional incident note contains this Base64 text: QUNDRVNTLVBPSU5ULUEx. Decode it and submit the plaintext exactly, using capital letters and hyphens.', '40bdad09932781c5305cb6d8320558de75dba3e20a2b6668540716d860377b26', 100, 1
WHERE NOT EXISTS (SELECT 1 FROM puzzles WHERE mission_id = 1 AND puzzle_order = 1);

INSERT INTO puzzles (id, mission_id, title, description, puzzle_type, instructions, solution_hash, points, puzzle_order)
SELECT 2, 1, 'Demo: Phishing Sign', 'Demo puzzle. Name the suspicious sign in one fictional message.', 'forensics', 'Fictional message, not a real email. From security@uconn-help.example. Subject: Mailbox expires tonight. The link host is uconn-help.example, which is not the real university site. Which label fits this sign? A) LOOKALIKE-DOMAIN B) ENCRYPTED-ATTACHMENT C) MISSING-SUBJECT. Submit the label only.', '4d88d8e149159dece508f9d4dbc460f362b6e2b366c87dc93fad34914c8341d1', 80, 2
WHERE NOT EXISTS (SELECT 1 FROM puzzles WHERE mission_id = 1 AND puzzle_order = 2);

INSERT INTO puzzles (id, mission_id, title, description, puzzle_type, instructions, solution_hash, points, puzzle_order)
SELECT 3, 2, 'Demo: Response Header', 'Demo puzzle. Read a simulated HTTP response from a fictional gate.', 'http', 'Simulated response only. No live server is contacted. Status line: HTTP/1.1 200 OK. Header: Content-Type: text/plain. Header: X-Access-Key: PERIM-KEY-17. Body: gate=closed. Submit the value of the X-Access-Key header.', '5403266dbe3d2f610f776ddb1e4bebc5a2e50ea7780c1d7446b0ce4e4b284d36', 100, 1
WHERE NOT EXISTS (SELECT 1 FROM puzzles WHERE mission_id = 2 AND puzzle_order = 1);

INSERT INTO puzzles (id, mission_id, title, description, puzzle_type, instructions, solution_hash, points, puzzle_order)
SELECT 4, 2, 'Demo: Request Log', 'Demo puzzle. Pick one line from a fictional request log.', 'networking', 'Simulated log from a fictional service: 10:01 GET /health 200; 10:02 GET /status 200; 10:03 POST /login 401. Which request returned 200 and was not the health check? Submit the method and path, for example POST /login.', '674ad8fb8ad950b3d2a352bbf210dc7e2c84d5bafaab46360574be50bb373907', 90, 2
WHERE NOT EXISTS (SELECT 1 FROM puzzles WHERE mission_id = 2 AND puzzle_order = 2);

INSERT INTO puzzles (id, mission_id, title, description, puzzle_type, instructions, solution_hash, points, puzzle_order)
SELECT 5, 3, 'Demo: Caesar Shift', 'Demo puzzle. Reverse a three-letter Caesar shift.', 'cryptography', 'The fictional ciphertext FDHVDU was shifted forward by 3 letters. Submit the original word in capital letters.', '203b8ade4aaee21728c5ecc2b53aadbe0cd25c7337c205da91f0686542ad3478', 100, 1
WHERE NOT EXISTS (SELECT 1 FROM puzzles WHERE mission_id = 3 AND puzzle_order = 1);

INSERT INTO puzzles (id, mission_id, title, description, puzzle_type, instructions, solution_hash, points, puzzle_order)
SELECT 6, 3, 'Demo: Hash Prefix', 'Demo puzzle. Match a short SHA-256 prefix to a candidate word.', 'hashing', 'A fictional vault label was hashed with SHA-256. The digest begins with e6f0a1fb. Candidates: lock, vault, key. Submit the matching word in lowercase. This compares a known prefix. It is not password cracking.', 'e6f0a1fbb43c89196dcfcbef85908f19ab4c5f7cc4f4c452284697757683d7ef', 120, 2
WHERE NOT EXISTS (SELECT 1 FROM puzzles WHERE mission_id = 3 AND puzzle_order = 2);

INSERT INTO puzzles (id, mission_id, title, description, puzzle_type, instructions, solution_hash, points, puzzle_order)
SELECT 7, 4, 'Demo: Read the Check', 'Demo puzzle. Read a fictional authentication function.', 'code-analysis', 'This function is fictional and does not protect a real account. def allow_entry(pin): grant access only when pin equals 2468. What PIN does the function accept? Submit the digits only.', 'a1fb4e703a9ef1fa4936801721ff285a97ac85330856674412e054892afe6972', 100, 1
WHERE NOT EXISTS (SELECT 1 FROM puzzles WHERE mission_id = 4 AND puzzle_order = 1);

INSERT INTO puzzles (id, mission_id, title, description, puzzle_type, instructions, solution_hash, points, puzzle_order)
SELECT 8, 4, 'Demo: Night Access Policy', 'Demo puzzle. Read a fictional access-control table.', 'access-control', 'Fictional policy. analyst: night access no. auditor: night access yes. guest: night access no. Which role is allowed night access? Submit the role name in lowercase.', 'c5a62ce3fa7f6d86af0009389ccd815277691ea64da0c5c98e302bb13dd59248', 90, 2
WHERE NOT EXISTS (SELECT 1 FROM puzzles WHERE mission_id = 4 AND puzzle_order = 2);

INSERT INTO puzzles (id, mission_id, title, description, puzzle_type, instructions, solution_hash, points, puzzle_order)
SELECT 9, 5, 'Demo: Join the Tokens', 'Demo puzzle. Combine two tokens from earlier demo puzzles.', 'integrated', 'Take the plaintext from the Base64 access note and the X-Access-Key value from the simulated HTTP response. Join them with one hyphen, access note first. Example shape: FIRST-TOKEN-SECOND-TOKEN. The vault is fictional.', '5741c210c99a114ead22fd335123337edb8b867c4fa25ce65ac6401578094b99', 150, 1
WHERE NOT EXISTS (SELECT 1 FROM puzzles WHERE mission_id = 5 AND puzzle_order = 1);

INSERT INTO puzzles (id, mission_id, title, description, puzzle_type, instructions, solution_hash, points, puzzle_order)
SELECT 10, 5, 'Demo: Careful Response', 'Demo puzzle. Choose a defensive order for a fictional incident.', 'integrated', 'A fictional lab machine shows unexpected files. Which label is the careful defensive order? A) ISOLATE-PRESERVE-REPORT B) DELETE-EVERYTHING-FIRST C) IGNORE-AND-CONTINUE. Submit the chosen label.', 'fc4831346e612deb173ee1567717343aecf4db92b1e6e09b3f65993cf28fcbb0', 150, 2
WHERE NOT EXISTS (SELECT 1 FROM puzzles WHERE mission_id = 5 AND puzzle_order = 2);

-- Sample progress. These statuses are hand-written snapshots.
-- They are not produced by a finished unlock rule.
-- One sample follows mission order. Another leaves missions 3 and 4
-- locked while mission 5 is in progress. The team still needs to
-- choose the real rule.
INSERT INTO user_progress (user_id, mission_id, status, completed_at)
SELECT 1, 1, 'completed', '2026-03-01 10:10:00'
WHERE NOT EXISTS (SELECT 1 FROM user_progress WHERE user_id = 1 AND mission_id = 1);

INSERT INTO user_progress (user_id, mission_id, status, completed_at)
SELECT 1, 2, 'in_progress', NULL
WHERE NOT EXISTS (SELECT 1 FROM user_progress WHERE user_id = 1 AND mission_id = 2);

INSERT INTO user_progress (user_id, mission_id, status, completed_at)
SELECT 1, 3, 'locked', NULL
WHERE NOT EXISTS (SELECT 1 FROM user_progress WHERE user_id = 1 AND mission_id = 3);

INSERT INTO user_progress (user_id, mission_id, status, completed_at)
SELECT 1, 4, 'locked', NULL
WHERE NOT EXISTS (SELECT 1 FROM user_progress WHERE user_id = 1 AND mission_id = 4);

INSERT INTO user_progress (user_id, mission_id, status, completed_at)
SELECT 1, 5, 'locked', NULL
WHERE NOT EXISTS (SELECT 1 FROM user_progress WHERE user_id = 1 AND mission_id = 5);

INSERT INTO user_progress (user_id, mission_id, status, completed_at)
SELECT 2, 1, 'completed', '2026-03-02 09:20:00'
WHERE NOT EXISTS (SELECT 1 FROM user_progress WHERE user_id = 2 AND mission_id = 1);

INSERT INTO user_progress (user_id, mission_id, status, completed_at)
SELECT 2, 2, 'completed', '2026-03-02 10:30:00'
WHERE NOT EXISTS (SELECT 1 FROM user_progress WHERE user_id = 2 AND mission_id = 2);

INSERT INTO user_progress (user_id, mission_id, status, completed_at)
SELECT 2, 3, 'available', NULL
WHERE NOT EXISTS (SELECT 1 FROM user_progress WHERE user_id = 2 AND mission_id = 3);

INSERT INTO user_progress (user_id, mission_id, status, completed_at)
SELECT 2, 4, 'locked', NULL
WHERE NOT EXISTS (SELECT 1 FROM user_progress WHERE user_id = 2 AND mission_id = 4);

INSERT INTO user_progress (user_id, mission_id, status, completed_at)
SELECT 2, 5, 'locked', NULL
WHERE NOT EXISTS (SELECT 1 FROM user_progress WHERE user_id = 2 AND mission_id = 5);

INSERT INTO user_progress (user_id, mission_id, status, completed_at)
SELECT 3, 1, 'available', NULL
WHERE NOT EXISTS (SELECT 1 FROM user_progress WHERE user_id = 3 AND mission_id = 1);

INSERT INTO user_progress (user_id, mission_id, status, completed_at)
SELECT 3, 2, 'locked', NULL
WHERE NOT EXISTS (SELECT 1 FROM user_progress WHERE user_id = 3 AND mission_id = 2);

INSERT INTO user_progress (user_id, mission_id, status, completed_at)
SELECT 3, 3, 'locked', NULL
WHERE NOT EXISTS (SELECT 1 FROM user_progress WHERE user_id = 3 AND mission_id = 3);

INSERT INTO user_progress (user_id, mission_id, status, completed_at)
SELECT 3, 4, 'locked', NULL
WHERE NOT EXISTS (SELECT 1 FROM user_progress WHERE user_id = 3 AND mission_id = 4);

INSERT INTO user_progress (user_id, mission_id, status, completed_at)
SELECT 3, 5, 'locked', NULL
WHERE NOT EXISTS (SELECT 1 FROM user_progress WHERE user_id = 3 AND mission_id = 5);

INSERT INTO user_progress (user_id, mission_id, status, completed_at)
SELECT 4, 1, 'in_progress', NULL
WHERE NOT EXISTS (SELECT 1 FROM user_progress WHERE user_id = 4 AND mission_id = 1);

INSERT INTO user_progress (user_id, mission_id, status, completed_at)
SELECT 4, 2, 'locked', NULL
WHERE NOT EXISTS (SELECT 1 FROM user_progress WHERE user_id = 4 AND mission_id = 2);

INSERT INTO user_progress (user_id, mission_id, status, completed_at)
SELECT 4, 3, 'locked', NULL
WHERE NOT EXISTS (SELECT 1 FROM user_progress WHERE user_id = 4 AND mission_id = 3);

INSERT INTO user_progress (user_id, mission_id, status, completed_at)
SELECT 4, 4, 'locked', NULL
WHERE NOT EXISTS (SELECT 1 FROM user_progress WHERE user_id = 4 AND mission_id = 4);

INSERT INTO user_progress (user_id, mission_id, status, completed_at)
SELECT 4, 5, 'locked', NULL
WHERE NOT EXISTS (SELECT 1 FROM user_progress WHERE user_id = 4 AND mission_id = 5);

INSERT INTO user_progress (user_id, mission_id, status, completed_at)
SELECT 5, 1, 'completed', '2026-03-05 08:25:00'
WHERE NOT EXISTS (SELECT 1 FROM user_progress WHERE user_id = 5 AND mission_id = 1);

INSERT INTO user_progress (user_id, mission_id, status, completed_at)
SELECT 5, 2, 'completed', '2026-03-05 08:40:00'
WHERE NOT EXISTS (SELECT 1 FROM user_progress WHERE user_id = 5 AND mission_id = 2);

INSERT INTO user_progress (user_id, mission_id, status, completed_at)
SELECT 5, 3, 'locked', NULL
WHERE NOT EXISTS (SELECT 1 FROM user_progress WHERE user_id = 5 AND mission_id = 3);

INSERT INTO user_progress (user_id, mission_id, status, completed_at)
SELECT 5, 4, 'locked', NULL
WHERE NOT EXISTS (SELECT 1 FROM user_progress WHERE user_id = 5 AND mission_id = 4);

INSERT INTO user_progress (user_id, mission_id, status, completed_at)
SELECT 5, 5, 'in_progress', NULL
WHERE NOT EXISTS (SELECT 1 FROM user_progress WHERE user_id = 5 AND mission_id = 5);

-- Sample attempts. Player 1 submits a correct answer for puzzle 1 twice.
-- Leaderboard scoring keeps the best correct attempt per puzzle.
INSERT INTO puzzle_attempts (user_id, puzzle_id, is_correct, points_earned, attempted_at)
SELECT 1, 1, 1, 100, '2026-03-01 10:00:00'
WHERE NOT EXISTS (SELECT 1 FROM puzzle_attempts WHERE user_id = 1 AND puzzle_id = 1 AND attempted_at = '2026-03-01 10:00:00');

INSERT INTO puzzle_attempts (user_id, puzzle_id, is_correct, points_earned, attempted_at)
SELECT 1, 1, 1, 100, '2026-03-01 10:05:00'
WHERE NOT EXISTS (SELECT 1 FROM puzzle_attempts WHERE user_id = 1 AND puzzle_id = 1 AND attempted_at = '2026-03-01 10:05:00');

INSERT INTO puzzle_attempts (user_id, puzzle_id, is_correct, points_earned, attempted_at)
SELECT 1, 2, 1, 80, '2026-03-01 10:10:00'
WHERE NOT EXISTS (SELECT 1 FROM puzzle_attempts WHERE user_id = 1 AND puzzle_id = 2 AND attempted_at = '2026-03-01 10:10:00');

INSERT INTO puzzle_attempts (user_id, puzzle_id, is_correct, points_earned, attempted_at)
SELECT 1, 3, 0, 0, '2026-03-01 11:00:00'
WHERE NOT EXISTS (SELECT 1 FROM puzzle_attempts WHERE user_id = 1 AND puzzle_id = 3 AND attempted_at = '2026-03-01 11:00:00');

INSERT INTO puzzle_attempts (user_id, puzzle_id, is_correct, points_earned, attempted_at)
SELECT 1, 3, 1, 100, '2026-03-01 11:06:00'
WHERE NOT EXISTS (SELECT 1 FROM puzzle_attempts WHERE user_id = 1 AND puzzle_id = 3 AND attempted_at = '2026-03-01 11:06:00');

INSERT INTO puzzle_attempts (user_id, puzzle_id, is_correct, points_earned, attempted_at)
SELECT 2, 1, 1, 100, '2026-03-02 09:00:00'
WHERE NOT EXISTS (SELECT 1 FROM puzzle_attempts WHERE user_id = 2 AND puzzle_id = 1 AND attempted_at = '2026-03-02 09:00:00');

INSERT INTO puzzle_attempts (user_id, puzzle_id, is_correct, points_earned, attempted_at)
SELECT 2, 2, 1, 80, '2026-03-02 09:20:00'
WHERE NOT EXISTS (SELECT 1 FROM puzzle_attempts WHERE user_id = 2 AND puzzle_id = 2 AND attempted_at = '2026-03-02 09:20:00');

INSERT INTO puzzle_attempts (user_id, puzzle_id, is_correct, points_earned, attempted_at)
SELECT 2, 3, 1, 100, '2026-03-02 10:00:00'
WHERE NOT EXISTS (SELECT 1 FROM puzzle_attempts WHERE user_id = 2 AND puzzle_id = 3 AND attempted_at = '2026-03-02 10:00:00');

INSERT INTO puzzle_attempts (user_id, puzzle_id, is_correct, points_earned, attempted_at)
SELECT 2, 4, 1, 90, '2026-03-02 10:30:00'
WHERE NOT EXISTS (SELECT 1 FROM puzzle_attempts WHERE user_id = 2 AND puzzle_id = 4 AND attempted_at = '2026-03-02 10:30:00');

INSERT INTO puzzle_attempts (user_id, puzzle_id, is_correct, points_earned, attempted_at)
SELECT 3, 1, 0, 0, '2026-03-03 12:00:00'
WHERE NOT EXISTS (SELECT 1 FROM puzzle_attempts WHERE user_id = 3 AND puzzle_id = 1 AND attempted_at = '2026-03-03 12:00:00');

INSERT INTO puzzle_attempts (user_id, puzzle_id, is_correct, points_earned, attempted_at)
SELECT 4, 1, 0, 0, '2026-03-04 15:00:00'
WHERE NOT EXISTS (SELECT 1 FROM puzzle_attempts WHERE user_id = 4 AND puzzle_id = 1 AND attempted_at = '2026-03-04 15:00:00');

INSERT INTO puzzle_attempts (user_id, puzzle_id, is_correct, points_earned, attempted_at)
SELECT 4, 2, 0, 0, '2026-03-04 15:12:00'
WHERE NOT EXISTS (SELECT 1 FROM puzzle_attempts WHERE user_id = 4 AND puzzle_id = 2 AND attempted_at = '2026-03-04 15:12:00');

INSERT INTO puzzle_attempts (user_id, puzzle_id, is_correct, points_earned, attempted_at)
SELECT 5, 1, 1, 100, '2026-03-05 08:00:00'
WHERE NOT EXISTS (SELECT 1 FROM puzzle_attempts WHERE user_id = 5 AND puzzle_id = 1 AND attempted_at = '2026-03-05 08:00:00');

INSERT INTO puzzle_attempts (user_id, puzzle_id, is_correct, points_earned, attempted_at)
SELECT 5, 2, 1, 80, '2026-03-05 08:25:00'
WHERE NOT EXISTS (SELECT 1 FROM puzzle_attempts WHERE user_id = 5 AND puzzle_id = 2 AND attempted_at = '2026-03-05 08:25:00');

INSERT INTO puzzle_attempts (user_id, puzzle_id, is_correct, points_earned, attempted_at)
SELECT 5, 3, 1, 100, '2026-03-05 08:40:00'
WHERE NOT EXISTS (SELECT 1 FROM puzzle_attempts WHERE user_id = 5 AND puzzle_id = 3 AND attempted_at = '2026-03-05 08:40:00');

INSERT INTO puzzle_attempts (user_id, puzzle_id, is_correct, points_earned, attempted_at)
SELECT 5, 9, 1, 150, '2026-03-05 09:10:00'
WHERE NOT EXISTS (SELECT 1 FROM puzzle_attempts WHERE user_id = 5 AND puzzle_id = 9 AND attempted_at = '2026-03-05 09:10:00');
