export function AuthPage({ register, onSubmit, busy, session }) {
  if (session)
    return (
      <section className="empty panel">
        <h1>You’re signed in.</h1>
        <p>Your next mission is waiting.</p>
        <a className="button primary" href="#/">
          Go to mission control ↗
        </a>
      </section>
    );
  return (
    <div className="auth-layout">
      <section className="auth-story">
        <p className="eyebrow">RESTRICTED ACCESS / AGENTS ONLY</p>
        <h1>
          Your identity.
          <br />
          Your operation.
          <br />
          <span className="accent">Your heist.</span>
        </h1>
        <p>
          Decode the clues. Follow the trail. Build your reputation, one solved
          puzzle at a time.
        </p>
        <div className="auth-facts">
          <span>01 — Establish your identity</span>
          <span>02 — Unlock the mission trail</span>
          <span>03 — Make the leaderboard</span>
        </div>
      </section>
      <section className="panel auth-panel">
        <span className="brand-mark">CH</span>
        <h2>{register ? "Become an agent" : "Welcome back, agent"}</h2>
        <p>
          {register
            ? "Create an account to save your progress."
            : "Sign in to pick up where you left off."}
        </p>
        {import.meta.env.VITE_GOOGLE_SIGN_IN === "1" && (
          <a className="button" href="/api/auth/google/start">
            Sign in with Google
          </a>
        )}
        {!register && import.meta.env.VITE_PASSWORD_RECOVERY === "1" && (
          <p>
            <a href="#/recover-password">Forgot your password?</a>
          </p>
        )}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            onSubmit(
              Object.fromEntries(new FormData(e.currentTarget)),
              register,
            );
          }}
          aria-busy={busy}
        >
          <label htmlFor="username">Agent username</label>
          <input
            id="username"
            name="username"
            required
            minLength={register ? 3 : 1}
            maxLength={32}
            autoComplete="username"
            placeholder="e.g. shadow.agent"
            aria-describedby={register ? "account-help" : undefined}
          />
          {register && (
            <>
              <label htmlFor="email">Email address</label>
              <input
                id="email"
                name="email"
                type="email"
                required
                maxLength={254}
                autoComplete="email"
                placeholder="you@example.com"
              />
            </>
          )}
          <label htmlFor="password">Password</label>
          <input
            id="password"
            name="password"
            type="password"
            required
            minLength={register ? 12 : 1}
            maxLength={128}
            autoComplete={register ? "new-password" : "current-password"}
            aria-describedby={register ? "account-help" : undefined}
          />
          {register && (
            <small id="account-help">
              Username: 3–32 letters, numbers, dots, underscores or hyphens.
              Password: at least 12 characters.
            </small>
          )}
          {!register && (
            <details>
              <summary>Use an authenticator or backup code</summary>
              <label htmlFor="mfa-code">Authenticator or backup code</label>
              <input
                id="mfa-code"
                name="mfa_code"
                type="text"
                maxLength={32}
                autoComplete="one-time-code"
              />
            </details>
          )}
          <button className="primary" disabled={busy}>
            {busy
              ? "Connecting…"
              : register
                ? "Create account & enter"
                : "Enter the operation"}{" "}
            ↗
          </button>
        </form>
        <p className="auth-switch">
          {register ? "Already an agent?" : "New to the operation?"}{" "}
          <a href={register ? "#/login" : "#/register"}>
            {register ? "Log in" : "Create account"}
          </a>
        </p>
        {!register && import.meta.env.DEV && (
          <details>
            <summary>Try the demo account</summary>
            <p>
              Username: <strong>nova.agent</strong>
              <br />
              Password: <strong>dev-only-nova</strong>
            </p>
          </details>
        )}
      </section>
    </div>
  );
}
