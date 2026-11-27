import { useEffect, useRef, useState } from "react";
import { api } from "../api";

export function SecurityPage({ token, busy, perform }) {
  const [status, setStatus] = useState(null);
  const [secret, setSecret] = useState("");
  const [codes, setCodes] = useState([]);
  const didLoad = useRef(false);

  function request(path, options = {}) {
    return api(`/auth/mfa${path}`, { token, ...options });
  }

  function load() {
    return perform(async () => setStatus(await request("")));
  }

  useEffect(() => {
    if (didLoad.current) return;
    didLoad.current = true;
    load();
  }, []);

  function submit(event) {
    event.preventDefault();
    const body = Object.fromEntries(new FormData(event.currentTarget));
    const action = status.enabled ? "disable" : secret ? "confirm" : "start";
    perform(async () => {
      const result = await request(`/${action}`, { method: "POST", body });
      if (action === "start") setSecret(result.secret);
      else {
        setSecret("");
        setCodes(result?.recovery_codes ?? []);
        setStatus({ ...status, enabled: action === "confirm" });
      }
    });
  }

  return (
    <section className="panel auth-panel">
      <h1>Account security</h1>
      {!status ? (
        <button onClick={load} disabled={busy}>
          Load security settings
        </button>
      ) : !status.available ? (
        <p>Authenticator setup is unavailable for this account.</p>
      ) : (
        <>
          <p>
            {status.enabled
              ? "Authenticator enabled."
              : "Add an authenticator to protect password sign-in."}
          </p>
          {codes.length > 0 && (
            <>
              <h2>Save your backup codes</h2>
              <p>
                Store these somewhere private. Each code works once if you lose
                your authenticator.
              </p>
              <ul>
                {codes.map((code) => (
                  <li key={code}>
                    <code>{code}</code>
                  </li>
                ))}
              </ul>
            </>
          )}
          {secret && (
            <p>
              Add a time-based account in your authenticator and enter this
              setup key. <code>{secret}</code>
            </p>
          )}
          <form
            key={status.enabled ? "disable" : secret ? "confirm" : "start"}
            onSubmit={submit}
          >
            {!secret && (
              <>
                <label htmlFor="security-password">Current password</label>
                <input
                  id="security-password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  maxLength={128}
                  required
                />
              </>
            )}
            {(secret || status.enabled) && (
              <>
                <label htmlFor="security-code">
                  {status.enabled
                    ? "Authenticator or backup code"
                    : "Six-digit authenticator code"}
                </label>
                <input
                  id="security-code"
                  name="code"
                  autoComplete="one-time-code"
                  inputMode={secret ? "numeric" : "text"}
                  maxLength={secret ? 6 : 32}
                  required
                />
              </>
            )}
            <button className="primary" disabled={busy}>
              {status.enabled
                ? "Disable authenticator"
                : secret
                  ? "Confirm authenticator"
                  : "Set up authenticator"}
            </button>
          </form>
        </>
      )}
    </section>
  );
}
