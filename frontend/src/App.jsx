import { useEffect, useState } from "react";
import "./App.css";

// Used only when the API is not running. The live page prefers /api/missions.
const FALLBACK_MISSIONS = [
  {
    mission_order: 1,
    title: "THE SETUP",
    topic: "Encoding and Digital Forensics",
    is_mvp: true,
    puzzle_count: 2,
    description:
      "Investigate fictional leaked files and hidden clues to locate the first access point.",
  },
  {
    mission_order: 2,
    title: "THE PERIMETER",
    topic: "Networking and HTTP",
    is_mvp: true,
    puzzle_count: 2,
    description:
      "Explore a simulated network and read sample web traffic to discover an access key.",
  },
  {
    mission_order: 3,
    title: "THE ENCRYPTION LAYER",
    topic: "Cryptography and Hashing",
    is_mvp: false,
    puzzle_count: 2,
    description:
      "Decode a short cipher and compare a hash prefix to recover a hidden word.",
  },
  {
    mission_order: 4,
    title: "INSIDE THE SYSTEM",
    topic: "Code Analysis and Access Control",
    is_mvp: false,
    puzzle_count: 2,
    description: "Read fictional program logic and a small access policy.",
  },
  {
    mission_order: 5,
    title: "THE FINAL HEIST",
    topic: "Integrated Cybersecurity Challenges",
    is_mvp: true,
    puzzle_count: 2,
    description:
      "Combine tokens from earlier missions in a fictional multi-stage vault puzzle.",
  },
];

const API_BASE = import.meta.env.VITE_API_BASE || "";

export default function App() {
  const [missions, setMissions] = useState(FALLBACK_MISSIONS);
  const [source, setSource] = useState("loading");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    let cancelled = false;

    fetch(`${API_BASE}/api/missions`)
      .then((response) => {
        if (!response.ok) {
          throw new Error("Mission request failed");
        }
        return response.json();
      })
      .then((data) => {
        if (!cancelled && Array.isArray(data) && data.length > 0) {
          setMissions(data);
          setSource("api");
        }
      })
      .catch(() => {
        if (!cancelled) {
          setSource("fallback");
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  function handleBegin() {
    setNotice(
      "Preview only. Login, puzzle play, and score submission are not part of this build yet.",
    );
  }

  const sourceText =
    source === "api"
      ? "Mission list loaded from the local API."
      : source === "fallback"
        ? "Showing the planned mission list. Start the API to load live records."
        : "Loading missions...";

  return (
    <div className="page">
      <header className="hero">
        <p className="eyebrow">CSE 4095 · Agentic Programming · Team 5</p>
        <h1>CYBER HEIST</h1>
        <p className="subtitle">Interactive Hacking Puzzle Game</p>
        <p className="intro">
          Play as a cybersecurity analyst inside a fictional network. Read
          clues, solve short puzzles, and unlock the next mission. Every
          system in the game is simulated. Cyber Heist does not connect to
          real machines.
        </p>
        <button type="button" className="start-button" onClick={handleBegin}>
          Begin Heist (Preview)
        </button>
        {notice ? (
          <p className="notice" role="status">
            {notice}
          </p>
        ) : null}
      </header>

      <main id="missions">
        <div className="section-heading">
          <h2>Five missions</h2>
          <p>
            Gold cards are the three MVP missions: The Setup, The Perimeter,
            and The Final Heist. The other two missions are stored for a later
            version. Unlock rules are not final yet.
          </p>
          <p className="source">{sourceText}</p>
        </div>
        <div className="grid">
          {missions.map((mission) => (
            <article
              key={mission.mission_order}
              className={mission.is_mvp ? "card mvp" : "card"}
            >
              <p className="order">Mission {mission.mission_order}</p>
              <h3>{mission.title}</h3>
              <p>{mission.description}</p>
              <p className="topic">{mission.topic}</p>
              <div className="card-footer">
                <span className={mission.is_mvp ? "badge mvp-badge" : "badge"}>
                  {mission.is_mvp ? "MVP mission" : "Later mission"}
                </span>
                {mission.puzzle_count ? (
                  <span className="puzzle-count">
                    {mission.puzzle_count} demo puzzles
                  </span>
                ) : null}
              </div>
            </article>
          ))}
        </div>
      </main>

      <footer>
        <p>Ganga Nomika Mahesh · Eshita Srivastava · Sushma Meghana Karri</p>
        <p>Simulated training game for CSE 4095. No real systems are targeted.</p>
      </footer>
    </div>
  );
}
