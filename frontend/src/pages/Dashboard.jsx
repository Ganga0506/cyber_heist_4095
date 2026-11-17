import { useState } from "react";
import { MissionMap } from "../components/MissionMap";
export function Dashboard({ missions, progress, session, loading }) {
  const completed =
    progress?.missions.filter((m) => m.status === "completed").length || 0;
  const next = missions.find((m) =>
    progress?.missions.some(
      (p) =>
        p.mission_id === m.id &&
        ["available", "in_progress"].includes(p.status),
    ),
  );
  const [selectedId, setSelectedId] = useState(null);
  const selected =
    missions.find((m) => m.id === (selectedId ?? next?.id)) || missions[0];
  const saved = progress?.missions.find((m) => m.mission_id === selected?.id);
  const playable = selected?.is_mvp && saved && saved.status !== "locked";
  const solved = saved?.puzzles.filter((p) => p.solved).length || 0;
  return (
    <>
      <div className="page-heading map-heading">
        <div>
          <p className="eyebrow">CHAPTER 01 / THE SILENT CITY</p>
          <h1>
            Mission control<span className="accent">.</span>
          </h1>
          <p>
            Choose a location. Follow the trail. Find your way to the vault.
          </p>
        </div>
        <a
          className="button primary"
          href={next ? `#/missions/${next.id}` : "#/leaderboard"}
        >
          {next ? "Continue operation" : "View your ranking"} ↗
        </a>
      </div>
      <section className="map-status" aria-label="Your operation statistics">
        <span>
          <strong>{session.user.username}</strong> / AGENT
        </span>
        <span>
          <strong>{progress?.score ?? 0}</strong> points
        </span>
        <span>
          <strong>{completed} / 3</strong> territories cleared
        </span>
        <span>
          <strong>{progress?.puzzles_solved ?? 0} / 6</strong> puzzles solved
        </span>
      </section>
      {loading ? (
        <div className="empty panel" role="status">
          Charting your route…
        </div>
      ) : !missions.length ? (
        <div className="empty panel">
          <h2>Map unavailable</h2>
          <p>Reconnect to retrieve your operation.</p>
        </div>
      ) : (
        <div className="map-layout">
          <MissionMap
            missions={missions}
            progress={progress}
            selectedId={selected?.id}
            onSelect={setSelectedId}
          />
          <aside
            className="panel location-detail"
            aria-label="Selected location"
            aria-live="polite"
            aria-atomic="true"
          >
            <p className="eyebrow">
              LOCATION {String(selected.mission_order).padStart(2, "0")}
            </p>
            <div
              className={`location-emblem ${playable ? "unlocked" : ""}`}
              aria-hidden="true"
            >
              {saved?.status === "completed"
                ? "✓"
                : selected.id === 5
                  ? "♜"
                  : "◇"}
            </div>
            <span
              className={`badge ${saved?.status === "completed" ? "success" : ""}`}
            >
              {!selected.is_mvp
                ? "Uncharted territory"
                : saved?.status?.replaceAll("_", " ") || "Loading"}
            </span>
            <h2>{selected.title}</h2>
            <p>{selected.description}</p>
            <p className="detail-topic">{selected.topic}</p>
            <div className="mission-progress">
              <span>
                {solved} / {selected.puzzle_count} puzzles solved
              </span>
            </div>
            <progress
              aria-label={`${selected.title} progress`}
              value={solved}
              max={selected.puzzle_count || 1}
            />
            {playable ? (
              <a className="button primary" href={`#/missions/${selected.id}`}>
                {saved.status === "completed"
                  ? "Revisit location"
                  : saved.status === "in_progress"
                    ? "Resume mission"
                    : "Enter mission"}{" "}
                ↗
              </a>
            ) : (
              <p className="lock-explanation">
                {!selected.is_mvp
                  ? "This district is coming in a future chapter. Your current route follows locations 01 → 02 → 05."
                  : `Clear ${selected.id === 2 ? "location 01" : "location 02"} to open this territory.`}
              </p>
            )}
            <a className="map-rank-link" href="#/leaderboard">
              View agent leaderboard →
            </a>
          </aside>
        </div>
      )}
    </>
  );
}
