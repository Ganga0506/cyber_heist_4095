import { CoinAmount } from "./CoinAmount";
import { useState } from "react";
import { api } from "../api";

export function CodeLesson({
  puzzle,
  code,
  onEdit,
  solved,
  token,
  busy,
  perform,
  refresh,
  setNotice,
}) {
  const { lesson } = puzzle;
  const [report, setReport] = useState(null);
  const [saved, setSaved] = useState(false);
  function edit(value) {
    onEdit(value);
    setReport(null);
    setSaved(false);
  }

  async function run(action) {
    await perform(async () => {
      const result = await api(`/puzzles/${puzzle.id}/code`, {
        token,
        method: "POST",
        body: { action, code },
      });
      setSaved(true);
      setReport(action === "save" ? null : result);
      if (result.attempt) {
        await refresh(token);
        if (
          result.attempt.coins_awarded > 0 ||
          result.attempt.unlocked_mission_ids.length
        ) {
          const reward = result.attempt.coins_awarded;
          setNotice(
            <span>
              {result.attempt.unlocked_mission_ids.length
                ? "Mission complete. Your next mission is now unlocked."
                : "Puzzle cleared!"}
              {reward > 0 && (
                <>
                  {" "}
                  <CoinAmount amount={reward} reward />
                </>
              )}
            </span>,
          );
        }
      }
    });
  }

  return (
    <div className="code-lesson">
      <p>
        <strong>{lesson.concept}</strong>
      </p>
      <p>{lesson.objective}</p>
      <p>{lesson.explanation}</p>
      <label htmlFor="lesson-code">Python expression</label>
      <p id="console-help" className="muted">
        Enter an expression. The test results show the value it returns for each
        input.
      </p>
      <textarea
        id="lesson-code"
        value={code}
        onChange={(event) => edit(event.target.value)}
        maxLength={512}
        rows={4}
        spellCheck={false}
        autoCapitalize="off"
        autoComplete="off"
        disabled={busy}
        aria-describedby="console-help"
      />
      <div className="actions">
        <button
          type="button"
          onClick={() => run("run")}
          disabled={busy || !code.trim()}
        >
          Run tests
        </button>
        {!solved && (
          <button
            type="button"
            className="primary"
            onClick={() => run("submit")}
            disabled={busy || !code.trim()}
          >
            Submit code
          </button>
        )}
        <button type="button" onClick={() => run("save")} disabled={busy}>
          Save draft
        </button>
        {solved && (
          <button
            type="button"
            onClick={() => edit(lesson.starter)}
            disabled={busy}
          >
            Replay from starter
          </button>
        )}
      </div>
      <div role="status">
        {saved && <p className="save-note">Draft saved.</p>}
        {report && (
          <>
            <h3>Test results</h3>
            <p>
              <strong>
                {report.status === "blocked"
                  ? "Blocked by console safety rules"
                  : report.status === "syntax_error"
                    ? "Python syntax error"
                    : `${report.cases.filter((test) => test.passed).length} of ${report.cases.length} visible tests passed`}
              </strong>
            </p>
            <p>
              {report.error ||
                (report.passed
                  ? "All tests passed."
                  : "Review the test results and try again.")}
            </p>
            {report.cases.map((test, index) => (
              <div className="evidence" key={index}>
                <div>
                  Test {index + 1} ·{" "}
                  {test.status === "skipped"
                    ? "Skipped"
                    : test.error
                      ? "Evaluation error"
                      : test.passed
                        ? "Passed"
                        : "Failed"}
                </div>
                <pre>{`Input     ${JSON.stringify(test.inputs)}\nExpected  ${JSON.stringify(test.expected)}\n${test.status === "skipped" ? "Output    Skipped before evaluation" : test.error ? `Error     ${test.error}` : `Output    ${JSON.stringify(test.output)}`}`}</pre>
              </div>
            ))}
            {report.attempt?.is_correct && <p>Puzzle solved.</p>}
          </>
        )}
      </div>
      {solved && <p className="solved-message">{lesson.recap}</p>}
    </div>
  );
}
