import { useState } from "react";
import { api } from "../api";

export function RecoveryPage({ token, busy, perform }) {
  const [submitted, setSubmitted] = useState(false);
  const field = token ? "password" : "email";

  function submit(event) {
    event.preventDefault();
    const value = new FormData(event.currentTarget).get(field);
    perform(async () => {
      await api(`/auth/recovery/${token ? "complete" : "request"}`, {
        method: "POST",
        body: token ? { token, password: value } : { email: value },
      });
      if (token) window.location.replace("#/password-updated");
      else setSubmitted(true);
    });
  }

  return (
    <section className="panel auth-panel">
      <h1>{token ? "Set a new password" : "Recover your password"}</h1>
      {submitted ? (
        <p role="status">
          If an eligible account exists, you’ll receive a recovery email.
        </p>
      ) : (
        <form onSubmit={submit} aria-busy={busy}>
          <label htmlFor={field}>
            {token ? "New password" : "Account email"}
          </label>
          <input
            id={field}
            name={field}
            type={field}
            autoComplete={token ? "new-password" : "email"}
            minLength={token ? 12 : undefined}
            maxLength={token ? 128 : 254}
            required
          />
          <button className="primary" disabled={busy}>
            {token ? "Update password" : "Send recovery email"}
          </button>
        </form>
      )}
      <a href="#/login">Back to sign in</a>
    </section>
  );
}
