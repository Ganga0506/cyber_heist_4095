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
  const [hints, setHints] = useState(0);
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
        if (result.attempt.unlocked_mission_ids.length)
          setNotice("Mission complete. Your next mission is now unlocked.");
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
            <p>
              {report.error ||
                (report.passed
                  ? "All tests passed."
                  : "Review the test results and try again.")}
            </p>
            {report.cases.map((test, index) => (
              <div className="evidence" key={index}>
                <div>
                  Test {index + 1} · {test.passed ? "Passed" : "Needs work"}
                </div>
                <pre>{`Input     ${JSON.stringify(test.inputs)}\nExpected  ${JSON.stringify(test.expected)}\n${test.error ? `Error     ${test.error}` : `Output    ${JSON.stringify(test.output)}`}`}</pre>
              </div>
            ))}
            {report.attempt?.points_awarded > 0 && (
              <p>+{report.attempt.points_awarded} points earned.</p>
            )}
          </>
        )}
      </div>
      {hints > 0 && (
        <ol>
          {lesson.hints.slice(0, hints).map((hint) => (
            <li key={hint}>{hint}</li>
          ))}
        </ol>
      )}
      {hints < lesson.hints.length && (
        <button type="button" onClick={() => setHints(hints + 1)}>
          Show {hints ? "next " : ""}hint
        </button>
      )}
      {solved && <p className="solved-message">{lesson.recap}</p>}
    </div>
  );
}
