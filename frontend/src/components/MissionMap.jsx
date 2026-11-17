const locations = {
  1: { x: 25, y: 80, name: "THE OUTSKIRTS", type: "gate" },
  2: { x: 72, y: 55, name: "THE CHECKPOINT", type: "tower" },
  3: { x: 16, y: 40, name: "CIPHER QUARTER", type: "tower" },
  4: { x: 85, y: 25, name: "SYSTEM DISTRICT", type: "tower" },
  5: { x: 44, y: 16, name: "THE VAULT", type: "vault" },
};
function Landmark({ type }) {
  return (
    <svg viewBox="0 0 100 100" aria-hidden="true" className="landmark">
      <path d="M7 73 50 94 93 73 50 52Z" fill="#183f45" />
      <path d="M7 65 50 86 93 65 50 44Z" fill="#2e6662" stroke="#82b6a1" />
      {type === "vault" ? (
        <>
          <path
            d="M25 62V29L50 15 75 29V62L50 76Z"
            fill="#314663"
            stroke="#b6c5df"
            strokeWidth="2"
          />
          <path d="M50 15V76M25 29 50 43 75 29" fill="none" stroke="#b6c5df" />
          <circle cx="51" cy="55" r="10" fill="#c5f277" />
          <path d="M46 55h10m-5-5v10" stroke="#243f38" strokeWidth="3" />
        </>
      ) : (
        <>
          <path
            d="M30 64V26L50 16 70 26V64L50 74Z"
            fill="#355b68"
            stroke="#a1c5c7"
            strokeWidth="2"
          />
          <path d="M50 16V74M30 26 50 36 70 26" fill="none" stroke="#a1c5c7" />
          <path
            d="M37 40v8m0 6v8m22-22v8m0 6v8"
            stroke="#c5f277"
            strokeWidth="4"
          />
          {type === "gate" && (
            <path
              d="M16 63V43L30 36M70 36 84 43V63"
              fill="none"
              stroke="#91b9be"
              strokeWidth="5"
            />
          )}
        </>
      )}
    </svg>
  );
}
export function MissionMap({ missions, progress, selectedId, onSelect }) {
  const firstComplete =
    progress?.missions.find((m) => m.mission_id === 1)?.status === "completed";
  const secondComplete =
    progress?.missions.find((m) => m.mission_id === 2)?.status === "completed";
  return (
    <section className="world-map" aria-label="Interactive mission map">
      <div className="map-caption">
        <span>THE SILENT CITY</span>
        <small>SELECT A LOCATION TO EXPLORE</small>
      </div>
      <div className="map-canvas">
        <svg
          className="terrain"
          viewBox="0 0 680 800"
          preserveAspectRatio="none"
          aria-hidden="true"
        >
          <defs>
            <pattern
              id="map-grid"
              width="40"
              height="40"
              patternUnits="userSpaceOnUse"
            >
              <path
                d="M40 0H0V40"
                fill="none"
                stroke="#62b4ab"
                strokeOpacity=".07"
              />
            </pattern>
            <pattern
              id="city-blocks"
              width="40"
              height="40"
              patternTransform="rotate(-25)"
              patternUnits="userSpaceOnUse"
            >
              <rect
                width="23"
                height="27"
                x="4"
                y="4"
                fill="#23474b"
                stroke="#518179"
                strokeOpacity=".3"
              />
            </pattern>
            <linearGradient id="island-fill" x2="0.8" y2="1">
              <stop stopColor="#2e5954" />
              <stop offset="1" stopColor="#172f3b" />
            </linearGradient>
          </defs>
          <rect width="680" height="800" fill="url(#map-grid)" />
          <path
            d="M110 693 52 600 75 491 35 417 111 283 166 257 176 154 287 61 411 76 454 146 576 147 628 247 586 350 634 433 564 553 467 573 413 699 282 751Z"
            fill="#081f2a"
            stroke="#3b918d"
            strokeOpacity=".3"
            strokeWidth="20"
          />
          <path
            d="M110 680 52 587 75 478 35 404 111 270 166 244 176 141 287 48 411 63 454 133 576 134 628 234 586 337 634 420 564 540 467 560 413 686 282 738Z"
            fill="url(#island-fill)"
            stroke="#588e79"
            strokeWidth="3"
          />
          <path
            d="M110 680 52 587 75 478 35 404 111 270 166 244 176 141 287 48 411 63 454 133 576 134 628 234 586 337 634 420 564 540 467 560 413 686 282 738Z"
            fill="url(#city-blocks)"
            opacity=".65"
          />
          <path
            d="M80 520Q230 470 270 340T610 300"
            fill="none"
            stroke="#0b2936"
            strokeWidth="32"
          />
          <path
            d="M80 520Q230 470 270 340T610 300"
            fill="none"
            stroke="#4f8b89"
            strokeOpacity=".35"
            strokeWidth="2"
          />
          <path
            d="M170 640C120 520 435 610 490 440S240 340 299 128"
            className="map-road-shadow"
          />
          <path
            d="M170 640C120 520 435 610 490 440S240 340 299 128"
            className="map-road"
          />
          <path
            d="M170 640C120 520 435 610 490 440"
            className={`map-road ${firstComplete ? "cleared" : "pending"}`}
          />
          <path
            d="M490 440C545 270 240 340 299 128"
            className={`map-road ${secondComplete ? "cleared" : "pending"}`}
          />
          <path d="M320 350 109 320M410 270 578 200" className="future-road" />
          <g fill="#6cbaa0" opacity=".5">
            <path d="m90 560 12-22 12 22Z" />
            <path d="m100 580 12-22 12 22Z" />
            <path d="m365 610 12-22 12 22Z" />
            <path d="m385 625 12-22 12 22Z" />
            <path d="m490 185 12-22 12 22Z" />
          </g>
        </svg>
        {missions.map((m) => {
          const point = locations[m.id];
          if (!point) return null;
          const saved = progress?.missions.find((p) => p.mission_id === m.id),
            state = !m.is_mvp ? "future" : saved?.status || "locked";
          return (
            <button
              key={m.id}
              style={{ left: `${point.x}%`, top: `${point.y}%` }}
              className={`map-node ${state} ${selectedId === m.id ? "selected" : ""}`}
              aria-pressed={selectedId === m.id}
              aria-label={`Location ${String(m.mission_order).padStart(2, "0")}: ${m.title}, ${state.replaceAll("_", " ")}`}
              onClick={() => onSelect(m.id)}
            >
              <span className="node-marker">
                {state === "completed"
                  ? "✓"
                  : state === "locked" || state === "future"
                    ? "◇"
                    : String(m.mission_order).padStart(2, "0")}
              </span>
              <Landmark type={point.type} />
              <span className="node-title">{point.name}</span>
              <span className="node-state">
                {state === "future"
                  ? "COMING SOON"
                  : state === "locked"
                    ? "LOCKED"
                    : state === "completed"
                      ? "CLEARED"
                      : state === "in_progress"
                        ? "RESUME"
                        : "ENTER TERRITORY"}
              </span>
            </button>
          );
        })}
        <span className="map-watermark" aria-hidden="true">
          N<br />↑
        </span>
      </div>
      <div className="map-legend">
        <span>
          <i className="legend-ready" />
          Available
        </span>
        <span>
          <i className="legend-complete" />
          Cleared
        </span>
        <span>
          <i />
          Locked / future
        </span>
      </div>
    </section>
  );
}
