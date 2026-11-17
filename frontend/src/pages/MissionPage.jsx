import { useEffect, useState } from "react";
import { api } from "../api";
export function MissionPage({
  id,
  token,
  progress,
  busy,
  perform,
  refresh,
  setNotice,
}) {
  const [mission, setMission] = useState(null),
    [loading, setLoading] = useState(true),
    [selected, setSelected] = useState(0),
    [answers, setAnswers] = useState({}),
    [feedback, setFeedback] = useState({});
  const saved = progress?.missions.find((m) => m.mission_id === id);
  async function load() {
    setLoading(true);
    await perform(async () => {
      await api(`/missions/${id}/start`, { token, method: "POST" });
      const detail = await api(`/missions/${id}`, { token });
      await refresh(token);
      setMission(detail);
    });
    setLoading(false);
  }
  useEffect(() => {
    if (token) load();
    else setLoading(false);
  }, [id, token]);
  if (!token)
    return (
      <section className="empty panel">
        <p className="eyebrow">AGENT ACCESS REQUIRED</p>
        <h1>Identify yourself, agent.</h1>
        <p>Log in to start this mission or resume saved progress.</p>
        <a className="button primary" href="#/login">
          Log in ↗
        </a>
      </section>
    );
  if (loading)
    return (
      <div className="empty panel" role="status">
        Retrieving mission briefing…
      </div>
    );
  if (!mission)
    return (
      <section className="empty panel">
        <h1>Mission unavailable</h1>
        <p>
          Complete the previous mission to unlock access. Missions 3 and 4 are
          coming soon.
        </p>
        <div className="actions">
          <a className="button" href="#/">
            Back to missions
          </a>
          <button disabled={busy} onClick={load}>
            Retry briefing
          </button>
        </div>
      </section>
    );
  const puzzle = mission.puzzles[selected],
    solved = saved?.puzzles.find((p) => p.puzzle_id === puzzle?.id)?.solved,
    complete = saved?.status === "completed";
  async function submit(e) {
    e.preventDefault();
    await perform(async () => {
      const result = await api(`/puzzles/${puzzle.id}/attempts`, {
        token,
        method: "POST",
        body: { answer: answers[puzzle.id] || "" },
      });
      setFeedback((old) => ({
        ...old,
        [puzzle.id]: {
          correct: result.is_correct,
          text: result.is_correct
            ? result.already_solved
              ? "Already solved. Your points are safely recorded."
              : `Access granted. +${result.points_awarded} points earned.`
            : "Access denied. Take another look at the clues and try again.",
        },
      }));
      if (result.mission.status === "completed")
        setNotice(
          result.unlocked_mission_ids.length
            ? "Mission complete. Your next mission is now unlocked."
            : "Operation complete. You cracked the final vault!",
        );
      await refresh(token);
    });
  }
  return (
    <>
      <a className="back-link" href="#/">
        ← Back to mission control
      </a>
      <div className="page-heading">
        <div>
          <p className="eyebrow">
            MISSION {String(mission.mission_order).padStart(2, "0")} /{" "}
            {mission.topic}
          </p>
          <h1>{mission.title}</h1>
          <p>{mission.description}</p>
        </div>
        <span className={`badge ${complete ? "success" : ""}`}>
          {complete ? "Completed" : "In progress"}
        </span>
      </div>
      {complete && (
        <div className="completion panel">
          <div>
            <h2>Mission accomplished.</h2>
            <p>
              All puzzle answers and points are saved. Ready for your next move?
            </p>
          </div>
          <a className="button primary" href="#/">
            Continue operation ↗
          </a>
        </div>
      )}
      <div className="play-layout">
        <aside className="panel puzzle-nav">
          <p className="eyebrow">MISSION OBJECTIVES</p>
          {mission.puzzles.map((p, i) => (
            <button
              key={p.id}
              aria-current={selected === i ? "step" : undefined}
              onClick={() => setSelected(i)}
            >
              <span className="objective-number">
                {saved?.puzzles.find((s) => s.puzzle_id === p.id)?.solved
                  ? "✓"
                  : `0${i + 1}`}
              </span>
              <span>
                {p.title}
                <small>{p.points} points</small>
              </span>
            </button>
          ))}
          <p className="save-note">
            Progress saves after every answer. You can leave and return any
            time.
          </p>
        </aside>
        {puzzle ? (
          <article className="panel puzzle-panel" key={puzzle.id}>
            <div className="card-top">
              <span className="eyebrow">
                PUZZLE {selected + 1} OF {mission.puzzles.length}
              </span>
              <span className="badge">{puzzle.points} PTS</span>
            </div>
            <h2>{puzzle.title}</h2>
            <p>{puzzle.description}</p>
            <div className="evidence">
              <div>
                <span className="terminal-dots" aria-hidden="true">
                  ● ● ●
                </span>{" "}
                EVIDENCE / BRIEFING
              </div>
              <pre>{puzzle.instructions}</pre>
            </div>
            {solved ? (
              <div className="solved-message" role="status">
                ✓ Puzzle solved. Your points have been recorded.
              </div>
            ) : (
              <form onSubmit={submit} aria-busy={busy}>
                <label htmlFor="answer">Submit your answer</label>
                <p id="answer-help" className="muted">
                  Use the briefing above to find the answer. Capitalization and
                  surrounding spaces don’t matter.
                </p>
                <input
                  id="answer"
                  value={answers[puzzle.id] || ""}
                  onChange={(e) =>
                    setAnswers((old) => ({
                      ...old,
                      [puzzle.id]: e.target.value,
                    }))
                  }
                  required
                  maxLength={4096}
                  autoComplete="off"
                  spellCheck={false}
                  placeholder="Enter the decoded answer…"
                  aria-describedby="answer-help"
                />
                <button
                  className="primary"
                  disabled={busy || !answers[puzzle.id]?.trim()}
                >
                  {busy ? "Checking…" : "Check answer"} ↗
                </button>
              </form>
            )}
            {feedback[puzzle.id] && (
              <p
                className={`answer-feedback ${feedback[puzzle.id].correct ? "correct" : "incorrect"}`}
                role="status"
              >
                {feedback[puzzle.id].text}
              </p>
            )}
            {solved && selected < mission.puzzles.length - 1 && (
              <button
                className="primary"
                onClick={() => setSelected(selected + 1)}
              >
                Next puzzle →
              </button>
            )}
          </article>
        ) : (
          <div className="empty panel">
            No puzzles are available for this mission.
          </div>
        )}
      </div>
    </>
  );
}
