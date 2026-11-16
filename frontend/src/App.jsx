import { useEffect, useState } from "react";
import { api } from "./api";
import "./App.css";

export default function App() {
  const [missions, setMissions] = useState([]);
  const [leaders, setLeaders] = useState([]);
  const [session, setSession] = useState(null);
  const [progress, setProgress] = useState(null);
  const [mission, setMission] = useState(null);
  const [answers, setAnswers] = useState({});
  const [feedback, setFeedback] = useState({});
  const [register, setRegister] = useState(false);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [online, setOnline] = useState(false);
  const token = session?.access_token;

  function clearSession() {
    setSession(null); setProgress(null); setMission(null); setAnswers({}); setFeedback({});
  }
  async function refresh(accessToken) {
    const [list, scores, health, saved] = await Promise.all([
      api("/missions"), api("/leaderboard"), api("/health"),
      accessToken ? api("/me/progress", { token: accessToken }) : Promise.resolve(null),
    ]);
    setMissions(list); setLeaders(scores.entries); setOnline(health.status === "ok"); setProgress(saved);
  }
  useEffect(() => {
    let active = true;
    Promise.all([api("/missions"), api("/leaderboard"), api("/health")])
      .then(([list, scores, health]) => {
        if (active) { setMissions(list); setLeaders(scores.entries); setOnline(health.status === "ok"); }
      }).catch(() => { if (active) setError("Cannot reach the API. Run python start.py, then click Refresh data."); });
    return () => { active = false; };
  }, []);
  async function perform(action) {
    setBusy(true); setError(""); setNotice("");
    try { await action(); }
    catch (err) {
      if (err.status === 401 && token) clearSession();
      if (!err.status) setOnline(false);
      setError(err.message === "Failed to fetch" ? "Cannot reach the API. Check both servers are running." : err.message);
    } finally { setBusy(false); }
  }
  function authenticate(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const fields = Object.fromEntries(new FormData(form));
    perform(async () => {
      if (register) {
        await api("/auth/register", { method: "POST", body: fields });
        setRegister(false); setNotice("Account created. Log in with your new credentials."); form.reset();
      } else {
        const result = await api("/auth/login", { method: "POST", body: fields });
        setSession(result);
        await api("/me", { token: result.access_token });
        await refresh(result.access_token);
        setNotice(`Welcome, ${result.user.username}. Your progress is saved on the server.`);
      }
    });
  }
  function openMission(id) {
    perform(async () => {
      await api(`/missions/${id}/start`, { token, method: "POST" });
      setMission(await api(`/missions/${id}`, { token }));
      setAnswers({}); setFeedback({}); await refresh(token);
    });
  }
  function submit(event, puzzle) {
    event.preventDefault();
    perform(async () => {
      try {
        const result = await api(`/puzzles/${puzzle.id}/attempts`, {
          token, method: "POST", body: { answer: answers[puzzle.id] || "" },
        });
        setFeedback((old) => ({ ...old, [puzzle.id]: result.is_correct
          ? `Correct! +${result.points_awarded} points${result.already_solved ? " (already solved)" : ""}.`
          : "Incorrect. Review the clues and try again." }));
        if (result.mission.status === "completed") setNotice("Mission complete! Check the dashboard for your next mission.");
      } finally { await refresh(token); }
    });
  }
  return <div className="page">
    <header className="hero">
      <p className="eyebrow">CSE 4095 · Team 5 · Live prototype</p><h1>CYBER HEIST</h1>
      <p className="subtitle">Interactive Hacking Puzzle Game</p>
      <p className="intro">Investigate fictional clues, solve puzzles, and unlock the vault. All systems are simulated.</p>
      <div className="toolbar"><span className="badge">API {online ? "connected" : "not connected"}</span>
        <button disabled={busy} onClick={() => perform(() => refresh(token))}>Refresh data</button>
        {session && <><span>{session.user.username} · {progress?.score ?? 0} points · {progress?.puzzles_solved ?? 0} solved</span>
          <button disabled={busy} onClick={() => perform(async () => {
            try { await api("/auth/logout", { token, method: "POST" }); } finally { clearSession(); }
          })}>Log out</button></>}
      </div>
    </header>
    {error && <p className="notice error" role="alert">{error}</p>}
    {notice && <p className="notice" role="status">{notice}</p>}
    {busy && <p role="status">Working…</p>}
    {!session && <section className="card auth-panel" aria-labelledby="auth-heading">
      <h2 id="auth-heading">{register ? "Create an agent account" : "Agent login"}</h2>
      <p>Demo: <strong>nova.agent</strong> / <strong>dev-only-nova</strong>. Register to start fresh.</p>
      <form onSubmit={authenticate}>
        <label>Username<input name="username" required minLength={register ? 3 : 1} maxLength={32} autoComplete="username" /></label>
        {register && <label>Email<input name="email" type="email" required maxLength={254} autoComplete="email" /></label>}
        <label>Password<input name="password" type="password" required minLength={register ? 12 : 1} maxLength={128} autoComplete={register ? "new-password" : "current-password"} /></label>
        {register && <p>Username: 3–32 letters, digits, dots, underscores or hyphens. Password: at least 12 characters.</p>}
        <button className="start-button" disabled={busy}>{register ? "Register" : "Log in"}</button>
        <button type="button" disabled={busy} onClick={() => { setRegister(!register); setError(""); }}>{register ? "Back to login" : "Create account"}</button>
      </form>
    </section>}
    <main>
      <div className="section-heading"><h2>Mission dashboard</h2>
        <p>MVP path: The Setup → The Perimeter → The Final Heist. Missions 3 and 4 are previews.</p>
        {!session && <p>Log in to start or resume a mission.</p>}
      </div>
      {!missions.length && <p>No missions loaded. Check the API connection and refresh.</p>}
      <div className="grid">{missions.map((item) => {
        const saved = progress?.missions.find((m) => m.mission_id === item.id);
        return <article key={item.id} className={`card ${item.is_mvp ? "mvp" : ""}`}>
          <p className="order">Mission {item.mission_order}</p><h3>{item.title}</h3>
          <p>{item.description}</p><p className="topic">{item.topic}</p>
          <div className="card-footer"><span className="badge">{!item.is_mvp ? "Later preview" : saved?.status || "Login required"}</span>
            <span>{saved?.puzzles.filter((p) => p.solved).length ?? 0}/{item.puzzle_count} solved</span></div>
          <button disabled={busy || !saved || saved.status === "locked"} onClick={() => openMission(item.id)}>
            {saved?.status === "completed" ? "Review" : saved?.status === "in_progress" ? "Resume" : "Start mission"}
          </button>
        </article>;
      })}</div>
      {mission && <section className="mission-play" aria-labelledby="mission-title">
        <div className="toolbar"><h2 id="mission-title">{mission.title}</h2><button disabled={busy} onClick={() => setMission(null)}>Close mission</button></div>
        <p>{mission.description}</p>
        {mission.puzzles.map((puzzle) => {
          const saved = progress?.missions.find((m) => m.mission_id === mission.id)?.puzzles.find((p) => p.puzzle_id === puzzle.id);
          return <article className="card puzzle" key={puzzle.id}>
            <h3>{puzzle.puzzle_order}. {puzzle.title}</h3><span>{puzzle.points} points · {saved?.solved ? "Solved" : "Unsolved"}</span>
            <p>{puzzle.description}</p><pre className="instructions">{puzzle.instructions}</pre>
            <form onSubmit={(event) => submit(event, puzzle)}>
              <label>Your answer<input required maxLength={4096} value={answers[puzzle.id] || ""} onChange={(event) => setAnswers({ ...answers, [puzzle.id]: event.target.value })} /></label>
              <button disabled={busy || !answers[puzzle.id]?.trim()}>Check answer</button>
            </form>
            {feedback[puzzle.id] && <p role="status" className="source">{feedback[puzzle.id]}</p>}
          </article>;
        })}
      </section>}
      <section className="section-heading"><h2>Leaderboard</h2>
        <div className="table-wrap"><table><thead><tr><th>Rank</th><th>Agent</th><th>Score</th><th>Solved</th></tr></thead>
          <tbody>{leaders.map((row) => <tr key={row.username}><td>{row.rank}</td><td>{row.username}</td><td>{row.score}</td><td>{row.puzzles_solved}</td></tr>)}</tbody>
        </table></div>{!leaders.length && <p>No leaderboard entries loaded.</p>}
      </section>
    </main>
    <footer>Progress is saved in SQLite. Sessions last 24 hours; refresh the browser and log in again to resume.</footer>
  </div>;
}
