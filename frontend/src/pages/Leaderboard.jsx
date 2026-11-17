export function Leaderboard({ leaders, session, loading }) {
  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">THE AGENTS WHO CRACKED IT</p>
          <h1>
            Leaderboard<span className="accent">.</span>
          </h1>
          <p>Every solved puzzle counts. Make your move up the ranks.</p>
        </div>
        <span className="badge">GLOBAL RANKINGS</span>
      </div>
      <div className="podium">
        {leaders.slice(0, 3).map((agent, i) => (
          <article
            className={`panel podium-card place-${i}`}
            key={agent.username}
          >
            <p className="eyebrow">
              RANK / {String(agent.rank).padStart(2, "0")}
            </p>
            <div className="rank-symbol" aria-hidden="true">
              {i === 0 ? "♛" : "◇"}
            </div>
            <h2>{agent.username}</h2>
            <strong>
              {agent.score} <small>PTS</small>
            </strong>
            <p>{agent.puzzles_solved} puzzles solved</p>
          </article>
        ))}
      </div>
      <section className="panel rankings">
        <div className="section-heading">
          <h2>Agent standings</h2>
          <span className="muted">Best score per puzzle</span>
        </div>
        {loading ? (
          <p role="status">Loading rankings…</p>
        ) : !leaders.length ? (
          <div className="empty">
            No rankings available yet. Complete a puzzle to get started.
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <caption className="sr-only">
                Agents ranked by total puzzle score
              </caption>
              <thead>
                <tr>
                  <th scope="col">Rank</th>
                  <th scope="col">Agent</th>
                  <th scope="col">Puzzles solved</th>
                  <th scope="col">Score</th>
                </tr>
              </thead>
              <tbody>
                {leaders.map((agent) => (
                  <tr
                    className={
                      agent.username === session?.user.username
                        ? "your-row"
                        : ""
                    }
                    key={agent.username}
                  >
                    <td>
                      <span className="rank">
                        {String(agent.rank).padStart(2, "0")}
                      </span>
                    </td>
                    <th scope="row">
                      {agent.username}{" "}
                      {agent.username === session?.user.username && (
                        <span className="badge">YOU</span>
                      )}
                    </th>
                    <td>{agent.puzzles_solved}</td>
                    <td className="score">
                      {agent.score} <small>PTS</small>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  );
}
