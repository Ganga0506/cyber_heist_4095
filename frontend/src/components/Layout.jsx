import { CoinAmount } from "./CoinAmount";

export function Layout({
  children,
  route,
  session,
  progress,
  online,
  busy,
  logout,
  headingRef,
}) {
  return (
    <div
      className={`app-shell lobby-shell ${session ? "signed-in" : "public-shell"}`}
    >
      <a
        className="skip-link"
        href="#main-content"
        onClick={(e) => {
          e.preventDefault();
          headingRef.current?.focus();
        }}
      >
        Skip to content
      </a>
      <div className="workspace">
        <header className="lobby-header">
          <a className="brand" href="#/" aria-label="Cyber Heist home">
            <span className="brand-mark">CH</span>
            <span>
              CYBER HEIST<small>THE VAULT CHRONICLES</small>
            </span>
          </a>
          {session ? (
            <>
              <nav aria-label="Main navigation">
                <a
                  href="#/"
                  aria-current={
                    route === "/" || route.startsWith("/missions/")
                      ? "page"
                      : undefined
                  }
                >
                  World map
                </a>
                <a
                  href="#/leaderboard"
                  aria-current={route === "/leaderboard" ? "page" : undefined}
                >
                  Leaderboard
                </a>
              </nav>
              <div className="lobby-account">
                {progress?.coins != null && (
                  <span className="player-score">
                    <CoinAmount amount={progress.coins} />
                  </span>
                )}
                <span className="player-name">{session.user.username}</span>
                {import.meta.env.VITE_MFA === "1" && (
                  <a
                    href="#/security"
                    aria-current={route === "/security" ? "page" : undefined}
                  >
                    Security
                  </a>
                )}
                <button disabled={busy} onClick={logout}>
                  Log out ↗
                </button>
              </div>
            </>
          ) : (
            <nav aria-label="Account navigation">
              <a href="#/login">Log in</a>
              <a className="button primary" href="#/register">
                Create account ↗
              </a>
            </nav>
          )}
        </header>
        <main id="main-content" tabIndex={-1} ref={headingRef}>
          {children}
        </main>
        <footer>
          <span>CYBER HEIST / 4095</span>
          <span className={`connection ${online ? "connected" : ""}`}>
            <i />
            {online ? "Systems online" : "Disconnected"}
          </span>
          <span>Fictional systems. Real problem solving.</span>
        </footer>
      </div>
    </div>
  );
}
