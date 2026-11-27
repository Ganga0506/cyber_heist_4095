import { useEffect, useRef, useState } from "react";
import { api } from "./api";
import { Layout } from "./components/Layout";
import { Dashboard } from "./pages/Dashboard";
import { AuthPage } from "./pages/AuthPage";
import { MissionPage } from "./pages/MissionPage";
import { Leaderboard } from "./pages/Leaderboard";
import { WelcomePage } from "./pages/WelcomePage";
import { RecoveryPage } from "./pages/RecoveryPage";
import { SecurityPage } from "./pages/SecurityPage";
import "./App.css";
const readRoute = () => window.location.hash.slice(1) || "/";
export default function App() {
  const [route, setRoute] = useState(readRoute),
    [session, setSession] = useState(null),
    [missions, setMissions] = useState([]),
    [leaders, setLeaders] = useState([]),
    [progress, setProgress] = useState(null),
    [busy, setBusy] = useState(false),
    [loading, setLoading] = useState(true),
    [online, setOnline] = useState(false),
    [error, setError] = useState(""),
    [notice, setNotice] = useState("");
  const heading = useRef(null),
    token = session?.access_token;
  const previousRoute = useRef(route);
  const googleExchangeStarted = useRef(false);
  useEffect(() => {
    const update = () => setRoute(readRoute());
    window.addEventListener("hashchange", update);
    return () => window.removeEventListener("hashchange", update);
  }, []);
  useEffect(() => {
    if (previousRoute.current !== route) heading.current?.focus();
    previousRoute.current = route;
    window.scrollTo(0, 0);
    document.title = `${route === "/leaderboard" ? "Leaderboard" : route.startsWith("/missions/") ? "Mission" : route === "/login" ? "Login" : route === "/register" ? "Create account" : "Mission control"} · Cyber Heist`;
  }, [route]);
  function clearSession() {
    setSession(null);
    setProgress(null);
    setMissions([]);
    setLeaders([]);
  }
  async function refresh(accessToken = token) {
    if (!accessToken) {
      const health = await api("/health");
      setOnline(health.status === "ok");
      return;
    }
    const [list, scores, health, saved] = await Promise.all([
      api("/missions"),
      api("/leaderboard"),
      api("/health"),
      accessToken
        ? api("/me/progress", { token: accessToken })
        : Promise.resolve(null),
    ]);
    setMissions(list);
    setLeaders(scores.entries);
    setOnline(health.status === "ok");
    setProgress(saved);
  }
  async function perform(action) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await action();
      return true;
    } catch (err) {
      if (err.status === 401 && token) {
        clearSession();
        window.location.hash = "/login";
        setError(
          "Your session expired. Log in again to resume your saved progress.",
        );
      } else {
        if (!err.status) setOnline(false);
        setError(
          !err.status
            ? "Connection lost. Check that the game servers are running, then retry."
            : err.message,
        );
      }
      return false;
    } finally {
      setBusy(false);
    }
  }
  useEffect(() => {
    perform(() => refresh()).finally(() => setLoading(false));
  }, []);
  useEffect(() => {
    if (route !== "/google" || googleExchangeStarted.current) return;
    googleExchangeStarted.current = true;
    perform(async () => {
      const result = await api("/auth/google/session", { method: "POST" });
      setSession(result);
      await refresh(result.access_token);
    }).then((ok) => {
      window.location.hash = ok ? "/" : "/google-error";
    });
  }, [route]);
  async function authenticate(fields, register) {
    return perform(async () => {
      if (register)
        await api("/auth/register", { method: "POST", body: fields });
      const result = await api("/auth/login", {
        method: "POST",
        body: {
          username: fields.username,
          password: fields.password,
          ...(fields.mfa_code ? { mfa_code: fields.mfa_code } : {}),
        },
      });
      setSession(result);
      await refresh(result.access_token);
      setNotice(
        register
          ? "Account created. Your first mission is ready."
          : `Welcome back, ${result.user.username}.`,
      );
      window.location.hash = "/";
    });
  }
  const match = route.match(/^\/missions\/(\d+)$/);
  const reset = route.match(/^\/reset-password\/([A-Za-z0-9_-]{43})$/);
  let page;
  if (route === "/google") page = <p role="status">Signing in with Google…</p>;
  else if (route === "/google-error")
    page = (
      <section className="empty panel">
        <h1>Google sign-in did not complete</h1>
        <p>Try again or sign in with your existing account.</p>
        <a href="#/login">Back to sign in</a>
      </section>
    );
  else if (route === "/password-updated")
    page = (
      <section className="empty panel">
        <h1>Password updated</h1>
        <a href="#/login">Sign in with your new password</a>
      </section>
    );
  else if (route === "/recover-password" || reset)
    page = (
      <RecoveryPage
        key={route}
        token={reset?.[1]}
        busy={busy}
        perform={perform}
      />
    );
  else if (route === "/login" || route === "/register")
    page = (
      <AuthPage
        key={route}
        register={route === "/register"}
        onSubmit={authenticate}
        busy={busy}
        session={session}
      />
    );
  else if (
    !session &&
    (route === "/leaderboard" || route === "/security" || match)
  )
    page = <AuthPage register={false} onSubmit={authenticate} busy={busy} />;
  else if (route === "/security")
    page = <SecurityPage token={token} busy={busy} perform={perform} />;
  else if (route === "/leaderboard")
    page = (
      <Leaderboard leaders={leaders} session={session} loading={loading} />
    );
  else if (match)
    page = (
      <MissionPage
        key={`${match[1]}-${token || "guest"}`}
        id={Number(match[1])}
        token={token}
        progress={progress}
        busy={busy}
        perform={perform}
        refresh={refresh}
        setNotice={setNotice}
      />
    );
  else if (route === "/")
    page = session ? (
      <Dashboard
        missions={missions}
        progress={progress}
        session={session}
        loading={loading}
      />
    ) : (
      <WelcomePage />
    );
  else
    page = (
      <section className="empty panel">
        <h1>Page not found</h1>
        <a className="button primary" href="#/">
          Return to mission control
        </a>
      </section>
    );
  return (
    <Layout
      route={route}
      session={session}
      progress={progress}
      online={online}
      busy={busy}
      headingRef={heading}
      logout={() =>
        perform(async () => {
          await api("/auth/logout", { token, method: "POST" });
          clearSession();
          window.location.hash = "/login";
        })
      }
    >
      {error && (
        <div className="notice error" role="alert">
          <span>{error}</span>
          <button disabled={busy} onClick={() => perform(() => refresh())}>
            Retry connection
          </button>
        </div>
      )}
      {notice && (
        <div className="notice" role="status">
          {notice}
          <button
            aria-label="Dismiss notification"
            onClick={() => setNotice("")}
          >
            ×
          </button>
        </div>
      )}
      {busy && (
        <div className="working" role="status">
          Syncing operation…
        </div>
      )}
      {page}
    </Layout>
  );
}
