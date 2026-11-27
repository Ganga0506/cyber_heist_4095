import { api } from "../api";
import { CoinAmount } from "./CoinAmount";

export function HintShop({
  puzzleId,
  prices,
  hints,
  coins,
  token,
  busy,
  perform,
  refresh,
}) {
  async function buy(number) {
    await perform(async () => {
      await api(`/puzzles/${puzzleId}/hints/${number}`, {
        token,
        method: "POST",
      });
      await refresh(token);
    });
  }

  return (
    <section className="hint-shop" aria-label="Hint shop">
      <div className="hint-shop-heading">
        <h3>Hint shop</h3>
        <CoinAmount amount={coins} />
      </div>
      <ol className="hint-cards">
        {prices.map((price, index) => {
          const owned = index < hints.length;
          const next = index === hints.length;
          const number = index + 1;
          return (
            <li
              className={owned ? "hint-owned" : next ? "hint-ready" : ""}
              key={number}
            >
              <h4>Hint {number}</h4>
              {owned ? (
                <p>{hints[index]}</p>
              ) : (
                <>
                  <button
                    type="button"
                    disabled={busy || !next || coins < price}
                    aria-label={`Buy hint ${number} for ${price} coins`}
                    onClick={() => buy(number)}
                  >
                    {next ? "Buy" : "Locked"} <CoinAmount amount={price} />
                  </button>
                  {next && coins < price && (
                    <small>Need {price - coins} more coins</small>
                  )}
                </>
              )}
            </li>
          );
        })}
      </ol>
    </section>
  );
}
