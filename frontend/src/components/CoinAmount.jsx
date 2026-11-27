export function CoinAmount({ amount, reward = false }) {
  const value = `${reward ? "+" : ""}${amount}`;
  return (
    <span
      className="coin-amount"
      role="img"
      aria-label={`${value} ${amount === 1 ? "coin" : "coins"}`}
    >
      <span className="coin-icon" aria-hidden="true" />
      <span aria-hidden="true">{value}</span>
    </span>
  );
}
