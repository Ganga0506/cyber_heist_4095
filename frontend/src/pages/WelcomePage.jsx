export function WelcomePage() {
  return (
    <section className="welcome-page">
      <div className="welcome-copy">
        <p className="eyebrow">A CYBERSECURITY PUZZLE ADVENTURE</p>
        <h1>
          The city holds secrets.
          <br />
          <span className="accent">Crack your way in.</span>
        </h1>
        <p>
          Step into the shadows of a locked-down digital city. Decode hidden
          messages, unravel the clues, and work your way to the vault.
        </p>
        <div className="welcome-actions">
          <a className="button primary" href="#/register">
            Start your heist ↗
          </a>
          <a className="button" href="#/login">
            I already have an account →
          </a>
        </div>
        <div className="welcome-features">
          <span>Decode the evidence</span>
          <span>Unlock new territory</span>
          <span>Climb the ranks</span>
        </div>
      </div>
      <div className="welcome-city" aria-hidden="true">
        <div className="city-moon" />
        <div className="city-building building-1" />
        <div className="city-building building-2" />
        <div className="city-building building-3" />
        <div className="city-building building-4" />
        <div className="city-building building-5" />
        <div className="city-grid" />
        <div className="city-caption">
          THE VAULT IS WAITING.
          <br />
          <span>YOUR STORY STARTS HERE.</span>
        </div>
      </div>
    </section>
  );
}
